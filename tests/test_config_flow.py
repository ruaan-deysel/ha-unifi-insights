"""Tests for the UniFi Insights config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unifi_official_api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiTimeoutError,
)

from custom_components.unifi_insights.const import (
    CONF_CONNECTION_TYPE,
    CONF_CONSOLE_ID,
    CONNECTION_TYPE_LOCAL,
    CONNECTION_TYPE_REMOTE,
    DOMAIN,
)

# All tests require custom_integrations to be enabled
pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_user_flow_shows_connection_type_selection(hass: HomeAssistant) -> None:
    """Test user flow shows connection type selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_local_flow_success(hass: HomeAssistant) -> None:
    """Test successful local connection flow."""
    # Create a mock client
    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(
        return_value=[MagicMock(id="default", name="Default")]
    )
    mock_client.close = AsyncMock()

    # Create async context manager mock
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        # Start the flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        # Select local connection
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "local"

        # Enter local connection details
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_api_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "UniFi Insights (Local)"
        assert result["data"] == {
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL,
            CONF_HOST: "https://192.168.1.1",
            CONF_API_KEY: "test_api_key",
            CONF_VERIFY_SSL: False,
        }


async def test_local_flow_auth_error(hass: HomeAssistant) -> None:
    """Test local flow with authentication error."""
    # Create async context manager mock that raises auth error
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(
        side_effect=UniFiAuthenticationError("Invalid credentials")
    )
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Select local connection
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )

        # Enter local connection details
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "bad_api_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_local_flow_connection_error(hass: HomeAssistant) -> None:
    """Test local flow with connection error."""
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=UniFiConnectionError("Cannot connect"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_api_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_local_flow_timeout_error(hass: HomeAssistant) -> None:
    """Test local flow with timeout error."""
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=UniFiTimeoutError("Timeout"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_api_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_local_flow_unknown_error(hass: HomeAssistant) -> None:
    """Test local flow with unknown error."""
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=Exception("Unknown error"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_api_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_remote_flow_success(hass: HomeAssistant) -> None:
    """Test successful remote connection flow."""
    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(
        return_value=[MagicMock(id="default", name="Default")]
    )
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.ApiKeyAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Select remote connection
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE},
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "remote"

        # Enter remote connection details
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONSOLE_ID: "console123",
                CONF_API_KEY: "test_api_key",
            },
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "UniFi Insights (Cloud)"
        assert result["data"] == {
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE,
            CONF_CONSOLE_ID: "console123",
            CONF_API_KEY: "test_api_key",
        }


async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test successful reauth flow."""
    mock_config_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(
        return_value=[MagicMock(id="default", name="Default")]
    )
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reauth_flow(hass)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "new_api_key"},
        )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"


async def test_reauth_flow_auth_failed(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reauth flow with authentication failure."""
    mock_config_entry.add_to_hass(hass)

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(
        side_effect=UniFiAuthenticationError("Invalid credentials")
    )
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reauth_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "wrong_key"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_local_flow_no_sites_found(hass: HomeAssistant) -> None:
    """Test local flow when no sites are found."""
    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(return_value=[])  # No sites
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_LOCAL},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_api_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_remote_flow_auth_error(hass: HomeAssistant) -> None:
    """Test remote flow with authentication error."""
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(
        side_effect=UniFiAuthenticationError("Invalid credentials")
    )
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.ApiKeyAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONSOLE_ID: "console123",
                CONF_API_KEY: "bad_api_key",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_remote_flow_connection_error(hass: HomeAssistant) -> None:
    """Test remote flow with connection error."""
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=UniFiConnectionError("Cannot connect"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.ApiKeyAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONSOLE_ID: "console123",
                CONF_API_KEY: "test_api_key",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_remote_flow_timeout_error(hass: HomeAssistant) -> None:
    """Test remote flow with timeout error."""
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=UniFiTimeoutError("Timeout"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.ApiKeyAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONSOLE_ID: "console123",
                CONF_API_KEY: "test_api_key",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_remote_flow_unknown_error(hass: HomeAssistant) -> None:
    """Test remote flow with unknown error."""
    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=Exception("Unknown error"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.ApiKeyAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONSOLE_ID: "console123",
                CONF_API_KEY: "test_api_key",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_remote_flow_no_sites_found(hass: HomeAssistant) -> None:
    """Test remote flow when no sites are found."""
    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(return_value=[])
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.ApiKeyAuth"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONSOLE_ID: "console123",
                CONF_API_KEY: "test_api_key",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_reauth_flow_remote_success(hass: HomeAssistant) -> None:
    """Test successful reauth flow for remote connection."""
    # Create a remote config entry
    remote_entry = MockConfigEntry(
        domain=DOMAIN,
        title="UniFi Insights (Cloud)",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE,
            CONF_CONSOLE_ID: "console123",
            CONF_API_KEY: "old_api_key",
        },
        unique_id="old_api_key",
    )
    remote_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(
        return_value=[MagicMock(id="default", name="Default")]
    )
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.ApiKeyAuth"),
    ):
        result = await remote_entry.start_reauth_flow(hass)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "new_api_key"},
        )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"


