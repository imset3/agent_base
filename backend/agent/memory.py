"""Small in-memory conversation history and markdown note storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Memory:
    max_messages: int = 8
    messages: list[dict[str, str]] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def clear(self) -> None:
        self.messages.clear()

    def recent(self) -> list[dict[str, str]]:
        return list(self.messages)


def append_note(notes_file: Path, text: str) -> str:
    notes_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with notes_file.open("a", encoding="utf-8") as file:
        file.write(f"\n## {timestamp}\n{text.strip()}\n")
    return "메모를 저장했습니다."

