# Start wxdown-service (credential capture service).
# Triggered by double-clicking tools/start-wxdown.bat (or desktop shortcut).
# All UI text kept ASCII to avoid PowerShell 5.1 GBK-vs-UTF8 parser bugs.

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WxdownDir = Join-Path $ProjectRoot "_staging\wxdown-service"
$VenvPython = Join-Path $WxdownDir ".venv\Scripts\python.exe"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  wxdown-service" -ForegroundColor Cyan
Write-Host "  (Credential capture)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $WxdownDir)) {
    Write-Host "[FATAL] wxdown-service dir not found:" -ForegroundColor Red
    Write-Host "  $WxdownDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "[FATAL] .venv python not found:" -ForegroundColor Red
    Write-Host "  $VenvPython" -ForegroundColor Red
    Write-Host "  Need to: cd $WxdownDir; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Set-Location $WxdownDir
Write-Host "[1/2] cd to: $WxdownDir" -ForegroundColor Gray
Write-Host "[2/2] Starting wxdown-service (via venv python) ..." -ForegroundColor Gray
Write-Host ""
Write-Host "WAIT FOR:  'Service started / listening successfully'" -ForegroundColor Green
Write-Host ""
Write-Host "After this service shows ready, do these (separately):" -ForegroundColor Green
Write-Host "  1. Run: _staging\wxdown-service\qi-dong-zhua-bao-liu-lan-qi.bat"
Write-Host "     (Chinese filename: 启动抓包浏览器.bat — launches a special Edge)"
Write-Host "  2. In that special Edge, open ANY WeChat article URL"
Write-Host "  3. wxdown captures credentials and pushes to exporter UI"
Write-Host "  4. Back in exporter UI (http://localhost:3000), crawl your account"
Write-Host ""
Write-Host "To stop: Ctrl+C in this window." -ForegroundColor Yellow
Write-Host ""

& $VenvPython main.py
