from __future__ import annotations

from datetime import timedelta, datetime
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from skola24 import API

DOMAIN = "hass_skola24"

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config: ConfigType):
    """Set up the Skola24 component."""
    host_name = config[DOMAIN]["host_name"]
    unit_name = config[DOMAIN]["unit_name"]
    schema_id = config[DOMAIN]["schema_id"]
    week = datetime.now().isocalendar()[1]
    coordinator = Skola24API()

class Skola24API(DataUpdateCoordinator):
    """Class to manage fetching Skola24 data."""

    def __init__(self, hass: HomeAssistant, host_name: str, unit_name: str, schema_id: str, week: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=12),
        )
        """Initialize the coordinator."""
        self.host_name = host_name
        self.unit_name = unit_name
        self.schema_id = schema_id
        self.week = week
        
        super().__init__(hass, _LOGGER, name=DOMAIN)

    async def _async_update_data(self) -> dict:
        """Fetch data from Skola24 API."""
        api = API()
        res = api.get_timetable(self.host_name, self.unit_name, self.schema_id, self.week)
        self.hass.states.set("skola24.schema_line", res)
        return res