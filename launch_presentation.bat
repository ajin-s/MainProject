@echo off
title SmartEduSync — Tabletop AI Tutoring Robot
color 0b
echo =======================================================================
echo          Starting SmartEduSync Presentation Defense Interface
echo                     Group 07 (MBCCET)
echo =======================================================================
echo.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_presentation.py
) else (
    python run_presentation.py
)
pause
