"""Small HTTP API and static file server for agent_base."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from agent.core import AgentCore
from config import DEFAULT_PROVIDER, FRONTEND_DIST_DIR


agent = AgentCore()


class Handler(BaseHTTPRequestHandler):
    server_version = "agent_base/0.1"

    def do_OPTIONS(self) -> None:
        self._send_empty(204)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send_json({"ok": True, "provider": DEFAULT_PROVIDER})
            return
        self._serve_static()

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self._send_json({"error": "Not found"}, 404)
            return

        try:
            payload = self._read_json()
            message = str(payload.get("message", ""))
            provider = payload.get("provider")
            response = agent.respond(message, provider)
            self._send_json(
                {
                    "answer": response.answer,
                    "provider": response.provider,
                    "references": response.references,
                }
            )
        except Exception as exc:
            self._send_json({"error": f"요청 처리 중 오류가 발생했습니다: {exc}"}, 500)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        if not raw:
            return {}
        return json.loads(raw)

    def _serve_static(self) -> None:
        if not FRONTEND_DIST_DIR.exists():
            self._send_json(
                {
                    "ok": True,
                    "message": "Backend is running. Start the React dev server or run `npm run build`.",
                }
            )
            return

        requested = unquote(self.path.split("?", 1)[0]).lstrip("/")
        target = (FRONTEND_DIST_DIR / requested).resolve() if requested else FRONTEND_DIST_DIR / "index.html"
        dist = FRONTEND_DIST_DIR.resolve()
        if dist not in target.parents and target != dist:
            self._send_empty(403)
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            target = FRONTEND_DIST_DIR / "index.html"

        content_type = self._content_type(target)
        body = target.read_bytes()
        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, status: int) -> None:
        self.send_response(status)
        self._cors_headers()
        self.end_headers()

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _content_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        return {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
        }.get(suffix, "application/octet-stream")


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"agent_base backend running at http://{host}:{port}")
    print(f"LLM_PROVIDER={DEFAULT_PROVIDER}")
    server.serve_forever()


if __name__ == "__main__":
    main()
