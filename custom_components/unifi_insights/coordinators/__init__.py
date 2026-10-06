"""Multi-coordinator architecture for UniFi Insights (Platinum compliance)."""

from __future__ import annotations

from .base import UnifiBaseCoordinator
from .carrier_fabric import UnifiCarrierFabricCoordinator
from .config import UnifiConfigCoordinator
from .device import UnifiDeviceCoordinator
from .facade import UnifiFacadeCoordinator
from .innerspace import UnifiInsightsInnerSpaceCoordinator
from .mobility import UnifiInsightsMobilityCoordinator
from .protect import UnifiProtectCoordinator
from .site_manager import UnifiInsightsSiteManagerCoordinator

__all__ = [
    "UnifiBaseCoordinator",
    "UnifiCarrierFabricCoordinator",
    "UnifiConfigCoordinator",
    "UnifiDeviceCoordinator",
    "UnifiFacadeCoordinator",
    "UnifiInsightsInnerSpaceCoordinator",
    "UnifiInsightsMobilityCoordinator",
    "UnifiInsightsSiteManagerCoordinator",
    "UnifiProtectCoordinator",
]
