"""Safe local tools used by the agent."""

from __future__ import annotations

from pathlib import Path


BLOCKED_PARTS = {".env", ".git", "__pycache__", "node_modules", ".venv", "venv"}


def _resolve_safe_path(base_dir: Path, user_path: str) -> Path:
    target = (base_dir / user_path).resolve()
    base = base_dir.resolve()
    if base not in target.parents and target != base:
        raise ValueError("프로젝트 폴더 밖의 경로는 읽을 수 없습니다.")
    if any(part in BLOCKED_PARTS or part.startswith(".") for part in target.parts):
        raise ValueError("숨김 파일이나 민감 파일은 읽을 수 없습니다.")
    return target


def read_text_file(base_dir: Path, user_path: str, max_chars: int = 6000) -> str:
    target = _resolve_safe_path(base_dir, user_path)
    if not target.is_file():
        return "파일을 찾을 수 없습니다."
    text = target.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n...내용이 길어서 일부만 표시했습니다."
    return text


def list_files(base_dir: Path, user_path: str = ".") -> list[str]:
    target = _resolve_safe_path(base_dir, user_path)
    if not target.exists():
        return []
    if target.is_file():
        return [str(target.relative_to(base_dir))]
    results: list[str] = []
    for child in sorted(target.iterdir()):
        if child.name.startswith(".") or child.name in BLOCKED_PARTS:
            continue
        suffix = "/" if child.is_dir() else ""
        results.append(f"{child.relative_to(base_dir)}{suffix}")
    return results

