const API_BASE = "http://localhost:8000";

const urlBox = document.getElementById("current-url");
const scanBtn = document.getElementById("scan-btn");
const resultsDiv = document.getElementById("results");
const backendStatus = document.getElementById("backend-status");

let currentUrl = "";

// ----------------------------------------------------------------------
// Get the active tab's URL
// ----------------------------------------------------------------------
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs[0] && tabs[0].url) {
    currentUrl = tabs[0].url;
    urlBox.textContent = currentUrl;

    // Disable scanning for internal browser pages
    if (currentUrl.startsWith("chrome://") || currentUrl.startsWith("about:")) {
      scanBtn.disabled = true;
      urlBox.textContent += " (cannot scan browser-internal pages)";
    }
  } else {
    urlBox.textContent = "No active tab URL found.";
    scanBtn.disabled = true;
  }
});

// ----------------------------------------------------------------------
// Check backend availability
// ----------------------------------------------------------------------
fetch(`${API_BASE}/`)
  .then((r) => r.json())
  .then((data) => {
    if (data.url_model_ready) {
      backendStatus.textContent = "✅ online";
      backendStatus.style.color = "#4dffc2";
    } else {
      backendStatus.textContent = "⚠️ models not trained";
      backendStatus.style.color = "#ffd95e";
    }
  })
  .catch(() => {
    backendStatus.textContent = "❌ offline (start api.py)";
    backendStatus.style.color = "#ff6b8a";
    scanBtn.disabled = true;
  });

// ----------------------------------------------------------------------
// Render helpers
// ----------------------------------------------------------------------
function verdictClass(label, score) {
  if (label === "phishing" && score >= 70) return ["verdict-danger", "🔴 HIGH RISK — LIKELY PHISHING"];
  if (label === "phishing" || score >= 40) return ["verdict-warn", "🟡 SUSPICIOUS — PROCEED WITH CAUTION"];
  return ["verdict-safe", "🟢 LOW RISK — LIKELY LEGITIMATE"];
}

function renderResult(result) {
  resultsDiv.innerHTML = "";

  const ml = result.ml_analysis || {};
  const score = ml.risk_score ?? result.overall_risk_score ?? 0;
  const label = result.overall_label || ml.label || "legitimate";

  const [cls, text] = verdictClass(label, score);

  const verdictDiv = document.createElement("div");
  verdictDiv.className = `verdict ${cls}`;
  verdictDiv.innerHTML = `<span>${text}</span><span>${score.toFixed(1)}%</span>`;
  resultsDiv.appendChild(verdictDiv);

  // Reputation
  const rep = result.reputation?.url_reputation;
  if (rep && rep.status === "listed") {
    const repDiv = document.createElement("div");
    repDiv.className = "factor up";
    repDiv.textContent = `⚠️ Listed on URLhaus — threat: ${rep.threat || "unknown"}`;
    resultsDiv.appendChild(repDiv);
  }

  // Top factors
  if (ml.top_factors && ml.top_factors.length) {
    const title = document.createElement("div");
    title.className = "section-title";
    title.textContent = "── WHY ──";
    resultsDiv.appendChild(title);

    ml.top_factors.slice(0, 4).forEach((f) => {
      const div = document.createElement("div");
      const cls2 = f.effect === "increases" ? "up" : "down";
      const arrow = f.effect === "increases" ? "▲" : "▼";
      div.className = `factor ${cls2}`;
      div.textContent = `${arrow} ${f.description}`;
      resultsDiv.appendChild(div);
    });
  }
}

// ----------------------------------------------------------------------
// Scan button
// ----------------------------------------------------------------------
scanBtn.addEventListener("click", async () => {
  scanBtn.disabled = true;
  scanBtn.textContent = "▶ SCANNING...";
  resultsDiv.innerHTML = `<div class="status">Analyzing URL + checking reputation...</div>`;

  try {
    const resp = await fetch(`${API_BASE}/analyze/full`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: currentUrl, include_screenshot: false }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || resp.statusText);
    }

    const data = await resp.json();
    renderResult(data);
  } catch (e) {
    resultsDiv.innerHTML = `<div class="factor up">Error: ${e.message}</div>`;
  } finally {
    scanBtn.disabled = false;
    scanBtn.textContent = "▶ SCAN THIS PAGE";
  }
});
