import os
import sys
import subprocess
import time
from urllib.request import urlopen
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

python_exe = r'C:\Users\enz0l\Documents\UNMSM\Gestion_Hotel-Bayes_version\.venv\Scripts\python.exe'
backend_dir = r'C:\Users\enz0l\Documents\UNMSM\Gestion_Hotel-Bayes_version\backend'

# Kill any process listening on 8001
proc = subprocess.run('netstat -ano | findstr :8001', shell=True, capture_output=True, text=True)
if proc.stdout.strip():
    lines = proc.stdout.strip().splitlines()
    import re
    pids = set()
    for line in lines:
        parts = re.split(r'\s+', line.strip())
        if parts:
            pids.add(parts[-1])
    for pid in pids:
        try:
            subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True, text=True)
        except Exception:
            pass

# Start uvicorn
p = subprocess.Popen([python_exe, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8001'], cwd=backend_dir)
print('started uvicorn pid', p.pid)

# Wait briefly for server to boot
time.sleep(2)

# Call analytics
try:
    with urlopen('http://127.0.0.1:8001/api/v1/analitica', timeout=10) as resp:
        body = resp.read()
        data = json.loads(body)
        print('reservas_activas', data.get('reservas_activas'))
        print('reservas_recomendadas_count', len(data.get('reservas_recomendadas', [])))
        for item in data.get('reservas_recomendadas', []):
            print('RECOM', item.get('ID_Reserva'), item.get('servicio_recomendado'))
except Exception as e:
    print('error calling analitica', e)

print('done')
