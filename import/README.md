# Import-Ordner

Dieser Ordner enthält alle Dateien, die für den Import in das Geothermie Erdsondentool verwendet werden.

## Struktur

```
import/
├── pipe.txt              # Rohrtypen-Datenbank (61 Typen)
└── eed_4_example/        # Beispiel-EED-Dateien für Import
    ├── EED_4_SFH-DE.dat
    ├── EED_4_SFH-SE.dat
    ├── EED_4_OFFICE-S.dat
    └── ...
```

## Dateien

### `pipe.txt`
Rohrtypen-Datenbank mit 61 verschiedenen Rohrtypen. Wird automatisch beim Start geladen, wenn keine benutzerdefinierte Rohrdatei angegeben ist.

### `eed_4_example/`
Beispiel-EED-Dateien im EED-Format (Version 4) für verschiedene Gebäudetypen:
- **SFH**: Einfamilienhäuser (Deutschland, Schweden, Griechenland)
- **OFFICE**: Bürogebäude (Small, Large)
- Verschiedene Lastprofile (SMHI, SVEBY)

Diese Dateien können über `Datei → EED .dat laden` importiert werden.

