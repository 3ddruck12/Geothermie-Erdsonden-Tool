"""Berechnungsmodule für Erdwärmesonden."""

from .borehole import BoreholeCalculator
from .thermal import ThermalResistanceCalculator
from .g_functions import GFunctionCalculator
from .hydraulics import HydraulicsCalculator
from .vdi4640 import VDI4640Calculator

try:
    from .borefield_gfunction import BorefieldGFunction
except ImportError:
    BorefieldGFunction = None  # pygfunction optional

__all__ = [
    'BoreholeCalculator',
    'ThermalResistanceCalculator', 
    'GFunctionCalculator',
    'HydraulicsCalculator',
    'VDI4640Calculator',
    'BorefieldGFunction',
]









