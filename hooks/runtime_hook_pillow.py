# PyInstaller Runtime Hook: Pillow-Kompatibilität für tkintermapview
# tkintermapview verwendet Image.ANTIALIAS, das in Pillow 10+ entfernt wurde.
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
except Exception:
    pass
