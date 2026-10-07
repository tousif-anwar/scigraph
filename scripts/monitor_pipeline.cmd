@echo off
setlocal
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0monitor_pipeline.ps1" %*
