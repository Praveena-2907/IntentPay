# IntentPay One-Command Launcher (Windows PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INTENTPAY: Programmable Payments MVP" -ForegroundColor Cyan
Write-Host "Simulated execution only - No real funds" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

# Start Backend in background job
$BackendJob = Start-Job -ScriptBlock {
    Set-Location -Path $using:PWD
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
}

Write-Host "Backend started at http://127.0.0.1:8000" -ForegroundColor Green

# Start Frontend
Set-Location -Path "$PWD\frontend"
npm run dev
