from skola24 import API
from datetime import datetime

skola24 = API()
skola24.x_scope = '8a22163c-8662-4535-9050-bc5e1923df48'
host_name = 'linkoping.skola24.se'
unit_name = 'Berzeliusskolan gymnasium'
schema_id = 'NA24E_BER'
week = datetime.now().isocalendar()[1]
print(f"Current week: {week}")
year = 2025

try:
    schema = skola24.get_timetable(host_name, unit_name, schema_id, week)
except Exception as e:
    print(f"Error: {e}")
    schema = None
print(schema)