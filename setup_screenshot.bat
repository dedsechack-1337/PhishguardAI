@echo off
REM PhishGuard AI - Screenshot Analysis Setup (Windows)
cd /d "%~dp0"
call venv\Scripts\activate.bat

echo [1/3] Installing playwright + imagehash...
python -m pip install -q playwright==1.48.0 imagehash==4.3.1

echo [2/3] Downloading Chromium browser (~170MB)...
python -m playwright install chromium

echo [3/3] Building brand reference hashes...
python src\build_brand_reference.py

echo.
echo Screenshot Analysis is now enabled! Restart with run.bat
