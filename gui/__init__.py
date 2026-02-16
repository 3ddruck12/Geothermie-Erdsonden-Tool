"""GUI-Module für das Geothermietool.

V3.4 Modulare Architektur:
- tabs/: InputTab, ResultsTab, MaterialsTab, DiagramsTab, BorefieldTab
- controllers/: CalculationController, FileController
- main_window_v3_professional.py: Koordinator-Klasse
"""

from .main_window_v3_professional import GeothermieGUIProfessional

__all__ = ['GeothermieGUIProfessional']
