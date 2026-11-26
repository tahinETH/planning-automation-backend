"""Bounded DeepSeek / OpenRouter SSE assembly. Reasoning and tool arguments never reach the browser."""
import json
import logging

import httpx

from ..config import settings
from .tools import definitions

logger = logging.getLogger(__name__)

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_exhausted_deepseek_key: str | None = None


class RaviResponseCapError(ValueError):
    """Raised when the provider response hits a length or size ceiling."""


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


def provider_request_body(provider_name: str, model_name: str, messages: list[dict], allow_tools: bool, *, stream: bool) -> dict:
    body: dict = {"model": model_name, "messages": messages, "stream": stream}
    if provider_name == "openrouter":
        body["reasoning"] = {"enabled": False}
    else:
        body["thinking"] = {"type": "disabled"}
    if allow_tools:
        body["tools"] = definitions()
    return body


async def provider_stream(client: httpx.AsyncClient, messages: list[dict], allow_tools: bool):
    targets = provider_targets() or [("deepseek", DEEPSEEK_URL, settings.deepseek_api_key, settings.deepseek_model)]
    for idx, (provider_name, url, api_key, model_name) in enumerate(targets):
        body = provider_request_body(provider_name, model_name, messages, allow_tools, stream=True)
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
                        logger.warning("Ravi stream exceeded raw byte cap (provider=%s, model=%s, total=%d)", provider_name, model_name, total)
                        raise RaviResponseCapError("Provider stream too large")
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    if data == "[DONE]":
                        if finish not in {"stop", "tool_calls"}:
                            logger.warning(
                                "Ravi stream ended with incomplete finish_reason (provider=%s, model=%s, finish=%s, content_len=%d, reasoning_len=%d, tool_calls=%d)",
                                provider_name, model_name, finish, len(content), len(reasoning), len(calls),
                            )
                            if finish == "length":
                                raise RaviResponseCapError("Incomplete provider answer (length)")
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
                        logger.warning("Ravi stream received mid-stream provider error (provider=%s, model=%s, emitted_delta=%s)", provider_name, model_name, emitted_delta)
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
                    reasoning_delta = delta.get("reasoning_content")
                    if not isinstance(reasoning_delta, str):
                        reasoning_delta = delta.get("reasoning")
                    if isinstance(reasoning_delta, str):
                        reasoning += reasoning_delta
                    if len(content) > 12000 or len(reasoning) > 30000:
                        logger.warning(
                            "Ravi stream exceeded output cap (provider=%s, model=%s, content_len=%d, reasoning_len=%d)",
                            provider_name, model_name, len(content), len(reasoning),
                        )
                        raise RaviResponseCapError("Provider output too large")
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
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            if provider_name == "deepseek" and status in {401, 402}:
                mark_deepseek_exhausted(api_key)
            if not emitted_delta and idx + 1 < len(targets):
                logger.warning("Ravi stream provider failed before output; trying fallback (provider=%s, model=%s, status=%s, error=%s)", provider_name, model_name, status, type(exc).__name__)
                continue
            logger.warning("Ravi stream HTTP error (provider=%s, model=%s, status=%s, emitted_delta=%s, error=%s)", provider_name, model_name, status, emitted_delta, type(exc).__name__)
            raise
        logger.warning("Ravi stream closed before [DONE] (provider=%s, model=%s, finish=%s, content_len=%d, emitted_delta=%s)", provider_name, model_name, finish, len(content), emitted_delta)
        raise ValueError("Provider disconnected before completion")
