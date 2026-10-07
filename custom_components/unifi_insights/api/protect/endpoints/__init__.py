"""Endpoint modules for UniFi Protect API."""

from __future__ import annotations

from .alarm_hubs import AlarmHubsEndpoint
from .application import ApplicationEndpoint
from .arm_profiles import ArmProfilesEndpoint
from .bridges import BridgesEndpoint
from .cameras import CamerasEndpoint
from .chimes import ChimesEndpoint
from .fobs import FobsEndpoint
from .lights import LightsEndpoint
from .link_stations import LinkStationsEndpoint
from .liveviews import LiveViewsEndpoint
from .nvr import NVREndpoint
from .pos import POSEndpoint
from .relays import RelaysEndpoint
from .sensors import SensorsEndpoint
from .sirens import SirensEndpoint
from .speakers import SpeakersEndpoint
from .ulp_users import UlpUsersEndpoint
from .users import UsersEndpoint
from .viewers import ViewersEndpoint

__all__ = [
    "AlarmHubsEndpoint",
    "ApplicationEndpoint",
    "ArmProfilesEndpoint",
    "BridgesEndpoint",
    "CamerasEndpoint",
    "ChimesEndpoint",
    "FobsEndpoint",
    "LightsEndpoint",
    "LinkStationsEndpoint",
    "LiveViewsEndpoint",
    "NVREndpoint",
    "POSEndpoint",
    "RelaysEndpoint",
    "SensorsEndpoint",
    "SirensEndpoint",
    "SpeakersEndpoint",
    "UlpUsersEndpoint",
    "UsersEndpoint",
    "ViewersEndpoint",
]
