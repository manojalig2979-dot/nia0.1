# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['nia_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('config.example.json', '.'), ('nia_avatar.jpg', '.'), ('nia_bot.html', '.'), ('3d-agent', '3d-agent'), ('mouth_frames', 'mouth_frames')],
    hiddenimports=['PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineCore'],
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
    a.binaries,
    a.datas,
    [],
    name='NiaAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['nia_icon.ico'],
)
