#!/bin/bash
# Git Repository initialisieren und zu GitHub pushen

set -e  # Bei Fehler abbrechen

echo "🚀 Initialisiere Git Repository für Geothermie Erdsondentool"
echo "============================================================"
echo ""

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Git initialisieren
echo -e "${BLUE}📦 Schritt 1: Git initialisieren${NC}"
if [ -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Git bereits initialisiert, überspringe...${NC}"
else
    git init
    echo -e "${GREEN}✅ Git initialisiert${NC}"
fi
echo ""

# 2. Remote hinzufügen
echo -e "${BLUE}🌐 Schritt 2: Remote Repository hinzufügen${NC}"
REMOTE_URL="https://github.com/3ddruck12/GeothermieErdsondentool.git"

if git remote | grep -q "origin"; then
    echo -e "${YELLOW}⚠️  Remote 'origin' existiert bereits${NC}"
    echo "Aktuelle Remote:"
    git remote -v
    read -p "Möchtest du die Remote URL aktualisieren? (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        git remote set-url origin $REMOTE_URL
        echo -e "${GREEN}✅ Remote URL aktualisiert${NC}"
    fi
else
    git remote add origin $REMOTE_URL
    echo -e "${GREEN}✅ Remote 'origin' hinzugefügt: $REMOTE_URL${NC}"
fi
echo ""

# 3. Dateien hinzufügen
echo -e "${BLUE}📝 Schritt 3: Dateien zum Commit hinzufügen${NC}"
git add .
echo -e "${GREEN}✅ Alle Dateien hinzugefügt${NC}"
echo ""

# 4. Status anzeigen
echo -e "${BLUE}📊 Git Status:${NC}"
git status --short
echo ""

# 5. Initial Commit
echo -e "${BLUE}💾 Schritt 4: Initial Commit${NC}"
if git rev-parse HEAD >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Repository hat bereits Commits${NC}"
    read -p "Möchtest du einen neuen Commit erstellen? (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        git commit -m "feat: Update to V3 Professional Edition with CI/CD"
        echo -e "${GREEN}✅ Commit erstellt${NC}"
    fi
else
    git commit -m "feat: Initial commit - V3 Professional Edition with CI/CD

- Vollständige Berechnungssoftware für Erdwärmesonden bis 100m
- Moderne GUI mit Tooltips und Info-Buttons
- Bodendatenbank (11 Typen nach VDI 4640)
- Verfüllmaterial-Datenbank (7 Materialien)
- PVGIS Klimadaten-Integration
- PDF-Export mit professionellen Berichten
- GitHub Actions CI/CD Pipeline
- Automatische Builds (Windows EXE + Linux DEB)
- Umfassende Dokumentation"
    echo -e "${GREEN}✅ Initial Commit erstellt${NC}"
fi
echo ""

# 6. Dev-Branch erstellen
echo -e "${BLUE}🌿 Schritt 5: Dev-Branch erstellen${NC}"
if git show-ref --verify --quiet refs/heads/dev; then
    echo -e "${YELLOW}⚠️  Branch 'dev' existiert bereits${NC}"
    git checkout dev
else
    git branch dev
    echo -e "${GREEN}✅ Branch 'dev' erstellt${NC}"
fi
echo ""

# 7. Zu GitHub pushen
echo -e "${BLUE}☁️  Schritt 6: Zu GitHub pushen${NC}"
echo "Dies wird folgende Branches pushen:"
echo "  - main (Produktions-Branch)"
echo "  - dev (Entwicklungs-Branch)"
echo ""
read -p "Möchtest du jetzt zu GitHub pushen? (j/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    # Main pushen
    git checkout main 2>/dev/null || git checkout -b main
    git push -u origin main
    echo -e "${GREEN}✅ Branch 'main' gepusht${NC}"
    
    # Dev pushen
    git checkout dev
    git push -u origin dev
    echo -e "${GREEN}✅ Branch 'dev' gepusht${NC}"
    
    echo ""
    echo -e "${GREEN}🎉 Erfolgreich zu GitHub gepusht!${NC}"
else
    echo -e "${YELLOW}⏭️  Push übersprungen${NC}"
    echo "Du kannst später manuell pushen mit:"
    echo "  git push -u origin main"
    echo "  git push -u origin dev"
fi
echo ""

# 8. Tag erstellen (optional)
echo -e "${BLUE}🏷️  Schritt 7: Release-Tag erstellen (optional)${NC}"
read -p "Möchtest du einen Release-Tag v3.0.0 erstellen? (j/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Jj]$ ]]; then
    git checkout main
    git tag -a v3.0.0 -m "Release v3.0.0 - Professional Edition

Features:
- Vollständige Erdwärmesonden-Berechnung bis 100m
- Moderne GUI mit Tooltips
- Datenbanken für Boden und Verfüllmaterial
- PVGIS Klimadaten-Integration
- PDF-Export
- CI/CD Pipeline mit automatischen Builds"
    
    echo -e "${GREEN}✅ Tag v3.0.0 erstellt${NC}"
    
    read -p "Tag zu GitHub pushen? (j/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        git push origin v3.0.0
        echo -e "${GREEN}✅ Tag gepusht - GitHub Actions wird automatisch Builds erstellen!${NC}"
    fi
fi
echo ""

# 9. Zusammenfassung
echo "============================================================"
echo -e "${GREEN}✨ Git-Setup abgeschlossen!${NC}"
echo ""
echo "📋 Nächste Schritte:"
echo ""
echo "1. Gehe zu: https://github.com/3ddruck12/GeothermieErdsondentool"
echo "2. Überprüfe die Repository-Einstellungen"
echo "3. Aktiviere Branch Protection Rules:"
echo "   - Settings → Branches → Add rule"
echo "   - Branch name pattern: main"
echo "   - ✅ Require pull request reviews before merging"
echo "   - ✅ Require status checks to pass"
echo ""
echo "4. Füge GitHub Topics hinzu:"
echo "   - Settings → About → Topics"
echo "   - Vorschläge: geothermal, python, gui, engineering, vdi-4640"
echo ""
echo "5. Wenn Tag gepusht: Checke GitHub Actions"
echo "   - Actions Tab → Build and Release Workflow"
echo "   - Nach ~10-15 Min: Release mit EXE & DEB verfügbar"
echo ""
echo "6. Erstelle Screenshots für README.md"
echo ""
echo "🚀 Viel Erfolg mit dem Open-Source-Projekt!"
echo "============================================================"









