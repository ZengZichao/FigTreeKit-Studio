"""
cli — 控制台入口

用法:
  figtreekit-studio                    # 原生桌面窗口（默认，不依赖浏览器）
  figtreekit-studio --browser          # 改用系统浏览器打开
  figtreekit-studio --no-window        # 仅启动服务，不打开任何界面
  figtreekit-studio --port 9000
  python -m figtreekit_studio          # 等效
"""

from __future__ import annotations

import argparse
import http.client
import json
import threading
import time
import webbrowser


def _smoke_test() -> int:
    """打包自检：起服务 → 健康检查 → POST /api/generate → 校验 PNG。

    仅与本进程刚启动的环回服务（固定 127.0.0.1 + OS 分配的整数端口）通信。
    """
    from figtreekit_studio.server import create_server

    server = create_server("127.0.0.1", 0)
    port = int(server.server_address[1])
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=180)

        # --- 健康检查 ---
        conn.request("GET", "/api/health")
        resp = conn.getresponse()
        health = json.loads(resp.read().decode("utf-8"))
        print(f"[smoke] health: java_ok={health.get('java_ok')} jar_ok={health.get('jar_ok')}")
        if not (health.get("java_ok") and health.get("jar_ok")):
            print("[smoke] environment incomplete")
            return 3

        # --- 生成 ---
        body = json.dumps({
            "tree_text": "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);",
            "layout": "rectilinear",
            "tip_labels": "show",
            "width": 600,
            "height": 400,
        })
        conn.request("POST", "/api/generate", body=body,
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        d = json.loads(resp.read().decode("utf-8"))
        conn.close()

        if not d.get("ok"):
            print(f"[smoke] generate FAILED: {d.get('error')}")
            return 2
        if not str(d.get("image", "")).startswith("data:image/png;base64,"):
            print("[smoke] image is not PNG data URI")
            return 2
        print(f"[smoke] generate OK, image {len(d['image'])} chars")
        print("SMOKE TEST PASSED")
        return 0
    finally:
        server.shutdown()
        server.server_close()


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="figtreekit-studio",
        description="FigTreeKit Studio — 可视化调参 + 实时预览 + 可复现脚本导出",
    )
    ap.add_argument("--host", default="127.0.0.1", help="绑定地址 (默认 127.0.0.1)")
    ap.add_argument("--port", type=int, default=None,
                    help="端口 (默认: 桌面模式自动选择, 浏览器模式 8777)")
    ap.add_argument("--browser", action="store_true",
                    help="用系统浏览器打开，而非原生桌面窗口")
    ap.add_argument("--no-window", action="store_true",
                    help="仅启动服务，不打开任何界面")
    ap.add_argument("--no-browser", action="store_true",
                    help="(兼容旧参数) 等价于 --no-window")
    ap.add_argument("--smoke-test", action="store_true",
                    help=argparse.SUPPRESS)  # 打包自检用
    args = ap.parse_args(argv)

    if args.smoke_test:
        raise SystemExit(_smoke_test())

    headless = args.no_window or args.no_browser

    # --- 仅起服务 ---
    if headless:
        from figtreekit_studio.server import serve
        serve(host=args.host, port=args.port if args.port is not None else 8777)
        return

    # --- 浏览器模式 ---
    if args.browser:
        port = args.port if args.port is not None else 8777
        url = f"http://{args.host}:{port}"

        def _open_browser():
            time.sleep(0.8)
            webbrowser.open(url)
        threading.Thread(target=_open_browser, daemon=True).start()

        from figtreekit_studio.server import serve
        serve(host=args.host, port=port)
        return

    # --- 桌面窗口模式（默认，不依赖浏览器）---
    from figtreekit_studio.desktop import run_desktop

    ok = run_desktop(host=args.host, port=args.port)
    if not ok:
        # pywebview 不可用 → 回退浏览器模式
        print("[FigTreeKit Studio] pywebview 不可用，回退到浏览器模式 "
              "(pip install pywebview 可启用原生窗口)")
        port = args.port if args.port is not None else 8777
        url = f"http://{args.host}:{port}"
        threading.Thread(
            target=lambda: (time.sleep(0.8), webbrowser.open(url)), daemon=True
        ).start()
        from figtreekit_studio.server import serve
        serve(host=args.host, port=port)


if __name__ == "__main__":
    main()
