#!/usr/bin/env bash
# PhishGuard AI — Screenshot Analysis Setup (Optional Add-on)
# Adds ~280MB: playwright library + Chromium browser binary
#
# Run AFTER setup_and_run.sh:
#   chmod +x setup_screenshot.sh
#   ./setup_screenshot.sh

set -e
cd "$(dirname "$0")"

echo "=================================================="
echo " PhishGuard AI — Screenshot Analysis Setup"
echo " This will download ~280MB (playwright + Chromium)"
echo "=================================================="

source venv/bin/activate 2>/dev/null || . venv/Scripts/activate

echo "[1/3] Installing playwright + imagehash..."
python -m pip install -q playwright==1.48.0 imagehash==4.3.1

echo "[2/3] Downloading Chromium browser (~170MB)..."
python -m playwright install chromium

echo "[3/3] Building brand reference hashes (captures 10 brand pages)..."
python src/build_brand_reference.py 2>/dev/null || echo "      (some sites may fail — that is fine)"

echo ""
echo "=================================================="
echo " Screenshot Analysis is now enabled!"
echo " Restart the web UI: ./run.sh"
echo "=================================================="
