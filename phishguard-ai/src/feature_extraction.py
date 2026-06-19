"""
URL Feature Extraction for Phishing Detection
Extracts lexical, structural, and host-based features from a URL.
"""

import re
import math
from urllib.parse import urlparse
from collections import Counter


SUSPICIOUS_WORDS = [
    "login", "verify", "account", "secure", "update", "banking",
    "confirm", "signin", "password", "ebayisapi", "webscr", "paypal",
    "free", "lucky", "bonus", "click", "urgent"
]

SHORTENING_SERVICES = [
    "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co", "is.gd",
    "buff.ly", "adf.ly", "shorte.st"
]


def shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string (measures randomness)."""
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def is_ip_address(host: str) -> int:
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    return 1 if re.match(pattern, host or "") else 0


def count_chars(s: str, chars: str) -> int:
    return sum(s.count(c) for c in chars)


def extract_url_features(url: str) -> dict:
    """
    Extract a dictionary of numeric features from a single URL.
    These features feed into the XGBoost / Random Forest models.
    """
    url = url.strip()
    parsed = urlparse(url if "://" in url else "http://" + url)

    host = parsed.netloc.lower()
    path = parsed.path or ""
    query = parsed.query or ""
    full = url.lower()

    # Strip port from host for analysis
    host_no_port = host.split(":")[0]
    subdomains = host_no_port.split(".")

    features = {
        # --- Basic length features ---
        "url_length": len(url),
        "host_length": len(host),
        "path_length": len(path),

        # --- Character composition ---
        "num_dots": full.count("."),
        "num_hyphens": full.count("-"),
        "num_underscores": full.count("_"),
        "num_slashes": full.count("/"),
        "num_at_symbols": full.count("@"),
        "num_question_marks": full.count("?"),
        "num_equal_signs": full.count("="),
        "num_ampersands": full.count("&"),
        "num_percent": full.count("%"),
        "num_digits": sum(c.isdigit() for c in full),
        "digit_ratio": (sum(c.isdigit() for c in full) / len(full)) if full else 0,

        # --- Structural ---
        "num_subdomains": max(len(subdomains) - 2, 0),
        "is_ip_address": is_ip_address(host_no_port),
        "has_port": 1 if ":" in host else 0,
        "uses_https": 1 if parsed.scheme == "https" else 0,

        # --- Suspicious indicators ---
        "has_at_symbol": 1 if "@" in url else 0,
        "double_slash_redirect": 1 if "//" in path else 0,
        "is_shortened": 1 if any(s in host_no_port for s in SHORTENING_SERVICES) else 0,
        "suspicious_word_count": sum(1 for w in SUSPICIOUS_WORDS if w in full),

        # --- Entropy (randomness, common in algorithmically generated domains) ---
        "host_entropy": shannon_entropy(host_no_port),
        "path_entropy": shannon_entropy(path),

        # --- TLD / domain checks ---
        "tld_length": len(host_no_port.split(".")[-1]) if "." in host_no_port else 0,
    }

    return features


def extract_features_batch(urls: list) -> "pd.DataFrame":
    """Extract features for a list of URLs and return a DataFrame."""
    import pandas as pd
    rows = [extract_url_features(u) for u in urls]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    test_urls = [
        "https://www.google.com",
        "http://paypal-secure-login.verify-account.tk/signin?user=123",
        "http://192.168.1.1/login.php",
        "https://bit.ly/3xYzAbC"
    ]
    for u in test_urls:
        print(u)
        print(extract_url_features(u))
        print("-" * 40)
