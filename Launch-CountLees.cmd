@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 goto failed
py countlees.py
if errorlevel 1 goto failed
exit /b 0
:failed
pause
exit /b 1
