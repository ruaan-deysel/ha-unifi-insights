"""UniFi InnerSpace API client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NoReturn

from custom_components.unifi_insights.api.base import BaseUniFiClient
from custom_components.unifi_insights.api.const import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_TIMEOUT,
    INNERSPACE_API_BASE_URL,
    INNERSPACE_INTEGRATION_PATH,
    ConnectionType,
)
from custom_components.unifi_insights.api.exceptions import UniFiResponseError

from .models import (
    InnerSpaceAccessPoint,
    InnerSpaceFloorPlan,
    InnerSpaceInventoryDevice,
    InnerSpaceProject,
    InnerSpaceSwitch,
)

if TYPE_CHECKING:
    import aiohttp

    from custom_components.unifi_insights.api.auth import ApiKeyAuth, LocalAuth


class UniFiInnerSpaceClient(BaseUniFiClient):
    """
    Async client for the UniFi InnerSpace Integration API.

    Supports both LOCAL (direct console `/proxy/innerspace/integration/v1/...`)
    and REMOTE (`https://api.ui.com/v1/connector/consoles/{consoleId}/innerspace/integration/v1/...`)
    connections using `X-API-Key` credentials.
    """

    def __init__(
        self,
        auth: ApiKeyAuth | LocalAuth,
        *,
        base_url: str | None = None,
        connection_type: ConnectionType = ConnectionType.LOCAL,
        console_id: str | None = None,
        session: aiohttp.ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
    ) -> None:
        """Initialize the UniFi InnerSpace client."""
        if base_url is None:
            if connection_type == ConnectionType.REMOTE:
                base_url = INNERSPACE_API_BASE_URL
            else:
                msg = "base_url is required for LOCAL connection type"
                raise ValueError(msg)

        if connection_type == ConnectionType.REMOTE and not console_id:
            msg = "console_id is required for REMOTE connection type"
            raise ValueError(msg)

        super().__init__(
            auth=auth,
            base_url=base_url,
            session=session,
            timeout=timeout,
            connect_timeout=connect_timeout,
        )

        self._connection_type = connection_type
        self._console_id = console_id

    @property
    def connection_type(self) -> ConnectionType:
        """Return the connection type."""
        return self._connection_type

    @property
    def console_id(self) -> str | None:
        """Return the console ID (for remote connections)."""
        return self._console_id

    def _build_api_path(self, endpoint: str) -> str:
        """Build the full API path for Local or Remote Cloud Connector."""
        endpoint = endpoint.lstrip("/")
        if self._connection_type == ConnectionType.LOCAL:
            return f"{INNERSPACE_INTEGRATION_PATH}/{endpoint}"
        connector_path = INNERSPACE_INTEGRATION_PATH.removeprefix("/proxy")
        return f"/v1/connector/consoles/{self._console_id}{connector_path}/{endpoint}"

    @staticmethod
    def _raise_malformed(endpoint: str) -> NoReturn:
        """Raise a UniFiResponseError for malformed responses."""
        msg = f"{endpoint} returned a malformed response"
        raise UniFiResponseError(msg, status_code=200)

    def _extract_list(
        self,
        response: dict[str, Any] | list[Any] | None,
        key: str,
        endpoint: str,
    ) -> list[dict[str, Any]]:
        """Extract a list of dicts from an InnerSpace response envelope."""
        if response is None:
            return []
        if isinstance(response, list):
            items = response
        elif isinstance(response, dict):
            raw = response.get(key)
            if raw is None and "data" in response:
                data = response.get("data")
                if isinstance(data, dict):
                    raw = data.get(key)
                elif isinstance(data, list):
                    raw = data
            if raw is None:
                self._raise_malformed(endpoint)
            items = raw
        else:
            self._raise_malformed(endpoint)

        if not isinstance(items, list) or not all(
            isinstance(item, dict) for item in items
        ):
            self._raise_malformed(endpoint)
        return items

    async def get_project(self, *, mode: str | None = None) -> InnerSpaceProject:
        """
        Get project data for integration (`GET /v1/project`).

        Args:
            mode: Optional representation mode ("3D" or "2D").

        Returns:
            Parsed `InnerSpaceProject` model.

        """
        params: dict[str, Any] | None = {"mode": mode} if mode else None
        path = self._build_api_path("project")
        response = await self._get(path, params=params)
        if not isinstance(response, dict):
            self._raise_malformed("/v1/project")

        payload = response.get("data") if "data" in response else response
        if payload is None:
            return InnerSpaceProject()
        if not isinstance(payload, dict):
            self._raise_malformed("/v1/project")
        known_keys = {
            "project",
            "plans",
            "products",
            "wall_types",
            "wallTypes",
            "attenuation_object_types",
            "attenuationObjectTypes",
            "shapes",
            "id",
            "title",
            "name",
            "model",
            "environment",
        }
        if payload and not (payload.keys() & known_keys):
            self._raise_malformed("/v1/project")
        return InnerSpaceProject.model_validate(payload)

    async def list_floor_plans(
        self, *, site_id: str | None = None
    ) -> list[InnerSpaceFloorPlan]:
        """
        List floor plans (`GET /v1/floor_plans`).

        Args:
            site_id: Optional UniFi site filter (`siteId`).

        Returns:
            List of parsed `InnerSpaceFloorPlan` models.

        """
        params: dict[str, Any] | None = {"siteId": site_id} if site_id else None
        path = self._build_api_path("floor_plans")
        response = await self._get(path, params=params)
        items = self._extract_list(response, "floor_plans", "/v1/floor_plans")
        return [InnerSpaceFloorPlan.model_validate(item) for item in items]

    async def list_access_points(
        self, *, site_id: str | None = None
    ) -> list[InnerSpaceAccessPoint]:
        """
        List placed access points (`GET /v1/access_points`).

        Args:
            site_id: Optional UniFi site filter (`siteId`).

        Returns:
            List of parsed `InnerSpaceAccessPoint` models.

        """
        params: dict[str, Any] | None = {"siteId": site_id} if site_id else None
        path = self._build_api_path("access_points")
        response = await self._get(path, params=params)
        items = self._extract_list(response, "access_points", "/v1/access_points")
        return [InnerSpaceAccessPoint.model_validate(item) for item in items]

    async def list_switches(
        self, *, site_id: str | None = None
    ) -> list[InnerSpaceSwitch]:
        """
        List placed switches (`GET /v1/switches`).

        Args:
            site_id: Optional UniFi site filter (`siteId`).

        Returns:
            List of parsed `InnerSpaceSwitch` models.

        """
        params: dict[str, Any] | None = {"siteId": site_id} if site_id else None
        path = self._build_api_path("switches")
        response = await self._get(path, params=params)
        items = self._extract_list(response, "switches", "/v1/switches")
        return [InnerSpaceSwitch.model_validate(item) for item in items]

    async def list_inventory(
        self, *, site_id: str | None = None
    ) -> list[InnerSpaceInventoryDevice]:
        """
        List unplaced device inventory (`GET /v1/inventory`).

        Args:
            site_id: Optional UniFi site filter (`siteId`).

        Returns:
            List of parsed `InnerSpaceInventoryDevice` models.

        """
        params: dict[str, Any] | None = {"siteId": site_id} if site_id else None
        path = self._build_api_path("inventory")
        response = await self._get(path, params=params)
        items = self._extract_list(response, "devices", "/v1/inventory")
        return [InnerSpaceInventoryDevice.model_validate(item) for item in items]

    async def validate_connection(self) -> bool:
        """
        Validate the connection and authentication by querying `/v1/project`.

        Returns:
            True if connection and authentication are valid, False otherwise.

        """
        try:
            await self.get_project()
        except Exception:
            return False
        else:
            return True
