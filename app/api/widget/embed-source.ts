/**
 * WIDGET_JS is the verbatim JavaScript that gets served at /api/widget.js
 *
 * Placeholder tokens replaced at serve-time:
 *   __ORIGIN__  → https://profitengine.alreadyherellc.com
 *   __REF__     → reseller referral code (or empty string)
 *   __THEME__   → "dark" | "light"
 *
 * Design goals
 * ─────────────
 * • Zero external dependencies — runs on any page
 * • Shadow DOM for CSS isolation — never breaks host site styles
 * • < 6 KB minified (this source is readable; Vercel serves it compressed)
 * • Single <script> tag embed; no additional CSS or HTML required
 * • Fires impression + CTA events back to /api/widget/track
 */

export const WIDGET_JS = /* js */ `
(function () {
  "use strict";

  var ORIGIN = "__ORIGIN__";
  var REF    = "__REF__";
  var THEME  = "__THEME__";
  var HOST   = (typeof location !== "undefined") ? location.hostname : "";

  // ── Config ────────────────────────────────────────────────────────────────

  var NICHES = {
    tech:      { label: "Tech / SaaS",    rpm: 14, cpm: 4.2 },
    finance:   { label: "Finance / Crypto",rpm:22, cpm: 8.1 },
    health:    { label: "Health / Fitness",rpm: 9, cpm: 3.4 },
    lifestyle: { label: "Lifestyle",       rpm: 7, cpm: 2.8 },
    travel:    { label: "Travel",          rpm:11, cpm: 3.9 },
  };

  var PALETTE = {
    dark:  { bg: "#0C0C0C", surface: "#141414", border: "#1F2937",
             ink: "#F3F4F6", muted: "#9CA3AF", acid: "#00FF41", acidSoft: "#CCFF00" },
    light: { bg: "#F9FAFB", surface: "#FFFFFF", border: "#E5E7EB",
             ink: "#111827", muted: "#6B7280", acid: "#16A34A", acidSoft: "#15803D" },
  };

  // ── Estimate engine ──────────────────────────────────────────────────────

  function estimate(nicheKey, postsPerMonth) {
    var n  = NICHES[nicheKey] || NICHES.tech;
    var pv = postsPerMonth * 320;           // avg 320 page-views / post / month
    var affiliate = pv * (n.rpm / 1000);
    var ads       = pv * (n.cpm / 1000);
    var monthly   = Math.round((affiliate + ads) * 0.9); // 0.9 ramp factor
    var hoursSaved = Math.round(postsPerMonth * 2.4);     // ~2.4h/post manual
    return { monthly: monthly, hoursSaved: hoursSaved };
  }

  // ── Analytics beacon ────────────────────────────────────────────────────

  function beacon(event) {
    try {
      fetch(ORIGIN + "/api/widget/track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event: event, ref: REF, host: HOST }),
        keepalive: true,
      }).catch(function () {});
    } catch (e) {}
  }

  // ── DOM builder ─────────────────────────────────────────────────────────

  function buildWidget(container) {
    var p  = PALETTE[THEME] || PALETTE.dark;
    var shadow = container.attachShadow({ mode: "open" });

    // State
    var nicheKey = "tech";
    var posts    = 12;

    function renderCSS() {
      return [
        "*{box-sizing:border-box;margin:0;padding:0}",
        "a{color:inherit;text-decoration:none}",
        ":host{display:block;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:13px}",
        ".w{background:" + p.bg + ";border:1px solid " + p.border + ";color:" + p.ink + ";padding:20px 22px;max-width:340px;min-width:260px}",
        ".label{color:" + p.muted + ";font-size:10px;letter-spacing:.15em;text-transform:uppercase;margin-bottom:6px}",
        "select,.slider{width:100%;background:" + p.surface + ";color:" + p.ink + ";border:1px solid " + p.border + ";padding:8px 10px;font-family:inherit;font-size:12px;outline:none;cursor:pointer;appearance:none;-webkit-appearance:none}",
        "select:focus,.slider:focus{border-color:" + p.acid + "}",
        ".slider{-webkit-appearance:none;appearance:none;height:4px;padding:0;background:" + p.border + ";cursor:pointer;border:none;margin-top:6px}",
        ".slider::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;background:" + p.acid + ";cursor:pointer;border-radius:0}",
        ".slider::-moz-range-thumb{width:14px;height:14px;background:" + p.acid + ";cursor:pointer;border-radius:0;border:none}",
        ".row{margin-bottom:14px}",
        ".posts-label{display:flex;justify-content:space-between;margin-bottom:4px}",
        ".posts-val{color:" + p.acid + ";font-weight:700}",
        ".result{background:" + p.surface + ";border:1px solid " + p.border + ";padding:14px 16px;margin:16px 0 14px}",
        ".result-row{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}",
        ".result-row:last-child{margin-bottom:0}",
        ".result-key{color:" + p.muted + ";font-size:10px;letter-spacing:.12em;text-transform:uppercase}",
        ".result-val{color:" + p.acid + ";font-weight:700;font-size:16px}",
        ".result-val.sm{font-size:13px}",
        ".cta-btn{display:block;width:100%;padding:11px;background:" + p.acid + ";color:#050505;font-weight:700;font-size:11px;letter-spacing:.18em;text-transform:uppercase;text-align:center;cursor:pointer;border:none;font-family:inherit;transition:background .15s}",
        ".cta-btn:hover{background:" + p.acidSoft + "}",
        ".badge{display:flex;align-items:center;justify-content:center;gap:5px;margin-top:10px;color:" + p.muted + ";font-size:10px;letter-spacing:.08em}",
        ".badge a{color:" + p.muted + ";transition:color .15s}",
        ".badge a:hover{color:" + p.acid + "}",
        ".dot{width:5px;height:5px;background:" + p.acid + ";animation:pulse 1.4s infinite;display:inline-block}",
        "@keyframes pulse{50%{opacity:.3}}",
      ].join("");
    }

    function ctaHref() {
      var url = ORIGIN + "/#waitlist";
      if (REF) url += "?ref=" + encodeURIComponent(REF);
      return url;
    }

    function renderHTML() {
      var est = estimate(nicheKey, posts);
      var options = Object.keys(NICHES).map(function (k) {
        return "<option value='" + k + "'" + (k === nicheKey ? " selected" : "") + ">" + NICHES[k].label + "</option>";
      }).join("");

      return [
        "<style>" + renderCSS() + "</style>",
        "<div class='w'>",
          "<div class='row'>",
            "<div class='label'>Your niche</div>",
            "<select id='pe-niche'>" + options + "</select>",
          "</div>",
          "<div class='row'>",
            "<div class='posts-label'><span class='label' style='margin:0'>Posts per month</span><span class='posts-val' id='pe-posts-val'>" + posts + "</span></div>",
            "<input id='pe-posts' class='slider' type='range' min='4' max='40' step='2' value='" + posts + "' />",
          "</div>",
          "<div class='result'>",
            "<div class='result-row'><span class='result-key'>Est. monthly revenue</span><span class='result-val'>$" + est.monthly.toLocaleString() + "</span></div>",
            "<div class='result-row'><span class='result-key'>Hours saved / month</span><span class='result-val sm'>" + est.hoursSaved + " hrs</span></div>",
          "</div>",
          "<a id='pe-cta' class='cta-btn' href='" + ctaHref() + "' target='_blank' rel='noopener noreferrer'>Automate this with ProfitEngine →</a>",
          "<div class='badge'><span class='dot'></span> <a href='" + ctaHref() + "' target='_blank' rel='noopener noreferrer'>Powered by ProfitEngine v5</a></div>",
        "</div>",
      ].join("");
    }

    function rerender() {
      var est = estimate(nicheKey, posts);
      shadow.getElementById("pe-posts-val").textContent = posts;
      shadow.querySelector(".result-val").textContent = "$" + est.monthly.toLocaleString();
      shadow.querySelectorAll(".result-val")[1].textContent = est.hoursSaved + " hrs";
      var href = ctaHref();
      shadow.getElementById("pe-cta").href = href;
      shadow.querySelector(".badge a").href = href;
    }

    shadow.innerHTML = renderHTML();

    shadow.getElementById("pe-niche").addEventListener("change", function (e) {
      nicheKey = e.target.value;
      rerender();
    });

    shadow.getElementById("pe-posts").addEventListener("input", function (e) {
      posts = parseInt(e.target.value, 10);
      rerender();
    });

    shadow.getElementById("pe-cta").addEventListener("click", function () {
      beacon("cta");
    });
  }

  // ── Bootstrap ────────────────────────────────────────────────────────────

  function init() {
    var containers = document.querySelectorAll("[data-pe-widget], .pe-widget");
    if (containers.length === 0) {
      // Auto-insert before the script tag
      var me = document.currentScript || document.querySelector("script[src*='pe-widget'],script[src*='widget.js']");
      var host = document.createElement("div");
      host.setAttribute("data-pe-widget", "");
      if (me && me.parentNode) {
        me.parentNode.insertBefore(host, me);
      } else {
        document.body.appendChild(host);
      }
      containers = [host];
    }

    for (var i = 0; i < containers.length; i++) {
      buildWidget(containers[i]);
    }

    beacon("impression");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
`;
