"""NG-PLAN01: valid plan saves must pass the staging request-size guard."""
from pathlib import Path
import re

import pytest


CONFIG = Path(__file__).parents[1] / "deploy/api-staging.planning.hfgok.com.nginx"
MIB = 1024 * 1024


def planning_location():
    blocks = re.findall(r"location\s*=\s*/api/planning-state\s*\{([^{}]*)\}", CONFIG.read_text())
    assert len(blocks) == 1, "Plan saves need one explicit, bounded staging ingress location."
    return blocks[0]


@pytest.mark.parametrize("size,accepted", [
    (1_196_832, True), (1_393_776, True), (6 * MIB, True),
    (8 * MIB, True), (8 * MIB + 1, False),
])
def test_ng_plan01_observed_plan_saves_and_reviewed_boundary(size, accepted):
    match = re.search(r"client_max_body_size\s+(\d+)m\s*;", planning_location())
    assert match
    limit = int(match.group(1)) * MIB
    assert 2 * MIB <= limit <= 8 * MIB, "Keep the allowance limited to the reviewed plan-save budget."
    assert (size <= limit) is accepted


def test_ng_plan01_keeps_proxy_headers_timeouts_and_other_routes():
    block = planning_location()
    for directive in (
        "proxy_pass http://127.0.0.1:8003;", "proxy_http_version 1.1;", "proxy_set_header Host $host;",
        "proxy_set_header X-Real-IP $remote_addr;", "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
        "proxy_set_header X-Forwarded-Proto $scheme;", "proxy_connect_timeout 60s;",
        'proxy_set_header Upgrade $http_upgrade;', 'proxy_set_header Connection "upgrade";',
        "proxy_send_timeout 60s;", "proxy_read_timeout 60s;",
        "proxy_buffering off;", "proxy_request_buffering off;",
    ):
        assert directive in block
    assert "Authorization" not in block and "Access-Control-" not in block
    config = CONFIG.read_text()
    generic = re.search(r"location\s+/\s*\{([^{}]*)\}", config)
    assert generic and "client_max_body_size" not in generic.group(1)
    assert re.search(r"location\s*=\s*/api/order-imports/preview\s*\{[^{}]*client_max_body_size\s+6m;", config)
