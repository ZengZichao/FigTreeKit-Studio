"""
py2app setup — 将 FigTreeKit Studio 打包为 macOS .app 应用（PyInstaller 之外的备选方案）。

用法:
    python setup_py2app.py py2app          # 构建 .app
    python setup_py2app.py py2app --alias  # 开发用 alias 模式（不复制依赖）

构建结果位于 dist/figtreekit-studio.app
（推荐主路径: pyinstaller "FigTreeKit Studio.spec"）
"""

from setuptools import setup

APP = ["figtreekit_studio/__main__.py"]

DATA_FILES = [
    # JAR 放到 figtreekit_studio/data/ 下，与 renderer.locate_jar() 的查找路径一致
    ("figtreekit_studio/data", ["figtreekit_studio/data/figtree_patched.jar"]),
    ("figtreekit_studio/static", [
        "figtreekit_studio/static/index.html",
        "figtreekit_studio/static/app.js",
        "figtreekit_studio/static/style.css",
        "figtreekit_studio/static/logo.svg",
    ]),
    ("", ["assets/icon.icns"]),
]

# 应用元数据
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "FigTreeKit Studio",
        "CFBundleDisplayName": "FigTreeKit Studio",
        "CFBundleIdentifier": "com.zengzichao.figtreekit-studio",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleIconFile": "icon.icns",
        "NSHumanReadableCopyright": "Copyright 2026 Zeng Zichao, GPL-2.0-or-later",
        "LSBackgroundOnly": False,
        "LSMinimumSystemVersion": "10.15",
        "NSRequiresAquaSystemAppearance": False,  # 支持深色模式
        "NSHighResolutionCapable": True,
    },
    "packages": [
        "figtreekit_studio",
        "figtreekit",
        "Bio",         # biopython
        "webview",     # pywebview（原生桌面窗口）
    ],
    "includes": [
        "http.server",
        "webbrowser",
        "json",
        "argparse",
        "threading",
        "subprocess",
        "tempfile",
        "base64",
        "shutil",
        "urllib.parse",
        "runpy",
        "webview.platforms.cocoa",
    ],
    "excludes": [
        "tkinter",
        "matplotlib",
        "scipy",
        "pandas",
        "pytest",
        "unittest",
    ],
    "resources": [
        "figtreekit_studio/data",
        "figtreekit_studio/static",
    ],
    "site_packages": True,
    "strip": False,  # 保留调试信息，避免剥离符号
}

setup(
    name="figtreekit-studio",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
