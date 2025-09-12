"""Adds config flow for Skola24 integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN, HOST_NAME, SCHEMA_NAME, TITLE, UNIT_NAME

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(HOST_NAME, default="linkoping.skola24.se"): str,
        vol.Required(UNIT_NAME, default=""): str,
        vol.Required(SCHEMA_NAME, default=""): str,
    }
)


class Skola24ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Represents the configuration flow for the Skola24 integration."""

    VERSION = 1
    MINOR_VERSION = 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input:
            return self.async_create_entry(
                title=TITLE,
                data=user_input,
            )
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
