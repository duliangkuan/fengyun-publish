@echo off
REM headless_ship.bat — 双击/cmd 入口,转发到 PowerShell .ps1
REM 用法: headless_ship.bat "ship 一篇关于 X 的文章"

setlocal

if "%~1"=="" (
    echo 用法: headless_ship.bat "ship 一篇关于 ^<主题^> 的文章"
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%headless_ship.ps1" -Topic "%~1"

endlocal
exit /b %ERRORLEVEL%
