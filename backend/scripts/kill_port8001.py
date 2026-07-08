import subprocess
import re
import sys

def get_pids():
    try:
        out = subprocess.check_output(['netstat','-ano'], text=True)
    except Exception as e:
        print('netstat failed:', e)
        return []
    pids = set()
    for line in out.splitlines():
        if ':8001' in line:
            m = re.search(r"\s+(\d+)$", line.strip())
            if m:
                pids.add(m.group(1))
    return list(pids)

pids = get_pids()
if not pids:
    print('No processes found listening on port 8001')
    sys.exit(0)
for pid in pids:
    try:
        subprocess.check_call(['taskkill','/PID',pid,'/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print('Killed PID', pid)
    except subprocess.CalledProcessError:
        print('Failed to kill PID', pid)
