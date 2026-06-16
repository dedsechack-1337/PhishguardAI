#!/usr/bin/env bash
# PhishGuard AI — Quick Launch
# Use this for every run AFTER the first-time setup (setup_and_run.sh).
# Skips dependency checks/training and just opens the web UI.

cd "$(dirname "$0")"

source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

echo "=================================================="
echo " PhishGuard AI - Launching..."
echo "=================================================="

streamlit run src/app.py
