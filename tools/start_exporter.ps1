# Start wechat-article-exporter service.
# Triggered by double-clicking tools/start-exporter.bat (or desktop shortcut).
# All UI text kept ASCII to avoid PowerShell 5.1 GBK-vs-UTF8 parser bugs.

$ErrorActionPreference = "Stop"

# Force UTF-8 output so any Chinese strings echoed by yarn / nuxt render correctly
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ExporterDir = Join-Path $ProjectRoot "_staging\wechat-article-exporter"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  WeChat Article Exporter" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $ExporterDir)) {
    Write-Host "[FATAL] Exporter dir not found:" -ForegroundColor Red
    Write-Host "  $ExporterDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Set-Location $ExporterDir
Write-Host "[1/4] cd to: $ExporterDir" -ForegroundColor Gray

# yarn is managed via corepack (no global install). Enable + activate once per run (idempotent).
Write-Host "[2/4] Activating yarn via corepack ..." -ForegroundColor Gray
$cp = Get-Command corepack -ErrorAction SilentlyContinue
if (-not $cp) {
    Write-Host "[FATAL] corepack not found. Install Node.js >= 22 first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
# PowerShell 5.1 把 native cmd 的 stderr 经 2>&1 重定向后会包成 ErrorRecord,
# 即使 exit code = 0 也让 $? 变 false,叠加 $ErrorActionPreference=Stop 直接终止脚本。
# 改用 cmd 文件级重定向 > $null 2>&1,避开这个坑。
& cmd /c "corepack enable > nul 2>&1"
& cmd /c "corepack prepare yarn@1.22.22 --activate > nul 2>&1"

if (-not (Test-Path "node_modules")) {
    Write-Host "[!] node_modules missing, running yarn install (a few minutes)..." -ForegroundColor Yellow
    corepack yarn install
}

Write-Host "[3/4] Browser will open http://localhost:3000 in 8 seconds." -ForegroundColor Gray

Start-Job -ScriptBlock {
    Start-Sleep -Seconds 8
    Start-Process "http://localhost:3000"
} | Out-Null

Write-Host "[4/4] Starting yarn dev (via corepack) ..." -ForegroundColor Gray
Write-Host ""
Write-Host "Steps in the browser:" -ForegroundColor Green
Write-Host "  1. Scan QR to log into WeChat Official Account assistant"
Write-Host "  2. Search your account name in UI (Yan Jiu Agent De Yun)"
Write-Host "  3. Crawl, then export as JSON format"
Write-Host "  4. Save JSON to:  corpus\raw\fengyun\wechat_articles.json"
Write-Host ""
Write-Host "To stop: press Ctrl+C in this window." -ForegroundColor Yellow
Write-Host ""

corepack yarn dev
