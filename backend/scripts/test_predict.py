import json
import urllib.request

url = 'http://127.0.0.1:8001/api/predict-upselling'
payload = {
    'Tipo_Habitacion': 'Suite',
    'Piso_Habitacion': '3',
    'Procedencia_Huesped': 'Local',
    'Dias_Estadia': 2,
}
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'})
try:
    res = urllib.request.urlopen(req, timeout=10)
    print('STATUS', res.getcode())
    print(res.read().decode())
except Exception as e:
    print('ERROR', e)
    try:
        import traceback; traceback.print_exc()
    except Exception:
        pass
