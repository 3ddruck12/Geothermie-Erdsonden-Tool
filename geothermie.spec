# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File für Geothermie Erdsondentool
Erzeugt eine Standalone-Anwendung mit allen Abhängigkeiten
"""
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# tkintermapview: nur Submodule (collect_all legt .py als datas → kann Import stören)
tkmap_hidden = collect_submodules('tkintermapview')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('import', 'import'),
        ('Icons', 'Icons'),
        ('data', 'data'),
        ('gui', 'gui'),
        ('parsers', 'parsers'),
        ('calculations', 'calculations'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'matplotlib.backends.backend_tkagg',
        'scipy',
        'scipy.spatial',
        'scipy.interpolate',
        'numpy',
        'pandas',
        'reportlab',
        'reportlab.lib',
        'reportlab.platypus',
        'requests',
        'certifi',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'gui.map_widget',
        'calculations',
        'calculations.thermal',
        'calculations.hydraulics',
        'calculations.borehole',
        'calculations.vdi4640',
        'calculations.g_functions',
        'calculations.borefield_gfunction',
        'calculations.longterm_simulation',
        'calculations.regeneration_analysis',
        'calculations.seasonal_efficiency',
        'utils',
        'utils.validators',
        'utils.version',
        'utils.osm_map',
        'data.load_profiles',
    ] + tkmap_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hooks/runtime_hook_pillow.py'] if os.path.exists('hooks/runtime_hook_pillow.py') else [],
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
    icon='Icons/icon.ico' if os.path.exists('Icons/icon.ico') else None,
)
