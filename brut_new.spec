# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

hidden_imports = collect_submodules('your_package_name')  # Replace 'your_package_name' if needed

a = Analysis(
    ['brut_new.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.'), ('aadhaar_config.json', '.'), ('models', 'models'), ('unprocessed_files', 'unprocessed_files')],
    hiddenimports=hidden_imports,
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
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Masking_Utility',
    debug=False,
    bootloader_ignore_signals=False,
    runtime_tmpdir=None,
    console=True,
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
    name='Masking_Utility'
)
