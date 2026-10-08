"""Siren endpoint for UniFi Protect API."""

from __future__ import annotations

from typing import Final

from ..models import Siren
from ._base import ProtectDeviceEndpoint

# Spec POST /v1/sirens/{id}/play body: ``duration`` is in SECONDS. The
# ``sirenStatus.duration`` the API reports back is in milliseconds.
SIREN_PLAY_DURATIONS: Final[tuple[int, ...]] = (5, 10, 20, 30)
# Spec PATCH /v1/sirens/{id} ``volume`` range (integer percent).
SIREN_VOLUME_MIN: Final = 1
SIREN_VOLUME_MAX: Final = 100


class SirensEndpoint(ProtectDeviceEndpoint[Siren]):
    """Endpoint for managing UniFi Protect sirens."""

    _resource = "sirens"
    _model = Siren

    async def play(
        self,
        siren_id: str,
        site_id: str | None = None,
        *,
        duration: int | None = None,
    ) -> bool:
        """
        Start playing a siren.

        Args:
            siren_id: The siren ID.
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).
            duration: Seconds to sound for; one of ``SIREN_PLAY_DURATIONS``.
                Omitted from the request when ``None`` so Protect uses its
                default.

        Returns:
            True if the request was accepted.

        Raises:
            ValueError: If ``duration`` is not an accepted value.

        """
        if duration is not None and duration not in SIREN_PLAY_DURATIONS:
            msg = f"Siren duration must be one of {SIREN_PLAY_DURATIONS} seconds"
            raise ValueError(msg)
        path = self._client.build_api_path(f"/sirens/{siren_id}/play", site_id)
        await self._client._post(
            path, json_data={"duration": duration} if duration is not None else None
        )
        return True

    async def set_volume(
        self,
        siren_id: str,
        volume: int,
        site_id: str | None = None,
    ) -> Siren:
        """
        Set the siren volume.

        Args:
            siren_id: The siren ID.
            volume: Volume level (1-100).
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            The updated siren.

        Raises:
            ValueError: If ``volume`` is outside the spec range.

        """
        if not SIREN_VOLUME_MIN <= volume <= SIREN_VOLUME_MAX:
            msg = (
                f"Siren volume must be between {SIREN_VOLUME_MIN} "
                f"and {SIREN_VOLUME_MAX}"
            )
            raise ValueError(msg)
        return await self.update(siren_id, site_id, volume=volume)

    async def stop(self, siren_id: str, site_id: str | None = None) -> bool:
        """
        Stop a playing siren.

        Args:
            siren_id: The siren ID.
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            True if the request was accepted.

        """
        path = self._client.build_api_path(f"/sirens/{siren_id}/stop", site_id)
        await self._client._post(path)
        return True

    async def test_sound(self, siren_id: str, site_id: str | None = None) -> bool:
        """
        Play the siren test sound.

        Args:
            siren_id: The siren ID.
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            True if the request was accepted.

        """
        path = self._client.build_api_path(f"/sirens/{siren_id}/test-sound", site_id)
        await self._client._post(path)
        return True
