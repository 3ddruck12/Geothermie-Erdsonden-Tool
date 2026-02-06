"""PDF-Generator für wasserrechtliche Bohranzeige (§ 49 WHG).

Erstellt ein behördengerechtes PDF-Formular zur Anzeige von Erdwärmesonden-
bohrungen bei der Unteren Wasserbehörde. Für Bohrungen ≤ 100m Tiefe.

Das Bergamt (§127 BBergG) ist erst ab >100m zuständig und daher hier
nicht relevant.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class BohranzeigePDFGenerator:
    """Generiert ein PDF-Formular für die wasserrechtliche Bohranzeige."""

    # Konstanten
    PAGE_MARGIN = 2 * cm
    LABEL_COL_WIDTH = 6 * cm
    VALUE_COL_WIDTH = 11 * cm
    FULL_WIDTH = LABEL_COL_WIDTH + VALUE_COL_WIDTH

    def __init__(self):
        """Initialisiert den Bohranzeige-PDF-Generator."""
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Erstellt benutzerdefinierte Styles für das Behörden-Formular."""
        self.styles.add(ParagraphStyle(
            name='FormTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='FormSubtitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#444444'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1f4788'),
            spaceBefore=14,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderPadding=0,
        ))

        self.styles.add(ParagraphStyle(
            name='FormBody',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='FormLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold'
        ))

        self.styles.add(ParagraphStyle(
            name='FormValue',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='FormHint',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#888888'),
            fontName='Helvetica-Oblique'
        ))

        self.styles.add(ParagraphStyle(
            name='FooterStyle',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

        self.styles.add(ParagraphStyle(
            name='CheckboxText',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            leftIndent=15
        ))

    def generate(self, filepath: str, data: dict) -> bool:
        """
        Generiert die Bohranzeige als PDF.

        Args:
            filepath: Pfad für die PDF-Datei
            data: Dictionary mit allen Formulardaten:
                - antragsteller: dict (name, strasse, plz, ort, telefon, email)
                - grundstueck: dict (flurstueck, gemarkung, gemeinde, landkreis)
                - koordinaten: dict (latitude, longitude) oder None
                - bohrunternehmen: dict (firma, ansprechpartner, dvgw_w120)
                - ausfuehrung: dict (start_datum, end_datum)
                - technik: dict (automatisch aus Berechnung)
                - gewaesserschutz: dict (wasserschutzgebiet, zone, grundwasserflurabstand, altlasten_geprueft)
                - checkboxen: dict (altlasten, wasserschutz)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            if not filepath.endswith('.pdf'):
                filepath += '.pdf'

            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=self.PAGE_MARGIN,
                leftMargin=self.PAGE_MARGIN,
                topMargin=1.5 * cm,
                bottomMargin=1.5 * cm
            )

            story = self._build_story(data)
            doc.build(story, onFirstPage=self._add_footer, onLaterPages=self._add_footer)

            logger.info(f"Bohranzeige PDF erstellt: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Bohranzeige: {e}")
            return False

    def _add_footer(self, canvas_obj, doc):
        """Fügt Kopf- und Fußzeile hinzu."""
        canvas_obj.saveState()

        # Fußzeile
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(colors.HexColor('#999999'))
        canvas_obj.drawCentredString(
            A4[0] / 2, 1 * cm,
            f"Erstellt mit GET - Geothermie Erdsonden-Tool | {datetime.now().strftime('%d.%m.%Y %H:%M')} | Seite {doc.page}"
        )

        # Kopfzeile-Linie
        canvas_obj.setStrokeColor(colors.HexColor('#1f4788'))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(
            self.PAGE_MARGIN, A4[1] - 1.2 * cm,
            A4[0] - self.PAGE_MARGIN, A4[1] - 1.2 * cm
        )

        canvas_obj.restoreState()

    def _build_story(self, data: dict) -> list:
        """Baut den gesamten PDF-Inhalt auf."""
        story = []

        # === TITEL ===
        story.append(Paragraph("Bohranzeige", self.styles['FormTitle']))
        story.append(Paragraph(
            "Anzeige einer Erdwärmesonden-Bohrung gemäß § 49 WHG<br/>"
            "zur Vorlage bei der Unteren Wasserbehörde",
            self.styles['FormSubtitle']
        ))
        story.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#1f4788'),
            spaceAfter=10
        ))

        # === 1. ANTRAGSTELLER ===
        story.extend(self._build_antragsteller(data.get('antragsteller', {})))

        # === 2. GRUNDSTÜCK ===
        story.extend(self._build_grundstueck(
            data.get('grundstueck', {}),
            data.get('koordinaten', {})
        ))

        # === 3. BOHRUNTERNEHMEN ===
        story.extend(self._build_bohrunternehmen(data.get('bohrunternehmen', {})))

        # === 4. AUSFÜHRUNGSZEITRAUM ===
        story.extend(self._build_ausfuehrung(data.get('ausfuehrung', {})))

        # === 5. TECHNISCHE ANGABEN ===
        story.extend(self._build_technik(data.get('technik', {})))

        # === 6. GEWÄSSERSCHUTZ ===
        story.extend(self._build_gewaesserschutz(data.get('gewaesserschutz', {})))

        # === SEITENUMBRUCH → ERKLÄRUNGEN & UNTERSCHRIFT ===
        story.append(PageBreak())

        # === 7. ERKLÄRUNGEN ===
        story.extend(self._build_erklaerungen(data.get('gewaesserschutz', {})))

        # === 8. UNTERSCHRIFT ===
        story.extend(self._build_unterschrift(data.get('antragsteller', {})))

        # === HINWEISE ===
        story.extend(self._build_hinweise())

        return story

    def _make_form_table(self, rows: list, col_widths=None) -> Table:
        """Erstellt eine formatierte Formular-Tabelle."""
        if col_widths is None:
            col_widths = [self.LABEL_COL_WIDTH, self.VALUE_COL_WIDTH]

        table = Table(rows, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table

    # ─── Abschnitt-Builder ────────────────────────────────────

    def _build_antragsteller(self, d: dict) -> list:
        """1. Antragsteller / Bauherr."""
        elements = []
        elements.append(Paragraph("1. Antragsteller / Bauherr", self.styles['SectionHeader']))

        rows = [
            ['Name:', d.get('name', '')],
            ['Straße, Nr.:', d.get('strasse', '')],
            ['PLZ, Ort:', f"{d.get('plz', '')} {d.get('ort', '')}"],
            ['Telefon:', d.get('telefon', '')],
            ['E-Mail:', d.get('email', '')],
        ]
        elements.append(self._make_form_table(rows))
        elements.append(Spacer(1, 0.3 * cm))
        return elements

    def _build_grundstueck(self, d: dict, koordinaten: dict) -> list:
        """2. Grundstück / Standort der Bohrung."""
        elements = []
        elements.append(Paragraph("2. Grundstück / Standort der Bohrung", self.styles['SectionHeader']))

        rows = [
            ['Flurstück-Nr.:', d.get('flurstueck', '')],
            ['Gemarkung:', d.get('gemarkung', '')],
            ['Gemeinde:', d.get('gemeinde', '')],
            ['Landkreis:', d.get('landkreis', '')],
        ]

        if koordinaten and (koordinaten.get('latitude') or koordinaten.get('longitude')):
            lat = koordinaten.get('latitude', '')
            lon = koordinaten.get('longitude', '')
            rows.append(['Koordinaten:', f"Breite: {lat}°  |  Länge: {lon}°"])

        elements.append(self._make_form_table(rows))
        elements.append(Spacer(1, 0.3 * cm))
        return elements

    def _build_bohrunternehmen(self, d: dict) -> list:
        """3. Bohrunternehmen."""
        elements = []
        elements.append(Paragraph("3. Bohrunternehmen", self.styles['SectionHeader']))

        rows = [
            ['Firma:', d.get('firma', '')],
            ['Ansprechpartner:', d.get('ansprechpartner', '')],
        ]

        dvgw = d.get('dvgw_w120', '')
        if dvgw:
            rows.append(['DVGW W 120-1:', dvgw])
        else:
            rows.append(['DVGW W 120-1:', '(keine Angabe)'])

        elements.append(self._make_form_table(rows))
        elements.append(Paragraph(
            "Hinweis: Die DVGW W 120-1 Zertifizierung wird von vielen Wasserbehörden "
            "als Qualifikationsnachweis empfohlen.",
            self.styles['FormHint']
        ))
        elements.append(Spacer(1, 0.3 * cm))
        return elements

    def _build_ausfuehrung(self, d: dict) -> list:
        """4. Geplanter Ausführungszeitraum."""
        elements = []
        elements.append(Paragraph("4. Geplanter Ausführungszeitraum", self.styles['SectionHeader']))

        rows = [
            ['Beginn (geplant):', d.get('start_datum', '')],
            ['Ende (geplant):', d.get('end_datum', '')],
        ]
        elements.append(self._make_form_table(rows))
        elements.append(Spacer(1, 0.3 * cm))
        return elements

    def _build_technik(self, d: dict) -> list:
        """5. Technische Angaben zur Erdwärmesondenanlage."""
        elements = []
        elements.append(Paragraph("5. Technische Angaben zur Erdwärmesondenanlage", self.styles['SectionHeader']))

        # 5a. Bohrungen
        num_bh = d.get('anzahl_bohrungen', 1)
        tiefe = d.get('bohrtiefe_m', 0)
        gesamt = d.get('gesamtbohrmeter', num_bh * tiefe)

        rows_bohrung = [
            ['Anzahl Bohrungen:', str(num_bh)],
            ['Bohrtiefe je Bohrung:', f"{tiefe:.1f} m"],
            ['Gesamtbohrmeter:', f"{gesamt:.1f} m"],
            ['Bohrdurchmesser:', f"{d.get('bohrdurchmesser_mm', 152):.0f} mm"],
            ['Abstand zw. Bohrungen:', f"{d.get('abstand_bohrungen_m', 6):.1f} m"],
        ]
        elements.append(Paragraph(
            "<b>5a. Bohrungen</b>", self.styles['FormBody']
        ))
        elements.append(self._make_form_table(rows_bohrung))
        elements.append(Spacer(1, 0.2 * cm))

        # 5b. Sonden
        sondentyp_map = {
            'single-u': 'Einfach-U-Sonde',
            'double-u': 'Doppel-U-Sonde',
            '4-rohr-dual': '4-Rohr (Dual-Verbinder)',
            '4-rohr-4verbinder': '4-Rohr (4-Verbinder)',
            'coaxial': 'Koaxialsonde',
        }
        sondentyp_raw = d.get('sondentyp', 'double-u')
        sondentyp = sondentyp_map.get(sondentyp_raw, sondentyp_raw)

        rows_sonde = [
            ['Sondentyp:', sondentyp],
            ['Rohrmaterial:', d.get('rohrmaterial', 'PE 100 RC')],
            ['Rohrdurchmesser (außen):', f"{d.get('rohrdurchmesser_mm', 32):.1f} mm"],
            ['Wandstärke:', f"{d.get('wandstaerke_mm', 3.0):.1f} mm"],
        ]
        elements.append(Paragraph(
            "<b>5b. Erdwärmesonden</b>", self.styles['FormBody']
        ))
        elements.append(self._make_form_table(rows_sonde))
        elements.append(Spacer(1, 0.2 * cm))

        # 5c. Verfüllung
        rows_verfuellung = [
            ['Verfüllmaterial:', d.get('verfuellmaterial', '')],
            ['Wärmeleitfähigkeit:', f"{d.get('verfuell_lambda', 0):.2f} W/(m·K)"],
        ]
        elements.append(Paragraph(
            "<b>5c. Verfüllung (Ringraumabdichtung)</b>", self.styles['FormBody']
        ))
        elements.append(self._make_form_table(rows_verfuellung))
        elements.append(Spacer(1, 0.2 * cm))

        # 5d. Wärmeträger
        rows_fluid = [
            ['Wärmeträgerfluid:', d.get('fluid_typ', 'Wasser/Glykol')],
            ['Konzentration:', d.get('fluid_konzentration', '')],
            ['Frostschutz bis:', d.get('frostschutz_bis', '')],
        ]
        elements.append(Paragraph(
            "<b>5d. Wärmeträgerflüssigkeit</b>", self.styles['FormBody']
        ))
        elements.append(self._make_form_table(rows_fluid))
        elements.append(Spacer(1, 0.2 * cm))

        # 5e. Wärmepumpe / Leistung
        rows_leistung = [
            ['Heizleistung:', f"{d.get('heizleistung_kw', 0):.1f} kW"],
            ['Kühlleistung:', f"{d.get('kuehlleistung_kw', 0):.1f} kW"],
            ['Jahres-Heizenergie:', f"{d.get('jahres_heizenergie_kwh', 0):,.0f} kWh"],
            ['Jahres-Kühlenergie:', f"{d.get('jahres_kuehlenergie_kwh', 0):,.0f} kWh"],
            ['Jahresarbeitszahl (COP):', f"{d.get('cop', 0):.1f}"],
        ]
        elements.append(Paragraph(
            "<b>5e. Leistungsdaten der Anlage</b>", self.styles['FormBody']
        ))
        elements.append(self._make_form_table(rows_leistung))
        elements.append(Spacer(1, 0.3 * cm))
        return elements

    def _build_gewaesserschutz(self, d: dict) -> list:
        """6. Standort- und Gewässerschutz."""
        elements = []
        elements.append(Paragraph("6. Standort- und Gewässerschutz", self.styles['SectionHeader']))

        wsg = d.get('wasserschutzgebiet', False)
        wsg_text = "Ja" if wsg else "Nein"
        zone = d.get('zone', '')
        if wsg and zone:
            wsg_text += f" – Zone {zone}"

        gw = d.get('grundwasserflurabstand', '')
        gw_text = f"{gw} m" if gw else "(nicht bekannt)"

        rows = [
            ['Wasserschutzgebiet:', wsg_text],
            ['Grundwasserflurabstand:', gw_text],
            ['Bodentyp:', d.get('bodentyp', '')],
            ['Wärmeleitfähigkeit Boden:', f"{d.get('lambda_boden', 0):.2f} W/(m·K)" if d.get('lambda_boden') else ''],
            ['Bodentemperatur:', f"{d.get('bodentemperatur', 0):.1f} °C" if d.get('bodentemperatur') else ''],
        ]
        elements.append(self._make_form_table(rows))
        elements.append(Spacer(1, 0.3 * cm))
        return elements

    def _build_erklaerungen(self, d: dict) -> list:
        """7. Erklärungen des Antragstellers."""
        elements = []
        elements.append(Paragraph("7. Erklärungen des Antragstellers", self.styles['SectionHeader']))

        altlasten = d.get('altlasten_geprueft', False)
        wsg_geprueft = d.get('wasserschutz_geprueft', False)

        checkbox_items = [
            (altlasten, "Hiermit erkläre ich, dass das Altlastenkataster geprüft wurde und "
                        "am geplanten Bohrstandort keine Altlasten bekannt sind."),
            (wsg_geprueft, "Hiermit erkläre ich, dass geprüft wurde, ob der Standort in einem "
                           "Wasser- oder Heilquellenschutzgebiet liegt."),
            (True, "Die Bohrung wird fachgerecht nach dem Stand der Technik (VDI 4640, "
                   "DVGW W 120) ausgeführt und der Ringraum vollständig verpresst."),
            (True, "Änderungen an den angezeigten Maßnahmen werden unverzüglich der "
                   "Unteren Wasserbehörde mitgeteilt."),
        ]

        for checked, text in checkbox_items:
            marker = "☑" if checked else "☐"
            elements.append(Paragraph(
                f"{marker}  {text}",
                self.styles['CheckboxText']
            ))
            elements.append(Spacer(1, 0.15 * cm))

        elements.append(Spacer(1, 0.5 * cm))
        return elements

    def _build_unterschrift(self, antragsteller: dict) -> list:
        """8. Unterschriftenfeld."""
        elements = []
        elements.append(Paragraph("8. Unterschrift", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.5 * cm))

        # Ort, Datum
        elements.append(Paragraph(
            "Ort, Datum: _____________________________________________",
            self.styles['FormBody']
        ))
        elements.append(Spacer(1, 1.5 * cm))

        # Unterschriftslinie
        elements.append(Paragraph(
            "Unterschrift: _____________________________________________",
            self.styles['FormBody']
        ))
        elements.append(Spacer(1, 0.3 * cm))

        name = antragsteller.get('name', '')
        if name:
            elements.append(Paragraph(
                f"({name})",
                self.styles['FormBody']
            ))

        elements.append(Spacer(1, 1 * cm))
        return elements

    def _build_hinweise(self) -> list:
        """Hinweise am Ende des Dokuments."""
        elements = []
        elements.append(HRFlowable(
            width="100%", thickness=0.5,
            color=colors.HexColor('#cccccc'),
            spaceBefore=10, spaceAfter=10
        ))

        hinweise = [
            "• Diese Bohranzeige ist gemäß § 49 WHG i.V.m. dem jeweiligen Landeswassergesetz "
            "bei der Unteren Wasserbehörde einzureichen.",
            "• Für Bohrungen bis 100 m Tiefe ist i.d.R. keine bergrechtliche Anzeige nach "
            "§ 127 BBergG erforderlich.",
            "• Die Bohrung darf frühestens nach Ablauf der behördlichen Wartefrist "
            "(i.d.R. 1 Monat nach Eingang) begonnen werden, sofern kein Widerspruch erfolgt.",
            "• Bitte beachten Sie die ggf. abweichenden Regelungen Ihres Bundeslandes.",
            "• Dieses Dokument wurde automatisch erstellt und ersetzt keine individuelle "
            "behördliche Beratung.",
        ]

        for h in hinweise:
            elements.append(Paragraph(h, self.styles['FormHint']))
            elements.append(Spacer(1, 0.1 * cm))

        return elements
