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

$backendCommand = @"
Set-Location -LiteralPath '$backend'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
"@

$frontendCommand = @"
Set-Location -LiteralPath '$frontend'
`$env:BROWSER='none'
if (-not (Test-Path -LiteralPath 'node_modules')) {
    Write-Host 'Installing frontend dependencies...'
    npm.cmd install --legacy-peer-deps
    if (`$LASTEXITCODE -ne 0) {
        Write-Host 'Retrying install with --ignore-scripts (EPERM workaround)...'
        npm.cmd install --legacy-peer-deps --ignore-scripts
    }
}
npm.cmd start
"@

Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $backendCommand
Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $frontendCommand

Write-Host "Backend starting on http://127.0.0.1:8000"
Write-Host "Frontend starting on http://localhost:3000"
