$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

if (-not (Test-Path (Join-Path $backend ".env"))) {
    Copy-Item (Join-Path $backend ".env.example") (Join-Path $backend ".env")
    Write-Host "Created backend/.env from backend/.env.example"
}

if (-not (Test-Path (Join-Path $frontend ".env"))) {
    Copy-Item (Join-Path $frontend ".env.example") (Join-Path $frontend ".env")
    Write-Host "Created frontend/.env from frontend/.env.example"
}

$backendCommand = "Set-Location '$backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
$frontendCommand = "Set-Location '$frontend'; `$env:BROWSER='none'; npm.cmd start"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "Backend starting on http://127.0.0.1:8000"
Write-Host "Frontend starting on http://localhost:3000"
