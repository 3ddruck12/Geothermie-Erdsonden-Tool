# Testing-Ordner

Dieser Ordner enthält alle Test-Dateien und Test-Skripte für das Geothermie Erdsondentool.

## Dateien

- `test_v32.py` - Tests für Version 3.2
- `test_vdi4640_*.py` - Tests für VDI 4640 Berechnungen
- `test_bug_100m_limit.py` - Test für 100m Limit Bugfix
- `VDI4640_*.py` - VDI 4640 Hilfsskripte
- `VDI4640_*.txt` - VDI 4640 Dokumentation

## Ausführen

Tests können mit Python direkt ausgeführt werden:

```bash
cd testing
python3 test_v32.py
```

