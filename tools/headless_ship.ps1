# headless_ship.ps1 - fengyun-publish headless entry point (Windows PowerShell)
#
# Usage:
#   .\tools\headless_ship.ps1 "ship a piece about Anthropic 7 things this week"
#   .\tools\headless_ship.ps1 -Topic "ship..." -DryRun
#   .\tools\headless_ship.ps1 -Topic "..." -AllowedDir "D:\Dev\ai-wechat-pipeline"
#
# Design (Phase 7 Round 4 consensus):
#   - Use `claude -p "$Topic" --dangerously-skip-permissions --add-dir <root>` headless
#   - --add-dir grants Claude read/write on output/ tools/ etc.
#   - Claude Code drives fengyun-publish skill 9 steps
#   - Log to .log file so Task Scheduler runs are auditable
#
# NOTE: ASCII-only comments / strings to avoid PowerShell 5.1 parser issues
# with non-BOM UTF-8 files containing CJK characters.

param(
    [Parameter(Position=0)]
    [string]$Topic,

    [string]$AllowedDir = "D:\Dev\ai-wechat-pipeline",

    [string]$OutLog = "",

    [switch]$DryRun
)

if (-not $Topic) {
    Write-Host "Usage: .\tools\headless_ship.ps1 ""ship a piece about <topic>""" -ForegroundColor Yellow
    Write-Host "Or:    .\tools\headless_ship.ps1 -Topic ""..."" -DryRun"
    exit 1
}

if (-not (Test-Path $AllowedDir)) {
    Write-Host "[ERROR] AllowedDir not found: $AllowedDir" -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrEmpty($OutLog)) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $logDir = Join-Path $AllowedDir "output\runs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    $OutLog = Join-Path $logDir "headless-$timestamp.log"
}

Write-Host "=== fengyun-publish headless ship ===" -ForegroundColor Cyan
Write-Host "Topic:       $Topic"
Write-Host "AllowedDir:  $AllowedDir"
Write-Host "OutLog:      $OutLog"
Write-Host "DryRun:      $DryRun"
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY-RUN] skipping actual execution, printing command only" -ForegroundColor Yellow
    Write-Host "claude -p ""$Topic"" --dangerously-skip-permissions --add-dir ""$AllowedDir"""
    exit 0
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] launching claude -p ..." -ForegroundColor Green

# Windows PowerShell 5.1: do NOT use 2>&1 on native exe (causes NativeCommandError).
# stderr is already captured. Tee-Object writes both screen and log file.
$exitCode = 0
& claude -p $Topic --dangerously-skip-permissions --add-dir $AllowedDir | Tee-Object -FilePath $OutLog
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] done, exit=$exitCode" -ForegroundColor Green
Write-Host "Log: $OutLog"

exit $exitCode
