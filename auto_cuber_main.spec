# -*- mode: python ; coding: utf-8 -*-

import shutil



a = Analysis(
    ['auto_cuber_main.py',
    'config_manager.py',
    'gui.py',
    'input_automation_controller.py',
'ocr_text_correction_engine.py',
'template_matcher.py',
'window_client_area_capture.py',
'window_manager.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=['./hooks'],
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
    a.zipfiles,
    a.datas,
    [],
    uac_admin=True,
    exclude_binaries=True,
    name='auto_cuber_main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='auto_cuber_main',
)

