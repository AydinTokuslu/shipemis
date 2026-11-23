"""shipemis – activity-based ship exhaust emission inventories.

Python implementation of the Trozzi & Vaccaro (MEET) and Entec UK Limited
methodologies as applied to the Istanbul Strait in Tokuşlu (2019).
"""
from . import entec, factors, io, trozzi

__all__ = ["entec", "factors", "io", "trozzi"]
__version__ = "0.1.0"
