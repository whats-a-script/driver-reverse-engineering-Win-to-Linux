# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — AstraForge GUI (v1.0)
# Build: pyinstaller AstraForgeGUI.spec

block_cipher = None

a = Analysis(
    ['AstraForgeGUI.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('diff_engine.py', '.'),
        ('normalize_linux.py', '.'),
        ('normalize_windows.py', '.'),
    ],
    hiddenimports=[
        'AstraForge',
        'config',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='AstraForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
)
