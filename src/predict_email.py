"""
Email phishing detection via the Anthropic API (Claude).

Replaces the local DistilBERT fine-tuning approach with an API call,
avoiding the ~1.2GB torch + transformers install. Requires an
ANTHROPIC_API_KEY environment variable.

If no API key is set (or the API call fails), falls back to a
keyword-based heuristic so the rest of the system keeps working offline.
"""

import os
import json
import re

FALLBACK_KEYWORDS = [
    "verify", "suspended", "urgent", "click here", "confirm your",
    "password will expire", "won", "claim your", "act now", "update your billing",
    "security alert", "unusual sign-in", "final notice", "account will be locked",
]

SYSTEM_PROMPT = """You are a phishing-email detection engine. Analyze the given email text \
and respond with ONLY a JSON object (no markdown, no preamble) in this exact format:

{
  "label": "phishing" or "legitimate",
  "risk_score": <number 0-100>,
  "signals": [
    {"phrase": "<short quoted phrase from the email, max 6 words>", "reason": "<why this is suspicious or benign, max 15 words>"}
  ]
}

Include up to 5 signals, the most important first. Base risk_score on urgency language, \
requests for credentials/payment, suspicious links, impersonation of brands, and \
generic/mismatched greetings. A risk_score >= 50 should correspond to label "phishing"."""


class EmailPhishingDetector:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.available = bool(self.api_key)
        self._client = None

        if self.available:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"[EmailPhishingDetector] anthropic SDK not available: {e}")
                self.available = False

    # ------------------------------------------------------------------
    def predict(self, text: str) -> dict:
        result = self.explain(text)
        return {
            "text": result["text"],
            "label": result["label"],
            "risk_score": result["risk_score"],
            "model_used": result["model_used"],
        }

    def explain(self, text: str, top_n: int = 5) -> dict:
        if self.available:
            try:
                return self._explain_api(text, top_n)
            except Exception as e:
                print(f"[EmailPhishingDetector] API call failed, using fallback: {e}")

        return self._explain_fallback(text, top_n)

    # ------------------------------------------------------------------
    def _explain_api(self, text: str, top_n: int) -> dict:
        message = self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text[:4000]}],
        )

        raw = "".join(block.text for block in message.content if hasattr(block, "text"))
        raw = raw.strip()
        raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()

        parsed = json.loads(raw)

        label = parsed.get("label", "legitimate")
        risk_score = float(parsed.get("risk_score", 0))
        signals = parsed.get("signals", [])[:top_n]

        top_tokens = [
            {"token": s.get("phrase", ""), "importance": 1.0, "reason": s.get("reason", "")}
            for s in signals
        ]

        return {
            "text": text,
            "label": label,
            "risk_score": round(risk_score, 2),
            "model_used": "claude-haiku-4-5 (api)",
            "top_tokens": top_tokens,
        }

    # ------------------------------------------------------------------
    def _explain_fallback(self, text: str, top_n: int) -> dict:
        lowered = text.lower()
        matches = [kw for kw in FALLBACK_KEYWORDS if kw in lowered]
        score = min(len(matches) * 22, 95) if matches else 5
        label = "phishing" if score >= 50 else "legitimate"

        return {
            "text": text,
            "label": label,
            "risk_score": float(score),
            "model_used": "keyword_fallback",
            "top_tokens": [
                {"token": kw, "importance": 1.0, "reason": "matched suspicious keyword"}
                for kw in matches[:top_n]
            ],
        }


if __name__ == "__main__":
    detector = EmailPhishingDetector()
    print(f"API available: {detector.available}\n")

    samples = [
        "URGENT: Your PayPal account has been suspended. Click here to verify your identity: http://paypal-secure.tk/verify",
        "Hi team, just a reminder that our weekly sync is moved to 10:00 AM tomorrow. Let me know if that works.",
    ]

    for text in samples:
        result = detector.explain(text)
        print(f"Text: {text}")
        print(f"  -> {result['label'].upper()} (risk: {result['risk_score']}%) via {result['model_used']}")
        for t in result["top_tokens"]:
            print(f"     - {t['token']}: {t.get('reason','')}")
        print()
