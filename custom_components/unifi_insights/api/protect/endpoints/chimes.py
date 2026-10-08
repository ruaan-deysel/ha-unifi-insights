"""Chimes endpoint for UniFi Protect API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from ..models import Chime

if TYPE_CHECKING:
    from ..client import UniFiProtectClient

_LOGGER = logging.getLogger(__name__)

# Fields of one ringSettings entry. The v7.3.70 chime PATCH requires all four
# and rejects any other key.
_RING_SETTINGS_FIELDS = ("cameraId", "repeatTimes", "ringtoneId", "volume")


class ChimesEndpoint:
    """Endpoint for managing UniFi Protect chimes."""

    def __init__(self, client: UniFiProtectClient) -> None:
        """
        Initialize the chimes endpoint.

        Args:
            client: The UniFi Protect client.

        """
        self._client = client
        # False when the most recent get_all() silently dropped an item on a
        # ValidationError. Callers need to tell a complete listing from a short
        # one: a device absent because its payload would not parse is still
        # adopted, and must not be treated as removed.
        self.last_result_complete: bool = True

    async def get_all(self, site_id: str | None = None) -> list[Chime]:
        """
        List all chimes.

        Args:
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            List of chimes.

        """
        path = self._client.build_api_path("/chimes", site_id)
        self.last_result_complete = True
        response = await self._client._get(path)

        if response is None:
            return []

        data = (
            response.get("data", response) if isinstance(response, dict) else response
        )
        if not isinstance(data, list):
            return []

        chimes: list[Chime] = []
        for item in data:
            try:
                chimes.append(Chime.model_validate(item))
            except ValidationError as err:
                self.last_result_complete = False
                _LOGGER.warning(
                    "Skipping chime that failed to parse (id=%s): %s",
                    item.get("id") if isinstance(item, dict) else "?",
                    err,
                )
        return chimes

    async def get(self, chime_id: str, site_id: str | None = None) -> Chime:
        """
        Get a specific chime.

        Args:
            chime_id: The chime ID.
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            The chime.

        """
        path = self._client.build_api_path(f"/chimes/{chime_id}", site_id)
        response = await self._client._get(path)

        if isinstance(response, dict):
            data = response.get("data", response)
            if isinstance(data, dict):
                return Chime.model_validate(data)
            if isinstance(data, list) and len(data) > 0:
                return Chime.model_validate(data[0])
        raise ValueError(f"Chime {chime_id} not found")

    async def update(
        self,
        chime_id: str,
        site_id: str | None = None,
        **kwargs: Any,
    ) -> Chime:
        """
        Update chime settings.

        Args:
            chime_id: The chime ID.
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).
            **kwargs: Settings to update.

        Returns:
            The updated chime.

        """
        path = self._client.build_api_path(f"/chimes/{chime_id}", site_id)
        response = await self._client._patch(path, json_data=kwargs)

        if isinstance(response, dict):
            result = response.get("data", response)
            if isinstance(result, dict):
                return Chime.model_validate(result)
        raise ValueError("Failed to update chime")

    async def _update_ring_settings(
        self,
        chime_id: str,
        site_id: str | None,
        **changes: Any,
    ) -> Chime:
        """
        Change fields in every ringSettings entry of a chime.

        The chime PATCH body has no top-level volume, ringtone or repeat
        count: they are set per paired doorbell in ``ringSettings``. This
        reads the chime's current ring settings and sends them back with
        ``changes`` applied to each entry.

        Raises:
            ValueError: If the chime has no paired doorbell, or an entry lacks
                a field that isn't being changed.

        """
        chime = await self.get(chime_id, site_id)
        entries = (chime.model_extra or {}).get("ringSettings")
        if not entries:
            raise ValueError(
                f"Chime {chime_id} has no paired doorbell to apply ring settings to"
            )
        kept = [key for key in _RING_SETTINGS_FIELDS if key not in changes]
        if not isinstance(entries, list) or not all(
            isinstance(entry, dict) and all(key in entry for key in kept)
            for entry in entries
        ):
            raise ValueError(f"Chime {chime_id} has incomplete ring settings")
        ring_settings = [
            {key: entry[key] for key in kept} | changes for entry in entries
        ]
        return await self.update(chime_id, site_id, ringSettings=ring_settings)

    async def set_volume(
        self,
        chime_id: str,
        volume: int,
        site_id: str | None = None,
    ) -> Chime:
        """
        Set chime volume for every paired doorbell.

        Args:
            chime_id: The chime ID.
            volume: Volume level (0-100).
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            The updated chime.

        Raises:
            ValueError: If the volume is out of range, the chime has no paired
                doorbell to set it for, or an entry lacks a required field.

        """
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be between 0 and 100")
        return await self._update_ring_settings(chime_id, site_id, volume=volume)

    async def set_repeat_times(
        self,
        chime_id: str,
        repeat_times: int,
        site_id: str | None = None,
    ) -> Chime:
        """
        Set how many times the ringtone repeats, for every paired doorbell.

        Args:
            chime_id: The chime ID.
            repeat_times: Repeat count (1-10).
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            The updated chime.

        Raises:
            ValueError: If the count is out of range, the chime has no paired
                doorbell to set it for, or an entry lacks a required field.

        """
        if not 1 <= repeat_times <= 10:
            raise ValueError("Repeat times must be between 1 and 10")
        return await self._update_ring_settings(
            chime_id, site_id, repeatTimes=repeat_times
        )

    async def play(self, chime_id: str, site_id: str | None = None) -> bool:
        """
        Play the chime sound.

        Not in the Protect v7.3.70 OpenAPI (chimes are GET/PATCH only);
        route existence not yet live-verified.

        Args:
            chime_id: The chime ID.
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            True if successful.

        """
        path = self._client.build_api_path(f"/chimes/{chime_id}/play", site_id)
        await self._client._post(path)
        return True
