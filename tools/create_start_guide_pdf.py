#!/usr/bin/env python3
"""Erstellt PDF-Anleitung zum Starten des Programms."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER

def create_pdf():
    """Erstellt PDF-Anleitung."""
    doc = SimpleDocTemplate(
        "docs/ANLEITUNG_PROGRAMM_STARTEN.pdf",
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        leftIndent=20,
        rightIndent=20,
        spaceAfter=6,
        backColor=colors.HexColor('#f5f5f5')
    )
    
    # Titel
    story.append(Paragraph("Anleitung: Programm starten", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Geothermie Erdsonden-Tool V3.3.0-beta3", styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Schnellstart
    story.append(Paragraph("Schnellstart", heading_style))
    
    story.append(Paragraph("<b>Option 1: Direkt starten (mit venv)</b>", styles['Normal']))
    story.append(Paragraph(
        '<font face="Courier">cd "/home/jens/Dokumente/Software Projekte/Geothermietool"<br/>'
        'source venv/bin/activate<br/>'
        'python3 main.py</font>',
        code_style
    ))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("<b>Option 2: Mit Start-Skript</b>", styles['Normal']))
    story.append(Paragraph(
        '<font face="Courier">cd "/home/jens/Dokumente/Software Projekte/Geothermietool"<br/>'
        './start.sh</font>',
        code_style
    ))
    story.append(Spacer(1, 1*cm))
    
    # Voraussetzungen
    story.append(Paragraph("Voraussetzungen", heading_style))
    story.append(Paragraph("<b>Python-Version:</b> Python 3.8 oder höher erforderlich", styles['Normal']))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>Abhängigkeiten:</b>", styles['Normal']))
    deps = [
        "numpy >= 1.24.0",
        "matplotlib >= 3.7.0",
        "pandas >= 2.0.0",
        "scipy >= 1.10.0",
        "reportlab >= 4.0.0",
        "requests >= 2.31.0",
        "pygfunction[plot] >= 2.3.0 (optional)"
    ]
    for dep in deps:
        story.append(Paragraph(f"• {dep}", styles['Normal']))
    
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("<b>Installation der Abhängigkeiten:</b>", styles['Normal']))
    story.append(Paragraph(
        '<font face="Courier">cd "/home/jens/Dokumente/Software Projekte/Geothermietool"<br/>'
        'source venv/bin/activate<br/>'
        'pip install -r requirements.txt</font>',
        code_style
    ))
    story.append(Spacer(1, 1*cm))
    
    # Programm starten
    story.append(PageBreak())
    story.append(Paragraph("Programm starten - Schritt für Schritt", heading_style))
    
    steps = [
        ("Schritt 1: Terminal öffnen", "Terminal öffnen (Strg+Alt+T unter Linux)"),
        ("Schritt 2: Zum Programmverzeichnis wechseln", 
         '<font face="Courier">cd "/home/jens/Dokumente/Software Projekte/Geothermietool"</font>'),
        ("Schritt 3: Virtuelles Environment aktivieren", 
         '<font face="Courier">source venv/bin/activate</font><br/>Sie sollten dann (venv) am Anfang der Zeile sehen.'),
        ("Schritt 4: Programm starten", 
         '<font face="Courier">python3 main.py</font>')
    ]
    
    for i, (title, desc) in enumerate(steps, 1):
        story.append(Paragraph(f"<b>{i}. {title}</b>", styles['Normal']))
        story.append(Paragraph(desc, styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
    
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Erfolgreicher Start", heading_style))
    story.append(Paragraph("Wenn alles funktioniert, sollten Sie sehen:", styles['Normal']))
    story.append(Paragraph(
        '<font face="Courier">✓ Starte Professional GUI V3<br/>'
        '✓ GUI erstellt, starte Event-Loop...</font>',
        code_style
    ))
    story.append(Paragraph("Das Hauptfenster öffnet sich mit:", styles['Normal']))
    story.append(Paragraph("• Titel: Geothermie Erdsonden-Tool - Professional Edition V3.2.1", styles['Normal']))
    story.append(Paragraph("• Größe: 1800x1100 Pixel", styles['Normal']))
    story.append(Paragraph("• Tabs: Eingabe, Ergebnisse, Diagramme, Material & Hydraulik, etc.", styles['Normal']))
    story.append(Spacer(1, 1*cm))
    
    # Fehlerbehebung
    story.append(PageBreak())
    story.append(Paragraph("Fehlerbehebung", heading_style))
    
    errors = [
        ("Fehler: 'No module named matplotlib'", 
         "Abhängigkeiten installieren:<br/>"
         '<font face="Courier">source venv/bin/activate<br/>pip install -r requirements.txt</font>'),
        ("Fehler: 'python3: command not found'", 
         "Python 3 installieren oder python statt python3 verwenden:<br/>"
         '<font face="Courier">python main.py</font>'),
        ("Fehler: 'Permission denied'", 
         "Ausführungsrechte setzen:<br/>"
         '<font face="Courier">chmod +x start.sh<br/>chmod +x main.py</font>'),
        ("Programm startet, aber Fenster erscheint nicht", 
         "Mögliche Ursachen:<br/>"
         "• Programm läuft im Hintergrund<br/>"
         "• Display-Variable nicht gesetzt (bei SSH)<br/>"
         "• Andere GUI läuft bereits<br/><br/>"
         "Lösung: Prüfen ob Programm läuft:<br/>"
         '<font face="Courier">ps aux | grep "python.*main.py"</font>')
    ]
    
    for title, solution in errors:
        story.append(Paragraph(f"<b>{title}</b>", styles['Normal']))
        story.append(Paragraph(solution, styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
    
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Tastenkürzel", heading_style))
    story.append(Paragraph("Nach dem Start:", styles['Normal']))
    story.append(Paragraph("• Strg+O: Projekt laden (.get Datei)", styles['Normal']))
    story.append(Paragraph("• Strg+S: Projekt speichern (.get Datei)", styles['Normal']))
    story.append(Paragraph("• Strg+P: PDF-Bericht erstellen", styles['Normal']))
    
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Programm beenden", heading_style))
    story.append(Paragraph("• Fenster schließen: Klicken Sie auf das X-Symbol", styles['Normal']))
    story.append(Paragraph("• Menü: Datei → Beenden", styles['Normal']))
    story.append(Paragraph("• Terminal: Strg+C (falls im Terminal gestartet)", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(
        "<para align='center'><font size=8>"
        "Version: 3.3.0-beta3 | Letzte Aktualisierung: Januar 2026"
        "</font></para>",
        styles['Normal']
    ))
    
    # PDF erstellen
    doc.build(story)
    print("✓ PDF erstellt: docs/ANLEITUNG_PROGRAMM_STARTEN.pdf")

if __name__ == "__main__":
    create_pdf()
