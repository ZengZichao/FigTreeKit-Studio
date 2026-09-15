"""
test_e2e_smoke — 端到端冒烟测试。

启动 server → POST /api/generate → 验证返回合法 PNG base64 且 ok=true。
"""

import json
import socket
import threading
import time
import urllib.request
import pytest
from figtreekit_studio.server import create_server


SIMPLE_TREE = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"


def _free_port():
    """获取一个可用端口。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def server_url():
    """启动测试 server。"""
    port = _free_port()
    server = create_server("127.0.0.1", port)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)  # 等 server 起来
    url = f"http://127.0.0.1:{port}"
    yield url
    server.shutdown()
    server.server_close()


class TestHealth:
    def test_health(self, server_url):
        r = urllib.request.urlopen(f"{server_url}/api/health", timeout=5)
        d = json.loads(r.read().decode())
        assert d["ok"] is True
        assert "figtreekit" in d
        assert "jar" in d

    def test_index_page(self, server_url):
        r = urllib.request.urlopen(f"{server_url}/", timeout=5)
        html = r.read().decode()
        assert "FigTreeKit Studio" in html

    def test_static_js(self, server_url):
        r = urllib.request.urlopen(f"{server_url}/static/app.js", timeout=5)
        js = r.read().decode()
        assert "collectParams" in js or "generate" in js


class TestGenerate:
    def test_simple_generate(self, server_url):
        """POST 一个简单 Newick → 返回合法 PNG base64 且 ok=true。"""
        payload = json.dumps({
            "tree_text": SIMPLE_TREE,
            "layout": "rectilinear",
            "tip_labels": "show",
            "width": 800,
            "height": 600,
        }).encode()
        req = urllib.request.Request(
            f"{server_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        r = urllib.request.urlopen(req, timeout=60)
        d = json.loads(r.read().decode())
        assert d["ok"] is True, f"Expected ok, error: {d.get('error')}"
        assert d["image"].startswith("data:image/png;base64,")
        assert len(d["image"]) > 1000  # base64 足够长
        assert "figtreekit" in d["command"]
        assert "java -jar" in d["command"]
        assert d["config_json"]  # 非空

    def test_empty_tree(self, server_url):
        """空树文本应返回 ok=false。"""
        payload = json.dumps({"tree_text": ""}).encode()
        req = urllib.request.Request(
            f"{server_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        r = urllib.request.urlopen(req, timeout=10)
        d = json.loads(r.read().decode())
        assert d["ok"] is False
        assert d["error"]

    def test_polar_layout(self, server_url):
        """极坐标布局。"""
        payload = json.dumps({
            "tree_text": SIMPLE_TREE,
            "layout": "polar",
            "tip_labels": "hide",
            "auto_color_rank": "phylum",
            "scale_axis": "show",
            "bg_color": "#FAFAFA",
            "branch_width": 2.0,
            "width": 800,
            "height": 800,
        }).encode()
        req = urllib.request.Request(
            f"{server_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        r = urllib.request.urlopen(req, timeout=60)
        d = json.loads(r.read().decode())
        assert d["ok"] is True, f"Error: {d.get('error')}"
        assert "POLAR" in d["config_json"]

    def test_404(self, server_url):
        """未知路径应 404。"""
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{server_url}/nonexistent", timeout=5)

    def test_curvature_null_returns_structured_error(self, server_url):
        """curvature=null 不应导致空响应，应返回结构化错误。"""
        payload = json.dumps({
            "tree_text": SIMPLE_TREE,
            "curvature": None,
        }).encode()
        req = urllib.request.Request(
            f"{server_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        r = urllib.request.urlopen(req, timeout=60)
        d = json.loads(r.read().decode())
        # curvature=null → 不传 --curvature → 正常生成（不应崩溃）
        assert d["ok"] is True, f"curvature=null should not crash: {d.get('error')}"

    def test_internal_error_returns_structured_response(self, server_url):
        """异常输入不应导致空响应，应返回结构化错误。"""
        payload = json.dumps({
            "tree_text": SIMPLE_TREE,
            "render_format": "INVALID_FORMAT",
        }).encode()
        req = urllib.request.Request(
            f"{server_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        r = urllib.request.urlopen(req, timeout=60)
        d = json.loads(r.read().decode())
        assert d["ok"] is False
        assert d.get("error_key") or d.get("error")
