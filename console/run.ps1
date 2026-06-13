# TRPG Console launcher — sets up venv on first run, then starts the Flask server.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $here ".venv"
$py = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Host "[console] creating venv at $venv"
    python -m venv $venv
    & $py -m pip install --upgrade pip
    & $py -m pip install -r (Join-Path $here "requirements.txt")
}

$env:PYTHONPATH = Join-Path $here "server"
Write-Host "[console] starting on http://127.0.0.1:8765"
& $py (Join-Path $here "server\app.py")
