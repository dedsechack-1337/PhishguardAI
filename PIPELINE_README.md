# PhishGuard AI

AI-based phishing detection: analyze URLs (XGBoost/Random Forest + SHAP
explanations) and email text (DistilBERT + saliency explanations, with a
keyword-based fallback) — all through a simple web UI.

## 🚀 Quick Start (One Command)

**First-time setup (Linux / macOS):**
```bash
chmod +x setup_and_run.sh run.sh
./setup_and_run.sh
```

**First-time setup (Windows):**
```bat
setup_and_run.bat
```

This will create a venv, install everything, train the URL model, and
open the web UI in your browser automatically.

**Every run after that:**
```bash
./run.sh        # Linux/macOS
run.bat         # Windows
```
This skips all setup checks and just launches the dashboard.

## 🌐 Web UI

Two tabs:
- **🔗 URL Analyzer** — paste a URL, get a risk score (0-100%), verdict, and
  a plain-English explanation of *why* (e.g. "no HTTPS", "domain looks
  randomly generated", "contains suspicious words like 'verify'").
- **✉️ Email Analyzer** — paste email text, get a risk score and the
  words/phrases that triggered the result.

## 🧠 Enabling AI-Based Email Detection (Optional)

By default, the email analyzer uses a fast keyword-based fallback. For
AI-based detection with DistilBERT (requires internet, one-time ~260MB
download):

```bash
source venv/bin/activate        # Windows: venv\Scripts\activate
cd src
python train_email_model.py
```

Re-run `setup_and_run.sh` (or just `streamlit run src/app.py`) afterward —
the UI automatically detects and uses the trained model.

## 📁 Project Structure
```
phishguard-ai/
├── setup_and_run.sh / .bat   # one-command setup & launch
├── requirements.txt
├── data/                     # generated datasets
├── models/                   # trained models (URL + SHAP, email BERT)
└── src/
    ├── app.py                # Streamlit web UI
    ├── feature_extraction.py # URL feature engineering
    ├── generate_dataset.py   # synthetic URL dataset
    ├── generate_email_dataset.py
    ├── train.py              # trains URL models
    ├── train_email_model.py  # fine-tunes DistilBERT
    ├── predict.py            # URL inference + SHAP
    └── predict_email.py      # email inference + saliency
```

## 🔄 Manual Setup (Advanced)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
pip install streamlit

cd src
python generate_dataset.py
python generate_email_dataset.py
python train.py
streamlit run app.py
```

## 📊 Replacing Synthetic Data with Real Datasets
- **URLs**: PhiUSIIL Phishing URL Dataset (Kaggle/UCI), PhishTank dumps —
  CSV with `url,label` columns.
- **Emails**: Nazario phishing corpus + Enron ham emails — CSV with
  `text,label` columns.

## 🛠️ Versions Tested
| Package | Version |
|---|---|
| Python | 3.10–3.12 |
| scikit-learn | 1.5.2 |
| xgboost | 2.1.1 |
| shap | 0.46.0 |
| pandas | 2.2.3 |
| numpy | 1.26.4 |
| torch | 2.4.1 (CPU) |
| transformers | 4.46.0 |
| accelerate | 1.0.1 |
| streamlit | 1.58.0 |

## 🐛 Troubleshooting
- **`pip install` runs out of disk space**: run `pip cache purge` first.
- **`streamlit: command not found`**: make sure the venv is activated
  (`source venv/bin/activate`).
- **SHAP errors after upgrading**: retrain with `python src/train.py` to
  regenerate `models/shap_explainer.joblib`.

---
⚠️ For research/educational use. Always exercise caution with suspicious
links and emails regardless of tool output.
