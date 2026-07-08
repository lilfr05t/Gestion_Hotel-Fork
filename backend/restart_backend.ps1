$lines = netstat -ano | findstr ":8001"
foreach ($l in $lines) {
    $parts = -split $l
    $procId = $parts[$parts.Length - 1]
    if ($procId) {
        try { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue } catch {}
    }
}
Set-Location 'C:/Users/enz0l/Documents/UNMSM/Gestion_Hotel-Bayes_version/backend'
& '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port 8001
