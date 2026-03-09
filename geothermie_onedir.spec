# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File für Geothermie Erdsondentool – ONEDIR Build.
Erzeugt einen Ordner mit allen Abhängigkeiten (für InstallForge Installer).

Verwendung:
    pyinstaller geothermie_onedir.spec
"""
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

block_cipher = None

# tkintermapview Submodule
tkmap_hidden = collect_submodules('tkintermapview')
# geocoder: tkintermapview braucht geocoder für Adress-Lookup
geocoder_hidden = collect_submodules('geocoder')
# PIL: collect_all liefert alle Submodule + Daten
pil_datas, pil_binaries, pil_hidden = collect_all('PIL')
# certifi: CA-Bundle für SSL/HTTPS
certifi_datas = collect_data_files('certifi')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[] + pil_binaries,
    datas=[
        ('import', 'import'),
        ('Icons', 'Icons'),
        ('data', 'data'),
        ('gui', 'gui'),
        ('parsers', 'parsers'),
        ('calculations', 'calculations'),
        ('utils', 'utils'),
        ('locales', 'locales'),
    ] + certifi_datas + pil_datas,
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
        'pyperclip',
        'ratelim',
        'six',
        'future',
        'sqlite3',
        'pygfunction',
        'gui.map_widget',
        'calculations.longterm_simulation',
        'calculations.regeneration_analysis',
        'calculations.seasonal_efficiency',
        'utils.validators',
        'utils.version',
        'utils.osm_map',
        'data.load_profiles',
    ] + tkmap_hidden + geocoder_hidden + pil_hidden,
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
    [],
    exclude_binaries=True,  # ONEDIR: Binaries separat
    name='GeothermieErdsondentool',
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
    icon='Icons/icon.ico' if os.path.exists('Icons/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GeothermieErdsondentool',
)
