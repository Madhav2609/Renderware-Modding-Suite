# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\karti\\Downloads\\Renderware modding suite\\frontend\\main.py'],
    pathex=[],
    binaries=[('C:\\Users\\karti\\Downloads\\Renderware modding suite\\backend\\build\\bin\\Debug\\renderware_backend.exe', 'backend')],
    datas=[],
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'darkdetect'],
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
    name='RenderwareModdingSuite',
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
)
