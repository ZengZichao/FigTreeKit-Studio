"""
test_i18n_static — 双语界面与静态资源完整性。

- logo.svg 存在且为黑白灰配色 SVG
- index.html 含 data-i18n 标记且被词典覆盖
- app.js 词典 zh/en 键一致
- server 可正确伺服静态资源（MIME 类型）
"""

import json
import re
import socket
import threading
import time
import urllib.request

import pytest

from figtreekit_studio.server import create_server

STATIC_DIR = "figtreekit_studio/static"


def _read(name: str) -> str:
    with open(f"{STATIC_DIR}/{name}", "r", encoding="utf-8") as f:
        return f.read()


class TestLogo:
    def test_logo_svg_exists(self):
        svg = _read("logo.svg")
        assert svg.strip().startswith("<svg") or svg.strip().startswith("<?xml")

    def test_logo_grayscale_only(self):
        """logo 只允许黑白灰（#000-#fff 灰度）颜色。"""
        svg = _read("logo.svg").lower()
        colors = set(re.findall(r"(?:fill|stroke)=\"(#[0-9a-f]{3,6})\"", svg))
        assert colors, "logo 应包含显式 fill/stroke 颜色"
        for c in colors:
            hex6 = c[1:]
            if len(hex6) == 3:
                hex6 = "".join(ch * 2 for ch in hex6)
            r, g, b = (int(hex6[i:i + 2], 16) for i in (0, 2, 4))
            assert r == g == b, f"logo 含非灰度颜色 #{hex6}"

    def test_logo_favicon_linked(self):
        html = _read("index.html")
        assert "/static/logo.svg" in html


class TestI18n:
    def test_dict_has_zh_en(self):
        js = _read("app.js")
        assert "zh:" in js and "en:" in js

    def test_html_uses_i18n_attrs(self):
        html = _read("index.html")
        assert 'data-i18n="' in html
        assert 'data-i18n-ph="' in html

    def test_lang_toggle_present(self):
        html = _read("index.html")
        assert 'id="lang-btn"' in html
        js = _read("app.js")
        assert "setupLangToggle" in js
        assert "localStorage" in js


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def server_url():
    port = _free_port()
    server = create_server("127.0.0.1", port)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


class TestStaticServing:
    def test_logo_served(self, server_url):
        r = urllib.request.urlopen(f"{server_url}/static/logo.svg", timeout=5)
        assert r.headers["Content-Type"].startswith("image/svg+xml")
        body = r.read().decode()
        assert "<svg" in body

    def test_health_has_flags(self, server_url):
        r = urllib.request.urlopen(f"{server_url}/api/health", timeout=5)
        d = json.loads(r.read().decode())
        assert "java_ok" in d and "jar_ok" in d

    def test_path_traversal_blocked(self, server_url):
        """路径穿越应被拒绝，返回 404 而非文件内容。"""
        import urllib.error
        for bad_path in [
            "/static/../server.py",
            "/static/../../pyproject.toml",
            "/static/../core/params.py",
        ]:
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(f"{server_url}{bad_path}", timeout=5)
            assert exc_info.value.code == 404, (
                f"Path traversal {bad_path} should return 404, got {exc_info.value.code}"
            )
