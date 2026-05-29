@echo off
title Launching exporter + wxdown
powershell -ExecutionPolicy Bypass -File "D:\Dev\ai-wechat-pipeline\tools\start_all.ps1"
if errorlevel 1 (
    echo.
    echo [FATAL] Launch failed, exit code = %errorlevel%
    echo Screenshot and send to Claude
    pause
)
