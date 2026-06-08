"""Tiny keyword retriever limited to backend/docs/knowledge."""

from __future__ import annotations

import re
from pathlib import Path


def search_knowledge(knowledge_dir: Path, query: str, limit: int = 2) -> list[str]:
    if not knowledge_dir.exists():
        return []

    words = {word.lower() for word in re.findall(r"[A-Za-z_가-힣:]+", query) if len(word) > 1}
    scored: list[tuple[int, str, str]] = []

    for path in knowledge_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        lower_text = text.lower()
        score = sum(1 for word in words if word in lower_text)
        if score > 0:
            snippet = text[:900].strip()
            scored.append((score, path.name, snippet))

    scored.sort(reverse=True)
    return [f"[{name}]\n{snippet}" for _, name, snippet in scored[:limit]]

