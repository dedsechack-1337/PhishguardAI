"""
Domain / URL reputation lookup using the URLhaus API (abuse.ch).

URLhaus is a free, public threat-intelligence feed of known malware/phishing
URLs. No API key is required.

API docs: https://urlhaus-api.abuse.ch/

If the API is unreachable (offline, blocked network, rate-limited), this
module fails gracefully and returns a neutral "unknown" result so the rest
of the pipeline keeps working.
"""

import requests

URLHAUS_URL_ENDPOINT = "https://urlhaus-api.abuse.ch/v1/url/"
URLHAUS_HOST_ENDPOINT = "https://urlhaus-api.abuse.ch/v1/host/"

TIMEOUT = 6  # seconds


def check_url_reputation(url: str) -> dict:
    """
    Check a full URL against URLhaus.

    Returns:
        {
            "source": "urlhaus",
            "status": "listed" | "not_listed" | "unknown",
            "threat": str | None,       # e.g. "malware_download"
            "tags": list[str],
            "url_status": str | None,   # "online" | "offline"
            "reference": str | None,    # link to URLhaus entry
        }
    """
    try:
        resp = requests.post(URLHAUS_URL_ENDPOINT, data={"url": url}, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {
            "source": "urlhaus",
            "status": "unknown",
            "threat": None,
            "tags": [],
            "url_status": None,
            "reference": None,
            "error": str(e),
        }

    if data.get("query_status") == "ok":
        return {
            "source": "urlhaus",
            "status": "listed",
            "threat": data.get("threat"),
            "tags": data.get("tags") or [],
            "url_status": data.get("url_status"),
            "reference": data.get("urlhaus_reference"),
        }
    elif data.get("query_status") == "no_results":
        return {
            "source": "urlhaus",
            "status": "not_listed",
            "threat": None,
            "tags": [],
            "url_status": None,
            "reference": None,
        }
    else:
        return {
            "source": "urlhaus",
            "status": "unknown",
            "threat": None,
            "tags": [],
            "url_status": None,
            "reference": None,
            "error": data.get("query_status"),
        }


def check_host_reputation(host: str) -> dict:
    """
    Check a domain/host against URLhaus (returns recent malicious URLs
    hosted on that domain, if any).

    Returns:
        {
            "source": "urlhaus",
            "status": "listed" | "not_listed" | "unknown",
            "url_count": int,
            "urls": list[dict],  # up to 5 most recent
        }
    """
    try:
        resp = requests.post(URLHAUS_HOST_ENDPOINT, data={"host": host}, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {
            "source": "urlhaus",
            "status": "unknown",
            "url_count": 0,
            "urls": [],
            "error": str(e),
        }

    if data.get("query_status") == "ok":
        urls = data.get("urls") or []
        return {
            "source": "urlhaus",
            "status": "listed",
            "url_count": len(urls),
            "urls": [
                {
                    "url": u.get("url"),
                    "threat": u.get("threat"),
                    "url_status": u.get("url_status"),
                    "date_added": u.get("date_added"),
                }
                for u in urls[:5]
            ],
        }
    elif data.get("query_status") == "no_results":
        return {"source": "urlhaus", "status": "not_listed", "url_count": 0, "urls": []}
    else:
        return {
            "source": "urlhaus",
            "status": "unknown",
            "url_count": 0,
            "urls": [],
            "error": data.get("query_status"),
        }


if __name__ == "__main__":
    from urllib.parse import urlparse

    test_url = "http://example.com/test"
    host = urlparse(test_url).netloc

    print("URL check:", check_url_reputation(test_url))
    print("Host check:", check_host_reputation(host))
