"""Cross-platform launcher for agent_base."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
RUNTIME_DIR = ROOT / ".runtime"
NODE_RUNTIME_DIR = RUNTIME_DIR / "node"
NODE_DIST_BASE_URL = "https://nodejs.org/dist"
NODE_FALLBACK_VERSION = "v22.22.2"
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
    npm_command = ensure_npm(selected_os)
    ensure_frontend_dependencies(npm_command)

    env = os.environ.copy()
    env["LLM_PROVIDER"] = selected_provider
    env["PORT"] = env.get("PORT", "8000")
    env["VITE_API_BASE"] = env.get("VITE_API_BASE", "http://127.0.0.1:8000")

    backend = subprocess.Popen([sys.executable, "server.py"], cwd=BACKEND_DIR, env=env)
    frontend = subprocess.Popen([npm_command, "run", "dev"], cwd=FRONTEND_DIR, env=env)

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


def ensure_command(name: str, command: str | None) -> str:
    if not command:
        raise RuntimeError(f"{name} 명령을 찾을 수 없습니다. 설치 후 다시 실행하세요.")
    return command


def ensure_npm(selected_os: str) -> str:
    local_npm = local_npm_path()
    if local_npm.exists():
        print(f"Using project Node.js runtime: {local_npm}")
        return str(local_npm)

    system_npm = shutil.which("npm.cmd" if platform.system().lower().startswith("win") else "npm")
    if system_npm:
        return system_npm

    print("\nnpm을 찾을 수 없습니다.")
    print("프로젝트 내부에 portable Node.js 런타임을 다운로드합니다.")
    install_node_runtime(selected_os)

    local_npm = local_npm_path()
    if not local_npm.exists():
        raise RuntimeError(
            "Node.js 다운로드는 끝났지만 npm 실행 파일을 찾지 못했습니다. "
            "https://nodejs.org 에서 Node.js LTS를 설치한 뒤 다시 실행해주세요."
        )
    return str(local_npm)


def local_npm_path() -> Path:
    if platform.system().lower().startswith("win"):
        return NODE_RUNTIME_DIR / "npm.cmd"
    return NODE_RUNTIME_DIR / "bin" / "npm"


def ensure_frontend_dependencies(npm_command: str) -> None:
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return
    print("\nfrontend dependencies not found. Running npm install...")
    try:
        subprocess.run([npm_command, "install"], cwd=FRONTEND_DIR, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "npm 실행 파일을 찾지 못했습니다. `start.py`를 다시 실행하거나 "
            "Node.js LTS를 설치한 뒤 다시 시도해주세요."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "npm install에 실패했습니다. 인터넷 연결을 확인한 뒤 다시 실행해주세요."
        ) from exc


def install_node_runtime(selected_os: str) -> None:
    system_name = platform.system().lower()
    machine = platform.machine().lower()
    target_os = detect_os()
    if selected_os != target_os and selected_os != "other":
        print(f"선택한 OS는 {selected_os}이지만 현재 실행 환경은 {target_os}로 감지되었습니다.")
        print(f"Node.js는 현재 실행 환경({target_os}) 기준으로 다운로드합니다.")
    node_version = resolve_node_lts_version()
    archive_name = node_archive_name(node_version, target_os, system_name, machine)
    url = f"{NODE_DIST_BASE_URL}/{node_version}/{archive_name}"

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / archive_name
        print(f"Downloading Node.js {node_version}...")
        print(url)
        download_file(url, archive_path)
        print("Extracting Node.js...")
        extracted_root = extract_archive(archive_path, Path(temp_dir))

        if NODE_RUNTIME_DIR.exists():
            shutil.rmtree(NODE_RUNTIME_DIR)
        NODE_RUNTIME_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(extracted_root), str(NODE_RUNTIME_DIR))

    print(f"Node.js runtime ready: {NODE_RUNTIME_DIR}")


def resolve_node_lts_version() -> str:
    try:
        with urllib.request.urlopen(f"{NODE_DIST_BASE_URL}/index.json", timeout=20) as response:
            releases = json.loads(response.read().decode("utf-8"))
        for release in releases:
            if release.get("lts"):
                return str(release["version"])
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        print(f"Node.js LTS 버전 확인 실패, fallback 사용: {exc}")
    return NODE_FALLBACK_VERSION


def node_archive_name(version: str, selected_os: str, system_name: str, machine: str) -> str:
    arch = "arm64" if machine in {"arm64", "aarch64"} else "x64"

    if selected_os == "windows" or system_name.startswith("win"):
        return f"node-{version}-win-{arch}.zip"
    if selected_os == "macos" or system_name == "darwin":
        return f"node-{version}-darwin-{arch}.tar.gz"
    if system_name == "linux":
        return f"node-{version}-linux-{arch}.tar.xz"

    raise RuntimeError(
        "현재 OS용 portable Node.js 자동 다운로드를 지원하지 않습니다. "
        "https://nodejs.org 에서 Node.js LTS를 설치한 뒤 다시 실행해주세요."
    )


def download_file(url: str, target: Path) -> None:
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            with target.open("wb") as file:
                shutil.copyfileobj(response, file)
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Node.js 다운로드에 실패했습니다. 인터넷 연결을 확인하거나 "
            "https://nodejs.org 에서 Node.js LTS를 설치한 뒤 다시 실행해주세요."
        ) from exc


def extract_archive(archive_path: Path, destination: Path) -> Path:
    before = {path.resolve() for path in destination.iterdir()}
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(destination)
    else:
        with tarfile.open(archive_path) as archive:
            archive.extractall(destination)

    after = [path for path in destination.iterdir() if path.resolve() not in before and path.is_dir()]
    if not after:
        raise RuntimeError("Node.js 압축 해제 후 폴더를 찾지 못했습니다.")
    return after[0]


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
