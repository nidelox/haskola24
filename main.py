import skola24

host_name = 'linkoping.skola24.se'
unit_name = 'Berzeliusskolan gymnasium'
schema_id = 'NA24E_BER'
week = 14
year = 2025
skola24.API.x_scope = '8a22163c-8662-4535-9050-bc5e1923df48'
try:
    schema = skola24.get_timetable(host_name, unit_name, schema_id, week, year)
except Exception as e:
    print(f"Error: {e}")
    schema = None
print(schema)