# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置 — FigTreeKit Studio (.app)
#
# 构建:  .venv-build/bin/pyinstaller "FigTreeKit Studio.spec" --noconfirm --clean
# 产物:  dist/FigTreeKit Studio.app

a = Analysis(
    ['figtreekit_studio/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('figtreekit_studio/static', 'figtreekit_studio/static'),
        ('figtreekit_studio/data', 'figtreekit_studio/data'),
    ],
    # webview.platforms.cocoa: pywebview 按平台动态导入，需要显式声明
    # figtreekit: 仅在函数内 import + runpy 动态执行，需要显式声明
    # figtreekit.__main__: runpy.run_module 需要，PyInstaller 默认不打包包级 __main__
    hiddenimports=['webview.platforms.cocoa', 'figtreekit', 'figtreekit.__main__', 'PIL', 'PIL.Image'],
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
        'CFBundleShortVersionString': '0.1.1',
        'CFBundleVersion': '0.1.1',
        'NSHumanReadableCopyright': 'Copyright 2026 Zeng Zichao, GPL-2.0-or-later',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
        # WKWebView 加载本机回环服务（http://127.0.0.1）
        'NSAppTransportSecurity': {'NSAllowsLocalNetworking': True},
    },
)
