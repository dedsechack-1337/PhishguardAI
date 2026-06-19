"""
Screenshot analysis for phishing detection.

1. Captures a screenshot of the target URL using Playwright (headless Chromium).
2. Computes a perceptual hash (pHash) of the screenshot.
3. Compares against a small reference set of known brand login-page hashes
   to flag potential visual spoofing (e.g. a fake page that LOOKS like
   PayPal/Microsoft/etc. but is hosted on an unrelated domain).

This is intentionally lightweight (no deep learning) to keep total install
size small. Reference hashes are precomputed and stored in
data/brand_reference_hashes.json.

Usage:
    from screenshot_analysis import capture_and_analyze
    result = capture_and_analyze("http://suspicious-site.tk")
"""

import os
import json
import imagehash
from PIL import Image

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots_cache")
REFERENCE_HASHES_PATH = os.path.join(DATA_DIR, "brand_reference_hashes.json")

# Similarity threshold: pHash hamming distance below this is considered "similar"
SIMILARITY_THRESHOLD = 10


def load_reference_hashes() -> dict:
    """Load precomputed perceptual hashes for known brand login pages."""
    if os.path.exists(REFERENCE_HASHES_PATH):
        with open(REFERENCE_HASHES_PATH) as f:
            return json.load(f)
    return {}


def capture_screenshot(url: str, output_path: str = None, timeout_ms: int = 15000) -> str:
    """
    Capture a screenshot of a URL using headless Chromium.
    Returns the path to the saved PNG.
    Raises an exception if the page can't be loaded (caller should handle).
    """
    from playwright.sync_api import sync_playwright

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    if output_path is None:
        safe_name = "".join(c if c.isalnum() else "_" for c in url)[:80]
        output_path = os.path.join(SCREENSHOT_DIR, f"{safe_name}.png")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, timeout=timeout_ms, wait_until="load")
            page.wait_for_timeout(1500)  # let dynamic content settle
            page.screenshot(path=output_path)
        finally:
            browser.close()

    return output_path


def compute_phash(image_path: str) -> str:
    """Compute a perceptual hash (pHash) for an image, returned as hex string."""
    img = Image.open(image_path)
    return str(imagehash.phash(img))


def compare_to_brands(image_phash: str, reference_hashes: dict = None) -> list:
    """
    Compare an image's pHash against known brand reference hashes.

    Returns a sorted list of {"brand": str, "distance": int, "similar": bool}
    for all reference brands, sorted by distance (closest match first).
    """
    if reference_hashes is None:
        reference_hashes = load_reference_hashes()

    target_hash = imagehash.hex_to_hash(image_phash)
    results = []

    for brand, ref_hex in reference_hashes.items():
        ref_hash = imagehash.hex_to_hash(ref_hex)
        distance = target_hash - ref_hash  # Hamming distance
        results.append({
            "brand": brand,
            "distance": int(distance),
            "similar": distance <= SIMILARITY_THRESHOLD,
        })

    results.sort(key=lambda x: x["distance"])
    return results


def capture_and_analyze(url: str) -> dict:
    """
    Full pipeline: capture screenshot, compute hash, compare to brand
    reference set, and return a structured result.

    Returns:
        {
            "url": str,
            "screenshot_path": str | None,
            "phash": str | None,
            "brand_matches": list,
            "warning": str | None,   # set if visual spoofing suspected
            "error": str | None,
        }
    """
    result = {
        "url": url,
        "screenshot_path": None,
        "phash": None,
        "brand_matches": [],
        "warning": None,
        "error": None,
    }

    try:
        screenshot_path = capture_screenshot(url)
        result["screenshot_path"] = screenshot_path

        phash = compute_phash(screenshot_path)
        result["phash"] = phash

        matches = compare_to_brands(phash)
        result["brand_matches"] = matches

        top_match = matches[0] if matches else None
        if top_match and top_match["similar"]:
            result["warning"] = (
                f"This page looks visually similar to {top_match['brand']} "
                f"(hash distance {top_match['distance']}). If this is not an "
                f"official {top_match['brand']} domain, it may be a phishing "
                f"clone."
            )

    except Exception as e:
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    test_url = "https://www.wikipedia.org"
    print(f"Analyzing screenshot for: {test_url}")
    result = capture_and_analyze(test_url)
    print(json.dumps(result, indent=2))
