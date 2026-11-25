"""Data update coordinator for Skola24."""

from __future__ import annotations

from datetime import timedelta
import logging

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, HOST_NAME, SCHEMA_NAME, UNIT_NAME
from .skola24 import API

_LOGGER = logging.getLogger(__name__)

type Skola24ConfigEntry = ConfigEntry[Skola24Coordinator]


class Skola24Coordinator(DataUpdateCoordinator[list[dict]]):
    """Class to manage fetching Skola24 data."""

    config_entry: Skola24ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: Skola24ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(hours=12),
        )
        self.api = API(async_get_clientsession(hass))

    async def _async_update_data(self) -> list[dict]:
        """Fetch lessons for the current and the next ISO week."""
        data = self.config_entry.data
        today = dt_util.now().date()
        lessons: list[dict] = []
        try:
            for day in (today, today + timedelta(days=7)):
                iso_year, iso_week, _ = day.isocalendar()
                lessons += await self.api.get_timetable(
                    data[HOST_NAME],
                    data[UNIT_NAME],
                    data[SCHEMA_NAME],
                    iso_week,
                    iso_year,
                )
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error fetching data: {err}") from err
        return lessons
