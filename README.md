# 🌡️ GET - Geothermie Erdsondentool

**GET** steht für **G**eothermie **E**rdsonden**t**ool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://github.com/3ddruck12/GeothermieErdsondentool/workflows/Build%20and%20Release/badge.svg)](https://github.com/3ddruck12/GeothermieErdsondentool/actions)
[![GitHub release](https://img.shields.io/github/release/3ddruck12/GeothermieErdsondentool.svg)](https://github.com/3ddruck12/GeothermieErdsondentool/releases)

> **Open-Source Tool zur professionellen Berechnung von Erdwärmesonden bis 100m Tiefe**

**GET** ist eine moderne, benutzerfreundliche Open-Source-Alternative zu kommerziellen Erdwärmesonden-Berechnungsprogrammen für Linux und Windows.

---

## 📋 Inhaltsverzeichnis

- [Features](#-features)
- [Installation](#-installation)
- [Schnellstart](#-schnellstart)
- [Dokumentation](#-dokumentation)
- [Screenshots](#-screenshots)
- [Entwicklung](#-entwicklung)
- [Roadmap](#-roadmap)
- [Lizenz](#-lizenz)

---

## ✨ Features

### 🔧 Berechnungen
- ✅ **Erdwärmesonden bis 100m Tiefe**
- ✅ **Multiple Konfigurationen**: Single-U, Double-U, 4-Rohr-Systeme
- ✅ **PE 100 RC Rohre**: 32mm mit Dual- und 4-Verbinder
- ✅ **Thermische Widerstände**: Multipole-Methode nach Hellström
- ✅ **G-Funktionen**: Nach Eskilson
- ✅ **Hydraulik-Berechnungen**: Druckverlust, Pumpenleistung
- ✅ **Multi-Bohrfeld**: Mehrere Bohrungen mit Abstandsberechnung

### 🌍 Datenbanken
- ✅ **Bodendatenbank**: 11 Bodentypen nach VDI 4640
  - Sand, Lehm, Schluff, Ton, Kies
  - Festgestein: Granit, Gneis, Basalt, Sandstein, Kalkstein
- ✅ **Verfüllmaterial-Datenbank**: 7 Materialien
  - Von Standard-Bentonit bis Hochleistungs-Graphit
- ✅ **Rohr-Datenbank**: Laden aus `pipe.txt` oder EED-Dateien

### 🌐 Klimadaten
- ✅ **PVGIS-Integration**: Automatischer Abruf von EU-Klimadaten
- ✅ **Temperaturschätzung**: Bodentemperatur aus Lufttemperatur
- ✅ **Geocoding**: Koordinaten aus Adresse

### 📊 Ausgabe & Export
- ✅ **PDF-Berichte**: Professionelle Berichte mit allen Berechnungen
- ✅ **Grafische Darstellung**: Bohrloch-Schema, Temperaturverläufe
- ✅ **Projektdaten**: Kunde, Adresse, Bohrfeld-Konfiguration
- ✅ **Materialberechnung**: Benötigte Verfüllmenge

### 💡 Benutzerfreundlichkeit
- ✅ **Info-Buttons**: Hilfe zu jedem Parameter
- ✅ **Dropdown-Auswahl**: Schnelle Wahl von Boden & Material
- ✅ **Auto-Vervollständigung**: Werte aus Datenbank
- ✅ **Moderne GUI**: Tkinter mit Tabs und Scrolling
- ✅ **Cross-Platform**: Linux & Windows

---

## 💾 Installation

### Windows

**Option 1: Standalone EXE** (empfohlen)

1. [Neueste Release herunterladen](https://github.com/3ddruck12/GeothermieErdsondentool/releases)
2. `GeothermieErdsondentool.exe` herunterladen
3. Doppelklick zum Starten

**Option 2: Python**

```powershell
git clone https://github.com/3ddruck12/GeothermieErdsondentool.git
cd GeothermieErdsondentool
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Linux

**Option 1: DEB-Paket** (Debian/Ubuntu)

```bash
wget https://github.com/3ddruck12/GeothermieErdsondentool/releases/download/v3.0.0/geothermie-erdsondentool_3.0.0_amd64.deb
sudo dpkg -i geothermie-erdsondentool_3.0.0_amd64.deb
sudo apt-get install -f  # Falls Abhängigkeiten fehlen
geothermie-erdsondentool
```

**Option 2: Shell-Script**

```bash
git clone https://github.com/3ddruck12/GeothermieErdsondentool.git
cd GeothermieErdsondentool
./start.sh
```

**Option 3: Python**

```bash
git clone https://github.com/3ddruck12/GeothermieErdsondentool.git
cd GeothermieErdsondentool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 🚀 Schnellstart

### 1. Projekt anlegen

```
📝 Projektdaten:
- Projektname: "Einfamilienhaus Müller"
- Kunde: "Familie Müller"
- Adresse: "Musterstraße 1, 12345 Musterstadt"
```

### 2. Bohrfeld konfigurieren

```
🏗️ Bohrfeld:
- Anzahl Bohrungen: 2
- Abstand zwischen Bohrungen: 6 m
- Abstand zum Grundstück: 3 m
- Abstand zum Gebäude: 3 m
```

### 3. Bodentyp wählen

```
🌍 Boden:
- Dropdown: "Sand" → λ = 1.8 W/m·K automatisch gesetzt
```

### 4. Verfüllmaterial wählen

```
🏗️ Verfüllung:
- Dropdown: "Zement-Bentonit verbessert" → λ = 1.3 W/m·K
```

### 5. Heizlast eingeben

```
🔥 Heizlast:
- Jahres-Heizenergie: 12000 kWh
- Heiz-Spitzenlast: 6 kW
- Wärmepumpen-COP: 4.0
```

### 6. Berechnen & PDF erstellen

```
🚀 Berechnung starten
📄 PDF-Bericht erstellen
```

---

## 📚 Dokumentation

Vollständige Dokumentation im [`docs/`](docs/) Ordner:

- [📘 Installationsanleitung](docs/INSTALL.md)
- [📗 Benutzerhandbuch](docs/ANLEITUNG.md)
- [📙 Schnellstart](docs/SCHNELLSTART.md)
- [📈 Roadmap](docs/ROADMAP.md) - Geplante Features
- [📕 Changelog](docs/CHANGELOG.md)
- [📓 Version 2 Features](docs/NEUE_FEATURES_V2.md)
- [📔 Version 3 Features](docs/PROFESSIONAL_FEATURES_V3.md)

### Technische Dokumentation

- **Thermische Berechnung**: Multipole-Methode nach Hellström
- **G-Funktionen**: Eskilson's dimensionless temperature response
- **VDI 4640**: Bodenwerte nach deutscher Norm
- **PVGIS API**: EU Joint Research Centre Klimadaten

---

## 🖼️ Screenshots

### Hauptfenster
*(Screenshot hier einfügen)*

### Dropdown-Auswahl
- Bodentyp-Auswahl mit Auto-Vervollständigung
- Verfüllmaterial mit Beschreibung

### Ergebnisse
- Detaillierte Berechnung
- Grafische Darstellung
- PDF-Export

### PDF-Bericht
- Projektdaten
- Berechnungsergebnisse
- Grafiken und Diagramme

---


## 📈 Roadmap

Die detaillierte Roadmap mit allen geplanten Features findest du in [docs/ROADMAP.md](docs/ROADMAP.md).

**Highlights:**
- 🌍 Mehrsprachigkeit (V3.1)
- 🎮 3D-Visualisierung (V4.0)
- 💰 Kostenberechnung (V4.0)
- 🤖 Optimierungsalgorithmus (V4.0)

---

## 🤝 Mitwirken

Beiträge sind willkommen! 

**Für Entwickler:**
- 📖 [Beitragsrichtlinien](docs/CONTRIBUTING.md) - Code-Style, Workflow
- 🔄 [Git-Workflow](docs/GIT_WORKFLOW.md) - Branch-Strategie, CI/CD
- 📈 [Roadmap](docs/ROADMAP.md) - Geplante Features

**Quick Start:**
```bash
git clone https://github.com/3ddruck12/GeothermieErdsondentool.git
cd GeothermieErdsondentool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Siehe [CONTRIBUTING.md](docs/CONTRIBUTING.md) für Details.

---

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.

---

## 🙏 Danksagungen

- **VDI 4640**: Bodenwerte und Berechnungsstandards
- **PVGIS**: EU-Klimadatenbank  
- **Wissenschaftliche Community**: Für Forschung und Methodik im Bereich Geothermie
- **Python Community**: Für die großartigen Libraries

---

## 📧 Kontakt

- **GitHub**: [3ddruck12](https://github.com/3ddruck12)
- **Issues**: [GitHub Issues](https://github.com/3ddruck12/GeothermieErdsondentool/issues)

---

## ⭐ Support

Wenn dir dieses Projekt gefällt, gib ihm einen **Star** ⭐ auf GitHub!

---

**Made with ❤️ for the geothermal community**
