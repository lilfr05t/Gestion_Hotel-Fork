import requests

r = requests.get('http://127.0.0.1:8001/api/v1/servicios-disponibles')
print('status', r.status_code)
print('cors', r.headers.get('Access-Control-Allow-Origin'))
print('count', len(r.json()))
