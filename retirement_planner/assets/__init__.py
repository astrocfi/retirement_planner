"""
Asset classes for retirement planning.

Contains base asset class and specific asset type implementations.
"""

from .base import Asset, AssetFactory, AssetAllocation

__all__ = [
    'Asset', 'AssetFactory', 'AssetAllocation',
]