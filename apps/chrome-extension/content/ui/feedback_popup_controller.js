(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const popupModuleRegistry = opts.popupModuleRegistry && typeof opts.popupModuleRegistry === "object"
      ? opts.popupModuleRegistry
      : null;
    const summarizeTarget = typeof opts.summarizeTarget === "function"
      ? opts.summarizeTarget
      : (target) => {
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
        };

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

    function debugLog(...args) {
      if (!uiDebugEnabled) {
        return;
      }
      console.debug("[LexiShift][UI]", ...args);
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

    function renderFeedbackModules(target) {
      if (!feedbackModules) {
        debugLog("Feedback modules container missing; skipping module render.");
        return;
      }
      feedbackModules.textContent = "";
      let moduleIds = [];
      if (popupModuleRegistry && typeof popupModuleRegistry.buildModules === "function") {
        const renderedModules = popupModuleRegistry.buildModules(target, debugLog);
        for (const moduleEntry of renderedModules) {
          if (!moduleEntry || !moduleEntry.node) {
            continue;
          }
          feedbackModules.appendChild(moduleEntry.node);
          moduleIds.push(String(moduleEntry.id || "").trim());
        }
      }
      if (feedbackPopup) {
        feedbackPopup.dataset.hasModules = feedbackModules.childElementCount > 0 ? "true" : "false";
      }
      debugLog("Rendered feedback modules.", {
        moduleCount: feedbackModules.childElementCount,
        moduleIds,
        hasJapaneseModule: moduleIds.includes("japanese-script"),
        target: summarizeTarget(target)
      });
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

    function handleFeedbackSelection(rating, buttonEl) {
      if (feedbackHandler && activeFeedbackTarget) {
        feedbackHandler({ rating, target: activeFeedbackTarget });
      }
      animateSelection(rating, buttonEl);
      closeFeedbackPopup();
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
      } catch (_err) {
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
        if (key === "1") return handleFeedbackSelection("again", null);
        if (key === "2") return handleFeedbackSelection("hard", null);
        if (key === "3") return handleFeedbackSelection("good", null);
        if (key === "4") return handleFeedbackSelection("easy", null);
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

    return {
      closeFeedbackPopup,
      attachFeedbackListener,
      setDebugEnabled,
      setFeedbackSoundEnabled
    };
  }

  root.uiFeedbackPopupController = {
    createController
  };
})();
