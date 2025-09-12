"""Sensor platform for Skola24 integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import as_utc

from .const import DOMAIN, SCHEMA_NAME, START_OF_DAY
from .coordinator import Skola24Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Skola24 sensors from a config entry."""
    import logging

    _LOGGER = logging.getLogger(__name__)
    _LOGGER.debug(
        "skola24.sensor: async_setup_entry called for entry_id=%s", entry.entry_id
    )
    coordinator = hass.data[DOMAIN][entry.entry_id]
    schema_id = entry.data[SCHEMA_NAME]
    _LOGGER.debug("skola24.sensor: coordinator.data=%s", coordinator.data)
    entities = []
    for description in SENSOR_TYPES:
        _LOGGER.debug(
            "skola24.sensor: Creating entity for description.key=%s", description.key
        )
        entities.append(Skola24Entity(coordinator, description, schema_id))
    _LOGGER.debug("skola24.sensor: Adding %d entities", len(entities))
    async_add_entities(entities)


@dataclass(frozen=True, kw_only=True)
class Skola24SensorEntityDescription(SensorEntityDescription):
    """Describes Skola24 sensor entity."""

    value_fn: Callable[[Skola24Entity], StateType | datetime]


SENSOR_TYPES: tuple[Skola24SensorEntityDescription, ...] = (
    Skola24SensorEntityDescription(
        key=START_OF_DAY,
        translation_key=START_OF_DAY,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda data: (
            as_utc(f"{data[0]['date']}T{data[0]['start_time']}")
            if data and len(data) > 0
            else None
        ),
    ),
)


class Skola24Entity(CoordinatorEntity[Skola24Coordinator], SensorEntity):
    @property
    def first_lesson_start_time_tomorrow(self) -> str | None:
        """Return the start time of the first lesson tomorrow, or None if none."""
        from datetime import date, timedelta

        if not self.coordinator.data:
            return None
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        lessons = [
            lesson for lesson in self.coordinator.data if lesson.get("date") == tomorrow
        ]
        if lessons:
            return lessons[0].get("start_time")
        return None

    @property
    def last_lesson_end_time_tomorrow(self) -> str | None:
        """Return the end time of the last lesson tomorrow, or None if none."""
        from datetime import date, timedelta

        if not self.coordinator.data:
            return None
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        lessons = [
            lesson for lesson in self.coordinator.data if lesson.get("date") == tomorrow
        ]
        if lessons:
            return lessons[-1].get("end_time")
        return None

    @property
    def last_lesson_end_time(self) -> str | None:
        """Return the end time of the last lesson today, or None if none."""
        todays = self.todays_schedule
        if todays and len(todays) > 0:
            return todays[-1].get("end_time")
        return None

    @property
    def first_lesson_start_time(self) -> str | None:
        """Return the start time of the first lesson today, or None if none."""
        todays = self.todays_schedule
        if todays and len(todays) > 0:
            return todays[0].get("start_time")
        return None

    @property
    def next_upcoming_lesson(self) -> dict | None:
        """Return the next upcoming lesson for today, or first lesson tomorrow if none left today."""
        from datetime import date, datetime as dt, timedelta

        if not self.coordinator.data:
            return None
        today = date.today().isoformat()
        now = dt.now().time()
        todays_lessons = [
            lesson for lesson in self.coordinator.data if lesson.get("date") == today
        ]
        # Find the first lesson whose start_time is after now
        for lesson in sorted(
            todays_lessons, key=lambda lesson: lesson.get("start_time")
        ):
            try:
                lesson_time = dt.fromisoformat(lesson["start_time"]).time()
                if lesson_time > now:
                    return lesson
            except Exception:
                continue
        # If no more lessons today, return the first lesson of tomorrow
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        tomorrows_lessons = [
            lesson for lesson in self.coordinator.data if lesson.get("date") == tomorrow
        ]
        if tomorrows_lessons:
            return sorted(
                tomorrows_lessons, key=lambda lesson: lesson.get("start_time")
            )[0]
        return None

    @property
    def todays_schedule(self) -> list | None:
        """Return a list of lessons for today."""
        from datetime import date

        if not self.coordinator.data:
            return None
        today = date.today().isoformat()
        return [
            lesson for lesson in self.coordinator.data if lesson.get("date") == today
        ]

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the extra state attributes for the sensor."""
        attrs = {}
        if self.coordinator.data is not None:
            attrs["lessons"] = self.coordinator.data
        # Add today's schedule
        todays = self.todays_schedule
        if todays is not None:
            attrs["todays_schedule"] = todays
        # Add next upcoming lesson
        next_lesson = self.next_upcoming_lesson
        if next_lesson is not None:
            attrs["next_upcoming_lesson"] = next_lesson
        # Add first lesson start time
        first_start = self.first_lesson_start_time
        if first_start is not None:
            attrs["first_lesson_start_time"] = first_start
        # Add last lesson end time
        last_end = self.last_lesson_end_time
        if last_end is not None:
            attrs["last_lesson_end_time"] = last_end
        # Add tomorrow's first and last lesson times
        first_start_tomorrow = self.first_lesson_start_time_tomorrow
        if first_start_tomorrow is not None:
            attrs["first_lesson_start_time_tomorrow"] = first_start_tomorrow
        last_end_tomorrow = self.last_lesson_end_time_tomorrow
        if last_end_tomorrow is not None:
            attrs["last_lesson_end_time_tomorrow"] = last_end_tomorrow
        return attrs if attrs else None

    @property
    def native_value(self):
        """Return the value of the sensor."""
        if self.coordinator.data is None:
            return None
        # Use the value_fn from the entity description to extract the value
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except Exception:  # Defensive: value_fn may fail if data is missing
            return None

    """Representation of a Skola24 base entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Skola24Coordinator,
        entity_description: EntityDescription,
        schema: str,
    ) -> None:
        """Initiate Skola24 base entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{schema}-{entity_description.key}"
        self.schema = schema
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, schema)},
            name=f"Skola24 {schema}",
            entry_type=DeviceEntryType.SERVICE,
        )
