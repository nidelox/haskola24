"""Calendar platform for Skola24 integration."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, SCHEMA_NAME
from .coordinator import Skola24Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Skola24 calendar from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    schema_id = entry.data[SCHEMA_NAME]
    async_add_entities([Skola24CalendarEntity(coordinator, schema_id)])


class Skola24CalendarEntity(CalendarEntity):
    """A calendar entity for Skola24 lessons."""

    def __init__(self, coordinator: Skola24Coordinator, schema: str) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{schema}-calendar"
        self._attr_name = f"Skola24 {schema}"
        self.schema = schema

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming lesson as a CalendarEvent."""
        next_lesson = self._get_next_lesson()
        if next_lesson:
            return self._lesson_to_event(next_lesson)
        return None

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return extra state attributes, including the next event as a dict."""
        next_lesson = self._get_next_lesson()
        if next_lesson:
            return {"next_event": next_lesson}
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ):
        """Return all lessons as CalendarEvents between start_date and end_date."""
        if not self.coordinator.data:
            return []
        events = []
        for lesson_dict in self.coordinator.data:
            lesson = self._lesson_to_event(lesson_dict)
            if start_date <= lesson.start <= end_date:
                events.append(lesson)
        return events

    async def async_get_events_today(self, hass: HomeAssistant):
        """Return all lessons for today as CalendarEvents."""
        today = date.today().isoformat()
        if not self.coordinator.data:
            return []
        return [
            self._lesson_to_event(lesson)
            for lesson in self.coordinator.data
            if lesson.get("date") == today
        ]

    def _get_next_lesson(self) -> dict | None:
        """Return the next upcoming lesson, or first lesson tomorrow if none left today."""

        if not self.coordinator.data:
            return None
        today = date.today().isoformat()
        now = datetime.now().time()
        todays_lessons = [
            lesson for lesson in self.coordinator.data if lesson.get("date") == today
        ]
        for lesson in sorted(
            todays_lessons, key=lambda lesson: lesson.get("start_time")
        ):
            try:
                lesson_time = datetime.fromisoformat(lesson["start_time"]).time()
                if lesson_time > now:
                    return lesson
            except Exception:
                continue
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        tomorrows_lessons = [
            lesson for lesson in self.coordinator.data if lesson.get("date") == tomorrow
        ]
        if tomorrows_lessons:
            return sorted(
                tomorrows_lessons, key=lambda lesson: lesson.get("start_time")
            )[0]
        return None

    def _lesson_to_event(self, lesson: dict) -> CalendarEvent:
        """Convert a lesson dict to a CalendarEvent."""
        start = f"{lesson['date']}T{lesson['start_time']}+02:00"
        end = f"{lesson['date']}T{lesson['end_time']}+02:00"
        summary = lesson.get("title", "Lesson")
        location = lesson.get("location", "")
        description = f"Teacher: {lesson.get('teacher', '')}, Location: {lesson.get('location', '')}"
        tz = ZoneInfo("Europe/Stockholm")
        return CalendarEvent(
            start=datetime.fromisoformat(start).replace(tzinfo=tz),
            end=datetime.fromisoformat(end).replace(tzinfo=tz),
            summary=summary,
            location=location,
            description=description,
        )