async def test_reauth_flow_connection_error(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reauth flow with connection error."""
    mock_config_entry.add_to_hass(hass)

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=UniFiConnectionError("Cannot connect"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reauth_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "test_api_key"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_flow_timeout_error(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reauth flow with timeout error."""
    mock_config_entry.add_to_hass(hass)

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=UniFiTimeoutError("Timeout"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reauth_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "test_api_key"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_flow_unknown_error(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reauth flow with unknown error."""
    mock_config_entry.add_to_hass(hass)

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=Exception("Unknown error"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reauth_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "test_api_key"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_reauth_flow_no_sites_found(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reauth flow when no sites are found."""
    mock_config_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(return_value=[])
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reauth_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_API_KEY: "test_api_key"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_reconfigure_local_success(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test successful reconfigure flow for local connection."""
    mock_config_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(
        return_value=[MagicMock(id="default", name="Default")]
    )
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reconfigure_flow(hass)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.2",
                CONF_API_KEY: "test_api_key",
                CONF_VERIFY_SSL: True,
            },
        )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"


async def test_reconfigure_remote_success(hass: HomeAssistant) -> None:
    """Test successful reconfigure flow for remote connection."""
    remote_entry = MockConfigEntry(
        domain=DOMAIN,
        title="UniFi Insights (Cloud)",
        data={
            CONF_CONNECTION_TYPE: CONNECTION_TYPE_REMOTE,
            CONF_CONSOLE_ID: "console123",
            CONF_API_KEY: "old_api_key",
        },
        unique_id="old_api_key",
    )
    remote_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(
        return_value=[MagicMock(id="default", name="Default")]
    )
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.ApiKeyAuth"),
    ):
        result = await remote_entry.start_reconfigure_flow(hass)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONSOLE_ID: "new_console",
                CONF_API_KEY: "old_api_key",
            },
        )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"


async def test_reconfigure_auth_error(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reconfigure flow with authentication error."""
    mock_config_entry.add_to_hass(hass)

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(
        side_effect=UniFiAuthenticationError("Invalid credentials")
    )
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reconfigure_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "bad_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_reconfigure_connection_error(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reconfigure flow with connection error."""
    mock_config_entry.add_to_hass(hass)

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=UniFiConnectionError("Cannot connect"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reconfigure_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_timeout_error(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reconfigure flow with timeout error."""
    mock_config_entry.add_to_hass(hass)

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=UniFiTimeoutError("Timeout"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reconfigure_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_unknown_error(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reconfigure flow with unknown error."""
    mock_config_entry.add_to_hass(hass)

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(side_effect=Exception("Unknown error"))
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reconfigure_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_reconfigure_no_sites_found(
    hass: HomeAssistant,
    mock_config_entry,
) -> None:
    """Test reconfigure flow when no sites are found."""
    mock_config_entry.add_to_hass(hass)

    mock_client = MagicMock()
    mock_client.sites = MagicMock()
    mock_client.sites.get_all = AsyncMock(return_value=[])
    mock_client.close = AsyncMock()

    async_cm = MagicMock()
    async_cm.__aenter__ = AsyncMock(return_value=mock_client)
    async_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "custom_components.unifi_insights.config_flow.UniFiNetworkClient",
            return_value=async_cm,
        ),
        patch("custom_components.unifi_insights.config_flow.LocalAuth"),
    ):
        result = await mock_config_entry.start_reconfigure_flow(hass)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "https://192.168.1.1",
                CONF_API_KEY: "test_key",
                CONF_VERIFY_SSL: False,
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}
