# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File für Geothermie Erdsondentool
Erzeugt eine Standalone-Anwendung mit allen Abhängigkeiten
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pipe.txt', '.'),
        ('EED_4_example_files', 'EED_4_example_files'),
        ('data', 'data'),
        ('gui', 'gui'),
        ('parsers', 'parsers'),
        ('calculations', 'calculations'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'matplotlib.backends.backend_tkagg',
        'scipy',
        'numpy',
        'pandas',
        'reportlab',
        'requests',
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
    name='GeothermieErdsondentool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI-Anwendung, kein Konsolen-Fenster
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

