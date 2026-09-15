"""
server — HTTP 服务（标准库 http.server）

路由：
  GET  /                 → 静态 index.html
  GET  /static/<file>    → 静态资源 (app.js, style.css)
  GET  /api/health       → {ok, figtreekit, jar, java}
  POST /api/generate     → {ok, image, command, config_json, error}
"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from figtreekit_studio.core.generator import generate_nex
from figtreekit_studio.core.renderer import render, locate_jar, check_java
from figtreekit_studio.core.exporter import export_cli, export_config
from figtreekit_studio.core.params import ParamSpec


# --------------------------------------------------------------------------- #
# 静态资源路径
# --------------------------------------------------------------------------- #
_HERE = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(_HERE, "static")

_MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".json": "application/json; charset=utf-8",
    ".gif": "image/gif",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


def _read_static(filename: str) -> tuple[bytes, str]:
    """读取 static 目录下的文件，返回 (content, mime)。拒绝目录穿越。"""
    base = os.path.realpath(STATIC_DIR)
    # 规范化路径并校验最终路径仍位于 STATIC_DIR 之内
    path = os.path.realpath(os.path.join(base, filename))
    if path != base and not path.startswith(base + os.sep):
        return b"", ""
    if not os.path.isfile(path):
        return b"", ""
    with open(path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(path)[1]
    mime = _MIME_TYPES.get(ext, "application/octet-stream")
    return data, mime


# --------------------------------------------------------------------------- #
# HTTP Handler
# --------------------------------------------------------------------------- #
class StudioHandler(BaseHTTPRequestHandler):

    def _send(self, code: int, body: bytes | str, ctype: str = "application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self'",
        )
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, obj: dict):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    # --- GET ---
    def do_GET(self):
        path = urlparse(self.path).path

        if path in ("/", "/index.html"):
            data, mime = _read_static("index.html")
            if data:
                self._send(200, data, mime)
            else:
                self._send(404, "index.html not found", "text/plain")
            return

        if path.startswith("/static/"):
            filename = path[len("/static/"):]
            data, mime = _read_static(filename)
            if data:
                self._send(200, data, mime)
            else:
                self._send(404, "not found", "text/plain")
            return

        if path == "/api/health":
            self._send_json(200, _health_check())
            return

        self._send(404, json.dumps({"ok": False, "error": "not found"}))

    # --- POST ---
    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/api/generate":
            self._send_json(404, {"ok": False, "error": "not found"})
            return

        # 请求体大小上限（20 MB），防止内存耗尽
        MAX_BODY = 20 * 1024 * 1024
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > MAX_BODY:
                self._send_json(413, {"ok": False, "error": "request body too large"})
                return
            raw = self.rfile.read(n) if n else b"{}"
            params_dict = json.loads(raw.decode("utf-8") or "{}")
        except Exception as e:
            self._send_json(400, {"ok": False, "error": f"bad request: {e}"})
            return

        try:
            result = _handle_generate(params_dict)
        except Exception as e:
            result = {
                "ok": False, "image": None, "command": "", "config_json": "",
                "error": f"{type(e).__name__}: {e}",
                "error_key": "internal_error",
                "error_detail": f"{type(e).__name__}: {e}",
            }
        self._send_json(200, result)

    # 静音默认日志
    def log_message(self, format, *args):
        pass


# --------------------------------------------------------------------------- #
# 业务逻辑
# --------------------------------------------------------------------------- #
def _health_check() -> dict:
    jar = locate_jar()
    java_ok, java_ver = check_java()
    try:
        import figtreekit
        ftk_path = os.path.dirname(os.path.abspath(figtreekit.__file__))
    except Exception:
        ftk_path = "(not found)"
    return {
        "ok": True,
        "figtreekit": ftk_path,
        "jar": jar or "(not found)",
        "jar_ok": bool(jar),
        "java": java_ver if java_ok else "(not available)",
        "java_ok": bool(java_ok),
    }


def _handle_generate(params_dict: dict) -> dict:
    """完整生成流程：generator → renderer → exporter。"""
    params = ParamSpec.from_dict(params_dict)
    work_dir = None

    try:
        # 1) 生成 .nex
        gen = generate_nex(params)
        work_dir = gen.work_dir or None
        if not gen.ok:
            return {
                "ok": False, "image": None, "command": "", "config_json": "",
                "error": gen.error,
                "error_key": gen.error_key, "error_detail": gen.error_detail,
            }

        # 2) 渲染图片
        rend = render(
            gen.nex_path,
            fmt=params.render_format or "PNG",
            width=params.width or 1600,
            height=params.height or 1000,
        )
        if not rend.ok:
            return {
                "ok": False, "image": None, "command": "", "config_json": "",
                "error": rend.error,
                "error_key": rend.error_key, "error_detail": rend.error_detail,
            }

        # 3) 导出 CLI 命令与 JSON 配置
        command = export_cli(params)
        config_json = export_config(params)

        return {
            "ok": True,
            "image": rend.image,
            "command": command,
            "config_json": config_json,
            "error": "",
        }
    finally:
        # 生成后清理临时工作目录（图片已转 base64 返回，无需保留）
        if work_dir:
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 启动
# --------------------------------------------------------------------------- #
def create_server(host: str = "127.0.0.1", port: int = 8777) -> ThreadingHTTPServer:
    """创建 ThreadingHTTPServer 实例。"""
    return ThreadingHTTPServer((host, port), StudioHandler)


def serve(host: str = "127.0.0.1", port: int = 8777):
    """启动 HTTP 服务（阻塞）。port=0 时由系统分配并打印实际端口。"""
    server = create_server(host, port)
    port = server.server_address[1]
    print(f"[FigTreeKit Studio] http://{host}:{port}")
    print(f"[FigTreeKit Studio] static  = {STATIC_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[FigTreeKit Studio] shutting down...")
    finally:
        server.server_close()
