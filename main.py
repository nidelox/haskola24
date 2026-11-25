"""Manual test script for the Skola24 API client."""

import asyncio
from datetime import date

import aiohttp

from skola24 import API

HOST_NAME = "linkoping.skola24.se"
UNIT_NAME = "Berzeliusskolan gymnasium"
SCHEMA_ID = "NA22E_BER"


async def main() -> None:
    year, week, _ = date.today().isocalendar()
    print(f"Current week: {week}")
    async with aiohttp.ClientSession() as session:
        api = API(session)
        try:
            print(await api.get_timetable(HOST_NAME, UNIT_NAME, SCHEMA_ID, week, year))
        except Exception as e:
            print(f"Error: {e}")


asyncio.run(main())
