"""
PhishGuard AI — Web UI (Streamlit)

A SOC-style dashboard to:
- Check a URL for phishing risk (XGBoost/RF + SHAP explanation)
- Check email text for phishing risk (DistilBERT + saliency, or keyword fallback)

Run with:
    streamlit run app.py
"""

import os
import sys
import time
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="PhishGuard AI | SOC Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


# ----------------------------------------------------------------------
# Styling — dark, technical "SOC console" theme
# ----------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: radial-gradient(circle at 20% 0%, #0d1b2a 0%, #050a12 55%, #03060c 100%);
    color: #e6f1ff;
}

/* Header */
.pg-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0 1.25rem 0;
    border-bottom: 1px solid rgba(0,255,170,0.15);
    margin-bottom: 1.5rem;
}
.pg-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    color: #ffffff;
}
.pg-title span { color: #00ffaa; }
.pg-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #7fa8c9;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}
.pg-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #00ffaa;
    border: 1px solid rgba(0,255,170,0.3);
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    background: rgba(0,255,170,0.06);
    white-space: nowrap;
}

/* Cards */
.pg-card {
    background: rgba(15, 30, 48, 0.65);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    backdrop-filter: blur(6px);
    margin-bottom: 1rem;
}

/* Verdict banners */
.verdict-box {
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 1.15rem;
    letter-spacing: 0.04em;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}
.verdict-danger {
    background: linear-gradient(90deg, rgba(255,59,92,0.18), rgba(255,59,92,0.04));
    border: 1px solid rgba(255,59,92,0.4);
    color: #ff6b8a;
}
.verdict-warn {
    background: linear-gradient(90deg, rgba(255,200,55,0.18), rgba(255,200,55,0.04));
    border: 1px solid rgba(255,200,55,0.4);
    color: #ffd95e;
}
.verdict-safe {
    background: linear-gradient(90deg, rgba(0,255,170,0.18), rgba(0,255,170,0.04));
    border: 1px solid rgba(0,255,170,0.4);
    color: #4dffc2;
}

.risk-score-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.4rem;
    font-weight: 800;
}

