param(
    [string]$Recipient = "2303a51751@sru.edu.in"
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Testing Real-Time OTP Delivery to SRU Inboxes" -ForegroundColor Green
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
    Write-Host "[ERROR] Python executable not found." -ForegroundColor Red
    exit 1
}

Write-Host "Using Python: $pyPath" -ForegroundColor Yellow
Write-Host "Testing recipient: $Recipient" -ForegroundColor Cyan
Write-Host ""

& $pyPath test_email.py $Recipient
