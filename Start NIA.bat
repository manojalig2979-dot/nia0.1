@echo off
cd /d "%~dp0nia_agent"
if exist "%~dp0.venv\Scripts\pythonw.exe" (
    start "" "%~dp0.venv\Scripts\pythonw.exe" nia_gui.py
) else (
    start "" pythonw nia_gui.py
)
exit
