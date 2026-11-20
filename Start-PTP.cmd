@echo off
rem Patent-to-Pilot Workbench launcher (PTP-2026-11-21 / G01). Double-click to start; keep this window open.
setlocal
cd /d "%~dp0"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  where py >nul 2>nul && (set "PY=py -3.12") || (set "PY=python")
)
title Patent-to-Pilot Workbench
%PY% "%~dp0scripts\ptp_run.py" --serve --open %*
if errorlevel 1 (
  echo.
  echo The workbench stopped with an error. For a diagnosis run:
  echo   %PY% scripts\ptp_run.py --doctor
  pause
)
endlocal
