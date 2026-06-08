"""Provider selection for mock and common chat API engines."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_BASE_URL,
    ANTHROPIC_MODEL,
    ANTHROPIC_VERSION,
    GEMINI_API_KEY,
    GEMINI_BASE_URL,
    GEMINI_MODEL,
    LMSTUDIO_API_KEY,
    LMSTUDIO_BASE_URL,
    LMSTUDIO_MODEL,
    OLLAMA_MODEL,
    OLLAMA_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)


@dataclass
class ProviderSettings:
    provider: str
    model: str = ""
    api_key: str = ""
    base_url: str = ""
    anthropic_version: str = ANTHROPIC_VERSION


def call_llm(provider: str, messages: list[dict[str, str]], settings: dict[str, Any] | None = None) -> str:
    resolved = resolve_settings(provider, settings)
    if resolved.provider == "openai":
        return _call_openai_compatible(resolved, messages)
    if resolved.provider == "gemini":
        return _call_gemini(resolved, messages)
    if resolved.provider == "claude":
        return _call_claude(resolved, messages)
    if resolved.provider == "ollama":
        return _call_ollama(resolved, messages)
    if resolved.provider == "lmstudio":
        return _call_openai_compatible(resolved, messages)
    return _call_mock(messages)


def resolve_settings(provider: str, overrides: dict[str, Any] | None = None) -> ProviderSettings:
    value = normalize_provider(provider)
    defaults = {
        "mock": ProviderSettings("mock"),
        "openai": ProviderSettings("openai", OPENAI_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL),
        "gemini": ProviderSettings("gemini", GEMINI_MODEL, GEMINI_API_KEY, GEMINI_BASE_URL),
        "claude": ProviderSettings("claude", ANTHROPIC_MODEL, ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_VERSION),
        "ollama": ProviderSettings("ollama", OLLAMA_MODEL, "", OLLAMA_URL),
        "lmstudio": ProviderSettings("lmstudio", LMSTUDIO_MODEL, LMSTUDIO_API_KEY, LMSTUDIO_BASE_URL),
    }
    resolved = defaults.get(value, defaults["mock"])
    overrides = overrides or {}
    return ProviderSettings(
        provider=resolved.provider,
        model=str(overrides.get("model") or resolved.model).strip(),
        api_key=str(overrides.get("apiKey") or overrides.get("api_key") or resolved.api_key).strip(),
        base_url=str(overrides.get("baseUrl") or overrides.get("base_url") or resolved.base_url).strip().rstrip("/"),
        anthropic_version=str(overrides.get("anthropicVersion") or resolved.anthropic_version).strip(),
    )


def normalize_provider(provider: str) -> str:
    value = (provider or "mock").strip().lower()
    if value == "gemmi":
        return "gemini"
    return value


def provider_status(settings_by_provider: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    settings_by_provider = settings_by_provider or {}
    providers = ["mock", "openai", "gemini", "claude", "ollama", "lmstudio"]
    return [inspect_provider(name, settings_by_provider.get(name) or {}) for name in providers]


def inspect_provider(provider: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = resolve_settings(provider, overrides)
    needs_key = settings.provider in {"openai", "gemini", "claude"}
    has_key = bool(settings.api_key)
    return {
        "provider": settings.provider,
        "model": settings.model,
        "baseUrl": settings.base_url,
        "needsKey": needs_key,
        "hasKey": has_key,
        "ready": settings.provider == "mock" or not needs_key or has_key,
        "message": _status_message(settings, needs_key, has_key),
    }


def _status_message(settings: ProviderSettings, needs_key: bool, has_key: bool) -> str:
    if settings.provider == "mock":
        return "로컬 Mock 응답으로 즉시 사용 가능합니다."
    if needs_key and not has_key:
        return "API Key가 필요합니다. 설정 창 또는 .env에 값을 넣어주세요."
    if settings.provider in {"ollama", "lmstudio"}:
        return "로컬 서버가 실행 중이면 연결 가능합니다."
    return "설정값이 준비되었습니다."


def _call_mock(messages: list[dict[str, str]]) -> str:
    user_text = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    return (
        "Mock chatbot 응답입니다.\n\n"
        "외부 API 없이 전체 요청 파이프라인이 정상 작동합니다.\n\n"
        f"사용자 메시지: {user_text[:500]}"
    )


def _call_openai_compatible(settings: ProviderSettings, messages: list[dict[str, str]]) -> str:
    if settings.provider == "openai" and not settings.api_key:
        return "OpenAI API Key가 없습니다. 설정 창이나 `.env`에 OPENAI_API_KEY를 설정하세요."
    endpoint = f"{settings.base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    payload = {"model": settings.model, "messages": messages, "stream": False}
    data = _post_json(endpoint, payload, headers)
    return _extract_openai_compatible_text(data)


def _call_gemini(settings: ProviderSettings, messages: list[dict[str, str]]) -> str:
    if not settings.api_key:
        return "Gemini API Key가 없습니다. 설정 창이나 `.env`에 GEMINI_API_KEY를 설정하세요."
    endpoint = f"{settings.base_url}/models/{settings.model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": settings.api_key}
    contents = []
    system_parts = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            system_parts.append({"text": content})
            continue
        contents.append({"role": "model" if role == "assistant" else "user", "parts": [{"text": content}]})
    payload: dict[str, Any] = {"contents": contents}
    if system_parts:
        payload["systemInstruction"] = {"parts": system_parts}
    data = _post_json(endpoint, payload, headers)
    return _extract_gemini_text(data)


def _call_claude(settings: ProviderSettings, messages: list[dict[str, str]]) -> str:
    if not settings.api_key:
        return "Claude API Key가 없습니다. 설정 창이나 `.env`에 ANTHROPIC_API_KEY를 설정하세요."
    endpoint = f"{settings.base_url}/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.api_key,
        "anthropic-version": settings.anthropic_version,
    }
    system_text = "\n\n".join(message["content"] for message in messages if message.get("role") == "system")
    chat_messages = [
        {"role": message.get("role"), "content": message.get("content", "")}
        for message in messages
        if message.get("role") in {"user", "assistant"}
    ]
    payload: dict[str, Any] = {"model": settings.model, "max_tokens": 1024, "messages": chat_messages}
    if system_text:
        payload["system"] = system_text
    data = _post_json(endpoint, payload, headers)
    return _extract_claude_text(data)


def _call_ollama(settings: ProviderSettings, messages: list[dict[str, str]]) -> str:
    payload = {"model": settings.model, "messages": messages, "stream": False}
    data = _post_json(settings.base_url, payload, {"Content-Type": "application/json"}, timeout=60)
    return data.get("message", {}).get("content", "") or "Ollama 응답이 비어 있습니다."


def _post_json(endpoint: str, payload: dict[str, Any], headers: dict[str, str], timeout: int = 45) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:800]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"연결할 수 없습니다: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("응답 시간이 초과되었습니다.") from exc


def _extract_openai_compatible_text(data: dict[str, Any]) -> str:
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return f"응답 형식을 해석하지 못했습니다: {json.dumps(data, ensure_ascii=False)[:800]}"


def _extract_gemini_text(data: dict[str, Any]) -> str:
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "\n".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError):
        return f"Gemini 응답 형식을 해석하지 못했습니다: {json.dumps(data, ensure_ascii=False)[:800]}"


def _extract_claude_text(data: dict[str, Any]) -> str:
    try:
        return "\n".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text").strip()
    except AttributeError:
        return f"Claude 응답 형식을 해석하지 못했습니다: {json.dumps(data, ensure_ascii=False)[:800]}"
