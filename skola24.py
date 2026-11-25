import datetime
import json
import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class API:
    x_scope = "8a22163c-8662-4535-9050-bc5e1923df48"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session
        self.base_url = "https://web.skola24.se"
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "X-Scope": self.x_scope,  # str(uuid.uuid4()),
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url,
            "Connection": "keep-alive",
        }

    # Function to get key
    async def get_key(self):
        """Retrieve the key required to render the timetable.

        Returns:
          str: The key required to render the timetable.
        """
        url = f"{self.base_url}/api/get/timetable/render/key"
        async with self.session.post(
            url, headers=self.headers, data=json.dumps(None)
        ) as response:
            json_response = await response.json()
            return json_response["data"]["key"]

    async def get_active_school_years(
        self, host_name: str, check_school_years_features: bool = False
    ):
        """Return a JSON object containing information about the active school years for the specified host.

        Args:
          host_name (str): The name of the host for which to retrieve active school years.
          check_school_years_features (bool, optional): Whether to check for school year features. Defaults to False.

        Returns:
          dict: A JSON object containing information about the active school years.
        """
        url = f"{self.base_url}/api/get/active/school/years"
        payload = {
            "hostName": host_name,
            "checkSchoolYearsFeatures": check_school_years_features,
        }

        async with self.session.post(
            url, headers=self.headers, json=payload
        ) as response:
            return await response.json()

    async def get_units(self, host_name: str):
        """Retrieve a list of units (schools) associated with the specified host name.

        Args:
            host_name (str): The name of the host to retrieve units for.

        Returns:
            list: A list of units (schools) associated with the specified host name.

        Raises:
            ValueError: If the specified host name is not found.
            Exception: If there is an error with the API response.

        """
        url = f"{self.base_url}/api/services/skola24/get/timetable/viewer/units"
        payload = {"getTimetableViewerUnitsRequest": {"hostName": host_name}}
        async with self.session.post(
            url, headers=self.headers, json=payload
        ) as response:
            jsonResponse = json.loads(await response.text())
            if not jsonResponse["data"].get("validationErrors"):
                return jsonResponse["data"]["getTimetableViewerUnitsResponse"]["units"]
            elif jsonResponse["data"]["validationErrors"][0]["id"] == 1:
                raise ValueError(f"Host {host_name} not found")
            else:
                raise Exception(f"Error: {jsonResponse['data']['validationErrors']}")

    async def get_schema_guid(self, host_name: str, unitGuid: str, schema_name: str):
        url = f"{self.base_url}/api/get/timetable/selection"
        payload = {
            "hostName": host_name,
            "unitGuid": unitGuid,
            "filters": {"class": True},
        }
        async with self.session.post(
            url, headers=self.headers, json=payload
        ) as response:
            jsonResponse = await response.json()
            if not jsonResponse["data"].get("validationErrors"):
                classes = jsonResponse["data"]["classes"]
                for _class in classes:
                    if _class["groupName"] == schema_name:
                        return _class["groupGuid"]
                raise ValueError(f"Schema {schema_name} not found in {host_name}")
            elif jsonResponse["data"]["validationErrors"][0]["id"] == 1:
                raise ValueError(f"Host {host_name} not found")
            else:
                raise Exception(f"Error: {jsonResponse['data']['validationErrors']}")

    # Function to get timetable
    async def __get_timetable(
        self,
        render_key,
        host_name,
        unit_guid,
        schema_guid,
        school_year_guid,
        week,
        year,
    ):
        """Retrieve the timetable for a given school unit, week and year.

        Args:
          render_key (str): The render key for the school unit.
          host_name (str): The host name for the school unit.
          unit_guid (str): The GUID for the school unit.
          schema_guid (str): The selection guid for the timetable.
          school_year_guid (str): The GUID for the school year.
          week (int): The week number for the timetable.
          year (int): The year for the timetable.

        Returns:
          dict: The JSON response from the API containing the timetable data.

        """
        url = f"{self.base_url}/api/render/timetable"
        payload = {
            "renderKey": render_key,
            "host": host_name,
            "unitGuid": unit_guid,
            "selection": schema_guid,
            "schoolYear": school_year_guid,
            # "startDate": "2023-11-06",
            # "endDate": "2023-11-08",
            # "scheduleDay": 0, #
            # "blackAndWhite": False, #
            "width": 500,
            "height": 615,
            "selectionType": 0,
            # "showHeader": False, #
            # "periodText": "", #
            "week": week,
            "year": year,
            # "privateFreeTextMode": False, #
            # "privateSelectionMode": None, #
            # "customerKey": "", #
        }

        # print(json.dumps(payload, indent=2))

        async with self.session.post(
            url, headers=self.headers, data=json.dumps(payload)
        ) as response:
            return await response.json()

    async def resolve_guids(self, host_name: str, unit_name: str, schema_id: str):
        """Return (unit_guid, schema_guid), raising ValueError if either is unknown."""
        units = await self.get_units(host_name)
        unit_guid = next(
            (unit["unitGuid"] for unit in units if unit["unitId"] == unit_name), None
        )
        if not unit_guid:
            raise ValueError(f"Unit {unit_name} not found in {host_name}")
        schema_guid = await self.get_schema_guid(host_name, unit_guid, schema_id)
        return unit_guid, schema_guid

    async def get_timetable(
        self, host_name: str, unit_name: str, schema_id: str, week: int, year: int
    ):
        """Return a list of lessons for a given ISO week and ISO year.

        Args:
        - host_name (str): The name of the host.
        - unit_name (str): The name of the unit.
        - schema_id (str): The schema ID.
        - week (int): The ISO week number.
        - year (int): The ISO year the week belongs to.

        Returns:
        - A list of dictionaries, where each dictionary represents a lesson and contains the following keys:
          - title (str): The title of the lesson.
          - date (str): The date of the lesson in the format "YYYY-MM-DD".
          - start_time (str): The start time of the lesson in the format "HH:MM".
          - end_time (str): The end time of the lesson in the format "HH:MM".
          - teacher (str): The name of the teacher.
          - location (str): The location of the lesson.

        """
        unit_guid, schema_guid = await self.resolve_guids(
            host_name, unit_name, schema_id
        )

        schoolyears_result = await self.get_active_school_years(host_name)
        school_year_guid = schoolyears_result["data"]["activeSchoolYears"][0]["guid"]

        render_key = await self.get_key()

        timetable_data = await self.__get_timetable(
            render_key, host_name, unit_guid, schema_guid, school_year_guid, week, year
        )
        if not len(timetable_data["validation"]) > 0:
            lessons = []
            for lesson in timetable_data["data"]["lessonInfo"]:
                teacher = lesson["texts"][1] if len(lesson["texts"]) > 1 else ""
                location = lesson["texts"][2] if len(lesson["texts"]) > 2 else ""
                date = datetime.date.fromisocalendar(
                    year, week, lesson["dayOfWeekNumber"]
                )
                start_time = datetime.time.fromisoformat(lesson["timeStart"])
                end_time = datetime.time.fromisoformat(lesson["timeEnd"])
                lessons.append(
                    {
                        "title": lesson["texts"][0],
                        "date": date.isoformat(),
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "teacher": teacher,
                        "location": location,
                    }
                )

            lessons.sort(key=lambda lesson: (lesson["date"], lesson["start_time"]))
            return lessons

        elif timetable_data["validation"][0]["code"] == 4:
            raise ValueError(f"Schema ID not found in {host_name}/{unit_name}")
        else:
            raise Exception(f"Error: {timetable_data['validation']}")
