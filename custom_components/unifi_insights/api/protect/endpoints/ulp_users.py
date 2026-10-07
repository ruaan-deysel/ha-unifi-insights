# Copyright (c) 2026 Ruaan Deysel
"""UniFi Identity (ULP) users endpoint for UniFi Protect API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError

from ..models import UlpUser  # noqa: TID252

if TYPE_CHECKING:
    from ..client import UniFiProtectClient  # noqa: TID252

_LOGGER = logging.getLogger(__name__)


class UlpUsersEndpoint:
    """Endpoint for UniFi Identity (ULP) users."""

    def __init__(self, client: UniFiProtectClient) -> None:
        """
        Initialize the ULP users endpoint.

        Args:
            client: The UniFi Protect client.

        """
        self._client = client
        self.last_result_complete: bool = True

    async def get_all(
        self,
        site_id: str | None = None,
        *,
        expected_unsupported: bool = False,
    ) -> list[UlpUser]:
        """
        Get all UniFi Identity users with enrolled credentials.

        Args:
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).
            expected_unsupported: Whether a non-JSON 2xx response is expected.

        Returns:
            List of UniFi Identity users.

        """
        path = self._client.build_api_path("/ulp-users", site_id)
        self.last_result_complete = True
        response = await self._client._get(
            path, expected_unsupported=expected_unsupported
        )

        if response is None:
            return []

        data = (
            response.get("data", response) if isinstance(response, dict) else response
        )
        if not isinstance(data, list):
            return []

        users: list[UlpUser] = []
        for item in data:
            try:
                users.append(UlpUser.model_validate(item))
            except ValidationError as err:
                self.last_result_complete = False
                _LOGGER.warning(
                    "Skipping ulp-user that failed to parse (id=%s): %s",
                    item.get("id") if isinstance(item, dict) else "?",
                    err,
                )
        return users

    async def get(self, user_id: str, site_id: str | None = None) -> UlpUser:
        """
        Get a specific UniFi Identity user by ID.

        Args:
            user_id: The primary key of the ULP user.
            site_id: The site ID (required for REMOTE connections, ignored for LOCAL).

        Returns:
            The UniFi Identity user.

        Raises:
            ValueError: If the ULP user is not found.

        """
        path = self._client.build_api_path(f"/ulp-users/{user_id}", site_id)
        response = await self._client._get(path)

        if isinstance(response, dict):
            data = response.get("data", response)
            if isinstance(data, dict):
                return UlpUser.model_validate(data)
            if isinstance(data, list) and len(data) > 0:
                return UlpUser.model_validate(data[0])
        msg = f"ULP user {user_id} not found"
        raise ValueError(msg)
