@echo off
title wxdown-service - Credential Capture
powershell -NoExit -ExecutionPolicy Bypass -File "D:\Dev\ai-wechat-pipeline\tools\start_wxdown.ps1"
if errorlevel 1 (
    echo.
    echo [FATAL] Launch failed, exit code = %errorlevel%
    echo Screenshot and send to Claude
    pause
)
