(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STYLE_ID = "lexishift-style";
  let clickListenerAttached = false;
  let feedbackListenerAttached = false;
  let feedbackHandler = null;
  let feedbackPopup = null;
  let feedbackModules = null;
  let activeFeedbackTarget = null;
  let keyListener = null;
  let closeListener = null;
  let feedbackSoundEnabled = true;
  let feedbackAllowedOrigins = null;
  let uiDebugEnabled = false;

  function ensureStyle(color, srsColor) {
    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement("style");
      style.id = STYLE_ID;
      const parent = document.head || document.documentElement;
      if (parent) {
        parent.appendChild(style);
      }
    }
    const srs = srsColor || color;
    style.textContent = `
      :root{--lexishift-highlight-color:${color};--lexishift-srs-highlight-color:${srs};}
      .lexishift-replacement{cursor:pointer;transition:color 120ms ease;}
      .lexishift-replacement.lexishift-highlight{color:var(--lexishift-highlight-color);}
      .lexishift-replacement.lexishift-highlight.lexishift-srs{color:var(--lexishift-srs-highlight-color);}
      .lexishift-feedback-popup{position:absolute;display:flex;flex-direction:column;gap:6px;
        align-items:flex-start;transform:translateY(6px) scale(0.92);opacity:0;
        transition:transform 140ms ease, opacity 140ms ease;z-index:2147483647;
        max-width:min(280px, calc(100vw - 16px));}
      .lexishift-feedback-popup.lexishift-open{transform:translateY(0) scale(1);opacity:1;}
      .lexishift-feedback-modules{display:flex;flex-direction:column;gap:6px;align-items:stretch;
        width:100%;}
      .lexishift-feedback-modules:empty{display:none;}
      .lexishift-popup-module{padding:8px 10px;border-radius:10px;background:rgba(28,26,23,0.94);
        color:#f7f4ef;box-shadow:0 10px 24px rgba(0,0,0,0.18);min-width:140px;
        max-width:min(280px, calc(100vw - 16px));}
      .lexishift-script-module-heading{display:block;font-size:10px;line-height:1.2;
        letter-spacing:0.06em;text-transform:uppercase;color:rgba(247,244,239,0.72);margin-bottom:6px;}
      .lexishift-script-module-row{display:grid;grid-template-columns:auto 1fr;column-gap:8px;align-items:start;}
      .lexishift-script-module-row + .lexishift-script-module-row{margin-top:4px;}
      .lexishift-script-module-label{font-size:10px;line-height:1.3;letter-spacing:0.06em;
        text-transform:uppercase;color:rgba(247,244,239,0.72);}
      .lexishift-script-module-value{font-size:13px;line-height:1.35;font-weight:600;word-break:break-word;}
      .lexishift-feedback-bar{display:flex;gap:6px;align-items:center;padding:6px 8px;
        border-radius:999px;background:rgba(28,26,23,0.9);box-shadow:0 10px 24px rgba(0,0,0,0.18);}
      .lexishift-feedback-option{width:22px;height:22px;border-radius:999px;border:0;cursor:pointer;
        display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:700;
        transition:transform 120ms ease, box-shadow 120ms ease;}
      .lexishift-feedback-option.lexishift-selected{transform:scale(1.15);
        box-shadow:0 0 0 3px rgba(255,255,255,0.45);}
      .lexishift-feedback-option[data-rating="again"]{background:#D64545;}
      .lexishift-feedback-option[data-rating="hard"]{background:#E07B39;}
      .lexishift-feedback-option[data-rating="good"]{background:#E0B84B;color:#2c2a26;}
      .lexishift-feedback-option[data-rating="easy"]{background:#2F74D0;}
    `;
  }

  function applyHighlightToDom(enabled) {
    const highlight = enabled !== false;
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      if (highlight) {
        node.classList.add("lexishift-highlight");
      } else {
        node.classList.remove("lexishift-highlight");
      }
      if (node.dataset.origin === "srs") {
        node.classList.add("lexishift-srs");
      } else {
        node.classList.remove("lexishift-srs");
      }
    });
  }

  function clearReplacements() {
    closeFeedbackPopup();
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      const original = node.dataset.original || node.textContent || "";
      node.replaceWith(document.createTextNode(original));
    });
  }

  const SCRIPT_FORM_ORDER = ["kanji", "kana", "romaji"];
  const SCRIPT_MODULE_ORDER = ["kana", "kanji", "romaji"];

  function debugLog(...args) {
    if (!uiDebugEnabled) {
      return;
    }
    console.debug("[LexiShift][UI]", ...args);
  }

  function summarizeTarget(target) {
    if (!target || !target.dataset) {
      return null;
    }
    return {
      origin: String(target.dataset.origin || "ruleset"),
      languagePair: String(target.dataset.languagePair || ""),
      displayScript: String(target.dataset.displayScript || ""),
      hasScriptForms: Boolean(String(target.dataset.scriptForms || "").trim()),
      displayReplacement: String(target.dataset.displayReplacement || "").slice(0, 80),
      replacement: String(target.dataset.replacement || "").slice(0, 80)
    };
  }

  function parseScriptForms(target) {
    const payload = target && target.dataset ? target.dataset.scriptForms : "";
    if (!payload) {
      debugLog("No script forms payload on target.", summarizeTarget(target));
      return null;
    }
    try {
      const parsed = JSON.parse(payload);
      if (!parsed || typeof parsed !== "object") {
        debugLog("Script forms payload parsed to non-object.", {
          payloadPreview: String(payload).slice(0, 120)
        });
        return null;
      }
      const normalized = {};
      for (const script of SCRIPT_FORM_ORDER) {
        const value = String(parsed[script] || "").trim();
        if (value) {
          normalized[script] = value;
        }
      }
      if (!Object.keys(normalized).length) {
        debugLog("Script forms object had no supported script values.", {
          keys: Object.keys(parsed)
        });
        return null;
      }
      debugLog("Parsed script forms.", {
        scripts: Object.keys(normalized),
        target: summarizeTarget(target)
      });
      return normalized;
    } catch (error) {
      debugLog("Failed to parse script forms payload.", {
        message: error && error.message ? error.message : String(error),
        payloadPreview: String(payload).slice(0, 120)
      });
      return null;
    }
  }

  function scriptLabel(script) {
    if (script === "kana") return "Kana";
    if (script === "romaji") return "Romaji";
    return "Kanji";
  }

  function resolvePrimaryScript(target, scriptForms) {
    const current = String(target.dataset.displayScript || "").trim().toLowerCase();
    if (current && scriptForms[current]) {
      return current;
    }
    for (const script of SCRIPT_FORM_ORDER) {
      if (scriptForms[script]) {
        return script;
      }
    }
    return "";
  }

  function buildJapaneseScriptModule(target) {
    debugLog("Building Japanese script module.", summarizeTarget(target));
    const scriptForms = parseScriptForms(target);
    if (!scriptForms) {
      debugLog("Skipping Japanese script module: no parsed script forms.", summarizeTarget(target));
      return null;
    }
    const availableScripts = SCRIPT_FORM_ORDER.filter((script) => Boolean(scriptForms[script]));
    if (availableScripts.length < 2) {
      debugLog("Skipping Japanese script module: fewer than two scripts available.", {
        availableScripts,
        target: summarizeTarget(target)
      });
      return null;
    }
    const primaryScript = resolvePrimaryScript(target, scriptForms);
    const alternatives = SCRIPT_MODULE_ORDER.filter(
      (script) => script !== primaryScript && Boolean(scriptForms[script])
    );
    if (!alternatives.length) {
      debugLog("Skipping Japanese script module: no alternatives after primary resolution.", {
        primaryScript,
        availableScripts,
        target: summarizeTarget(target)
      });
      return null;
    }
    const moduleEl = document.createElement("section");
    moduleEl.className = "lexishift-popup-module lexishift-script-module";
    const heading = document.createElement("span");
    heading.className = "lexishift-script-module-heading";
    heading.textContent = "Japanese";
    moduleEl.appendChild(heading);

    for (const script of alternatives) {
      const row = document.createElement("div");
      row.className = "lexishift-script-module-row";
      const label = document.createElement("span");
      label.className = "lexishift-script-module-label";
      label.textContent = scriptLabel(script);
      const value = document.createElement("span");
      value.className = "lexishift-script-module-value";
      value.textContent = scriptForms[script];
      row.appendChild(label);
      row.appendChild(value);
      moduleEl.appendChild(row);
    }

    debugLog("Built Japanese script module.", {
      primaryScript,
      alternatives,
      target: summarizeTarget(target)
    });
    return moduleEl;
  }

  function renderFeedbackModules(target) {
    if (!feedbackModules) {
      debugLog("Feedback modules container missing; skipping module render.");
      return;
    }
    feedbackModules.textContent = "";
    const scriptModule = buildJapaneseScriptModule(target);
    if (scriptModule) {
      feedbackModules.appendChild(scriptModule);
    }
    if (feedbackPopup) {
      feedbackPopup.dataset.hasModules = feedbackModules.childElementCount > 0 ? "true" : "false";
    }
    debugLog("Rendered feedback modules.", {
      moduleCount: feedbackModules.childElementCount,
      hasJapaneseModule: Boolean(scriptModule),
      target: summarizeTarget(target)
    });
  }

  function attachClickListener() {
    if (clickListenerAttached) {
      return;
    }
    document.addEventListener("click", (event) => {
      const target = event.target && event.target.closest ? event.target.closest(".lexishift-replacement") : null;
      if (!target) {
        return;
      }
      closeFeedbackPopup();
      const state = target.dataset.state || "replacement";
      if (state === "replacement") {
        target.textContent = target.dataset.original || target.textContent;
        target.dataset.state = "original";
      } else {
        target.textContent = target.dataset.displayReplacement || target.dataset.replacement || target.textContent;
        target.dataset.state = "replacement";
      }
    });
    clickListenerAttached = true;
  }

  function ensureFeedbackPopup() {
    if (feedbackPopup) {
      return feedbackPopup;
    }
    const popup = document.createElement("div");
    popup.className = "lexishift-feedback-popup";
    popup.setAttribute("role", "dialog");
    popup.setAttribute("aria-live", "polite");
    const modules = document.createElement("div");
    modules.className = "lexishift-feedback-modules";
    popup.appendChild(modules);
    feedbackModules = modules;

    const feedbackBar = document.createElement("div");
    feedbackBar.className = "lexishift-feedback-bar";
    const options = [
      { rating: "again", label: "1" },
      { rating: "hard", label: "2" },
      { rating: "good", label: "3" },
      { rating: "easy", label: "4" }
    ];
    for (const opt of options) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "lexishift-feedback-option";
      btn.dataset.rating = opt.rating;
      btn.textContent = opt.label;
      btn.addEventListener("click", (event) => {
        event.stopPropagation();
        handleFeedbackSelection(opt.rating, btn);
      });
      feedbackBar.appendChild(btn);
    }
    popup.appendChild(feedbackBar);
    document.body.appendChild(popup);
    feedbackPopup = popup;
    return popup;
  }

  function openFeedbackPopup(target) {
    const popup = ensureFeedbackPopup();
    renderFeedbackModules(target);
    activeFeedbackTarget = target;
    popup.classList.remove("lexishift-open");
    const rect = target.getBoundingClientRect();
    const popupRect = popup.getBoundingClientRect();
    const viewportTop = window.scrollY;
    const viewportBottom = window.scrollY + window.innerHeight;
    const viewportLeft = window.scrollX;
    const viewportRight = window.scrollX + document.documentElement.clientWidth;
    let top = window.scrollY + rect.top - popupRect.height - 8;
    if (top < viewportTop + 8) {
      top = window.scrollY + rect.bottom + 8;
    }
    let left = window.scrollX + rect.left + rect.width / 2 - popupRect.width / 2;
    top = Math.min(Math.max(top, viewportTop + 8), Math.max(viewportTop + 8, viewportBottom - popupRect.height - 8));
    left = Math.min(Math.max(left, viewportLeft + 8), Math.max(viewportLeft + 8, viewportRight - popupRect.width - 8));
    popup.style.top = `${top}px`;
    popup.style.left = `${left}px`;
    debugLog("Opening feedback popup.", {
      top,
      left,
      moduleCount: feedbackModules ? feedbackModules.childElementCount : 0,
      target: summarizeTarget(target)
    });
    requestAnimationFrame(() => popup.classList.add("lexishift-open"));
    attachFeedbackKeyListener();
    attachFeedbackCloseListener();
  }

  function closeFeedbackPopup() {
    if (!feedbackPopup) {
      return;
    }
    feedbackPopup.classList.remove("lexishift-open");
    activeFeedbackTarget = null;
    detachFeedbackKeyListener();
    detachFeedbackCloseListener();
  }

  function handleFeedbackSelection(rating) {
    return handleFeedbackSelection(rating, null);
  }

  function handleFeedbackSelection(rating, buttonEl) {
    if (feedbackHandler && activeFeedbackTarget) {
      feedbackHandler({ rating, target: activeFeedbackTarget });
    }
    animateSelection(rating, buttonEl);
    closeFeedbackPopup();
  }

  function animateSelection(rating, buttonEl) {
    const popup = feedbackPopup || ensureFeedbackPopup();
    const button =
      buttonEl || (popup ? popup.querySelector(`[data-rating="${rating}"]`) : null);
    if (button) {
      button.classList.add("lexishift-selected");
      setTimeout(() => button.classList.remove("lexishift-selected"), 220);
    }
    playFeedbackSound(rating);
  }

  function playFeedbackSound(rating) {
    if (!feedbackSoundEnabled) {
      return;
    }
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const base = rating === "again" ? 220 : rating === "hard" ? 260 : rating === "good" ? 300 : 340;
      osc.frequency.value = base;
      osc.type = "sine";
      gain.gain.value = 0.12;
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.08);
      osc.onended = () => ctx.close();
    } catch (err) {
      // Ignore audio errors (blocked or unavailable).
    }
  }

  function attachFeedbackKeyListener() {
    if (keyListener) {
      return;
    }
    keyListener = (event) => {
      if (!activeFeedbackTarget) {
        return;
      }
      if (event.key === "Escape") {
        closeFeedbackPopup();
        return;
      }
      const key = event.key;
      if (!event.ctrlKey) {
        return;
      }
      if (key === "1") return handleFeedbackSelection("again");
      if (key === "2") return handleFeedbackSelection("hard");
      if (key === "3") return handleFeedbackSelection("good");
      if (key === "4") return handleFeedbackSelection("easy");
    };
    document.addEventListener("keydown", keyListener);
  }

  function detachFeedbackKeyListener() {
    if (keyListener) {
      document.removeEventListener("keydown", keyListener);
      keyListener = null;
    }
  }

  function attachFeedbackCloseListener() {
    if (closeListener) {
      return;
    }
    closeListener = (event) => {
      if (!feedbackPopup || !feedbackPopup.classList.contains("lexishift-open")) {
        return;
      }
      const target = event && event.target;
      if (target instanceof Node && feedbackPopup.contains(target)) {
        return;
      }
      closeFeedbackPopup();
    };
    document.addEventListener("click", closeListener);
    window.addEventListener("scroll", closeListener, { passive: true });
    window.addEventListener("resize", closeListener);
  }

  function detachFeedbackCloseListener() {
    if (closeListener) {
      document.removeEventListener("click", closeListener);
      window.removeEventListener("scroll", closeListener);
      window.removeEventListener("resize", closeListener);
      closeListener = null;
    }
  }

  function attachFeedbackListener(handler, options = {}) {
    feedbackHandler = handler;
    feedbackAllowedOrigins = options.allowOrigins || null;
    debugLog("Configured feedback listener.", {
      allowOrigins: Array.isArray(feedbackAllowedOrigins) ? feedbackAllowedOrigins : null
    });
    if (feedbackListenerAttached) {
      return;
    }
    document.addEventListener("contextmenu", (event) => {
      const target = event.target && event.target.closest ? event.target.closest(".lexishift-replacement") : null;
      if (!target) {
        return;
      }
      const origin = String(target.dataset.origin || "ruleset");
      if (feedbackAllowedOrigins && !feedbackAllowedOrigins.includes(origin)) {
        debugLog("Skipping feedback popup due to origin gating.", {
          origin,
          allowOrigins: feedbackAllowedOrigins,
          target: summarizeTarget(target)
        });
        return;
      }
      event.preventDefault();
      debugLog("Opening contextmenu feedback popup for target.", {
        origin,
        target: summarizeTarget(target)
      });
      openFeedbackPopup(target);
    });
    feedbackListenerAttached = true;
  }

  function setDebugEnabled(enabled) {
    uiDebugEnabled = enabled === true;
    if (uiDebugEnabled) {
      console.debug("[LexiShift][UI] Debug logging enabled.");
    }
  }

  function setFeedbackSoundEnabled(enabled) {
    feedbackSoundEnabled = enabled !== false;
  }

  root.ui = {
    ensureStyle,
    applyHighlightToDom,
    clearReplacements,
    attachClickListener,
    attachFeedbackListener,
    setDebugEnabled,
    setFeedbackSoundEnabled
  };
})();
