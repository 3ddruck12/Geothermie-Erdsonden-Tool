"""PDF-Bericht-Generator für Erdwärmesonden-Berechnungen."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import tempfile
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import matplotlib.patches as mpatches
from typing import Optional


class PDFReportGenerator:
    """Generiert professionelle PDF-Berichte für Erdwärmesonden-Berechnungen."""
    
    def __init__(self):
        """Initialisiert den PDF-Generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Erstellt benutzerdefinierte Styles."""
        # Titel-Style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Untertitel
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Normal mit Einzug
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_report(
        self,
        filepath: str,
        result,
        params: dict,
        project_info: dict,
        borehole_config: dict,
        grout_calculation: dict = None,
        hydraulics_result: dict = None,
        borefield_result: dict = None,
        vdi4640_result = None,
        fluid_info: dict = None
    ):
        """
        Generiert einen kompletten PDF-Bericht.
        
        Args:
            filepath: Pfad für die PDF-Datei
            result: Berechnungsergebnis (BoreholeResult)
            params: Berechnungsparameter
            project_info: Projektinformationen (Name, Kunde, Adresse)
            borehole_config: Bohrfeld-Konfiguration (Anzahl, Abstände)
            grout_calculation: Verfüllmaterial-Berechnung (optional)
            hydraulics_result: Hydraulik-Berechnung (optional)
            borefield_result: Bohrfeld g-Funktionen-Ergebnis (optional)
            vdi4640_result: VDI 4640 Berechnungsergebnis (optional)
            fluid_info: Wärmeträgerfluid-Informationen (optional)
        """
        # PDF erstellen
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # === TITELSEITE ===
        story.append(Spacer(1, 1*cm))
        
        # Logo-Platzhalter / Titel
        title = Paragraph(
            "Erdwärmesonden-Berechnung",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.5*cm))
        
        # Datum
        date_para = Paragraph(
            f"<para align='center'>Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}</para>",
            self.styles['CustomBody']
        )
        story.append(date_para)
        story.append(Spacer(1, 1*cm))
        
        # === PROJEKTINFORMATIONEN ===
        story.append(Paragraph("Projektinformationen", self.styles['CustomHeading']))
        
        project_data = [
            ['Projekt:', project_info.get('project_name', 'N/A')],
            ['Kunde:', project_info.get('customer_name', 'N/A')],
            ['Adresse:', project_info.get('address', 'N/A')],
            ['Ort:', project_info.get('city', 'N/A')],
            ['PLZ:', project_info.get('postal_code', 'N/A')]
        ]
        
        project_table = Table(project_data, colWidths=[4*cm, 13*cm])
        project_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(project_table)
        story.append(Spacer(1, 0.8*cm))
        
        # === BOHRFELD-KONFIGURATION ===
        story.append(Paragraph("Bohrfeld-Konfiguration", self.styles['CustomHeading']))
        
        num_boreholes = borehole_config.get('num_boreholes', 1)
        borehole_data = [
            ['Anzahl Bohrungen:', str(num_boreholes)],
            ['Abstand zwischen Bohrungen:', f"{borehole_config.get('spacing_between', 6)} m"],
            ['Abstand zum Grundstücksrand:', f"{borehole_config.get('spacing_property', 3)} m"],
            ['Abstand zum Gebäude:', f"{borehole_config.get('spacing_building', 3)} m"],
            ['Bohrloch-Durchmesser:', f"{params.get('borehole_diameter', 0.152)*1000:.0f} mm"],
            ['Rohrkonfiguration:', params.get('pipe_configuration', 'single-u').upper()]
        ]
        
        borehole_table = Table(borehole_data, colWidths=[6*cm, 11*cm])
        borehole_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(borehole_table)
        story.append(Spacer(1, 1*cm))
        
        # === BERECHNUNGSERGEBNISSE ===
        story.append(Paragraph("Berechnungsergebnisse", self.styles['CustomHeading']))
        
        results_data = [
            ['Parameter', 'Wert', 'Einheit'],
            ['Erforderliche Bohrtiefe (pro Bohrung)', f"{result.required_depth:.1f}", 'm'],
            ['Gesamte Bohrmeter', f"{result.required_depth * num_boreholes:.1f}", 'm'],
            ['Wärmeentzugsrate', f"{result.heat_extraction_rate:.2f}", 'W/m'],
            ['Gesamtleistung Bohrfeld', f"{result.heat_extraction_rate * result.required_depth * num_boreholes / 1000:.2f}", 'kW'],
            ['Min. Fluidtemperatur', f"{result.fluid_temperature_min:.2f}", '°C'],
            ['Max. Fluidtemperatur', f"{result.fluid_temperature_max:.2f}", '°C'],
            ['Bohrloch-Widerstand (Rb)', f"{result.borehole_resistance:.4f}", 'm·K/W'],
            ['Effektiver Widerstand', f"{result.effective_resistance:.4f}", 'm·K/W']
        ]
        
        results_table = Table(results_data, colWidths=[9*cm, 5*cm, 3*cm])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        story.append(results_table)
        story.append(Spacer(1, 1*cm))
        
        # === EINGABEPARAMETER ===
        story.append(PageBreak())
        story.append(Paragraph("Bodeneigenschaften", self.styles['CustomHeading']))
        
        ground_data = [
            ['Parameter', 'Wert', 'Einheit'],
            ['Wärmeleitfähigkeit Boden', f"{params.get('ground_thermal_conductivity', 0):.2f}", 'W/m·K'],
            ['Wärmekapazität Boden', f"{params.get('ground_heat_capacity', 0)/1e6:.2f}", 'MJ/m³·K'],
            ['Ungestörte Bodentemperatur', f"{params.get('undisturbed_ground_temp', 0):.1f}", '°C'],
            ['Geothermischer Gradient', f"{params.get('geothermal_gradient', 0)*100:.2f}", 'K/100m']
        ]
        
        ground_table = Table(ground_data, colWidths=[9*cm, 5*cm, 3*cm])
        ground_table.setStyle(self._get_table_style())
        story.append(ground_table)
        story.append(Spacer(1, 0.8*cm))
        
        # Rohr-Eigenschaften
        story.append(Paragraph("Rohr-Eigenschaften", self.styles['CustomHeading']))
        
        pipe_data = [
            ['Parameter', 'Wert', 'Einheit'],
            ['Außendurchmesser', f"{params.get('pipe_outer_diameter', 0)*1000:.1f}", 'mm'],
            ['Wandstärke', f"{params.get('pipe_wall_thickness', 0)*1000:.1f}", 'mm'],
            ['Wärmeleitfähigkeit Rohr', f"{params.get('pipe_thermal_conductivity', 0):.2f}", 'W/m·K'],
            ['Schenkelabstand', f"{params.get('shank_spacing', 0)*1000:.0f}", 'mm'],
            ['Wärmeleitfähigkeit Verfüllung', f"{params.get('grout_thermal_conductivity', 0):.2f}", 'W/m·K']
        ]
        
        pipe_table = Table(pipe_data, colWidths=[9*cm, 5*cm, 3*cm])
        pipe_table.setStyle(self._get_table_style())
        story.append(pipe_table)
        story.append(Spacer(1, 0.8*cm))
        
        # Lasten
        story.append(Paragraph("Heiz- und Kühllast", self.styles['CustomHeading']))
        
        load_data = [
            ['Parameter', 'Wert', 'Einheit'],
            ['Jahres-Heizenergie', f"{params.get('annual_heating_demand', 0):.2f}", 'MWh'],
            ['Jahres-Kühlenergie', f"{params.get('annual_cooling_demand', 0):.2f}", 'MWh'],
            ['Heiz-Spitzenlast', f"{params.get('peak_heating_load', 0):.1f}", 'kW'],
            ['Kühl-Spitzenlast', f"{params.get('peak_cooling_load', 0):.1f}", 'kW'],
            ['Wärmepumpen-COP', f"{params.get('heat_pump_cop', 0):.1f}", '-'],
            ['Simulationsdauer', f"{params.get('simulation_years', 25):.0f}", 'Jahre']
        ]
        
        load_table = Table(load_data, colWidths=[9*cm, 5*cm, 3*cm])
        load_table.setStyle(self._get_table_style())
        story.append(load_table)
        story.append(Spacer(1, 1*cm))
        
        # === VERFÜLLMATERIAL-BERECHNUNG ===
        if grout_calculation:
            story.append(Paragraph("Verfüllmaterial-Berechnung", self.styles['CustomHeading']))
            
            material = grout_calculation.get('material')
            amounts = grout_calculation.get('amounts')
            num_boreholes = grout_calculation.get('num_boreholes', 1)
            volume_per_bh = grout_calculation.get('volume_per_bh', 0)
            total_volume = volume_per_bh * num_boreholes
            
            # Material-Info
            material_info = Paragraph(
                f"<b>Material:</b> {material.name}<br/>"
                f"<b>Wärmeleitfähigkeit:</b> {material.thermal_conductivity} W/m·K<br/>"
                f"<b>Dichte:</b> {material.density} kg/m³<br/>"
                f"<b>Preis:</b> {material.price_per_kg} EUR/kg",
                self.styles['CustomBody']
            )
            story.append(material_info)
            story.append(Spacer(1, 0.5*cm))
            
            # Mengen-Tabelle mit Liter!
            grout_data = [
                ['Parameter', 'Wert', 'Einheit'],
                ['Volumen pro Bohrung', f"{volume_per_bh:.3f} m³ ({volume_per_bh*1000:.1f} Liter)", ''],
                ['Volumen gesamt', f"{total_volume:.3f} m³ ({total_volume*1000:.1f} Liter)", ''],
                ['Masse gesamt', f"{amounts['mass_kg']:.1f}", 'kg'],
                ['Säcke (25 kg)', f"{amounts['bags_25kg']:.1f}", 'Stück'],
                ['Kosten gesamt', f"{amounts['total_cost_eur']:.2f}", 'EUR'],
                ['Kosten pro Meter', f"{amounts['cost_per_m']:.2f}", 'EUR/m']
            ]
            
            grout_table = Table(grout_data, colWidths=[9*cm, 6*cm, 2*cm])
            grout_table.setStyle(self._get_table_style())
            story.append(grout_table)
            story.append(Spacer(1, 1*cm))
        
        # === WÄRMETRÄGERFLUID (NEU) ===
        if fluid_info:
            story.append(Paragraph("Wärmeträgerfluid", self.styles['CustomHeading']))
            
            fluid_data = [
                ['Parameter', 'Wert', 'Einheit'],
                ['Fluid', fluid_info.get('name', 'N/A'), ''],
                ['Typ', fluid_info.get('type', 'N/A'), ''],
                ['Konzentration', f"{fluid_info.get('concentration_percent', 0):.1f}", '%'],
                ['Frostschutz bis', f"{fluid_info.get('min_temp', 0):.1f}", '°C'],
                ['Max. Betriebstemp.', f"{fluid_info.get('max_temp', 95):.1f}", '°C'],
                ['Dichte (bei Betriebstemp.)', f"{fluid_info.get('density', 0):.1f}", 'kg/m³'],
                ['Viskosität (bei Betriebstemp.)', f"{fluid_info.get('viscosity', 0):.6f}", 'Pa·s'],
                ['Wärmeleitfähigkeit', f"{fluid_info.get('thermal_conductivity', 0):.3f}", 'W/m·K'],
                ['Wärmekapazität', f"{fluid_info.get('heat_capacity', 0):.1f}", 'J/kg·K']
            ]
            
            fluid_table = Table(fluid_data, colWidths=[9*cm, 5*cm, 3*cm])
            fluid_table.setStyle(self._get_table_style())
            story.append(fluid_table)
            story.append(Spacer(1, 1*cm))
        
        # === HYDRAULIK-BERECHNUNG ===
        if hydraulics_result:
            story.append(Paragraph("Hydraulik-Berechnung", self.styles['CustomHeading']))
            
            # Unterstütze neue Datenstruktur (flow, system, pump) und alte Struktur
            flow = hydraulics_result.get('flow', {})
            system = hydraulics_result.get('system', {})
            pump = hydraulics_result.get('pump', {})
            
            # Neue Struktur
            if flow and system and pump:
                volume_flow_m3h = flow.get('volume_flow_m3_h', 0)
                volume_flow_lmin = flow.get('volume_flow_l_min', 0)
                total_pressure_drop_bar = system.get('total_pressure_drop_bar', 0)
                total_pressure_drop_mbar = system.get('total_pressure_drop_mbar', 0)
                pressure_drop_borehole = system.get('pressure_drop_borehole_bar', 0)
                reynolds = system.get('reynolds', 0)
                velocity = system.get('velocity_m_s', 0)
                hydraulic_power = pump.get('hydraulic_power_w', 0)
                electric_power = pump.get('electric_power_w', 0)
                electric_power_kw = pump.get('electric_power_kw', 0)
            else:
                # Alte Struktur (Fallback)
                volume_flow_m3h = hydraulics_result.get('volume_flow_m3_h', 0)
                volume_flow_lmin = volume_flow_m3h * 1000 / 60
                total_pressure_drop_mbar = hydraulics_result.get('total_pressure_drop_mbar', 0)
                total_pressure_drop_bar = total_pressure_drop_mbar / 1000
                pressure_drop_borehole = hydraulics_result.get('pressure_drop_per_borehole_mbar', 0) / 1000
                reynolds = hydraulics_result.get('reynolds_number', 0)
                velocity = 0
                hydraulic_power = hydraulics_result.get('pump_power_w', 0)
                electric_power = hydraulic_power
                electric_power_kw = electric_power / 1000
            
            hydraulics_data = [
                ['Parameter', 'Wert', 'Einheit'],
                ['Volumenstrom (gesamt)', f"{volume_flow_m3h:.3f}", 'm³/h'],
                ['Volumenstrom', f"{volume_flow_lmin:.2f}", 'L/min'],
                ['Strömungsgeschwindigkeit', f"{velocity:.2f}", 'm/s'],
                ['Reynolds-Zahl', f"{reynolds:.0f}", '-'],
                ['Druckverlust Bohrungen', f"{pressure_drop_borehole:.2f}", 'bar'],
                ['System-Gesamtdruckverlust', f"{total_pressure_drop_bar:.2f}", 'bar'],
                ['System-Gesamtdruckverlust', f"{total_pressure_drop_mbar:.0f}", 'mbar'],
                ['Hydraulische Pumpenleistung', f"{hydraulic_power:.0f}", 'W'],
                ['Elektrische Pumpenleistung', f"{electric_power:.0f}", 'W'],
                ['Elektrische Pumpenleistung', f"{electric_power_kw:.2f}", 'kW']
            ]
            
            hydraulics_table = Table(hydraulics_data, colWidths=[9*cm, 5*cm, 3*cm])
            hydraulics_table.setStyle(self._get_table_style())
            story.append(hydraulics_table)
            story.append(Spacer(1, 1*cm))
        
        # === VDI 4640 BERECHNUNGSERGEBNISSE (NEU in V3.2) ===
        if vdi4640_result:
            story.append(PageBreak())
            story.append(Paragraph("VDI 4640 Berechnungsergebnisse", self.styles['CustomHeading']))
            story.append(Spacer(1, 0.5*cm))
            
            # Auslegungsfall
            design_case = vdi4640_result.design_case if hasattr(vdi4640_result, 'design_case') else vdi4640_result.get('design_case', 'N/A')
            story.append(Paragraph(f"<b>Auslegungsfall:</b> {design_case.upper()}", self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*cm))
            
            # Sondenlängen
            vdi_data = [
                ['Parameter', 'Wert', 'Einheit'],
                ['Erforderliche Sondenlänge (Heizen)', f"{vdi4640_result.required_depth_heating if hasattr(vdi4640_result, 'required_depth_heating') else vdi4640_result.get('required_depth_heating', 0):.1f}", 'm'],
                ['Erforderliche Sondenlänge (Kühlen)', f"{vdi4640_result.required_depth_cooling if hasattr(vdi4640_result, 'required_depth_cooling') else vdi4640_result.get('required_depth_cooling', 0):.1f}", 'm'],
                ['Ausgelegte Sondenlänge', f"{vdi4640_result.required_depth_final if hasattr(vdi4640_result, 'required_depth_final') else vdi4640_result.get('required_depth_final', 0):.1f}", 'm'],
                ['Min. WP-Austrittstemp. (Heizen)', f"{vdi4640_result.t_wp_aus_heating_min if hasattr(vdi4640_result, 't_wp_aus_heating_min') else vdi4640_result.get('t_wp_aus_heating_min', 0):.2f}", '°C'],
                ['Max. WP-Austrittstemp. (Kühlen)', f"{vdi4640_result.t_wp_aus_cooling_max if hasattr(vdi4640_result, 't_wp_aus_cooling_max') else vdi4640_result.get('t_wp_aus_cooling_max', 0):.2f}", '°C']
            ]
            
            vdi_table = Table(vdi_data, colWidths=[9*cm, 5*cm, 3*cm])
            vdi_table.setStyle(self._get_table_style())
            story.append(vdi_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Thermische Widerstände
            story.append(Paragraph("Thermische Widerstände:", self.styles['CustomBody']))
            resistances_data = [
                ['Parameter', 'Wert', 'Einheit'],
                ['R_Grundlast (10 Jahre)', f"{vdi4640_result.r_grundlast if hasattr(vdi4640_result, 'r_grundlast') else vdi4640_result.get('r_grundlast', 0):.6f}", 'm·K/W'],
                ['R_Periodisch (1 Monat)', f"{vdi4640_result.r_per if hasattr(vdi4640_result, 'r_per') else vdi4640_result.get('r_per', 0):.6f}", 'm·K/W'],
                ['R_Peak (6 Stunden)', f"{vdi4640_result.r_peak if hasattr(vdi4640_result, 'r_peak') else vdi4640_result.get('r_peak', 0):.6f}", 'm·K/W'],
                ['R_Bohrloch', f"{vdi4640_result.r_borehole if hasattr(vdi4640_result, 'r_borehole') else vdi4640_result.get('r_borehole', 0):.6f}", 'm·K/W']
            ]
            
            resistances_table = Table(resistances_data, colWidths=[9*cm, 5*cm, 3*cm])
            resistances_table.setStyle(self._get_table_style())
            story.append(resistances_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Lasten
            story.append(Paragraph("Lasten:", self.styles['CustomBody']))
            loads_data = [
                ['Lasttyp', 'Heizen [kW]', 'Kühlen [kW]'],
                ['Nettogrundlast', 
                 f"{vdi4640_result.q_nettogrundlast_heating/1000 if hasattr(vdi4640_result, 'q_nettogrundlast_heating') else vdi4640_result.get('q_nettogrundlast_heating', 0)/1000:.3f}",
                 f"{vdi4640_result.q_nettogrundlast_cooling/1000 if hasattr(vdi4640_result, 'q_nettogrundlast_cooling') else vdi4640_result.get('q_nettogrundlast_cooling', 0)/1000:.3f}"],
                ['Periodisch', 
                 f"{vdi4640_result.q_per_heating/1000 if hasattr(vdi4640_result, 'q_per_heating') else vdi4640_result.get('q_per_heating', 0)/1000:.3f}",
                 f"{vdi4640_result.q_per_cooling/1000 if hasattr(vdi4640_result, 'q_per_cooling') else vdi4640_result.get('q_per_cooling', 0)/1000:.3f}"],
                ['Peak', 
                 f"{vdi4640_result.q_peak_heating/1000 if hasattr(vdi4640_result, 'q_peak_heating') else vdi4640_result.get('q_peak_heating', 0)/1000:.3f}",
                 f"{vdi4640_result.q_peak_cooling/1000 if hasattr(vdi4640_result, 'q_peak_cooling') else vdi4640_result.get('q_peak_cooling', 0)/1000:.3f}"]
            ]
            
            loads_table = Table(loads_data, colWidths=[6*cm, 5*cm, 5*cm])
            loads_table.setStyle(self._get_table_style())
            story.append(loads_table)
            story.append(Spacer(1, 1*cm))
        
        # === BOHRFELD-SIMULATION (NEU in V3.2) ===
        if borefield_result:
            story.append(PageBreak())
            story.append(Paragraph("Bohrfeld-Simulation (g-Funktionen)", self.styles['CustomHeading']))
            story.append(Spacer(1, 0.5*cm))
            
            # Bohrfeld-Informationen
            story.append(Paragraph("Konfiguration:", self.styles['CustomBody']))
            borefield_info_data = [
                ['Parameter', 'Wert'],
                ['Layout', borefield_result.get('layout', 'N/A').upper()],
                ['Anzahl Bohrungen', str(borefield_result.get('num_boreholes', 0))],
                ['Gesamttiefe', f"{borefield_result.get('total_depth', 0)} m"],
                ['Feldgröße', f"{borefield_result.get('field_area', 0):.1f} m²"],
                ['Abstand X', f"{borefield_result.get('spacing_x', 0)} m"],
                ['Abstand Y', f"{borefield_result.get('spacing_y', 0)} m"],
                ['Simulationsjahre', str(borefield_result.get('simulation_years', 0))]
            ]
            
            borefield_info_table = Table(borefield_info_data, colWidths=[9*cm, 8*cm])
            borefield_info_table.setStyle(self._get_table_style())
            story.append(borefield_info_table)
            story.append(Spacer(1, 1*cm))
            
            # Erstelle Bohrfeld-Visualisierung
            borefield_layout_path = self._create_borefield_layout_plot(borefield_result)
            gfunction_path = self._create_gfunction_plot(borefield_result)
            
            if borefield_layout_path and os.path.exists(borefield_layout_path):
                story.append(Paragraph("Bohrfeld-Layout:", self.styles['CustomBody']))
                img = Image(borefield_layout_path, width=12*cm, height=10*cm)
                story.append(img)
                story.append(Spacer(1, 0.5*cm))
            
            if gfunction_path and os.path.exists(gfunction_path):
                story.append(Paragraph("g-Funktions-Verlauf:", self.styles['CustomBody']))
                img = Image(gfunction_path, width=14*cm, height=9*cm)
                story.append(img)
                story.append(Spacer(1, 0.5*cm))
        
        # === VISUALISIERUNGEN ===
        story.append(PageBreak())
        story.append(Paragraph("Visualisierungen", self.styles['CustomHeading']))
        
        # Erstelle Diagramme
        temp_plot_path = self._create_temperature_plot(result)
        borehole_plot_path = self._create_detailed_borehole_plot(params, result)
        static_borehole_path = self._create_static_borehole_graphic(params)
        
        if temp_plot_path and os.path.exists(temp_plot_path):
            story.append(Paragraph("Monatliche Fluidtemperaturen", self.styles['CustomBody']))
            img = Image(temp_plot_path, width=16*cm, height=10*cm)
            story.append(img)
            story.append(Spacer(1, 0.5*cm))
        
        if static_borehole_path and os.path.exists(static_borehole_path):
            story.append(Paragraph("Erdsonden-Aufbau (4-Rohr-System)", self.styles['CustomBody']))
            img = Image(static_borehole_path, width=10*cm, height=14*cm)
            story.append(img)
            story.append(Spacer(1, 0.5*cm))
        
        if borehole_plot_path and os.path.exists(borehole_plot_path):
            story.append(PageBreak())
            story.append(Paragraph("Bohrloch-Schema mit Berechnungswerten", self.styles['CustomBody']))
            img = Image(borehole_plot_path, width=16*cm, height=12*cm)
            story.append(img)
        
        # === FUSSNOTE ===
        story.append(Spacer(1, 2*cm))
        footer = Paragraph(
            "<para align='center'><font size=8>"
            "Dieser Bericht wurde automatisch mit dem Geothermie Erdsonden-Berechnungstool V3.2.1 erstellt.<br/>"
            "Open Source Software - MIT Lizenz<br/>"
            "Berechnungen nach VDI 4640, Eskilson (1987), Hellström (1991) und pygfunction (2024)"
            "</font></para>",
            self.styles['Normal']
        )
        story.append(footer)
        
        # PDF bauen
        doc.build(story)
        
        # Temporäre Dateien löschen
        temp_files = [temp_plot_path, borehole_plot_path, static_borehole_path]
        if borefield_result:
            borefield_layout_path = self._create_borefield_layout_plot(borefield_result)
            gfunction_path = self._create_gfunction_plot(borefield_result)
            temp_files.extend([borefield_layout_path, gfunction_path])
        
        for temp_file in temp_files:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def _get_table_style(self):
        """Gibt einen Standard-Tabellenstyle zurück."""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ])
    
    def _create_temperature_plot(self, result):
        """Erstellt das Temperatur-Diagramm."""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            months = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
            x = range(len(months))
            
            ax.plot(x, result.monthly_temperatures, 'o-', linewidth=2.5, 
                   markersize=8, color='#1f4788', label='Monatliche Temperatur')
            ax.axhline(y=result.fluid_temperature_min, color='blue', linestyle='--', 
                      linewidth=2, label=f'Min: {result.fluid_temperature_min:.1f}°C')
            ax.axhline(y=result.fluid_temperature_max, color='red', linestyle='--',
                      linewidth=2, label=f'Max: {result.fluid_temperature_max:.1f}°C')
            
            ax.set_xlabel('Monat', fontsize=14, fontweight='bold')
            ax.set_ylabel('Temperatur [°C]', fontsize=14, fontweight='bold')
            ax.set_title('Jahresverlauf der Fluidtemperatur', fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(months)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(fontsize=12, loc='best')
            
            plt.tight_layout()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            return temp_file.name
        except Exception as e:
            print(f"Fehler beim Erstellen des Temperatur-Plots: {e}")
            return None
    
    def _create_detailed_borehole_plot(self, params, result):
        """Erstellt eine detaillierte Bohrloch-Grafik mit Beschriftungen."""
        try:
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Bohrloch-Parameter
            depth = result.required_depth
            bh_diameter = params.get('borehole_diameter', 0.152)
            pipe_diameter = params.get('pipe_outer_diameter', 0.040)
            
            # Skalierung für bessere Darstellung
            scale = 100  # cm
            depth_cm = depth * scale
            bh_radius_cm = (bh_diameter / 2) * scale
            pipe_radius_cm = (pipe_diameter / 2) * scale
            
            # Bohrloch zeichnen
            borehole = Rectangle(
                (-bh_radius_cm, 0), 2*bh_radius_cm, depth_cm,
                facecolor='#d9d9d9', edgecolor='black', linewidth=2
            )
            ax.add_patch(borehole)
            
            # 4 Rohre zeichnen (typische Position für 4-Rohr-System)
            pipe_positions = [
                (-bh_radius_cm*0.5, depth_cm*0.5),  # Links oben
                (bh_radius_cm*0.5, depth_cm*0.5),   # Rechts oben
                (-bh_radius_cm*0.5, depth_cm*0.8),  # Links unten
                (bh_radius_cm*0.5, depth_cm*0.8)    # Rechts unten
            ]
            
            colors_pipes = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']
            labels_pipes = ['Vorlauf 1', 'Rücklauf 1', 'Vorlauf 2', 'Rücklauf 2']
            
            for i, ((x, y), color, label) in enumerate(zip(pipe_positions, colors_pipes, labels_pipes)):
                pipe = Circle((x, y), pipe_radius_cm*2, 
                            facecolor=color, edgecolor='black', linewidth=1.5,
                            alpha=0.8, label=label if i < 2 else '')
                ax.add_patch(pipe)
                
                # Beschriftung
                ax.text(x, y, str(i+1), ha='center', va='center', 
                       fontsize=10, fontweight='bold', color='white')
            
            # Beschriftungen mit Pfeilen
            # Bohrtiefe
            ax.annotate(f'Bohrtiefe:\n{depth:.1f} m', 
                       xy=(bh_radius_cm*1.5, depth_cm/2),
                       xytext=(bh_radius_cm*3, depth_cm/2),
                       fontsize=12, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))
            
            # Bohrloch-Durchmesser
            ax.plot([0, 0], [-bh_radius_cm*1.5, 0], 'k-', linewidth=1)
            ax.plot([-bh_radius_cm, bh_radius_cm], [-bh_radius_cm, -bh_radius_cm], 'k-', linewidth=2)
            ax.plot([-bh_radius_cm, -bh_radius_cm], [-bh_radius_cm*1.2, -bh_radius_cm*0.8], 'k-', linewidth=2)
            ax.plot([bh_radius_cm, bh_radius_cm], [-bh_radius_cm*1.2, -bh_radius_cm*0.8], 'k-', linewidth=2)
            ax.text(0, -bh_radius_cm*2, f'Ø {bh_diameter*1000:.0f} mm',
                   ha='center', fontsize=11, fontweight='bold')
            
            # Wärmeentzugsrate
            ax.annotate(f'Wärmeentzug:\n{result.heat_extraction_rate:.1f} W/m',
                       xy=(-bh_radius_cm*1.5, depth_cm*0.2),
                       xytext=(-bh_radius_cm*4, depth_cm*0.2),
                       fontsize=12, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', lw=2, color='blue'))
            
            # Temperaturbereich
            temp_text = f'Fluid-Temp:\n{result.fluid_temperature_min:.1f}°C bis {result.fluid_temperature_max:.1f}°C'
            ax.annotate(temp_text,
                       xy=(bh_radius_cm*1.5, depth_cm*0.8),
                       xytext=(bh_radius_cm*3, depth_cm*0.8),
                       fontsize=11, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', lw=2, color='red'))
            
            # Rohrdurchmesser
            ax.annotate(f'Rohr Ø {pipe_diameter*1000:.0f} mm',
                       xy=pipe_positions[0],
                       xytext=(-bh_radius_cm*4, depth_cm*0.5),
                       fontsize=10,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
            
            # Titel und Achsen
            ax.set_title('Erdwärmesonden-Schema (4-Rohr-System)', 
                        fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Breite [cm]', fontsize=12)
            ax.set_ylabel('Tiefe [cm]', fontsize=12)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.2, linestyle='--')
            ax.legend(loc='upper right', fontsize=10)
            
            # Achsengrenzen
            ax.set_xlim(-bh_radius_cm*5, bh_radius_cm*4)
            ax.set_ylim(-bh_radius_cm*3, depth_cm*1.1)
            ax.invert_yaxis()
            
            plt.tight_layout()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            return temp_file.name
        except Exception as e:
            print(f"Fehler beim Erstellen des Bohrloch-Plots: {e}")
            return None
    
    def _create_static_borehole_graphic(self, params):
        """Erstellt eine statische Erklärungsgrafik einer Erdsonde mit 4 Leitungen (wie in der GUI)."""
        try:
            from matplotlib.patches import Arc
            
            fig, ax = plt.subplots(figsize=(5.5, 8), facecolor='white')
            
            # === SEITLICHE ANSICHT (Schnitt durch Sonde) ===
            # Boden (braun)
            ground = Rectangle((0, 0), 10, 15, facecolor='#8B4513', alpha=0.3)
            ax.add_patch(ground)
            
            # Bohrloch (hellgrau) - EIN Bohrloch mit 4 Leitungen ENGER zusammen
            borehole_width = 1.0
            borehole_center = 5.0
            borehole = Rectangle((borehole_center - borehole_width/2, 0), borehole_width, 15, 
                                facecolor='#d9d9d9', edgecolor='black', linewidth=2)
            ax.add_patch(borehole)
            
            # 4 Leitungen ENGER zusammen
            spacing = 0.2
            center_offset = spacing * 1.5
            
            # Rohr 1 & 2 (links im Bohrloch)
            ax.plot([borehole_center - center_offset, borehole_center - center_offset], [0, 15], 
                   color='#ff6b6b', linewidth=5, solid_capstyle='round')
            ax.plot([borehole_center - center_offset + spacing, borehole_center - center_offset + spacing], [0, 15], 
                   color='#4ecdc4', linewidth=5, solid_capstyle='round')
            
            # Rohr 3 & 4 (rechts im Bohrloch)
            ax.plot([borehole_center + center_offset - spacing, borehole_center + center_offset - spacing], [0, 15], 
                   color='#ff6b6b', linewidth=5, solid_capstyle='round')
            ax.plot([borehole_center + center_offset, borehole_center + center_offset], [0, 15], 
                   color='#4ecdc4', linewidth=5, solid_capstyle='round')
            
            # U-Bogen unten
            arc1 = Arc((borehole_center - center_offset + spacing/2, 0.3), spacing*1.5, 0.4, 
                      angle=0, theta1=180, theta2=360, color='black', linewidth=2)
            arc2 = Arc((borehole_center + center_offset - spacing/2, 0.3), spacing*1.5, 0.4, 
                      angle=0, theta1=180, theta2=360, color='black', linewidth=2)
            ax.add_patch(arc1)
            ax.add_patch(arc2)
            
            # === BESCHRIFTUNGEN ===
            bh_left = borehole_center - borehole_width/2
            bh_right = borehole_center + borehole_width/2
            bh_diameter = params.get('borehole_diameter', 0.152)
            
            # Durchmesser
            ax.annotate('', xy=(bh_left, 16), xytext=(bh_right, 16),
                       arrowprops=dict(arrowstyle='<->', color='black', lw=2))
            ax.text(borehole_center, 16.6, f'Bohrloch Ø {bh_diameter*1000:.0f}mm', ha='center', fontsize=12, 
                   fontweight='bold', bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', edgecolor='black'))
            
            # Tiefe
            ax.annotate('', xy=(0.5, 0), xytext=(0.5, 15),
                       arrowprops=dict(arrowstyle='<->', color='#2196f3', lw=2))
            ax.text(-0.3, 7.5, 'Tiefe\nbis 100m', ha='center', fontsize=11, 
                   fontweight='bold', color='#1976d2', rotation=90,
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#2196f3'))
            
            # Verfüllung
            ax.text(borehole_center, 10, 'Verfüllung\n(Zement-Bentonit)', ha='center', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#e0e0e0', edgecolor='black'))
            
            # Rohrmaterial
            ax.text(7.5, 12, 'PE 100 RC\nØ 32mm', ha='left', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black'))
            ax.annotate('', xy=(bh_right + 0.1, 12), xytext=(7.3, 12),
                       arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
            
            # === QUERSCHNITT (größer, ohne Text - nur Nummern) ===
            from matplotlib.transforms import Bbox
            ax_inset = fig.add_axes([0.58, 0.52, 0.38, 0.42])
            
            # Bohrloch-Kreis
            bh_circle = Circle((0, 0), 1, facecolor='#d9d9d9', edgecolor='black', linewidth=2.5)
            ax_inset.add_patch(bh_circle)
            
            # 4 Rohre in QUADRAT-Anordnung
            positions = [(-0.35, 0.35), (0.35, 0.35), (-0.35, -0.35), (0.35, -0.35)]
            colors_pipes = ['#ff6b6b', '#4ecdc4', '#ff6b6b', '#4ecdc4']
            
            for i, ((x, y), color) in enumerate(zip(positions, colors_pipes)):
                pipe_circle = Circle((x, y), 0.2, facecolor=color, edgecolor='black', linewidth=1.5)
                ax_inset.add_patch(pipe_circle)
                ax_inset.text(x, y, str(i+1), ha='center', va='center', 
                             fontsize=12, fontweight='bold', color='white')
            
            ax_inset.set_xlim(-1.1, 1.1)
            ax_inset.set_ylim(-1.1, 1.1)
            ax_inset.set_aspect('equal')
            ax_inset.axis('off')
            
            # Hauptgrafik-Einstellungen
            ax.set_xlim(0, 9)
            ax.set_ylim(-1, 18)
            ax.set_aspect('equal')
            ax.axis('off')
            
            fig.tight_layout()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            return temp_file.name
        except Exception as e:
            print(f"Fehler beim Erstellen der statischen Bohrloch-Grafik: {e}")
            return None
    
    def _create_borefield_layout_plot(self, borefield_result):
        """Erstellt Plot des Bohrfeld-Layouts für PDF."""
        try:
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Extrahiere Bohrfeld-Daten
            boreField = borefield_result.get('boreField')
            if not boreField:
                return None
            
            x_coords = [b.x for b in boreField]
            y_coords = [b.y for b in boreField]
            
            # Plotte Bohrungen
            ax.scatter(x_coords, y_coords, s=300, c='#1f4788', alpha=0.7, 
                      edgecolors='black', linewidths=2, zorder=3)
            
            # Nummerierung
            for i, (x, y) in enumerate(zip(x_coords, y_coords), 1):
                ax.text(x, y, str(i), ha='center', va='center', 
                       color='white', fontweight='bold', fontsize=12, zorder=4)
            
            # Verbindungslinien (nur für Visualisierung der Abstände)
            if len(x_coords) > 1:
                # Horizontale Linien
                for i in range(len(x_coords)-1):
                    if abs(y_coords[i] - y_coords[i+1]) < 0.1:  # Gleiche Y-Position
                        ax.plot([x_coords[i], x_coords[i+1]], [y_coords[i], y_coords[i+1]], 
                               'k--', alpha=0.3, linewidth=1, zorder=1)
            
            ax.set_xlabel('X-Position [m]', fontsize=12, fontweight='bold')
            ax.set_ylabel('Y-Position [m]', fontsize=12, fontweight='bold')
            ax.set_title(
                f'Bohrfeld-Layout: {borefield_result.get("layout", "N/A").upper()}\n'
                f'{borefield_result.get("num_boreholes", 0)} Bohrungen, '
                f'Feldgröße: {borefield_result.get("field_area", 0):.1f} m²',
                fontsize=14, fontweight='bold', pad=15
            )
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_aspect('equal')
            
            # Legende mit Info
            info_text = (
                f'Abstand X: {borefield_result.get("spacing_x", 0)} m\n'
                f'Abstand Y: {borefield_result.get("spacing_y", 0)} m\n'
                f'Tiefe: {borefield_result.get("borehole_depth", 0)} m'
            )
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            
            # Speichere in temporäre Datei
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            return temp_file.name
        except Exception as e:
            print(f"Fehler beim Erstellen des Bohrfeld-Layout-Plots: {e}")
            return None
    
    def _create_gfunction_plot(self, borefield_result):
        """Erstellt Plot der g-Funktion für PDF."""
        try:
            import numpy as np
            
            fig, ax = plt.subplots(figsize=(12, 7))
            
            # Extrahiere g-Funktions-Daten
            gFunc = borefield_result.get('gFunction')
            time = borefield_result.get('time')
            
            if not gFunc or not time:
                return None
            
            # Zeit in Jahre umrechnen
            time_years = time / (365.25 * 24 * 3600)
            
            # Plotte g-Funktion
            ax.plot(time_years, gFunc.gFunc, 'b-', linewidth=2.5, label='g-Funktion')
            
            # Markiere wichtige Zeitpunkte
            milestones = [1, 5, 10, 20, 25]
            for milestone in milestones:
                if milestone <= time_years[-1]:
                    idx = np.argmin(np.abs(time_years - milestone))
                    ax.plot(time_years[idx], gFunc.gFunc[idx], 'ro', markersize=8, zorder=5)
                    ax.text(time_years[idx], gFunc.gFunc[idx] + 0.1, f'{milestone}a',
                           ha='center', fontsize=9, fontweight='bold')
            
            ax.set_xlabel('Zeit [Jahre]', fontsize=12, fontweight='bold')
            ax.set_ylabel('g-Funktion [-]', fontsize=12, fontweight='bold')
            ax.set_title(
                f'Thermische Response-Funktion (g-Funktion)\n'
                f'Simulation über {borefield_result.get("simulation_years", 0)} Jahre',
                fontsize=14, fontweight='bold', pad=15
            )
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(loc='lower right', fontsize=11)
            
            # Info-Box
            info_text = (
                f'Bohrungen: {borefield_result.get("num_boreholes", 0)}\n'
                f'Gesamttiefe: {borefield_result.get("total_depth", 0)} m\n'
                f'Layout: {borefield_result.get("layout", "N/A").upper()}'
            )
            ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            
            # Speichere in temporäre Datei
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            return temp_file.name
        except Exception as e:
            print(f"Fehler beim Erstellen des g-Funktions-Plots: {e}")
            return None


if __name__ == "__main__":
    print("PDF-Export-Modul geladen")

