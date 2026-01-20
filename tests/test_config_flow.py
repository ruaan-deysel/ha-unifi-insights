"""Tests for the UniFi Insights config flow."""

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from unifi_official_api import (
    UniFiAuthenticationError,
    UniFiConnectionError,
    UniFiTimeoutError,
)

from custom_components.unifi_insights.const import DOMAIN

TEST_USER_INPUT = {
    CONF_HOST: "https://192.168.1.1",
    CONF_API_KEY: "test_api_key",
    CONF_VERIFY_SSL: False,
}


async def test_user_flow_success(
    hass: HomeAssistant,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_USER_INPUT,
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "UniFi Insights"
    assert result["data"] == TEST_USER_INPUT


async def test_user_flow_auth_error(
    hass: HomeAssistant,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test user flow with authentication error."""
    mock_network_client.validate_connection.return_value = False

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_USER_INPUT,
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_user_flow_auth_exception(
    hass: HomeAssistant,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test user flow with authentication exception."""
    mock_network_client.validate_connection.side_effect = UniFiAuthenticationError(
        "Invalid credentials"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_USER_INPUT,
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_API_KEY: "invalid_auth"}


async def test_user_flow_connection_error(
    hass: HomeAssistant,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test user flow with connection error."""
    mock_network_client.validate_connection.side_effect = UniFiConnectionError(
        "Cannot connect"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_USER_INPUT,
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_timeout_error(
    hass: HomeAssistant,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test user flow with timeout error."""
    mock_network_client.validate_connection.side_effect = UniFiTimeoutError("Timeout")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_USER_INPUT,
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_unknown_error(
    hass: HomeAssistant,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test user flow with unknown error."""
    mock_network_client.validate_connection.side_effect = Exception("Unknown error")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_USER_INPUT,
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_config_entry,
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test successful reauth flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )
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
    mock_network_client,
    mock_local_auth,
) -> None:
    """Test reauth flow with authentication failure."""
    mock_config_entry.add_to_hass(hass)
    mock_network_client.validate_connection.return_value = False

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
        data=mock_config_entry.data,
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "wrong_key"},
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_API_KEY: "invalid_auth"}
