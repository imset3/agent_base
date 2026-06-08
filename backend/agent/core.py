"""Core chatbot behavior for the API and optional terminal use."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.llm import call_llm, normalize_provider
from agent.memory import Memory, append_note
from agent.prompts import SYSTEM_PROMPT
from agent.retriever import search_knowledge
from agent.tools import list_files, read_text_file
from config import ALLOWED_PROVIDERS, BASE_DIR, DEFAULT_PROVIDER, KNOWLEDGE_DIR, NOTES_FILE


@dataclass
class AgentResponse:
    answer: str
    provider: str
    references: list[str]


class AgentCore:
    def __init__(self) -> None:
        self.memory = Memory()

    def respond(
        self,
        message: str,
        provider: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> AgentResponse:
        selected_provider = self._normalize_provider(provider)
        message = message.strip()
        if not message:
            return AgentResponse("메시지를 입력해주세요.", selected_provider, [])

        command_answer = self._handle_command(message)
        if command_answer:
            return AgentResponse(command_answer, selected_provider, [])

        references = search_knowledge(KNOWLEDGE_DIR, message)
        messages = self._build_messages(message, references)

        try:
            answer = call_llm(selected_provider, messages, settings)
        except Exception as exc:
            answer = f"{selected_provider} 호출 중 오류가 발생했습니다: {exc}"

        self.memory.add("user", message)
        self.memory.add("assistant", answer)
        return AgentResponse(answer=answer, provider=selected_provider, references=references)

    def _normalize_provider(self, provider: str | None) -> str:
        value = normalize_provider(provider or DEFAULT_PROVIDER)
        if value not in {normalize_provider(item) for item in ALLOWED_PROVIDERS}:
            return "mock"
        return value

    def _handle_command(self, message: str) -> str | None:
        if message == "/help":
            return "\n".join(
                [
                    "사용 가능한 명령어",
                    "- /help: 도움말 보기",
                    "- /clear: 대화 기록 초기화",
                    "- /note 저장할 내용: data/notes.md에 메모 저장",
                    "- /read backend/docs/knowledge/chatbot_base.md: 안전한 파일 읽기",
                    "- /files backend/docs/knowledge: 파일 목록 보기",
                ]
            )
        if message == "/clear":
            self.memory.clear()
            return "대화 기록을 초기화했습니다."
        if message.startswith("/note "):
            return append_note(NOTES_FILE, message.removeprefix("/note "))
        if message.startswith("/read "):
            return read_text_file(BASE_DIR.parent, message.removeprefix("/read ").strip())
        if message.startswith("/files"):
            path = message.removeprefix("/files").strip() or "."
            files = list_files(BASE_DIR.parent, path)
            return "\n".join(files) if files else "표시할 파일이 없습니다."
        return None

    def _build_messages(self, user_message: str, references: list[str]) -> list[dict[str, str]]:
        context = "\n\n".join(references)
        system_prompt = SYSTEM_PROMPT
        if context:
            system_prompt = f"{SYSTEM_PROMPT}\n\nReference snippets:\n{context}"
        return [
            {"role": "system", "content": system_prompt},
            *self.memory.recent(),
            {"role": "user", "content": user_message},
        ]
