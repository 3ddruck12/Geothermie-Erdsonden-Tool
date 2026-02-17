# Locales – Übersetzungsdateien

Hier werden zukünftig `.po`-Dateien für die Internationalisierung abgelegt.

## Struktur

```
locales/
├── en/
│   └── LC_MESSAGES/
│       ├── get.po
│       └── get.mo
├── fr/
│   └── LC_MESSAGES/
│       └── ...
└── README.md
```

## Übersetzung erstellen

```bash
# .pot-Template extrahieren (zukünftig)
xgettext -o locales/get.pot utils/i18n.py gui/**/*.py

# Neue Sprache anlegen
msginit -i locales/get.pot -o locales/en/LC_MESSAGES/get.po -l en

# Übersetzen, dann kompilieren
msgfmt locales/en/LC_MESSAGES/get.po -o locales/en/LC_MESSAGES/get.mo
```
