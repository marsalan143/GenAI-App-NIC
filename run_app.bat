@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Please create the virtual environment and install requirements first. See README.md.
    pause
    exit /b 1
)
set PYTHONDONTWRITEBYTECODE=1
".venv\Scripts\python.exe" -B -m streamlit run app.py
