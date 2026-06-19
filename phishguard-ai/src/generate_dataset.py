"""
Synthetic URL dataset generator.

Generates a labeled dataset of "legitimate" and "phishing-style" URLs
so the training pipeline can run end-to-end without external downloads.

NOTE: For production-quality models, replace this with a real dataset
(e.g., PhiUSIIL Phishing URL Dataset from Kaggle/UCI, PhishTank dumps,
or your own labeled corpus). The feature_extraction.py module works
the same regardless of data source.
"""

import random
import pandas as pd

random.seed(42)

LEGIT_DOMAINS = [
    "google.com", "github.com", "amazon.com", "wikipedia.org", "microsoft.com",
    "apple.com", "netflix.com", "linkedin.com", "spotify.com", "dropbox.com",
    "nytimes.com", "bbc.com", "reddit.com", "stackoverflow.com", "yahoo.com",
    "office.com", "adobe.com", "salesforce.com", "zoom.us", "slack.com",
]

LEGIT_PATHS = [
    "", "/home", "/about", "/products", "/blog/2024/article",
    "/login", "/account/settings", "/docs/api", "/search?q=test",
    "/user/profile", "/help/support", "/news/latest"
]

BRAND_NAMES = [
    "paypal", "amazon", "netflix", "microsoft", "apple", "google",
    "bankofamerica", "wellsfargo", "chase", "instagram", "facebook", "dhl"
]

SUSPICIOUS_TLDS = ["tk", "ml", "ga", "cf", "gq", "xyz", "top", "club", "info"]

SUSPICIOUS_KEYWORDS = [
    "secure", "verify", "update", "confirm", "account", "signin",
    "login", "alert", "suspended", "billing", "support"
]

SHORTENERS = ["bit.ly", "tinyurl.com", "t.co", "is.gd", "ow.ly"]


def random_string(length, charset="abcdefghijklmnopqrstuvwxyz0123456789"):
    return "".join(random.choice(charset) for _ in range(length))


def generate_legit_url():
    domain = random.choice(LEGIT_DOMAINS)
    path = random.choice(LEGIT_PATHS)
    scheme = "https"
    if random.random() < 0.15:
        domain = "www." + domain

    # Add variety so dedup doesn't collapse the dataset
    if random.random() < 0.4:
        path += f"/{random_string(random.randint(4, 10))}"
    if random.random() < 0.3:
        path += f"?id={random.randint(1, 99999)}"
    if random.random() < 0.2:
        path += f"&ref={random_string(5)}"

    return f"{scheme}://{domain}{path}"


def generate_phishing_url():
    """Generate a synthetic phishing-style URL with varied attack patterns."""
    pattern = random.choice(["typosquat", "subdomain_spoof", "ip_based", "shortener", "long_random"])

    brand = random.choice(BRAND_NAMES)
    keyword = random.choice(SUSPICIOUS_KEYWORDS)

    if pattern == "typosquat":
        # e.g. paypa1-secure.tk
        typo_brand = brand.replace("o", "0").replace("l", "1") + "-" + keyword
        tld = random.choice(SUSPICIOUS_TLDS)
        url = f"http://{typo_brand}.{tld}/{keyword}.php"

    elif pattern == "subdomain_spoof":
        # e.g. secure-paypal.account-verify.com
        sub = f"{keyword}-{brand}"
        domain = f"{random_string(8)}.com"
        url = f"http://{sub}.{domain}/{keyword}"

    elif pattern == "ip_based":
        ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
        url = f"http://{ip}/{brand}/{keyword}.php?id={random.randint(1000,9999)}"

    elif pattern == "shortener":
        shortener = random.choice(SHORTENERS)
        url = f"https://{shortener}/{random_string(7)}"

    else:  # long_random
        sub = random_string(random.randint(10, 20))
        tld = random.choice(SUSPICIOUS_TLDS)
        url = (f"http://{brand}-{keyword}-{sub}.{tld}/"
               f"{keyword}/{random_string(6)}?token={random_string(12)}&{keyword}=1")

    return url


def generate_dataset(n_legit=1500, n_phish=1500) -> pd.DataFrame:
    rows = []
    for _ in range(n_legit):
        rows.append({"url": generate_legit_url(), "label": 0})
    for _ in range(n_phish):
        rows.append({"url": generate_phishing_url(), "label": 1})

    df = pd.DataFrame(rows).drop_duplicates(subset="url").reset_index(drop=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate_dataset()
    print(df.head(10))
    print(f"\nTotal samples: {len(df)}")
    print(df["label"].value_counts())
    df.to_csv("/home/claude/phishguard-ai/data/urls_dataset.csv", index=False)
    print("\nSaved to data/urls_dataset.csv")
