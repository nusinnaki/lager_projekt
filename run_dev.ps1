# run_dev.ps1
$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

$backendHost = "127.0.0.1"
$backendPort = 8000
$frontendPort = 5500

# Dev admin token (must match what frontend users type)
$env:ADMIN_TOKEN = "popsite"

# Stop old processes (best-effort)
Get-Process -Name uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name python  -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Starting backend on http://$backendHost`:$backendPort"
Start-Process -NoNewWindow -WorkingDirectory $ROOT -FilePath "powershell.exe" -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy", "ByPass",
  "-Command",
  "Set-Location '$ROOT'; `$env:ADMIN_TOKEN='popsite'; pipenv run uvicorn backend.main:app --reload --host $backendHost --port $backendPort"
)

Write-Host "Starting frontend on http://127.0.0.1`:$frontendPort"
Set-Location (Join-Path $ROOT "frontend")
python -m http.server $frontendPort