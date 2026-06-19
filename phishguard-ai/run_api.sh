#!/usr/bin/env bash
# PhishGuard AI — Backend API launcher
# Starts the FastAPI backend (required for the browser extension).

cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

echo "=================================================="
echo " PhishGuard AI API - http://localhost:8000"
echo " API docs:           http://localhost:8000/docs"
echo "=================================================="
uvicorn src.api:app --host 0.0.0.0 --port 8000
