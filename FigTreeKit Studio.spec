# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置 — FigTreeKit Studio (.app)
#
# 构建:  .venv-build/bin/pyinstaller "FigTreeKit Studio.spec" --noconfirm --clean
# 产物:  dist/FigTreeKit Studio.app

import importlib.util as _ilu
import os as _os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# PyInstaller locates modules by walking sys.path, which a PEP 660 editable
# install of figtreekit (a .pth + MetaPathFinder pair) does not expose: with
# core installed editable, collect_submodules() lists the names but every
# "Hidden import 'figtreekit._cli' not found" error follows and the frozen app
# dies on the first generation. Resolve the real source directory through
# importlib -- which does understand editable installs -- and hand that
# directory to the analysis as a search path.
_spec = _ilu.find_spec("figtreekit")
_ftk_parent = _os.path.dirname(_os.path.dirname(_spec.origin))

# 0.1.2 起渲染与生成全部下沉到 figtreekit 核心：core/generator.py 在函数内
# `from figtreekit._cli import main`，core/renderer.py 调用
# `figtreekit._renderer` 并把补丁 JAR 的解析交给核心包。hiddenimports 只写
# 包名只会收进 __init__.py，既不含子模块也不含 figtree_patched.jar，
# 冻结包因此会 ModuleNotFoundError / 找不到 JAR。这里显式收全。
_ftk_hidden = collect_submodules("figtreekit")
_ftk_datas = collect_data_files("figtreekit", includes=["*.jar"])
assert any(m.endswith("_cli") for m in _ftk_hidden), (
    "figtreekit 子模块收集为空：核心库未以可导入形式安装在构建环境中")
assert any(f.endswith(".jar") for f, _ in _ftk_datas), (
    "未收集到 figtreekit 的补丁 JAR")

a = Analysis(
    ['figtreekit_studio/__main__.py'],
    pathex=[_ftk_parent],
    binaries=[],
    datas=[
        ('figtreekit_studio/static', 'figtreekit_studio/static'),
        ('figtreekit_studio/data', 'figtreekit_studio/data'),
        *_ftk_datas,
    ],
    # webview.platforms.cocoa: pywebview 按平台动态导入，需要显式声明
    # figtreekit: 仅在函数内 import + runpy 动态执行，需要显式声明
    # figtreekit.__main__: runpy.run_module 需要，PyInstaller 默认不打包包级 __main__
    hiddenimports=['webview.platforms.cocoa', 'PIL', 'PIL.Image'] + _ftk_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FigTreeKit Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='FigTreeKit Studio',
)
app = BUNDLE(
    coll,
    name='FigTreeKit Studio.app',
    icon='assets/icon.icns',
    bundle_identifier='com.zengzichao.figtreekit-studio',
    info_plist={
        'CFBundleDisplayName': 'FigTreeKit Studio',
        'CFBundleName': 'FigTreeKit Studio',
        'CFBundleShortVersionString': '0.1.2',
        'CFBundleVersion': '0.1.2',
        'NSHumanReadableCopyright': 'Copyright 2026 Zeng Zichao, GPL-2.0-or-later',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
        # WKWebView 加载本机回环服务（http://127.0.0.1）
        'NSAppTransportSecurity': {'NSAllowsLocalNetworking': True},
    },
)