/* Factor rows */
.factor-row {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    padding: 0.55rem 0.8rem;
    margin-bottom: 0.4rem;
    border-radius: 8px;
    background: rgba(255,255,255,0.03);
    border-left: 3px solid rgba(255,255,255,0.15);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
}
.factor-row.up { border-left-color: #ff6b8a; }
.factor-row.down { border-left-color: #4dffc2; }
.factor-desc { color: #cfe7ff; }
.factor-meta { color: #6f93b8; font-size: 0.75rem; white-space: nowrap; }

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background: rgba(0,0,0,0.35) !important;
    border: 1px solid rgba(0,255,170,0.25) !important;
    color: #e6f1ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #00ffaa !important;
    box-shadow: 0 0 0 1px rgba(0,255,170,0.3) !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(90deg, #00ffaa, #00c3ff) !important;
    color: #03060c !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    letter-spacing: 0.05em;
    padding: 0.6rem 1.4rem !important;
}
.stButton button:hover {
    filter: brightness(1.1);
}
.stButton button:disabled {
    background: rgba(255,255,255,0.08) !important;
    color: #6f93b8 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace;
    background: rgba(255,255,255,0.03);
    border-radius: 10px 10px 0 0;
    padding: 0.6rem 1.2rem;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [aria-selected="true"] {
    background: rgba(0,255,170,0.08) !important;
    border-color: rgba(0,255,170,0.3) !important;
    color: #00ffaa !important;
}

/* Misc */
code {
    color: #00ffaa !important;
    background: rgba(0,255,170,0.08) !important;
}
hr { border-color: rgba(255,255,255,0.08) !important; }
[data-testid="stExpander"] {
    background: rgba(15, 30, 48, 0.4);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Model loaders
# ----------------------------------------------------------------------
@st.cache_resource
def load_url_detector():
    from predict import PhishingURLDetector
    return PhishingURLDetector()


@st.cache_resource
def load_email_detector():
    from predict_email import EmailPhishingDetector
    return EmailPhishingDetector()


# ----------------------------------------------------------------------
# Render helpers
# ----------------------------------------------------------------------
def verdict_class(label, score):
    if label == "phishing" and score >= 70:
        return "verdict-danger", "🔴 HIGH RISK — LIKELY PHISHING"
    if label == "phishing" or score >= 40:
        return "verdict-warn", "🟡 SUSPICIOUS — PROCEED WITH CAUTION"
    return "verdict-safe", "🟢 LOW RISK — LIKELY LEGITIMATE"


def render_result_card(label, score, model_used, factors=None, factor_kind="url"):
    css_class, verdict_text = verdict_class(label, score)

    st.markdown(f"""
    <div class="verdict-box {css_class}">
        <span>{verdict_text}</span>
        <span class="risk-score-num">{score:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace;font-size:0.78rem;"
        f"color:#6f93b8;margin-bottom:0.8rem;'>"
        f"ENGINE: <code>{model_used}</code> &nbsp;|&nbsp; "
        f"RISK SCORE: <code>{score:.2f} / 100</code></div>",
        unsafe_allow_html=True,
    )

    if not factors:
        return

    st.markdown("<div style='font-family:JetBrains Mono,monospace;font-size:0.8rem;"
                 "color:#7fa8c9;letter-spacing:0.1em;margin-bottom:0.5rem;'>"
                 "── ANALYSIS BREAKDOWN ──</div>", unsafe_allow_html=True)

    for f in factors:
        if factor_kind == "url":
            direction = f["effect"]
            cls = "up" if direction == "increases" else "down"
            arrow = "▲" if direction == "increases" else "▼"
            st.markdown(f"""
            <div class="factor-row {cls}">
                <span class="factor-desc">{arrow} {f['description']}</span>
                <span class="factor-meta">val={f['value']:.3g} | score={f.get('contribution', f.get('shap_contribution', 0)):+.3f}</span>
            </div>
            """, unsafe_allow_html=True)
        else:  # token/signal-based (email)
            reason = f.get("reason", "")
            st.markdown(f"""
            <div class="factor-row up">
                <span class="factor-desc">▲ "<code>{f['token']}</code>"</span>
                <span class="factor-meta">{reason}</span>
            </div>
            """, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
url_models_exist = os.path.exists(os.path.join(MODELS_DIR, "best_model.txt"))
email_api_available = bool(os.environ.get("ANTHROPIC_API_KEY"))

status_text = "● ENGINES ONLINE" if url_models_exist else "● MODELS NOT TRAINED"
status_color = "#00ffaa" if url_models_exist else "#ff6b8a"

st.markdown(f"""
<div class="pg-header">
    <div>
        <div class="pg-title">🛡️ Phish<span>Guard</span> AI</div>
        <div class="pg-subtitle">AI-Driven Phishing Detection Console — URL / Email Threat Analysis</div>
    </div>
    <div class="pg-status" style="color:{status_color};border-color:{status_color}55;background:{status_color}11;">
        {status_text}
    </div>
</div>
""", unsafe_allow_html=True)

if not url_models_exist:
    st.warning(
        "⚠️ URL detection models not found. Run `setup_and_run.sh` / `setup_and_run.bat` "
        "or `python src/train.py` to train them."
    )

tab1, tab2, tab3, tab4 = st.tabs([
    "🔗  URL ANALYZER", "✉️  EMAIL ANALYZER", "🌐  DOMAIN REPUTATION", "🖼️  SCREENSHOT ANALYSIS"
])

# ----------------------------------------------------------------------
# Tab 1: URL Analyzer
# ----------------------------------------------------------------------
with tab1:
    col_input, col_info = st.columns([2.2, 1])

    with col_input:
        st.markdown("<div class='pg-card'>", unsafe_allow_html=True)
        url_input = st.text_input(
            "TARGET URL",
            placeholder="http://paypal-secure-login.verify-account.tk/signin",
            key="url_input",
            label_visibility="visible",
        )
        analyze_url = st.button("▶ RUN ANALYSIS", type="primary", disabled=not url_models_exist, key="url_btn")

        if analyze_url and url_input.strip():
            detector = load_url_detector()
            with st.spinner("Scanning URL structure, domain reputation signals..."):
                t0 = time.time()
                result = detector.explain(url_input.strip())
                elapsed = (time.time() - t0) * 1000

            render_result_card(result["label"], result["risk_score"], result["model_used"],
                                result["top_factors"], factor_kind="url")
            st.caption(f"⏱ analyzed in {elapsed:.1f} ms")

        elif analyze_url:
            st.error("⚠ Please enter a URL.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown("<div class='pg-card'>", unsafe_allow_html=True)
        st.markdown("**🧪 TEST SAMPLES**")
        examples = [
            ("https://www.google.com", "legit"),
            ("http://paypal-secure-login.verify-account.tk/signin?user=123", "phishing"),
            ("http://192.168.1.1/login.php?id=4521", "phishing"),
            ("https://bit.ly/3xYzAbC", "shortener"),
        ]
        for ex, tag in examples:
            st.code(ex, language=None)
        st.markdown("---")
        st.markdown(
            "**Engine:** XGBoost / Random Forest  \n"
            "**Explainability:** SHAP feature attribution  \n"
            "**Features analyzed:** 25 lexical & structural signals"
        )
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Tab 2: Email Analyzer
# ----------------------------------------------------------------------
with tab2:
    col_input, col_info = st.columns([2.2, 1])

    with col_input:
        st.markdown("<div class='pg-card'>", unsafe_allow_html=True)
        email_input = st.text_area(
            "EMAIL BODY",
            placeholder="Paste suspicious email content here...",
            height=200,
            key="email_input",
        )
        analyze_email = st.button("▶ RUN ANALYSIS", type="primary", key="email_btn")

        if analyze_email and email_input.strip():
            detector = load_email_detector()

            if not detector.available:
                st.info(
                    "ℹ️ No `ANTHROPIC_API_KEY` set — using keyword-based "
                    "fallback engine. Set the environment variable for AI-based detection via Claude."
                )

            with st.spinner("Analyzing email content for phishing indicators..."):
                t0 = time.time()
                result = detector.explain(email_input.strip())
                elapsed = (time.time() - t0) * 1000

            render_result_card(result["label"], result["risk_score"], result["model_used"],
                                result.get("top_tokens"), factor_kind="email")
            st.caption(f"⏱ analyzed in {elapsed:.1f} ms")

        elif analyze_email:
            st.error("⚠ Please paste some email text.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown("<div class='pg-card'>", unsafe_allow_html=True)
        st.markdown("**🧪 TEST SAMPLE**")
        st.code(
            "URGENT: Your PayPal account has been suspended. "
            "Click here to verify your identity within 24 hours: "
            "http://paypal-secure.tk/verify",
            language=None,
        )
        st.markdown("---")
        engine_label = "Claude (claude-haiku-4-5 via API)" if email_api_available else "Keyword heuristic (fallback)"
        st.markdown(
            f"**Engine:** {engine_label}  \n"
            "**Explainability:** AI-identified signals / keyword match  \n"
            f"**Status:** {'✅ API key detected' if email_api_available else '⚠️ Using fallback — set ANTHROPIC_API_KEY for AI mode'}"
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Tab 3: Domain Reputation
# ----------------------------------------------------------------------
with tab3:
    col_input, col_info = st.columns([2.2, 1])

    with col_input:
        st.markdown("<div class='pg-card'>", unsafe_allow_html=True)
        rep_input = st.text_input(
            "URL OR DOMAIN",
            placeholder="e.g. http://example.com or example.com",
            key="rep_input",
        )
        check_rep = st.button("▶ CHECK REPUTATION", type="primary", key="rep_btn")

        if check_rep and rep_input.strip():
            from domain_reputation import check_url_reputation, check_host_reputation

            target = rep_input.strip()
            from urllib.parse import urlparse
            host = urlparse(target if "://" in target else "http://" + target).netloc.split(":")[0] or target

            with st.spinner(f"Querying URLhaus threat intelligence for {host}..."):
                t0 = time.time()
                url_rep = check_url_reputation(target)
                host_rep = check_host_reputation(host)
                elapsed = (time.time() - t0) * 1000

            if url_rep.get("error") or host_rep.get("error"):
                st.warning(
                    "⚠️ Could not reach URLhaus (network blocked or rate-limited). "
                    f"Details: `{url_rep.get('error') or host_rep.get('error')}`"
                )
            else:
                if url_rep["status"] == "listed":
                    st.markdown(f"""
                    <div class="verdict-box verdict-danger">
                        <span>🔴 KNOWN MALICIOUS URL (URLhaus)</span>
                        <span class="risk-score-num">100%</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(
                        f"**Threat type:** `{url_rep.get('threat')}`  \n"
                        f"**Status:** `{url_rep.get('url_status')}`  \n"
                        f"**Tags:** {', '.join(url_rep.get('tags', [])) or 'none'}  \n"
                        f"**Reference:** {url_rep.get('reference')}"
                    )
                elif host_rep["status"] == "listed":
                    st.markdown(f"""
                    <div class="verdict-box verdict-warn">
                        <span>🟡 DOMAIN HAS HOSTED MALICIOUS URLS</span>
                        <span class="risk-score-num">{host_rep['url_count']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"**{host}** has {host_rep['url_count']} known malicious URL(s) on URLhaus:")
                    for u in host_rep["urls"]:
                        st.markdown(
                            f"- `{u['url']}` — threat: `{u['threat']}`, "
                            f"status: `{u['url_status']}`, added: `{u['date_added']}`"
                        )
                else:
                    st.markdown(f"""
                    <div class="verdict-box verdict-safe">
                        <span>🟢 NOT FOUND IN URLHAUS THREAT FEED</span>
                        <span class="risk-score-num">0%</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"No known malicious activity recorded for **{host}**.")

            st.caption(f"⏱ queried in {elapsed:.1f} ms")

        elif check_rep:
            st.error("⚠ Please enter a URL or domain.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown("<div class='pg-card'>", unsafe_allow_html=True)
        st.markdown("**🧪 TEST SAMPLES**")
        for ex in ["google.com", "example.com"]:
            st.code(ex, language=None)
        st.markdown("---")
        st.markdown(
            "**Source:** URLhaus (abuse.ch)  \n"
            "**Lookup type:** Full URL + host history  \n"
            "**Cost:** Free, no API key required"
        )
        st.markdown(
            "<div style='font-size:0.78rem;color:#6f93b8;margin-top:0.6rem;'>"
            "Note: requires outbound access to urlhaus-api.abuse.ch. "
            "If your network blocks this, the check will show a warning."
            "</div>", unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Tab 4: Screenshot Analysis
# ----------------------------------------------------------------------
with tab4:
    screenshot_available = False
    try:
        import playwright  # noqa: F401
        import imagehash  # noqa: F401
        screenshot_available = True
    except ImportError:
        pass

    col_input, col_info = st.columns([2.2, 1])

    with col_input:
        st.markdown("<div class='pg-card'>", unsafe_allow_html=True)

        if not screenshot_available:
            st.markdown("""
            <div style='font-family:JetBrains Mono,monospace;padding:1rem;
            border:1px solid rgba(255,200,55,0.4);border-radius:10px;
            background:rgba(255,200,55,0.06);color:#ffd95e;'>
            <div style='font-size:1rem;font-weight:700;margin-bottom:0.5rem;'>
            ○ SCREENSHOT ANALYSIS — NOT INSTALLED</div>
            <div style='font-size:0.8rem;color:#cfe7ff;'>
            This is an optional add-on (+280MB) that captures screenshots of
            suspicious URLs and compares them visually against known brand pages
            to detect phishing clones.<br><br>
            <b>To install:</b><br>
            Linux/macOS: <code>./setup_screenshot.sh</code><br>
            Windows: <code>setup_screenshot.bat</code><br><br>
            Then restart the web UI.
            </div></div>
            """, unsafe_allow_html=True)
        else:
            shot_input = st.text_input(
                "TARGET URL",
                placeholder="https://example.com",
                key="shot_input",
            )
            analyze_shot = st.button("▶ CAPTURE & ANALYZE", type="primary", key="shot_btn")

            if analyze_shot and shot_input.strip():
                from screenshot_analysis import capture_and_analyze

                with st.spinner("Launching headless browser and capturing screenshot..."):
                    t0 = time.time()
                    result = capture_and_analyze(shot_input.strip())
                    elapsed = (time.time() - t0) * 1000

                if result.get("error"):
                    st.error(f"⚠ Could not capture screenshot: `{result['error']}`")
                else:
                    if result.get("screenshot_path") and os.path.exists(result["screenshot_path"]):
                        st.image(result["screenshot_path"], caption=shot_input.strip(), use_container_width=True)

                    if result.get("warning"):
                        st.markdown(f"""
                        <div class="verdict-box verdict-warn">
                            <span>🟡 VISUAL SIMILARITY DETECTED</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(result["warning"])
                    else:
                        st.markdown(f"""
                        <div class="verdict-box verdict-safe">
                            <span>🟢 NO BRAND IMPERSONATION DETECTED</span>
                        </div>
                        """, unsafe_allow_html=True)

                    if result.get("brand_matches"):
                        st.markdown("**Closest brand matches (lower = more similar):**")
                        for m in result["brand_matches"][:5]:
                            flag = "⚠️" if m["similar"] else "✓"
                            st.markdown(f"- {flag} `{m['brand']}` — hash distance: `{m['distance']}`")

                    st.caption(f"⏱ captured & analyzed in {elapsed/1000:.2f} s | pHash: `{result.get('phash')}`")

            elif analyze_shot:
                st.error("⚠ Please enter a URL.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown("<div class='pg-card'>", unsafe_allow_html=True)
        st.markdown("**🧪 TEST SAMPLE**")
        st.code("https://www.wikipedia.org", language=None)
        st.markdown("---")
        ref_count = 0
        ref_path = os.path.join(os.path.dirname(__file__), "..", "data", "brand_reference_hashes.json")
        if os.path.exists(ref_path):
            import json as _json
            with open(ref_path) as _f:
                ref_count = len(_json.load(_f))
        st.markdown(
            "**Method:** Perceptual hashing (pHash)  \n"
            f"**Reference brands loaded:** {ref_count}  \n"
            "**Engine size:** lightweight (no deep learning)"
        )
        st.markdown(
            "<div style='font-size:0.78rem;color:#6f93b8;margin-top:0.6rem;'>"
            "Run <code>python src/build_brand_reference.py</code> to (re)build "
            "the brand reference set with more sites."
            "</div>", unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#6f93b8;text-align:center;'>"
    "PhishGuard AI — for research & educational use only. "
    "Always verify suspicious links/emails through additional channels."
    "</div>",
    unsafe_allow_html=True,
)
