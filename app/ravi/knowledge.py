from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import unicodedata

DIRECTORY = Path(__file__).with_name("knowledge")


@lru_cache(maxsize=1)
def catalog() -> dict:
    return json.loads((DIRECTORY / "topics.json").read_text())


@lru_cache(maxsize=1)
def source_map() -> dict:
    return json.loads((DIRECTORY / "source-map.json").read_text())


@lru_cache(maxsize=1)
def version() -> str:
    return hashlib.sha256((DIRECTORY / "topics.json").read_bytes() + (DIRECTORY / "source-map.json").read_bytes()).hexdigest()[:16]


def normalize(value: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", value.lower().replace("ı", "i")) if not unicodedata.combining(char))


def search_topics(query: str, limit: int = 5) -> list[dict]:
    words = set(re.findall(r"\w{3,}", normalize(query)))
    ranked = []
    for topic in catalog()["topics"]:
        heading = normalize(" ".join([topic["id"], topic["title"], *topic["aliases"]]))
        body = normalize(topic["body"])
        score = sum(4 * (word in heading) + (word in body) for word in words)
        if score:
            ranked.append((score, topic))
    return [topic for _, topic in sorted(ranked, key=lambda pair: -pair[0])[:limit]]


def read_topic(topic_id: str) -> dict:
    topic = next((topic for topic in catalog()["topics"] if topic["id"] == topic_id), None)
    if topic is None:
        raise ValueError("Bilinmeyen bilgi başlığı")
    return topic


def navigation_targets(is_admin: bool) -> list[dict]:
    return [target for target in catalog()["navigation"] if is_admin or not target.get("adminOnly")]


def search_source(query: str) -> list[dict]:
    words = set(re.findall(r"[\w-]{3,}", normalize(query)))
    matches = []
    for path, module in source_map()["modules"].items():
        symbols = [symbol for symbol in module["symbols"] if any(word in normalize(symbol["name"]) for word in words)][:12]
        score = sum(word in normalize(path) for word in words) * 8 + len(symbols) * 5
        if any(normalize(symbol["name"]) == normalize(query) for symbol in symbols):
            score += 20
        snippets = []
        if not score and len(query.strip()) >= 4:
            for index, line in enumerate(module["source"].splitlines()):
                if normalize(query) in normalize(line):
                    snippets.append({"line": index + 1, "text": line[:250]})
                    if len(snippets) >= 3:
                        break
            score = len(snippets)
        if score:
            matches.append((score, {"path": path, "lines": module["lines"], "symbols": symbols, "matches": snippets, "dependencies": module["dependencies"], "endpoints": module["endpoints"]}))
    return [match for _, match in sorted(matches, key=lambda pair: -pair[0])[:6]]


def read_source(path: str, start_line: int = 1, line_count: int = 80) -> dict:
    module = source_map()["modules"].get(path)
    if module is None:
        raise ValueError("Kaynak haritasında bu dosya yok")
    if not 1 <= start_line <= module["lines"] or not 1 <= line_count <= 120:
        raise ValueError("Geçerli satır aralığı seçin (en fazla 120 satır)")
    lines = module["source"].splitlines()
    selected = []
    size = 0
    for index in range(start_line - 1, min(len(lines), start_line - 1 + line_count)):
        line = lines[index]
        # A minified JSX line may be larger than the complete result budget.
        selected.append({"line": index + 1, "text": line[:12000], "truncated": len(line) > 12000})
        size += len(selected[-1]["text"])
        if size >= 12000:
            break
    return {"path": path, "sha256": module["sha256"], "totalLines": len(lines), "lines": selected,
            "nextLine": selected[-1]["line"] + 1 if selected and selected[-1]["line"] < len(lines) else None}
