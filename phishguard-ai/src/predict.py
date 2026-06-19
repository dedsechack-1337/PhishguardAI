"""
Inference module for PhishGuard AI — URL phishing detection.

Uses a pre-trained Random Forest (or XGBoost) and a lightweight
explainer artifact (training correlation + feature importances)
to produce per-URL risk scores and human-readable explanations.
No SHAP/numba/llvmlite required.
"""

import os
import joblib
import numpy as np
import pandas as pd

from feature_extraction import extract_url_features

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

FEATURE_DESCRIPTIONS = {
    "url_length":            "the URL is unusually long",
    "host_length":           "the domain name is unusually long",
    "path_length":           "the URL path is unusually long",
    "num_dots":              "the URL contains many dots",
    "num_hyphens":           "the domain contains multiple hyphens",
    "num_underscores":       "the URL contains underscores",
    "num_slashes":           "the URL has many path segments",
    "num_at_symbols":        "the URL contains an '@' symbol (can hide real destination)",
    "num_question_marks":    "the URL contains query parameters",
    "num_equal_signs":       "the URL contains multiple parameters",
    "num_ampersands":        "the URL contains multiple chained parameters",
    "num_percent":           "the URL contains encoded characters",
    "num_digits":            "the URL contains many digits",
    "digit_ratio":           "a large portion of the URL is numeric",
    "num_subdomains":        "the domain has an unusual number of subdomains",
    "is_ip_address":         "the domain is a raw IP address instead of a name",
    "has_port":              "the URL specifies a non-standard port",
    "uses_https":            "the connection uses HTTPS",
    "has_at_symbol":         "the URL contains an '@' symbol",
    "double_slash_redirect": "the path contains a suspicious '//' redirect",
    "is_shortened":          "the URL uses a link-shortening service",
    "suspicious_word_count": "the URL contains suspicious words (e.g. 'verify', 'secure')",
    "host_entropy":          "the domain name looks randomly generated",
    "path_entropy":          "the URL path looks randomly generated",
    "tld_length":            "the domain extension (TLD) is unusual",
}


class PhishingURLDetector:
    def __init__(self, models_dir: str = MODELS_DIR):
        with open(os.path.join(models_dir, "best_model.txt")) as f:
            self.model_name = f.read().strip()

        model_file = "xgboost.joblib" if self.model_name == "xgboost" else "random_forest.joblib"
        self.model      = joblib.load(os.path.join(models_dir, model_file))
        self.feature_names = joblib.load(os.path.join(models_dir, "feature_names.joblib"))

        explainer_path = os.path.join(models_dir, "explainer.joblib")
        self.explainer = joblib.load(explainer_path) if os.path.exists(explainer_path) else None

    def _featurize(self, url: str) -> pd.DataFrame:
        return pd.DataFrame([extract_url_features(url)])[self.feature_names]

    def predict(self, url: str) -> dict:
        X = self._featurize(url)
        prob = float(self.model.predict_proba(X)[0, 1])
        return {
            "url": url,
            "label": "phishing" if prob >= 0.5 else "legitimate",
            "risk_score": round(prob * 100, 2),
            "model_used": self.model_name,
        }

    def explain(self, url: str, top_n: int = 5) -> dict:
        X = self._featurize(url)
        prob = float(self.model.predict_proba(X)[0, 1])
        label = "phishing" if prob >= 0.5 else "legitimate"

        sample = X.iloc[0]
        factors = []

        if self.explainer:
            importances  = self.explainer["feature_importances"]
            means        = self.explainer["feature_means"]
            stds         = self.explainer["feature_stds"]
            directions   = self.explainer["feature_directions"]

            scored = []
            for feat in self.feature_names:
                imp   = importances.get(feat, 0.0)
                mean  = means.get(feat, 0.0)
                std   = max(stds.get(feat, 1.0), 1e-6)
                z     = (sample[feat] - mean) / std          # how unusual is this value?
                dirn  = directions.get(feat, 1)
                score = imp * z * dirn                        # signed contribution
                scored.append((feat, score, sample[feat]))

            ranked = sorted(scored, key=lambda x: abs(x[1]), reverse=True)[:top_n]
        else:
            # Fallback: rank by feature importance alone
            imps = self.model.feature_importances_
            ranked = sorted(
                zip(self.feature_names, imps * (1 if prob >= 0.5 else -1), sample),
                key=lambda x: abs(x[1]), reverse=True
            )[:top_n]

        for fname, score, fval in ranked:
            factors.append({
                "feature":      fname,
                "value":        round(float(fval), 4),
                "contribution": round(float(score), 4),
                "effect":       "increases" if score > 0 else "decreases",
                "description":  self._describe(fname, fval),
            })

        return {
            "url":        url,
            "label":      label,
            "risk_score": round(prob * 100, 2),
            "model_used": self.model_name,
            "top_factors": factors,
        }

    @staticmethod
    def _describe(fname: str, fval: float) -> str:
        if fname == "uses_https":
            return "the connection uses HTTPS" if fval >= 1 else "the connection does NOT use HTTPS"
        if fname == "is_ip_address":
            return "the domain is a raw IP address" if fval >= 1 else "the domain is a normal hostname"
        if fname == "is_shortened":
            return "the URL uses a link shortener" if fval >= 1 else "the URL is not shortened"
        if fname in ("has_at_symbol", "num_at_symbols"):
            return "the URL contains an '@' symbol" if fval >= 1 else "no '@' symbol in URL"
        if fname == "has_port":
            return "the URL specifies a non-standard port" if fval >= 1 else "no custom port"
        if fname == "double_slash_redirect":
            return "the path contains a '//' redirect" if fval >= 1 else "no suspicious redirect"
        return FEATURE_DESCRIPTIONS.get(fname, fname)


if __name__ == "__main__":
    d = PhishingURLDetector()
    for url in [
        "https://www.google.com",
        "http://paypal-secure-login.verify-account.tk/signin?user=123",
        "http://192.168.1.1/login.php?id=4521",
    ]:
        r = d.explain(url)
        print(f"\n{r['url']}")
        print(f"  -> {r['label'].upper()} ({r['risk_score']}%)")
        for f in r["top_factors"]:
            a = "▲" if f["effect"] == "increases" else "▼"
            print(f"     {a} {f['description']}  (z-score contribution: {f['contribution']:+.3f})")
