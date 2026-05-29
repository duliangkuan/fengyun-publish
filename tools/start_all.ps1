# Launch BOTH exporter UI and wxdown credential service in separate windows.
# Triggered by double-clicking tools/start-all.bat (or desktop shortcut).
# Each service gets its own PowerShell window so you can see logs / Ctrl+C separately.

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = $PSScriptRoot
$ExporterScript = Join-Path $ScriptDir "start_exporter.ps1"
$WxdownScript = Join-Path $ScriptDir "start_wxdown.ps1"

$Host.UI.RawUI.WindowTitle = "公众号数据抓取 - launcher"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  公众号数据抓取 - 启动 2 个服务" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $ExporterScript)) {
    Write-Host "[FATAL] $ExporterScript not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
if (-not (Test-Path $WxdownScript)) {
    Write-Host "[FATAL] $WxdownScript not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/2] Starting exporter UI (yarn dev) in a new window ..." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$ExporterScript`""

Start-Sleep -Seconds 1

Write-Host "[2/2] Starting wxdown credential service in a new window ..." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$WxdownScript`""

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "  Both services started." -ForegroundColor Green
Write-Host "  Check the 2 new windows for logs." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your job (in browser/Edge yourself):" -ForegroundColor Yellow
Write-Host "  1. Wait for exporter UI to open (http://localhost:3000)"
Write-Host "  2. Wait for wxdown to show 'Service started' in its window"
Write-Host "  3. Open WeChat article in a browser that goes through mitmproxy"
Write-Host "  4. Back in exporter UI: crawl your account, export JSON"
Write-Host ""
Write-Host "This launcher window will close in 8 seconds." -ForegroundColor Gray

Start-Sleep -Seconds 8
