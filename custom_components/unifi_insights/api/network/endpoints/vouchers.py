"""Vouchers endpoint for UniFi Network API."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Final

from pydantic import ValidationError

from custom_components.unifi_insights.api.validation import sanitized_validation_fields

from ..models.voucher import Voucher

_LOGGER = logging.getLogger(__name__)

VOUCHER_PAGE_SIZE: Final = 1000
VOUCHER_MAX_PAGES: Final = 50

if TYPE_CHECKING:
    from ..client import UniFiNetworkClient


def _validate_voucher(item: Any) -> Voucher:
    """Validate voucher model while sanitizing validation errors."""
    try:
        return Voucher.model_validate(item)
    except ValidationError as err:
        msg = f"Invalid voucher data (fields: {sanitized_validation_fields(err)})"
        raise ValueError(msg) from None


class VouchersEndpoint:
    """Endpoint for managing hotspot vouchers."""

    def __init__(self, client: UniFiNetworkClient) -> None:
        """
        Initialize the vouchers endpoint.

        Args:
            client: The UniFi Network client.

        """
        self._client = client

    async def get_all_pages(self, site_id: str) -> list[Voucher]:
        """List every voucher, retrying one inconsistent inventory from offset 0."""
        for _ in range(2):
            vouchers = await self._get_all_pages_attempt(site_id)
            if vouchers is not None:
                return vouchers
        msg = (
            f"Incomplete voucher listing for site {site_id}: "
            "distinct inventory is smaller than totalCount"
        )
        raise RuntimeError(msg)

    async def _get_all_pages_attempt(self, site_id: str) -> list[Voucher] | None:
        """Return a fresh inventory, or None when distinct IDs fall short of total."""
        path = self._client.build_api_path(f"/sites/{site_id}/hotspot/vouchers")
        vouchers_by_id: dict[str, Voucher] = {}
        offset = 0
        for _ in range(VOUCHER_MAX_PAGES):
            response = await self._client._get(
                path,
                params={"offset": offset, "limit": VOUCHER_PAGE_SIZE},
                expected_unsupported=True,
                log_body=False,
            )
            data = (
                response.get("data", response)
                if isinstance(response, dict)
                else response
            )
            items = data if isinstance(data, list) else []
            if not items:
                break
            prior_count = len(vouchers_by_id)
            for item in items:
                voucher = _validate_voucher(item)
                vouchers_by_id[voucher.id] = voucher
            if len(vouchers_by_id) == prior_count:
                msg = (
                    f"Incomplete voucher listing for site {site_id}: "
                    "no progress made on page"
                )
                raise RuntimeError(msg)
            offset += len(items)
            total = response.get("totalCount") if isinstance(response, dict) else None
            if isinstance(total, int) and not isinstance(total, bool):
                if offset >= total:
                    if len(vouchers_by_id) < total:
                        # Inserts ahead of the offset can overlap pages. Discard
                        # this inventory so the caller can restart once.
                        return None
                    break
            elif len(items) < VOUCHER_PAGE_SIZE:
                break
        else:
            msg = (
                f"Incomplete voucher listing for site {site_id}: "
                f"reached page limit {VOUCHER_MAX_PAGES}"
            )
            raise RuntimeError(msg)
        return list(vouchers_by_id.values())

    async def get_all(
        self,
        site_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
        filter_str: str | None = None,
    ) -> list[Voucher]:
        """
        List all vouchers.

        Args:
            site_id: The site ID.
            offset: Pagination offset.
            limit: Maximum results (max 1000).
            filter_str: Filter query string using API filter syntax.
                Example: "expired.eq(false)" or "and(name.like('guest*'), expired.eq(false))"

        Returns:
            List of vouchers.

        """
        path = self._client.build_api_path(f"/sites/{site_id}/hotspot/vouchers")
        params: dict[str, Any] = {"offset": offset, "limit": min(limit, 1000)}
        if filter_str:
            params["filter"] = filter_str

        response = await self._client._get(
            path, params=params, expected_unsupported=True, log_body=False
        )

        if response is None:
            return []

        data = (
            response.get("data", response) if isinstance(response, dict) else response
        )
        if isinstance(data, list):
            return [_validate_voucher(item) for item in data]
        return []

    async def get(self, site_id: str, voucher_id: str) -> Voucher:
        """
        Get a specific voucher.

        Args:
            site_id: The site ID.
            voucher_id: The voucher ID.

        Returns:
            The voucher.

        """
        path = self._client.build_api_path(
            f"/sites/{site_id}/hotspot/vouchers/{voucher_id}"
        )
        response = await self._client._get(
            path, expected_unsupported=True, log_body=False
        )

        if isinstance(response, dict):
            data = response.get("data", response)
            if isinstance(data, dict):
                return _validate_voucher(data)
            if isinstance(data, list) and len(data) > 0:
                return _validate_voucher(data[0])
        msg = f"Voucher {voucher_id} not found"
        raise ValueError(msg)

    async def create(
        self,
        site_id: str,
        *,
        name: str,
        time_limit_minutes: int,
        count: int = 1,
        authorized_guest_limit: int | None = None,
        data_usage_limit_mbytes: int | None = None,
        rx_rate_limit_kbps: int | None = None,
        tx_rate_limit_kbps: int | None = None,
    ) -> list[Voucher]:
        """
        Generate new vouchers.

        Args:
            site_id: The site ID.
            name: Voucher note/label.
            time_limit_minutes: Access duration in minutes.
            count: Number of vouchers to create (1-10000).
            authorized_guest_limit: Maximum guests per voucher.
            data_usage_limit_mbytes: Download limit in megabytes.
            rx_rate_limit_kbps: Download speed limit.
            tx_rate_limit_kbps: Upload speed limit.

        Returns:
            List of created vouchers.

        """
        path = self._client.build_api_path(f"/sites/{site_id}/hotspot/vouchers")
        data: dict[str, Any] = {
            "count": count,
            "name": name,
            "timeLimitMinutes": time_limit_minutes,
        }
        if authorized_guest_limit is not None:
            data["authorizedGuestLimit"] = authorized_guest_limit
        if data_usage_limit_mbytes is not None:
            data["dataUsageLimitMBytes"] = data_usage_limit_mbytes
        if rx_rate_limit_kbps is not None:
            data["rxRateLimitKbps"] = rx_rate_limit_kbps
        if tx_rate_limit_kbps is not None:
            data["txRateLimitKbps"] = tx_rate_limit_kbps

        response = await self._client._post(path, json_data=data, log_body=False)

        if isinstance(response, dict):
            result = response.get("data", response)
            # The spec's creation result wraps the list: {"vouchers": [...]}.
            if isinstance(result, dict) and isinstance(result.get("vouchers"), list):
                result = result["vouchers"]
            if isinstance(result, list) and len(result) > 0:
                return [_validate_voucher(item) for item in result]
            if isinstance(result, dict):
                return [_validate_voucher(result)]
        msg = "Failed to create vouchers"
        raise ValueError(msg)

    async def delete(self, site_id: str, voucher_id: str) -> bool:
        """
        Delete a specific voucher.

        Args:
            site_id: The site ID.
            voucher_id: The voucher ID.

        Returns:
            True if successful.

        """
        path = self._client.build_api_path(
            f"/sites/{site_id}/hotspot/vouchers/{voucher_id}"
        )
        await self._client._delete(path, log_body=False)
        return True

    async def delete_by_filter(self, site_id: str, filter_str: str) -> int:
        """
        Delete vouchers matching a filter expression.

        Args:
            site_id: The site ID.
            filter_str: Filter query string using API filter syntax.

        Returns:
            The number of vouchers deleted.

        """
        path = self._client.build_api_path(f"/sites/{site_id}/hotspot/vouchers")
        response = await self._client._delete(
            path, params={"filter": filter_str}, log_body=False
        )
        if isinstance(response, dict):
            return int(response.get("vouchersDeleted", 0))
        return 0

    async def delete_multiple(self, site_id: str, voucher_ids: list[str]) -> bool:
        """
        Delete multiple vouchers.

        Args:
            site_id: The site ID.
            voucher_ids: List of voucher IDs to delete.

        Returns:
            True if successful.

        """
        # Delete each voucher individually
        for voucher_id in voucher_ids:
            await self.delete(site_id, voucher_id)
        return True
