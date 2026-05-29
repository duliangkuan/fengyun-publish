@echo off
title WeChat Article Exporter
powershell -NoExit -ExecutionPolicy Bypass -File "D:\Dev\ai-wechat-pipeline\tools\start_exporter.ps1"
if errorlevel 1 (
    echo.
    echo [FATAL] Launch failed, exit code = %errorlevel%
    echo Screenshot and send to Claude
    pause
)
