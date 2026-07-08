import urllib.request
import urllib.error

url = 'http://127.0.0.1:8001/api/v1/huespedes/72084436'
req = urllib.request.Request(url, headers={'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req) as r:
        print('STATUS', r.getcode())
        print(r.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTPError', e.code, e.reason)
    try:
        print(e.read().decode('utf-8'))
    except Exception:
        pass
except Exception as e:
    print(type(e).__name__, e)
