"""
Trading module for OFI-based signal generation and trade path simulation.
"""

from .ofi_signals import generate_ofi_signals
from .trade_path_simulator import simulate_trade_paths

__all__ = [
    'generate_ofi_signals',
    'simulate_trade_paths',
]

