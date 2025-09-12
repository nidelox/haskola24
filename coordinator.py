from datetime import datetime, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .skola24 import API

_LOGGER = logging.getLogger(__name__)


class Skola24Coordinator(DataUpdateCoordinator):
    """Class to manage fetching Skola24 data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host_name: str,
        unit_name: str,
        schema_id: str,
        week: int,
    ) -> None:
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
        async with API() as api:
            try:
                res = await api.get_timetable(
                    self.host_name, self.unit_name, self.schema_id, self.week
                )
                self.async_set_updated_data({"schema": res})
                return res
            except Exception as err:
                raise UpdateFailed(f"Error fetching data: {err}") from err
