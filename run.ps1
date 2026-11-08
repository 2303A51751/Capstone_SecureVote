# PowerShell Start Script for Blockchain E-Voting System
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Starting Blockchain E-Voting System (Django 5 + ECDSA)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd) {
    $pyPath = $cmd.Source
} else {
    $cmdPy = Get-Command py -ErrorAction SilentlyContinue
    if ($cmdPy) {
        $pyPath = $cmdPy.Source
    } else {
        $defaultPy = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
        if (Test-Path $defaultPy) {
            $pyPath = $defaultPy
        }
    }
}

if (-not $pyPath) {
    Write-Host "[ERROR] Python 3.9+ executable not found." -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $pyPath" -ForegroundColor Yellow
Write-Host "Checking migrations..." -ForegroundColor Cyan
& $pyPath manage.py migrate

Write-Host ""
Write-Host "Starting server at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Default Admin: username 'admin' / password 'admin123'" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to terminate." -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan
& $pyPath manage.py runserver 127.0.0.1:8000

