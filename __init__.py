from __future__ import annotations
import logging
from datetime import datetime
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, HOST_NAME, UNIT_NAME, SCHEMA_NAME, PLATFORMS
from .coordinator import Skola24Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up Skola24 from a config entry.

    This function should only set up shared data (like the coordinator)
    and store it in hass.data. Entity setup is handled in platform files
    (e.g., sensor.py) via their own async_setup_entry.
    """
    try:
        host_name = entry.data[HOST_NAME]
        unit_name = entry.data[UNIT_NAME]
        schema_id = entry.data[SCHEMA_NAME]
    except KeyError as err:
        _LOGGER.error("Missing config data: %s", err)
        return False

    week = datetime.now().isocalendar()[1]
    coordinator = Skola24Coordinator(hass, host_name, unit_name, schema_id, week)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
