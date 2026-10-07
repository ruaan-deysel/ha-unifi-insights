"""NVR endpoint for UniFi Protect API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models import NVR

if TYPE_CHECKING:
    from ..client import UniFiProtectClient


class NVREndpoint:
    """Endpoint for managing UniFi Protect NVR."""

    def __init__(self, client: UniFiProtectClient) -> None:
        """
        Initialize the NVR endpoint.

        Args:
            client: The UniFi Protect client.

        """
        self._client = client

    async def get(self, site_id: str | None = None) -> NVR:
        """
        Get NVR information.

        Args:
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            The NVR information.

        """
        path = self._client.build_api_path("/nvrs", site_id)
        response = await self._client._get(path)

        if isinstance(response, dict):
            data = response.get("data", response)
            if isinstance(data, dict):
                return NVR.model_validate(data)
            if isinstance(data, list) and len(data) > 0:
                return NVR.model_validate(data[0])
        raise ValueError("NVR not found")
