"""Test the staging template with isolated nginx and a loopback auth stub.

This manual check does not contact an application API or load application data.
It needs an existing nginx binary. All listeners, logs and files are temporary.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlsplit


def probe(port, method, path, size):
    prefix, suffix = b'{"seed":{},"padding":"', b'"}'
    body = prefix + b"x" * (size - len(prefix) - len(suffix)) + suffix
    with socket.create_connection(("127.0.0.1", port), timeout=10) as connection:
        stream = connection.makefile("rb")
        headers = (f"{method} {path} HTTP/1.1\r\nHost: api-staging.planning.hfgok.com\r\n"
                   f"Origin: https://staging.planning.hfgok.com\r\nX-Production-Area: piston\r\n"
                   f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n"
                   "Expect: 100-continue\r\nConnection: close\r\n\r\n")
        connection.sendall(headers.encode())
        sent = False
        while True:
            line = stream.readline().decode().strip()
            if not line: raise RuntimeError("nginx closed before a response")
            status = int(line.split()[1]); response_headers = {}
            while (line := stream.readline()) not in (b"\r\n", b"\n", b""):
                key, value = line.decode().split(":", 1)
                response_headers[key.lower()] = value.strip()
            if status == 100:
                if not sent: connection.sendall(body); sent = True
                continue
            length = int(response_headers.get("content-length", 0))
            if length: stream.read(length)
            return {"method": method, "path": path, "body_bytes": size, "status": status,
                    "allow_origin": response_headers.get("access-control-allow-origin"), "body_sent": sent}


def run(config_path, nginx):
    forwarded = []
    class Upstream(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_PUT(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            forwarded.append({"method": self.command, "path": self.path, "body_bytes": len(body),
                              "area": self.headers.get("X-Production-Area")})
            response = b'{"detail":"Oturum gerekli"}'
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.send_header("Access-Control-Allow-Origin", "https://staging.planning.hfgok.com")
            self.end_headers(); self.wfile.write(response)
        do_POST = do_PUT
    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True); thread.start()
    process = None; results = []
    with tempfile.TemporaryDirectory(prefix="planning-ingress-") as temporary:
        root = Path(temporary)
        try:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
            template = config_path.read_text().replace("listen 80;", f"listen 127.0.0.1:{port};")
            template = template.replace("http://127.0.0.1:8003", f"http://127.0.0.1:{upstream.server_port}")
            assert re.findall(r"\blisten\s+([^;]+);", template) == [f"127.0.0.1:{port}"]
            upstreams = [urlsplit(value.strip()) for value in re.findall(r"\bproxy_pass\s+([^;]+);", template)]
            assert upstreams and all(value.scheme == "http" and value.netloc == f"127.0.0.1:{upstream.server_port}" for value in upstreams)
            assert not re.search(r"\binclude\s+", template), "Only the self-contained loopback template is supported"
            username = pwd.getpwuid(os.getuid()).pw_name
            text = (f"user {username};\nworker_processes 1;\npid {root}/nginx.pid;\n"
                    f"error_log {root}/error.log error;\nevents {{ worker_connections 64; }}\n"
                    f"http {{ access_log off; client_body_temp_path {root}/body; proxy_temp_path {root}/proxy;\n{template}\n}}\n")
            config = root / "nginx.conf"; config.write_text(text)
            command = [nginx, "-p", str(root), "-c", str(config), "-e", str(root / "error.log")]
            subprocess.run([*command, "-t"], check=True, capture_output=True, text=True)
            process = subprocess.Popen([*command, "-g", "daemon off;"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            for _ in range(200):
                if process.poll() is not None: raise RuntimeError(process.stderr.read().decode())
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=.1): break
                except OSError: time.sleep(.025)
            else: raise RuntimeError("Isolated nginx did not start")
            cases = [("PUT", "/api/planning-state", 1_393_776, 401),
                     ("PUT", "/api/planning-state", 6 * 1024 * 1024, 401),
                     ("PUT", "/api/planning-state", 8 * 1024 * 1024, 401),
                     ("PUT", "/api/planning-state", 8 * 1024 * 1024 + 1, 413),
                     ("POST", "/api/order-imports/preview", 2 * 1024 * 1024, 401),
                     ("POST", "/api/scenarios", 1_393_776, 413)]
            for method, path, size, expected in cases:
                row = probe(port, method, path, size); results.append(row)
                assert row["status"] == expected, f"{path}: expected {expected}, got {row['status']} for {size} bytes"
                if expected == 401:
                    assert row["allow_origin"] == "https://staging.planning.hfgok.com"
            assert len(forwarded) == 4 and all(row["area"] == "piston" for row in forwarded)
            return {"passed": True, "cases": results, "forwarded": forwarded,
                    "method": "Isolated nginx on loopback with an auth stub, no application or database access"}
        finally:
            if process:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait()
            upstream.shutdown(); upstream.server_close(); thread.join(timeout=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--nginx", default=shutil.which("nginx"))
    args = parser.parse_args()
    if not args.nginx: raise SystemExit("An existing nginx binary is required for this manual check")
    print(json.dumps(run(args.config, args.nginx), indent=2))
