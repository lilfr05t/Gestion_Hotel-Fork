import urllib.request
import json

headers = {'Origin': 'http://localhost:5173'}
try:
    req = urllib.request.Request('http://127.0.0.1:8001/api/v1/servicios-disponibles', headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read()
        print('status', resp.getcode())
        print('Access-Control-Allow-Origin:', resp.getheader('Access-Control-Allow-Origin'))
        print('Content-Type:', resp.getheader('Content-Type'))
        print('Body length', len(body))
        try:
            parsed = json.loads(body)
            print('count', len(parsed))
        except Exception:
            print('body (truncated):', body[:500])
except urllib.error.HTTPError as he:
    body = he.read()
    print('HTTPError code', he.code)
    print('Access-Control-Allow-Origin:', he.headers.get('Access-Control-Allow-Origin'))
    print('Content-Type:', he.headers.get('Content-Type'))
    print('Error body (truncated):', body[:1000])
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR', e)
