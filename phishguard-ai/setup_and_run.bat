@echo off
REM PhishGuard AI - One-command setup & launch (Windows)
REM Core install: ~510MB  |  +Screenshots add-on: +280MB (optional)

cd /d "%~dp0"

echo ==================================================
echo  PhishGuard AI -- Setup ^& Launch
echo ==================================================

if not exist venv (
    echo [1/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/5] Virtual environment already exists, skipping.
)

call venv\Scripts\activate.bat

echo [2/5] Installing core dependencies...
python -m pip install --upgrade pip -q
python -m pip install -q -r requirements.txt
python -m pip install -q "streamlit==1.39.0" --no-deps
python -m pip install -q "altair>=4.0,<6" blinker "cachetools>=4.0,<6" click gitpython "packaging>=20,<25" "protobuf>=3.20,<6" "rich>=10.14.0,<14" tenacity toml tornado "typing-extensions>=4.3.0" watchdog

echo.
set /p SCREENSHOTS="OPTIONAL: Install Screenshot Analysis add-on? (+280MB playwright+chromium) [y/N]: "
if /i "%SCREENSHOTS%"=="y" (
    python -m pip install -q playwright==1.48.0
    python -m playwright install chromium
    echo Screenshot add-on installed.
) else (
    echo Screenshot add-on skipped.
    echo To enable later: pip install playwright==1.48.0 ^&^& python -m playwright install chromium
)

echo [3/5] Checking datasets...
if not exist data\urls_dataset.csv (
    python src\generate_dataset.py
)

echo [4/5] Checking models...
if not exist models\best_model.txt (
    cd src
    python train.py
    cd ..
) else (
    echo       URL model already trained, skipping.
)

if "%ANTHROPIC_API_KEY%"=="" (
    echo.
    echo       TIP: set ANTHROPIC_API_KEY=sk-ant-... for AI email analysis
)

echo.
echo [5/5] Launching PhishGuard AI...
echo ==================================================
echo  Web UI:  http://localhost:8501
echo  API:     run run_api.bat for browser extension
echo  Daily:   use run.bat instead of this script
echo ==================================================
streamlit run src\app.py --server.headless false
