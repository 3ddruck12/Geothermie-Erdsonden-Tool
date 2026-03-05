# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File für Geothermie Erdsondentool
Erzeugt eine Standalone-Anwendung mit allen Abhängigkeiten
"""
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# tkintermapview vollständig einbinden (Quellcode + Daten + Submodule)
tkmap_datas, tkmap_binaries, tkmap_hiddenimports = collect_all('tkintermapview')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=tkmap_binaries,
    datas=[
        ('import', 'import'),
        ('Icons', 'Icons'),
        ('data', 'data'),
        ('gui', 'gui'),
        ('parsers', 'parsers'),
        ('calculations', 'calculations'),
        ('utils', 'utils'),
    ] + tkmap_datas,
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
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        # Internes Karten-Widget (try/except → PyInstaller findet es nicht selbst)
        'gui.map_widget',
        # Interne Berechnungsmodule
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
    ] + tkmap_hiddenimports,
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
    icon='Icons/icon.ico' if os.path.exists('Icons/icon.ico') else None,
)
