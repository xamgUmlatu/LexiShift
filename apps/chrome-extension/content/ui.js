(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STYLE_ID = "lexishift-style";
  const PROFILE_BACKGROUND_ID = "lexishift-profile-background";
  let clickListenerAttached = false;
  let feedbackListenerAttached = false;
  let feedbackHandler = null;
  let feedbackPopup = null;
  let activeFeedbackTarget = null;
  let keyListener = null;
  let closeListener = null;
  let feedbackSoundEnabled = true;
  let feedbackAllowedOrigins = null;
  let profileBackgroundLayer = null;

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
      .lexishift-feedback-popup{position:absolute;display:flex;gap:6px;align-items:center;
        padding:6px 8px;border-radius:999px;background:rgba(28,26,23,0.9);
        box-shadow:0 10px 24px rgba(0,0,0,0.18);transform:translateY(6px) scale(0.92);
        opacity:0;transition:transform 140ms ease, opacity 140ms ease;z-index:2147483647;}
      .lexishift-feedback-popup.lexishift-open{transform:translateY(0) scale(1);opacity:1;}
      .lexishift-feedback-option{width:22px;height:22px;border-radius:999px;border:0;cursor:pointer;
        display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:700;
        transition:transform 120ms ease, box-shadow 120ms ease;}
      .lexishift-feedback-option.lexishift-selected{transform:scale(1.15);
        box-shadow:0 0 0 3px rgba(255,255,255,0.45);}
      .lexishift-feedback-option[data-rating="again"]{background:#D64545;}
      .lexishift-feedback-option[data-rating="hard"]{background:#E07B39;}
      .lexishift-feedback-option[data-rating="good"]{background:#E0B84B;color:#2c2a26;}
      .lexishift-feedback-option[data-rating="easy"]{background:#2F74D0;}
      .lexishift-profile-background{position:fixed;inset:0;pointer-events:none;z-index:2147483000;
        background-size:cover;background-position:center;background-repeat:no-repeat;
        mix-blend-mode:soft-light;opacity:0;transition:opacity 180ms ease;}
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
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      const original = node.dataset.original || node.textContent || "";
      node.replaceWith(document.createTextNode(original));
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
      const state = target.dataset.state || "replacement";
      if (state === "replacement") {
        target.textContent = target.dataset.original || target.textContent;
        target.dataset.state = "original";
      } else {
        target.textContent = target.dataset.replacement || target.textContent;
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
      popup.appendChild(btn);
    }
    document.body.appendChild(popup);
    feedbackPopup = popup;
    return popup;
  }

  function openFeedbackPopup(target) {
    const popup = ensureFeedbackPopup();
    activeFeedbackTarget = target;
    const rect = target.getBoundingClientRect();
    const popupRect = popup.getBoundingClientRect();
    const top = window.scrollY + rect.top - popupRect.height - 8;
    const left = window.scrollX + rect.left + rect.width / 2 - popupRect.width / 2;
    popup.style.top = `${Math.max(8, top)}px`;
    popup.style.left = `${Math.max(8, left)}px`;
    popup.classList.add("lexishift-open");
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
    if (feedbackListenerAttached) {
      return;
    }
    document.addEventListener("contextmenu", (event) => {
      const target = event.target && event.target.closest ? event.target.closest(".lexishift-replacement") : null;
      if (!target) {
        return;
      }
      if (feedbackAllowedOrigins && !feedbackAllowedOrigins.includes(target.dataset.origin || "ruleset")) {
        return;
      }
      event.preventDefault();
      openFeedbackPopup(target);
    });
    feedbackListenerAttached = true;
  }

  function setFeedbackSoundEnabled(enabled) {
    feedbackSoundEnabled = enabled !== false;
  }

  function escapeCssUrl(url) {
    return String(url || "").replace(/["\\\n\r]/g, "\\$&");
  }

  function clampOpacity(value) {
    const parsed = Number.parseFloat(value);
    if (!Number.isFinite(parsed)) {
      return 0.18;
    }
    return Math.min(1, Math.max(0, parsed));
  }

  function ensureProfileBackgroundLayer() {
    let layer = profileBackgroundLayer || document.getElementById(PROFILE_BACKGROUND_ID);
    if (layer) {
      profileBackgroundLayer = layer;
      return layer;
    }
    layer = document.createElement("div");
    layer.id = PROFILE_BACKGROUND_ID;
    layer.className = "lexishift-profile-background";
    const parent = document.documentElement || document.body;
    if (!parent) {
      return null;
    }
    parent.appendChild(layer);
    profileBackgroundLayer = layer;
    return layer;
  }

  function clearProfileBackground() {
    const layer = profileBackgroundLayer || document.getElementById(PROFILE_BACKGROUND_ID);
    if (!layer) {
      return;
    }
    layer.remove();
    profileBackgroundLayer = null;
  }

  function applyProfileBackground(config = {}) {
    const enabled = config.enabled === true;
    const dataUrl = enabled ? String(config.dataUrl || "").trim() : "";
    if (!enabled || !dataUrl) {
      clearProfileBackground();
      return;
    }
    const layer = ensureProfileBackgroundLayer();
    if (!layer) {
      return;
    }
    layer.style.backgroundImage = `url("${escapeCssUrl(dataUrl)}")`;
    layer.style.opacity = String(clampOpacity(config.opacity));
  }

  root.ui = {
    ensureStyle,
    applyHighlightToDom,
    clearReplacements,
    attachClickListener,
    attachFeedbackListener,
    setFeedbackSoundEnabled,
    applyProfileBackground
  };
})();
