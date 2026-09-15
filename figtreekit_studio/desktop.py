"""
desktop — 原生桌面窗口入口（pywebview）

在原生窗口（macOS 使用 WKWebView）中加载本地服务，应用不再依赖浏览器。
窗口关闭时自动停止 HTTP 服务。
"""

from __future__ import annotations

import socket
import threading


def free_port(host: str = "127.0.0.1") -> int:
    """获取一个可用端口。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _StudioApi:
    """暴露给前端 JS 调用的最小 API（仅桌面窗口模式可用）。"""

    def select_folder(self) -> str:
        """打开原生文件夹选择对话框，返回选中路径；取消/失败返回空字符串。"""
        try:
            import webview
            # 取当前主窗口打开对话框
            window = webview.active_window() or (webview.windows[0] if webview.windows else None)
            if window is None:
                return ""
            selected = window.create_file_dialog(webview.FOLDER_DIALOG)
            # pywebview 返回的是 list 或 str
            if isinstance(selected, list):
                return selected[0] if selected else ""
            return selected or ""
        except Exception:
            return ""


def run_desktop(
    host: str = "127.0.0.1",
    port: int | None = None,
    title: str = "FigTreeKit Studio",
    width: int = 1440,
    height: int = 920,
) -> bool:
    """
    启动本地 HTTP 服务并在原生桌面窗口中打开（阻塞直到窗口关闭）。

    返回 True 表示窗口正常退出；False 表示 pywebview 不可用（调用方可回退浏览器模式）。
    """
    try:
        import webview  # pywebview
    except Exception:
        return False

    from figtreekit_studio.server import create_server

    if port is None:
        port = free_port(host)

    server = create_server(host, port)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    url = f"http://{host}:{port}"
    print(f"[FigTreeKit Studio] {url}")
    try:
        window = webview.create_window(
            title, url, width=width, height=height, min_size=(1080, 680),
            js_api=_StudioApi(),
        )
        webview.start()
    except Exception as e:
        # 运行期异常（如 webview.start 失败）应返回 False 以触发回退
        import sys
        print(f"[FigTreeKit Studio] pywebview 运行失败: {e}", file=sys.stderr)
        return False
    finally:
        server.shutdown()
        server.server_close()
    return True
