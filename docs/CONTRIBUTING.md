# 🤝 Beitragen zum Geothermie Erdsondentool

Vielen Dank für dein Interesse, zum Projekt beizutragen! 🎉

## 📋 Inhaltsverzeichnis

- [Code of Conduct](#code-of-conduct)
- [Wie kann ich beitragen?](#wie-kann-ich-beitragen)
- [Entwicklungsumgebung](#entwicklungsumgebung)
- [Branch-Strategie](#branch-strategie)
- [Commit-Richtlinien](#commit-richtlinien)
- [Pull Request Prozess](#pull-request-prozess)
- [Code-Style](#code-style)

---

## Code of Conduct

Dieses Projekt folgt einem Code of Conduct. Durch Teilnahme verpflichtest du dich, diesen einzuhalten.

**Grundsätze:**
- Sei respektvoll und professionell
- Konstruktive Kritik ist willkommen
- Keine Diskriminierung jeglicher Art
- Hilf anderen, zu lernen und zu wachsen

---

## Wie kann ich beitragen?

### 🐛 Bugs melden

Bugs werden als [GitHub Issues](https://github.com/3ddruck12/GeothermieErdsondentool/issues) getracked.

**Vor dem Melden:**
- Überprüfe, ob der Bug bereits gemeldet wurde
- Sammle Informationen über den Bug

**Bug-Report sollte enthalten:**
- **Titel**: Kurze, beschreibende Zusammenfassung
- **Beschreibung**: Was ist passiert? Was sollte passieren?
- **Schritte zur Reproduktion**:
  1. Gehe zu '...'
  2. Klicke auf '...'
  3. Scrolle zu '...'
  4. Siehe Fehler
- **Erwartetes Verhalten**
- **Screenshots** (falls relevant)
- **Umgebung**:
  - OS: [z.B. Ubuntu 22.04, Windows 11]
  - Python Version: [z.B. 3.12]
  - Tool Version: [z.B. 3.0.0]

### 💡 Feature-Vorschläge

Feature-Requests werden ebenfalls als GitHub Issues getracked.

**Feature-Request sollte enthalten:**
- **Titel**: Beschreibender Name des Features
- **Problem**: Welches Problem löst dieses Feature?
- **Lösung**: Beschreibe die gewünschte Lösung
- **Alternativen**: Welche Alternativen hast du erwogen?
- **Zusätzlicher Kontext**: Screenshots, Mockups, etc.

### 🔧 Code beitragen

1. **Fork** das Repository
2. **Clone** deinen Fork
3. **Branch** erstellen (siehe Branch-Strategie)
4. **Änderungen** machen
5. **Testen**
6. **Commit** (siehe Commit-Richtlinien)
7. **Push** zu deinem Fork
8. **Pull Request** öffnen

---

## Entwicklungsumgebung

### Voraussetzungen

- Python 3.12+
- Git
- tkinter (meist mit Python vorinstalliert)

### Setup

```bash
# Repository clonen
git clone https://github.com/3ddruck12/GeothermieErdsondentool.git
cd GeothermieErdsondentool

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Tool starten
python main.py
```

### Testen

```bash
# Modul-Tests
python -m calculations.thermal
python -m data.soil_types
python -m utils.pvgis_api

# GUI-Test
python main.py
```

---

## Branch-Strategie

Wir verwenden **Git Flow**:

### Branches

- `main` - Produktions-Branch (stabil, getestet)
- `dev` - Entwicklungs-Branch (latest features)
- `feature/*` - Feature-Branches
- `bugfix/*` - Bug-Fix-Branches
- `hotfix/*` - Dringende Fixes für main

### Workflow

```bash
# Feature entwickeln
git checkout dev
git pull origin dev
git checkout -b feature/mein-feature

# ... Änderungen machen ...

git add .
git commit -m "feat: Beschreibung"
git push origin feature/mein-feature

# Pull Request zu dev öffnen
```

### Merge-Strategie

- `feature/*` → `dev` - Squash Merge
- `dev` → `main` - Merge Commit
- `hotfix/*` → `main` und `dev` - Merge Commit

---

## Commit-Richtlinien

Wir folgen **Conventional Commits**:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` - Neues Feature
- `fix` - Bug-Fix
- `docs` - Dokumentation
- `style` - Formatierung, Whitespace
- `refactor` - Code-Refactoring
- `test` - Tests hinzufügen
- `chore` - Build, Dependencies

### Beispiele

```bash
# Feature
git commit -m "feat(gui): Info-Buttons hinzugefügt"

# Bug-Fix
git commit -m "fix(calculations): Schenkelabstand-Umrechnung korrigiert"

# Dokumentation
git commit -m "docs(readme): Installation für Windows hinzugefügt"

# Refactoring
git commit -m "refactor(thermal): Multipole-Methode vereinfacht"
```

---

## Pull Request Prozess

### Vor dem PR

- [ ] Code folgt dem Style-Guide
- [ ] Alle Tests laufen durch
- [ ] Dokumentation aktualisiert
- [ ] CHANGELOG.md aktualisiert
- [ ] Branch ist aktuell mit `dev`

### PR erstellen

1. **Titel**: Kurz und beschreibend
2. **Beschreibung**:
   - Was wurde geändert?
   - Warum wurde es geändert?
   - Wie wurde es getestet?
3. **Screenshots** (bei GUI-Änderungen)
4. **Linked Issues**: Schließt #123

### Template

```markdown
## Beschreibung
Kurze Beschreibung der Änderungen

## Art der Änderung
- [ ] Bug-Fix
- [ ] Neues Feature
- [ ] Breaking Change
- [ ] Dokumentation

## Wie wurde getestet?
- [ ] Unit-Tests
- [ ] Manuelle Tests
- [ ] Integration-Tests

## Screenshots (optional)
```

### Review-Prozess

- Mindestens 1 Approval benötigt
- CI/CD muss erfolgreich sein
- Keine Merge-Konflikte

---

## Code-Style

### Python Style Guide

Wir folgen **PEP 8** mit folgenden Ergänzungen:

#### Namenskonventionen

```python
# Module: lowercase_with_underscores
import calculations.thermal

# Klassen: PascalCase
class BoreholeCalculator:
    pass

# Funktionen: lowercase_with_underscores
def calculate_thermal_resistance():
    pass

# Konstanten: UPPERCASE_WITH_UNDERSCORES
MAX_DEPTH = 100

# Variablen: lowercase_with_underscores
pipe_diameter = 0.032
```

#### Docstrings

Alle öffentlichen Funktionen/Klassen benötigen Docstrings:

```python
def calculate_required_depth(
    thermal_conductivity: float,
    heat_load: float
) -> float:
    """
    Berechnet die erforderliche Bohrtiefe.
    
    Args:
        thermal_conductivity: Wärmeleitfähigkeit in W/m·K
        heat_load: Wärmelast in kW
        
    Returns:
        Erforderliche Tiefe in Metern
        
    Raises:
        ValueError: Wenn Parameter negativ sind
        
    Example:
        >>> calculate_required_depth(2.0, 6.0)
        85.5
    """
    if thermal_conductivity <= 0:
        raise ValueError("Wärmeleitfähigkeit muss positiv sein")
    
    return heat_load * 10 / thermal_conductivity
```

#### Type Hints

Verwende Type Hints für Funktion-Signaturen:

```python
from typing import List, Dict, Optional, Tuple

def process_data(
    values: List[float],
    config: Dict[str, str],
    depth: Optional[float] = None
) -> Tuple[float, float]:
    """..."""
    pass
```

#### Imports

```python
# Standard Library
import os
import sys
from typing import List

# Third Party
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk

# Local
from calculations import BoreholeCalculator
from data.soil_types import SoilTypeDB
```

#### Formatierung

- **Zeilenlänge**: Max 100 Zeichen (nicht 79)
- **Einrückung**: 4 Spaces (keine Tabs)
- **Strings**: Doppelte Quotes `"` bevorzugt
- **Trailing Commas**: In Multi-Line

```python
# Gut
data = {
    "name": "Sand",
    "lambda": 1.8,
    "capacity": 2.4,
}

# Schlecht
data = {'name': 'Sand', 'lambda': 1.8, 'capacity': 2.4}
```

---

## Spezifische Bereiche

### GUI-Entwicklung

- Tkinter mit `ttk` für moderne Widgets
- Layouts mit `grid()` bevorzugt
- Trennung von GUI und Logic
- Info-Buttons für alle wichtigen Felder

### Berechnungen

- NumPy für numerische Berechnungen
- SciPy für wissenschaftliche Funktionen
- Dokumentiere Formeln in Docstrings
- Unit-Tests für alle Berechnungen

### Datenbanken

- Verwende `@dataclass` für Datenstrukturen
- Alle Werte mit Einheiten kommentieren
- Quellen angeben (z.B. VDI 4640)

---

## Fragen?

Bei Fragen:
- 📧 GitHub Issues öffnen
- 💬 Diskussionen starten
- 📖 Dokumentation lesen

---

**Vielen Dank für deinen Beitrag! 🚀**









