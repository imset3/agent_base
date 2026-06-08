"""Runtime configuration for the backend."""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIST_DIR = PROJECT_DIR / "frontend" / "dist"
DATA_DIR = BASE_DIR / "data"
NOTES_FILE = DATA_DIR / "notes.md"
KNOWLEDGE_DIR = BASE_DIR / "docs" / "knowledge"

APP_NAME = "agent_base"
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "mock").strip().lower() or "mock"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

ALLOWED_PROVIDERS = {"mock", "openai", "ollama"}

