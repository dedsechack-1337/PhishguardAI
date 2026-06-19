#!/usr/bin/env bash
# PhishGuard AI — One-command setup & launch
# Core install: ~510MB (scikit-learn, pandas, streamlit, fastapi, anthropic…)
# Screenshots add-on: +280MB (optional, see step 3b)

set -e
cd "$(dirname "$0")"

echo "=================================================="
echo " PhishGuard AI — Setup & Launch"
echo "=================================================="

# 1. Virtual environment
if [ ! -d "venv" ]; then
    echo "[1/5] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/5] Virtual environment already exists, skipping."
fi

source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

# 2. Core dependencies (~510MB)
echo "[2/5] Installing core dependencies..."
python -m pip install --upgrade pip -q
python -m pip install -q -r requirements.txt
# Install streamlit without pyarrow/pydeck to save ~175MB
# (our UI does not use st.map, st.dataframe arrow backend, or pydeck)
python -m pip install -q "streamlit==1.39.0" --no-deps
python -m pip install -q \
    "altair>=4.0,<6" blinker "cachetools>=4.0,<6" click gitpython \
    "packaging>=20,<25" "protobuf>=3.20,<6" "rich>=10.14.0,<14" \
    tenacity toml tornado "typing-extensions>=4.3.0" "watchdog>=2.1.5,<6"
echo "      Core dependencies installed."

# 3a. Screenshot analysis add-on (optional, +280MB)
INSTALL_SCREENSHOTS="${PHISHGUARD_SCREENSHOTS:-}"
if [ -z "$INSTALL_SCREENSHOTS" ]; then
    echo ""
    echo "      OPTIONAL: Install Screenshot Analysis add-on? (+280MB, playwright+chromium)"
    printf "      [y/N]: "
    read -r ans </dev/tty && ans="${ans:-N}"
    if [[ "$ans" =~ ^[Yy]$ ]]; then
        INSTALL_SCREENSHOTS=yes
    fi
fi

if [ "$INSTALL_SCREENSHOTS" = "yes" ]; then
    echo "      Installing playwright..."
    python -m pip install -q playwright==1.48.0
    echo "      Downloading Chromium browser (~170MB, one-time)..."
    python -m playwright install chromium
    echo "      Screenshot add-on installed."
else
    echo "      Screenshot add-on skipped. Enable later:"
    echo "        pip install playwright==1.48.0 && python -m playwright install chromium"
fi

# 4. Generate datasets + train model
echo "[3/5] Checking datasets..."
if [ ! -f "data/urls_dataset.csv" ]; then
    echo "      Generating URL dataset..."
    python src/generate_dataset.py
fi

echo "[4/5] Checking models..."
if [ ! -f "models/best_model.txt" ]; then
    echo "      Training URL phishing model (Random Forest)..."
    (cd src && python train.py)
else
    echo "      URL model already trained, skipping."
fi

# 5. Launch
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "      TIP: Set ANTHROPIC_API_KEY for AI-powered email analysis:"
    echo "        export ANTHROPIC_API_KEY=sk-ant-..."
fi

echo ""
echo "[5/5] Launching PhishGuard AI..."
echo "=================================================="
echo " Web UI:  http://localhost:8501"
echo " API:     run ./run_api.sh for browser extension"
echo " Daily:   use ./run.sh instead of this script"
echo "=================================================="
streamlit run src/app.py --server.headless false
