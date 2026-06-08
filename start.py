"""Cross-platform launcher for agent_base."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
PROVIDERS = ("mock", "openai", "gemini", "claude", "ollama", "lmstudio")
OS_OPTIONS = ("windows", "macos", "other")


def main() -> int:
    parser = argparse.ArgumentParser(description="Start agent_base backend and React GUI.")
    parser.add_argument("--os", choices=OS_OPTIONS, help="Target OS label for setup guidance.")
    parser.add_argument("--provider", choices=PROVIDERS, help="LLM engine to use.")
    parser.add_argument("--yes", action="store_true", help="Use detected OS and mock provider without prompts.")
    args = parser.parse_args()

    selected_os = args.os or detect_os()
    selected_provider = args.provider or "mock"

    if not args.yes and sys.stdin.isatty():
        selected_os = ask_choice("OS", OS_OPTIONS, selected_os)
        selected_provider = ask_choice("Engine", PROVIDERS, selected_provider)

    print(f"\nagent_base starting for OS={selected_os}, engine={selected_provider}")
    ensure_command("python", sys.executable)
    ensure_command("npm", shutil.which("npm"))
    ensure_frontend_dependencies()

    env = os.environ.copy()
    env["LLM_PROVIDER"] = selected_provider
    env["PORT"] = env.get("PORT", "8000")
    env["VITE_API_BASE"] = env.get("VITE_API_BASE", "http://127.0.0.1:8000")

    backend = subprocess.Popen([sys.executable, "server.py"], cwd=BACKEND_DIR, env=env)
    frontend = subprocess.Popen(["npm", "run", "dev"], cwd=FRONTEND_DIR, env=env)

    print("\nBackend: http://127.0.0.1:8000")
    print("GUI:     http://127.0.0.1:5173")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            backend_code = backend.poll()
            frontend_code = frontend.poll()
            if backend_code is not None:
                return backend_code
            if frontend_code is not None:
                return frontend_code
            backend.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        return main_loop(backend, frontend)
    except KeyboardInterrupt:
        print("\nStopping agent_base...")
        stop_process(backend)
        stop_process(frontend)
        return 0


def main_loop(backend: subprocess.Popen, frontend: subprocess.Popen) -> int:
    try:
        while True:
            backend_code = backend.poll()
            frontend_code = frontend.poll()
            if backend_code is not None:
                return backend_code
            if frontend_code is not None:
                return frontend_code
            import time

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping agent_base...")
        stop_process(backend)
        stop_process(frontend)
        return 0


def detect_os() -> str:
    name = platform.system().lower()
    if "windows" in name:
        return "windows"
    if "darwin" in name:
        return "macos"
    return "other"


def ask_choice(label: str, choices: tuple[str, ...], default: str) -> str:
    display = "/".join(choices)
    value = input(f"{label} 선택 [{display}] 기본={default}: ").strip().lower()
    if not value:
        return default
    if value not in choices:
        print(f"지원하지 않는 값입니다. 기본값 {default}를 사용합니다.")
        return default
    return value


def ensure_command(name: str, command: str | None) -> None:
    if not command:
        raise RuntimeError(f"{name} 명령을 찾을 수 없습니다. 설치 후 다시 실행하세요.")


def ensure_frontend_dependencies() -> None:
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return
    print("\nfrontend dependencies not found. Running npm install...")
    subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True)


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
