import urllib.request
import json

URL = 'http://127.0.0.1:8001/api/v1/analitica'
try:
    with urllib.request.urlopen(URL, timeout=10) as resp:
        body = resp.read()
        data = json.loads(body)
        print('reservas_activas', data.get('reservas_activas'))
        print('reservas_recomendadas_count', len(data.get('reservas_recomendadas', [])))
        for item in data.get('reservas_recomendadas', []):
            print('RECOM', item.get('ID_Reserva'), item.get('servicio_recomendado'), item.get('probabilidades'))
except Exception as e:
    print('error', e)
