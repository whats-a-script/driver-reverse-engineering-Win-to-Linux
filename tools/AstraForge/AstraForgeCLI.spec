# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — AstraForge CLI (v1.0)
# Build: pyinstaller AstraForgeCLI.spec

block_cipher = None

a = Analysis(
    ['AstraForge.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('diff_engine.py', '.'),
        ('normalize_linux.py', '.'),
        ('normalize_windows.py', '.'),
    ],
    hiddenimports=[
        'config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AstraForgeCLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
)
