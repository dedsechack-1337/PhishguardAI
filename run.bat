@echo off
REM PhishGuard AI - Quick Launch
REM Use this for every run AFTER the first-time setup (setup_and_run.bat).
REM Skips dependency checks/training and just opens the web UI.

cd /d "%~dp0"

call venv\Scripts\activate.bat

echo ==================================================
echo  PhishGuard AI - Launching...
echo ==================================================

streamlit run src\app.py
