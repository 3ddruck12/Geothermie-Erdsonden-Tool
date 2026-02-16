"""GUI Tab-Module für die modulare Professional Edition.

Extrahiert aus der God-Class GeothermieGUIProfessional (V3.4 Refactoring).
"""

from gui.tabs.input_tab import InputTab
from gui.tabs.results_tab import ResultsTab
from gui.tabs.materials_tab import MaterialsTab
from gui.tabs.diagrams_tab import DiagramsTab
from gui.tabs.borefield_tab import BorefieldTab

__all__ = [
    'InputTab',
    'ResultsTab',
    'MaterialsTab',
    'DiagramsTab',
    'BorefieldTab',
]
