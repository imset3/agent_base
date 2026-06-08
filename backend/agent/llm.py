"""Provider selection for mock, OpenAI, and Ollama engines."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from config import OLLAMA_MODEL, OLLAMA_URL, OPENAI_API_KEY, OPENAI_MODEL


def call_llm(provider: str, messages: list[dict[str, str]]) -> str:
    if provider == "openai":
        return _call_openai(messages)
    if provider == "ollama":
        return _call_ollama(messages)
    return _call_mock(messages)


def _call_mock(messages: list[dict[str, str]]) -> str:
    user_text = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    return (
        "Mock 엔진 응답입니다.\n\n"
        "입력 내용을 확인했고, 실제 모델 연결 없이도 agent 흐름이 정상 작동합니다.\n\n"
        f"최근 질문 요약: {user_text[:160]}"
    )


def _call_openai(messages: list[dict[str, str]]) -> str:
    if not OPENAI_API_KEY:
        return "OpenAI API Key가 없습니다. `.env`에 OPENAI_API_KEY를 설정하거나 mock 엔진을 사용하세요."
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        return "OpenAI 패키지가 설치되어 있지 않습니다. `pip install openai` 후 다시 실행하세요."

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(model=OPENAI_MODEL, messages=messages)
        return response.choices[0].message.content or ""
    except Exception as exc:  # pragma: no cover - provider errors vary by environment.
        return f"OpenAI 호출 중 오류가 발생했습니다: {exc}"


def _call_ollama(messages: list[dict[str, str]]) -> str:
    payload = json.dumps({"model": OLLAMA_MODEL, "messages": messages, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("message", {}).get("content", "") or "Ollama 응답이 비어 있습니다."
    except urllib.error.URLError:
        return "Ollama 서버에 연결할 수 없습니다. Ollama 실행 여부와 모델 설치 상태를 확인하세요."
    except TimeoutError:
        return "Ollama 응답 시간이 초과되었습니다. 더 작은 모델을 사용해보세요."
    except Exception as exc:  # pragma: no cover - provider errors vary by environment.
        return f"Ollama 호출 중 오류가 발생했습니다: {exc}"

