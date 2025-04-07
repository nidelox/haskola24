import requests
import json
import datetime
import uuid

class API:
  x_scope="8a22163c-8662-4535-9050-bc5e1923df48"
  def __init__(self):
    self.session = requests.Session()
    self.base_url = "https://web.skola24.se"
    self.headers = {
      "Accept": "application/json, text/javascript, */*; q=0.01",
      "Accept-Language": "en-US,en;q=0.5",
      "Content-Type": "application/json",
      "X-Scope": self.x_scope, #str(uuid.uuid4()),
      "X-Requested-With": "XMLHttpRequest",
      "Origin": self.base_url,
      "Connection": "keep-alive",
    }

  # Function to get key
  def get_key(self):
    """
    Retrieves the key required to render the timetable.

    Returns:
      str: The key required to render the timetable.
    """
    url = f"{self.base_url}/api/get/timetable/render/key"
    response = self.session.post(url, headers=self.headers, data=json.dumps(None)) # data-raw null
    return response.json()['data']['key']


  def get_active_school_years(self, host_name:str, check_school_years_features:bool=False):
    """
    Returns a JSON object containing information about the active school years for the specified host.

    Args:
      host_name (str): The name of the host for which to retrieve active school years.
      check_school_years_features (bool, optional): Whether to check for school year features. Defaults to False.

    Returns:
      dict: A JSON object containing information about the active school years.
    """
    url = f"{self.base_url}/api/get/active/school/years"
    payload = {
      "hostName":host_name,
      "checkSchoolYearsFeatures":check_school_years_features
    }
    
    response = self.session.post(url, headers=self.headers, json=payload)
    return response.json()

  def get_units(self, host_name:str):
      
      """
      Retrieves a list of units (schools) associated with the specified host name.

      Args:
          host_name (str): The name of the host to retrieve units for.

      Returns:
          list: A list of units (schools) associated with the specified host name.

      Raises:
          ValueError: If the specified host name is not found.
          Exception: If there is an error with the API response.
      """
      url = f"{self.base_url}/api/services/skola24/get/timetable/viewer/units"
      payload = {
        "getTimetableViewerUnitsRequest": {
          "hostName": host_name
        }
      }

      response = self.session.post(url, headers=self.headers, json=payload)

      jsonResponse = json.loads(response.text)
      if not jsonResponse['data'].get('validationErrors'):
        return jsonResponse['data']['getTimetableViewerUnitsResponse']['units']
      elif jsonResponse['data']['validationErrors'][0]['id'] == 1:
        raise ValueError(f'Host {host_name} not found')
      else:
        raise Exception(f'Error: {jsonResponse["data"]["validationErrors"]}')
    
  def get_schema_guid(self, host_name:str, unitGuid:str, schema_name:str):
      url = f"{self.base_url}/api/get/timetable/selection"
      payload = {
          "hostName": host_name,
          "unitGuid": unitGuid,
          "filters": {
            "class": True
        }
      }
      response = self.session.post(url, headers=self.headers, json=payload)
      jsonResponse = json.loads(response.text)
      if not jsonResponse['data'].get('validationErrors'):
        classes = jsonResponse['data']['classes']
        for _class in classes:
          if _class['groupName'] == schema_name:
            return _class['groupGuid']
      elif jsonResponse['data']['validationErrors'][0]['id'] == 1:
        raise ValueError(f'Host {host_name} not found')
      else:
        raise Exception(f'Error: {jsonResponse["data"]["validationErrors"]}')

  # Function to get timetable
  def get_timetable_internal(self, render_key, host_name, unit_guid, schema_guid, school_year_guid, week, year):
    """
    Retrieves the timetable for a given school unit, week and year.

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
      #"startDate": "2023-11-06", 
      #"endDate": "2023-11-08",
      #"scheduleDay": 0, #
      #"blackAndWhite": False, #
      "width": 500,
      "height": 615,
      "selectionType": 0,
      #"showHeader": False, #
      #"periodText": "", #
      "week": week,
      "year": year,
      #"privateFreeTextMode": False, #
      #"privateSelectionMode": None, #
      #"customerKey": "", #
    }
    
    #print(json.dumps(payload, indent=2))
    
    response = self.session.post(url, headers=self.headers, data=json.dumps(payload))
    return response.json()



  def get_timetable(self, host_name:str, unit_name, schema_id:str, week:int):
    """
    Returns a list of lessons for a given week and year, for a specific unit and schema ID.

    Args:
    - host_name (str): The name of the host.
    - unit_name (str): The name of the unit.
    - schema_id (str): The schema ID.
    - week (int): The week number.


    Returns:
    - A list of dictionaries, where each dictionary represents a lesson and contains the following keys:
      - title (str): The title of the lesson.
      - date (str): The date of the lesson in the format "YYYY-MM-DD".
      - start_time (str): The start time of the lesson in the format "HH:MM".
      - end_time (str): The end time of the lesson in the format "HH:MM".
      - teacher (str): The name of the teacher.
      - location (str): The location of the lesson.
    """
    
    # Get unit guid
    units = self.get_units(host_name)
    unit_guid = None
    for unit in units:
      if unit['unitId'] == unit_name:
        unit_guid = unit['unitGuid']
        
    if not unit_guid:
      raise ValueError(f'Unit {unit_name} not found in {host_name}')

    # Get school year guid
    year = datetime.date.today().year
    school_year_guid = self.get_active_school_years(host_name)['data']['activeSchoolYears'][0]['guid']
    
    render_key = self.get_key()

    schema_guid = self.get_schema_guid(host_name, unit_guid, schema_id)
    
    timetable_data = self.get_timetable_internal(render_key, host_name, unit_guid, schema_guid, school_year_guid, week, year)
    if not len(timetable_data['validation']) > 0:
      dates = {}
      
      for item in timetable_data["data"]["textList"]:
        if item['type'] == 'HeadingDay':
          day_of_week = item['text'].split(' ')[0]
          day = int(item['text'].split(' ')[1].split('/')[0])
          month = int(item['text'].split(' ')[1].split('/')[1])
          dates[{'Måndag':1, 'Tisdag':2, 'Onsdag':3, 'Torsdag':4, 'Fredag':5,}[day_of_week]] = {'day':day, 'month':month}
      lessons = []
      for lesson in timetable_data["data"]["lessonInfo"]:
        teacher = lesson['texts'][1] if len(lesson['texts']) > 1 else ''
        location = lesson['texts'][2] if len(lesson['texts']) > 2 else ''
        date=datetime.date(year, dates[lesson['dayOfWeekNumber']]['month'], dates[lesson['dayOfWeekNumber']]['day'])
        start_time = datetime.time.fromisoformat(lesson['timeStart'])
        end_time = datetime.time.fromisoformat(lesson['timeEnd'])
        lessons.append({
          'title': lesson['texts'][0],
          'date': date.isoformat(), 
          'start_time': start_time.isoformat(),
          'end_time': end_time.isoformat(),
          'teacher': teacher,
          'location': location,
        })
        
      return lessons

    elif timetable_data['validation'][0]['code'] == 4:
      raise ValueError(f'Schema ID not found in {host_name}/{unit_name}')
    else:
      raise Exception(f"Error: {timetable_data['validation']}")