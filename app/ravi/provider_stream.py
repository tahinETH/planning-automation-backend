"""Bounded DeepSeek SSE assembly. Reasoning and tool arguments never reach the browser."""
import json

import httpx

from ..config import settings
from .tools import definitions


async def provider_stream(client: httpx.AsyncClient, messages: list[dict], allow_tools: bool):
    body = {"model": settings.deepseek_model, "messages": messages, "max_tokens": 2400,
            "thinking": {"type": "disabled"}, "stream": True}
    if allow_tools:
        body["tools"] = definitions()
    content, reasoning, calls = "", "", {}
    finish = None
    total = 0
    async with client.stream("POST", "https://api.deepseek.com/chat/completions", json=body,
                             headers={"Authorization": f"Bearer {settings.deepseek_api_key}"}) as response:
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
            reasoning += delta.get("reasoning_content") or ""
            if len(content) > 12000 or len(reasoning) > 30000:
                raise ValueError("Provider output too large")
            if text:
                yield {"type": "delta", "text": text}
            for part in delta.get("tool_calls") or []:
                index = part["index"]
                if not isinstance(index, int) or not 0 <= index < 16:
                    raise ValueError("Invalid tool index")
                call = calls.setdefault(index, {"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                call["id"] += part.get("id") or ""
                function = part.get("function") or {}
                for key in ("name", "arguments"):
                    call["function"][key] += function.get(key) or ""
                if len(call["id"]) > 200 or len(call["function"]["name"]) > 100 or len(call["function"]["arguments"]) > 4000:
                    raise ValueError("Tool arguments too large")
    raise ValueError("Provider disconnected before completion")
