"""
Build the brand reference perceptual-hash database used by
screenshot_analysis.py for visual similarity / spoofing detection.

Captures screenshots of well-known brand login/home pages and stores
their perceptual hashes (pHash) in data/brand_reference_hashes.json.

Run this once during setup (requires internet access):
    python build_brand_reference.py

You can add/remove brands by editing BRAND_URLS below.
"""

import os
import json
from screenshot_analysis import capture_screenshot, compute_phash, SCREENSHOT_DIR

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "brand_reference_hashes.json")

# Well-known brand pages commonly impersonated in phishing attacks.
# Using public homepages (not login pages) to avoid auth walls.
BRAND_URLS = {
    "Google": "https://www.google.com",
    "Microsoft": "https://www.microsoft.com",
    "Apple": "https://www.apple.com",
    "PayPal": "https://www.paypal.com",
    "Amazon": "https://www.amazon.com",
    "Facebook": "https://www.facebook.com",
    "Netflix": "https://www.netflix.com",
    "GitHub": "https://github.com",
    "Wikipedia": "https://www.wikipedia.org",
    "LinkedIn": "https://www.linkedin.com",
}


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    hashes = {}
    # Load existing hashes so partial failures don't wipe out previous runs
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            hashes = json.load(f)

    for brand, url in BRAND_URLS.items():
        try:
            print(f"Capturing {brand} ({url})...")
            path = capture_screenshot(url, output_path=os.path.join(SCREENSHOT_DIR, f"ref_{brand}.png"))
            phash = compute_phash(path)
            hashes[brand] = phash
            print(f"  -> {phash}")
        except Exception as e:
            print(f"  !! Failed: {e}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(hashes, f, indent=2)

    print(f"\nSaved {len(hashes)} brand hashes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
