# run_dev.ps1
$ErrorActionPreference = "Stop"

# Move to repo root (directory where this script lives)
Set-Location -LiteralPath $PSScriptRoot

# Config
$env:ADMIN_TOKEN = "popsite"
$backendPort = 8000
$frontendPort = 5500

# Kill only processes bound to our ports (safe)
function Kill-Port($port) {
  $pids = netstat -ano | Select-String ":$port\s" | ForEach-Object {
    ($_ -split "\s+")[-1]
  } | Sort-Object -Unique

  foreach ($pid in $pids) {
    if ($pid -match "^\d+$" -and $pid -ne "0") {
      try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {}
    }
  }
}

Kill-Port $backendPort
Kill-Port $frontendPort

Write-Host "Starting backend on http://127.0.0.1:$backendPort"
Start-Process -WorkingDirectory $PSScriptRoot -NoNewWindow powershell -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy", "Bypass",
  "-Command",
  "cd `"$PSScriptRoot`"; `$env:ADMIN_TOKEN='popsite'; pipenv run uvicorn backend.main:app --reload --host 127.0.0.1 --port $backendPort"
)

Write-Host "Starting frontend on http://127.0.0.1:$frontendPort"
Set-Location -LiteralPath (Join-Path $PSScriptRoot "frontend")
python -m http.server $frontendPort