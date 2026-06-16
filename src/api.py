"""
PhishGuard AI — FastAPI Backend

Provides REST endpoints for:
  POST /analyze/url        -> URL risk score + SHAP explanation
  POST /analyze/email      -> Email risk score + explanation (Claude API / fallback)
  POST /analyze/reputation -> URLhaus domain/URL reputation lookup
  POST /analyze/screenshot -> Screenshot capture + brand visual-similarity check
  POST /analyze/full       -> Combines url + reputation (+ screenshot if requested)

Used by:
  - The Streamlit web UI (optional — UI can also call modules directly)
  - The browser extension (extension/ directory)

Run with:
    uvicorn api:app --reload --port 8000

CORS is enabled for all origins so the browser extension (running from a
chrome-extension:// origin) can call this API when running locally.
"""

import os
import sys
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))

from predict import PhishingURLDetector
from predict_email import EmailPhishingDetector
from domain_reputation import check_url_reputation, check_host_reputation

app = FastAPI(title="PhishGuard AI API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------
# Lazy-loaded detectors (loaded on first request, not at import time)
# ----------------------------------------------------------------------
_url_detector = None
_email_detector = None


def get_url_detector():
    global _url_detector
    if _url_detector is None:
        _url_detector = PhishingURLDetector()
    return _url_detector


def get_email_detector():
    global _email_detector
    if _email_detector is None:
        _email_detector = EmailPhishingDetector()
    return _email_detector


# ----------------------------------------------------------------------
# Request/response models
# ----------------------------------------------------------------------
class URLRequest(BaseModel):
    url: str


class EmailRequest(BaseModel):
    text: str


class FullAnalysisRequest(BaseModel):
    url: str
    include_screenshot: bool = False


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------
@app.get("/")
def root():
    url_models_exist = os.path.exists(
        os.path.join(os.path.dirname(__file__), "..", "models", "best_model.txt")
    )
    return {
        "service": "PhishGuard AI API",
        "status": "ok",
        "url_model_ready": url_models_exist,
    }


@app.post("/analyze/url")
def analyze_url(req: URLRequest):
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL must not be empty")

    try:
        detector = get_url_detector()
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="URL models not found. Run setup_and_run.sh / train.py first.",
        )

    return detector.explain(req.url.strip())


@app.post("/analyze/email")
def analyze_email(req: EmailRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Email text must not be empty")

    detector = get_email_detector()
    return detector.explain(req.text.strip())


@app.post("/analyze/reputation")
def analyze_reputation(req: URLRequest):
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL must not be empty")

    url = req.url.strip()
    host = urlparse(url if "://" in url else "http://" + url).netloc.split(":")[0]

    return {
        "url": url,
        "host": host,
        "url_reputation": check_url_reputation(url),
        "host_reputation": check_host_reputation(host),
    }


@app.post("/analyze/screenshot")
def analyze_screenshot(req: URLRequest):
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL must not be empty")

    # Imported lazily: playwright/imagehash are heavier and only needed here
    from screenshot_analysis import capture_and_analyze

    return capture_and_analyze(req.url.strip())


@app.post("/analyze/full")
def analyze_full(req: FullAnalysisRequest):
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL must not be empty")

    url = req.url.strip()
    host = urlparse(url if "://" in url else "http://" + url).netloc.split(":")[0]

    result = {"url": url}

    try:
        detector = get_url_detector()
        result["ml_analysis"] = detector.explain(url)
    except FileNotFoundError:
        result["ml_analysis"] = {"error": "URL models not found"}

    result["reputation"] = {
        "url_reputation": check_url_reputation(url),
        "host_reputation": check_host_reputation(host),
    }

    if req.include_screenshot:
        from screenshot_analysis import capture_and_analyze
        result["screenshot"] = capture_and_analyze(url)

    # Combine risk scores into an overall verdict
    ml_score = result["ml_analysis"].get("risk_score", 0) if "risk_score" in result["ml_analysis"] else 0
    reputation_listed = result["reputation"]["url_reputation"].get("status") == "listed"

    overall_score = ml_score
    if reputation_listed:
        overall_score = max(overall_score, 95)

    result["overall_risk_score"] = round(overall_score, 2)
    result["overall_label"] = "phishing" if overall_score >= 50 else "legitimate"

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
