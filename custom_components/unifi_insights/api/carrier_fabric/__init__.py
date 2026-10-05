# Copyright 2026 UniFi Insights contributors
"""UniFi Carrier Fabric API package."""

from __future__ import annotations

from .client import UniFiCarrierFabricClient
from .models import CarrierFabricMeta, ServicePlan, Subscriber

__all__ = [
    "CarrierFabricMeta",
    "ServicePlan",
    "Subscriber",
    "UniFiCarrierFabricClient",
]
