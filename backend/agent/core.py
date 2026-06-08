"""Core agent behavior for the API and optional terminal use."""

from __future__ import annotations

import ast
from dataclasses import dataclass

from agent.llm import call_llm
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

    def respond(self, message: str, provider: str | None = None) -> AgentResponse:
        selected_provider = self._normalize_provider(provider)
        message = message.strip()
        if not message:
            return AgentResponse("분석할 코드나 질문을 입력해주세요.", selected_provider, [])

        command_answer = self._handle_command(message)
        if command_answer:
            return AgentResponse(command_answer, selected_provider, [])

        references = search_knowledge(KNOWLEDGE_DIR, message)
        analysis = self._analyze_python(message)
        messages = self._build_messages(message, analysis, references)
        answer = call_llm(selected_provider, messages)

        if selected_provider == "mock":
            answer = analysis

        self.memory.add("user", message)
        self.memory.add("assistant", answer)
        return AgentResponse(answer=answer, provider=selected_provider, references=references)

    def _normalize_provider(self, provider: str | None) -> str:
        value = (provider or DEFAULT_PROVIDER).strip().lower()
        if value not in ALLOWED_PROVIDERS:
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
                    "- /read backend/docs/knowledge/python_syntax.md: 안전한 파일 읽기",
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

    def _build_messages(self, user_message: str, analysis: str, references: list[str]) -> list[dict[str, str]]:
        context = "\n\n".join(references) if references else "관련 지식 문서를 찾지 못했습니다."
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.memory.recent(),
            {
                "role": "user",
                "content": (
                    f"사용자 입력:\n{user_message}\n\n"
                    f"로컬 문법 분석:\n{analysis}\n\n"
                    f"참고 문서:\n{context}"
                ),
            },
        ]

    def _analyze_python(self, text: str) -> str:
        code = self._extract_code(text)
        if not code:
            return self._explain_plain_question(text)

        try:
            ast.parse(code)
        except SyntaxError as exc:
            return self._format_syntax_error(code, exc)

        return "\n".join(
            [
                "문법 분석 결과",
                "",
                "현재 Mock 분석기로는 Python 문법 오류를 찾지 못했습니다.",
                "",
                "확인할 점",
                "- 실행 중 오류라면 에러 메시지도 함께 붙여 넣어주세요.",
                "- 변수 이름 오타, 파일 경로, 설치되지 않은 패키지는 실행 환경에서 확인해야 합니다.",
            ]
        )

    def _extract_code(self, text: str) -> str:
        stripped = text.strip()
        if "```" in stripped:
            parts = stripped.split("```")
            if len(parts) >= 3:
                code = parts[1]
                if code.startswith("python"):
                    code = code.removeprefix("python")
                return code.strip()
        code_markers = ("def ", "if ", "for ", "while ", "print(", "import ", "class ", "=")
        if "\n" in stripped or any(marker in stripped for marker in code_markers):
            return stripped
        return ""

    def _format_syntax_error(self, code: str, exc: SyntaxError) -> str:
        line_number = exc.lineno or 1
        line = (code.splitlines() or [""])[line_number - 1] if line_number > 0 else ""
        pointer = " " * max((exc.offset or 1) - 1, 0) + "^"
        reason = self._friendly_reason(exc.msg, line)

        return "\n".join(
            [
                "문법 오류를 찾았습니다.",
                "",
                f"오류 위치: {line_number}번째 줄",
                "",
                "문제 코드:",
                "```python",
                line,
                pointer,
                "```",
                "",
                "오류 원인:",
                reason,
                "",
                "수정 방향:",
                self._suggest_fix(exc.msg, line),
                "",
                "짧은 메모:",
                "if, for, while, def, class처럼 블록을 여는 문장은 끝에 콜론(:)이 필요하고, 다음 줄은 들여쓰기해야 합니다.",
            ]
        )

    def _friendly_reason(self, message: str, line: str) -> str:
        lower = message.lower()
        if "expected ':'" in lower:
            return "조건문, 반복문, 함수 정의처럼 블록을 시작하는 줄 끝에 콜론(:)이 빠졌습니다."
        if "was never closed" in lower or "unexpected eof" in lower:
            return "괄호, 대괄호, 중괄호, 따옴표 중 하나가 닫히지 않았을 가능성이 큽니다."
        if "indent" in lower:
            return "Python은 들여쓰기로 코드 블록을 구분하므로, 필요한 위치의 들여쓰기가 맞지 않습니다."
        if line.count('"') % 2 == 1 or line.count("'") % 2 == 1:
            return "문자열을 여는 따옴표와 닫는 따옴표의 개수가 맞지 않습니다."
        return f"Python 파서가 이 줄을 문법적으로 해석하지 못했습니다. 원본 오류: {message}"

    def _suggest_fix(self, message: str, line: str) -> str:
        lower = message.lower()
        stripped = line.rstrip()
        if "expected ':'" in lower and not stripped.endswith(":"):
            return f"`{stripped}:`처럼 줄 끝에 콜론을 추가해보세요."
        if "indent" in lower:
            return "블록 안에서 실행될 줄을 스페이스 4칸으로 들여쓰기해보세요."
        if "was never closed" in lower:
            return "열린 괄호나 따옴표가 어디서 시작됐는지 보고 같은 종류로 닫아주세요."
        return "오류 줄 바로 앞뒤를 함께 확인하고, 괄호/콜론/따옴표/들여쓰기를 먼저 점검해보세요."

    def _explain_plain_question(self, text: str) -> str:
        return "\n".join(
            [
                "질문을 확인했습니다.",
                "",
                "Mock 모드에서는 Python 코드나 에러 메시지를 넣으면 로컬 규칙으로 먼저 분석합니다.",
                "",
                "예시:",
                "```python",
                "if score >= 60",
                "    print('pass')",
                "```",
                "",
                f"입력한 내용: {text}",
            ]
        )

