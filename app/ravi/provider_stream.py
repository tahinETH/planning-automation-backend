"""Bounded DeepSeek / OpenRouter SSE assembly. Reasoning and tool arguments never reach the browser."""
import json

import httpx

from ..config import settings
from .tools import definitions

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_exhausted_deepseek_key: str | None = None


def ravi_configured() -> bool:
    return bool(settings.deepseek_api_key or settings.openrouter_api_key)


def openrouter_model(model: str) -> str:
    cleaned = model.strip() or "deepseek-v4-flash"
    return cleaned if "/" in cleaned else f"deepseek/{cleaned}"


def mark_deepseek_exhausted(key: str) -> None:
    global _exhausted_deepseek_key
    if key:
        _exhausted_deepseek_key = key


def reset_provider_fallback() -> None:
    global _exhausted_deepseek_key
    _exhausted_deepseek_key = None


def provider_targets() -> list[tuple[str, str, str, str]]:
    targets: list[tuple[str, str, str, str]] = []
    if settings.deepseek_api_key and not (settings.openrouter_api_key and _exhausted_deepseek_key == settings.deepseek_api_key):
        targets.append(("deepseek", DEEPSEEK_URL, settings.deepseek_api_key, settings.deepseek_model))
    if settings.openrouter_api_key:
        targets.append(("openrouter", OPENROUTER_URL, settings.openrouter_api_key, openrouter_model(settings.deepseek_model)))
    return targets


async def provider_stream(client: httpx.AsyncClient, messages: list[dict], allow_tools: bool):
    targets = provider_targets() or [("deepseek", DEEPSEEK_URL, settings.deepseek_api_key, settings.deepseek_model)]
    for idx, (provider_name, url, api_key, model_name) in enumerate(targets):
        body = {"model": model_name, "messages": messages, "max_tokens": 2400,
                "thinking": {"type": "disabled"}, "stream": True}
        if allow_tools:
            body["tools"] = definitions()
        content, reasoning, calls = "", "", {}
        finish = None
        total = 0
        emitted_delta = False
        try:
            async with client.stream("POST", url, json=body,
                                     headers={"Authorization": f"Bearer {api_key}"}) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    total += len(line)
                    if total > 500000:
                        raise ValueError("Provider stream too large")
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        if finish not in {"stop", "tool_calls"}:
                            raise ValueError("Incomplete provider answer")
                        message = {"role": "assistant", "content": content or None}
                        if calls:
                            message["tool_calls"] = [calls[index] for index in sorted(calls)]
                        if reasoning:
                            message["reasoning_content"] = reasoning
                        yield {"type": "message", "message": message}
                        return
                    chunk = json.loads(data)
                    if chunk.get("error"):
                        raise ValueError("Provider error")
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    choice = choices[0]
                    finish = choice.get("finish_reason") or finish
                    delta = choice.get("delta") or {}
                    text = delta.get("content") or ""
                    if not isinstance(text, str):
                        raise ValueError("Invalid text delta")
                    content += text
                    reasoning += delta.get("reasoning_content") or delta.get("reasoning") or ""
                    if len(content) > 12000 or len(reasoning) > 30000:
                        raise ValueError("Provider output too large")
                    if text:
                        emitted_delta = True
                        yield {"type": "delta", "text": text}
                    for part in delta.get("tool_calls") or []:
                        index = part.get("index", 0)
                        if not isinstance(index, int) or not 0 <= index < 16:
                            raise ValueError("Invalid tool index")
                        call = calls.setdefault(index, {"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                        call["id"] += part.get("id") or ""
                        function = part.get("function") or {}
                        for key in ("name", "arguments"):
                            call["function"][key] += function.get(key) or ""
                        if len(call["id"]) > 200 or len(call["function"]["name"]) > 100 or len(call["function"]["arguments"]) > 4000:
                            raise ValueError("Tool arguments too large")
        except httpx.HTTPError as exc:
            if provider_name == "deepseek" and isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in {401, 402}:
                mark_deepseek_exhausted(api_key)
            if not emitted_delta and idx + 1 < len(targets):
                continue
            raise
        raise ValueError("Provider disconnected before completion")
