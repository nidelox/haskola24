"""Adds config flow for Skola24 integration."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, HOST_NAME, SCHEMA_NAME, TITLE, UNIT_NAME
from .skola24 import API

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(HOST_NAME, default="linkoping.skola24.se"): str,
        vol.Required(UNIT_NAME): str,
        vol.Required(SCHEMA_NAME): str,
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
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[HOST_NAME]}/{user_input[UNIT_NAME]}/{user_input[SCHEMA_NAME]}"
            )
            self._abort_if_unique_id_configured()
            api = API(async_get_clientsession(self.hass))
            try:
                await api.resolve_guids(
                    user_input[HOST_NAME],
                    user_input[UNIT_NAME],
                    user_input[SCHEMA_NAME],
                )
            except ValueError:
                errors["base"] = "not_found"
            except (ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating Skola24 settings")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=TITLE, data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
            errors=errors,
        )
