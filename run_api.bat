@echo off
REM PhishGuard AI - Backend API launcher
REM Starts the FastAPI backend (required for the browser extension).

cd /d "%~dp0"
call venv\Scripts\activate.bat

echo ==================================================
echo  PhishGuard AI API - http://localhost:8000
echo  API docs:           http://localhost:8000/docs
echo ==================================================
uvicorn src.api:app --host 0.0.0.0 --port 8000
