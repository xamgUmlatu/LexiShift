(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const POPUP_VIEWPORT_MARGIN = 8;
  const POPUP_ANCHOR_GAP = 8;
  function finiteNumber(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  function clamp(value, lower, upper) {
    const safeLower = finiteNumber(lower, 0);
    const safeUpper = Math.max(safeLower, finiteNumber(upper, safeLower));
    return Math.min(Math.max(finiteNumber(value, safeLower), safeLower), safeUpper);
  }
  function normalizeRect(value) {
    const rect = value && typeof value === "object" ? value : {};
    const left = finiteNumber(rect.left, 0);
    const top = finiteNumber(rect.top, 0);
    const width = Math.max(0, finiteNumber(rect.width, finiteNumber(rect.right, left) - left));
    const height = Math.max(0, finiteNumber(rect.height, finiteNumber(rect.bottom, top) - top));
    return {
      left, top,
      right: finiteNumber(rect.right, left + width),
      bottom: finiteNumber(rect.bottom, top + height),
      width, height
    };
  }
  function computePopupPlacement(options = {}) {
    const viewportWidth = Math.max(0, finiteNumber(options.viewportWidth, 0));
    const viewportHeight = Math.max(0, finiteNumber(options.viewportHeight, 0));
    const margin = Math.max(0, finiteNumber(options.margin, POPUP_VIEWPORT_MARGIN));
    const gap = Math.max(0, finiteNumber(options.gap, POPUP_ANCHOR_GAP));
    const targetRect = normalizeRect(options.targetRect);
    const viewportPopupWidth = Math.max(0, viewportWidth - (margin * 2));
    const viewportPopupHeight = Math.max(0, viewportHeight - (margin * 2));
    const popupWidth = Math.min(Math.max(0, finiteNumber(options.popupWidth, 0)), viewportPopupWidth);
    const desiredHeight = Math.min(Math.max(0, finiteNumber(options.popupHeight, 0)), viewportPopupHeight);
    const spaceBelow = Math.max(0, viewportHeight - margin - targetRect.bottom - gap);
    const spaceAbove = Math.max(0, targetRect.top - margin - gap);
    const fitsBelow = desiredHeight <= spaceBelow;
    const fitsAbove = desiredHeight <= spaceAbove;
    let vertical = "viewport";
    if (fitsBelow) {
      vertical = "below";
    } else if (fitsAbove) {
      vertical = "above";
    }
    const availableHeight = vertical === "viewport"
      ? viewportPopupHeight
      : vertical === "above" ? spaceAbove : spaceBelow;
    const maxHeight = Math.max(0, Math.min(desiredHeight || availableHeight, availableHeight));
    const renderedHeight = Math.min(desiredHeight, maxHeight);
    let top = margin;
    if (vertical === "below") {
      top = targetRect.bottom + gap;
    } else if (vertical === "above") {
      top = targetRect.top - gap - renderedHeight;
    } else {
      top = targetRect.bottom + gap;
    }
    top = clamp(top, margin, viewportHeight - margin - renderedHeight);
    const anchor = options.anchorPoint && typeof options.anchorPoint === "object"
      ? options.anchorPoint : {};
    const targetCenterX = targetRect.left + (targetRect.width / 2);
    const anchorX = clamp(
      finiteNumber(anchor.clientX, targetCenterX), margin,
      Math.max(margin, viewportWidth - margin)
    );
    const rightCandidate = anchorX + gap;
    const leftCandidate = anchorX - gap - popupWidth;
    let horizontal = "right";
    let left = rightCandidate;
    if (rightCandidate + popupWidth > viewportWidth - margin && leftCandidate >= margin) {
      horizontal = "left";
      left = leftCandidate;
    } else if (rightCandidate + popupWidth > viewportWidth - margin) {
      const spaceRight = Math.max(0, viewportWidth - margin - rightCandidate);
      const spaceLeft = Math.max(0, anchorX - gap - margin);
      horizontal = spaceLeft > spaceRight ? "clamped-left" : "clamped-right";
      left = horizontal === "clamped-left" ? leftCandidate : rightCandidate;
    }
    left = clamp(left, margin, viewportWidth - margin - popupWidth);
    return { top, left, maxHeight, vertical, horizontal };
  }
  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const popupModuleRegistry = opts.popupModuleRegistry && typeof opts.popupModuleRegistry === "object"
      ? opts.popupModuleRegistry
      : null;
    const applyModuleTheme = typeof opts.applyModuleTheme === "function"
      ? opts.applyModuleTheme
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
    let activeFeedbackAnchor = null;
    let feedbackOpenFrame = null;
    let feedbackPositionFrame = null;
    let feedbackResizeObserver = null;
    let feedbackMutationObserver = null;
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

    function cancelFrame(frameId) {
      if (frameId === null || typeof window.cancelAnimationFrame !== "function") {
        return;
      }
      window.cancelAnimationFrame(frameId);
    }

    function positionFeedbackPopup() {
      if (!feedbackPopup || !activeFeedbackTarget) {
        return null;
      }
      const popup = feedbackPopup;
      const targetRect = activeFeedbackTarget.getBoundingClientRect();
      const viewportWidth = Number(document.documentElement.clientWidth
        || window.innerWidth || 0);
      const viewportHeight = Number(window.innerHeight
        || document.documentElement.clientHeight || 0);
      const viewportMaxHeight = Math.max(1, viewportHeight - (POPUP_VIEWPORT_MARGIN * 2));
      popup.classList.add("lexishift-measuring");
      popup.style.maxHeight = `${viewportMaxHeight}px`;
      try {
        const placeMeasuredPopup = () => {
          const popupRect = popup.getBoundingClientRect();
          const popupHeight = root.uiPopupLayoutMeasurement.measureNaturalHeight(popup, feedbackModules);
          return computePopupPlacement({
            targetRect, viewportWidth, viewportHeight,
            popupWidth: popupRect.width, popupHeight,
            anchorPoint: activeFeedbackAnchor
          });
        };
        let placement = placeMeasuredPopup();
        popup.style.maxHeight = `${Math.max(1, placement.maxHeight)}px`;
        placement = placeMeasuredPopup();
        popup.style.maxHeight = `${Math.max(1, placement.maxHeight)}px`;
        popup.style.top = `${window.scrollY + placement.top}px`;
        popup.style.left = `${window.scrollX + placement.left}px`;
        popup.dataset.verticalPlacement = placement.vertical;
        popup.dataset.horizontalPlacement = placement.horizontal;
        return placement;
      } finally {
        popup.classList.remove("lexishift-measuring");
      }
    }

    function scheduleFeedbackPopupPosition() {
      if (!activeFeedbackTarget || feedbackPositionFrame !== null) {
        return;
      }
      feedbackPositionFrame = requestAnimationFrame(() => {
        feedbackPositionFrame = null;
        if (activeFeedbackTarget && feedbackPopup) {
          positionFeedbackPopup();
        }
      });
    }

    function attachPopupLayoutObservers(popup) {
      if (!feedbackResizeObserver && typeof ResizeObserver === "function") {
        feedbackResizeObserver = new ResizeObserver(() => {
          scheduleFeedbackPopupPosition();
        });
        feedbackResizeObserver.observe(popup);
      }
      if (!feedbackMutationObserver
        && feedbackModules
        && typeof MutationObserver === "function") {
        feedbackMutationObserver = new MutationObserver(() => {
          scheduleFeedbackPopupPosition();
        });
        feedbackMutationObserver.observe(feedbackModules, {
          attributes: true,
          attributeFilter: ["class"],
          characterData: true,
          childList: true,
          subtree: true
        });
      }
    }

    function ensureFeedbackPopup() {
      if (feedbackPopup) {
        return feedbackPopup;
      }
      const popup = document.createElement("div");
      popup.className = "lexishift-feedback-popup";
      popup.dataset.lexishiftScanSkip = "true";
      popup.setAttribute("role", "dialog");
      popup.setAttribute("aria-live", "polite");
      popup.setAttribute("aria-hidden", "true");
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
      attachPopupLayoutObservers(popup);
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
          const moduleId = String(moduleEntry.id || "").trim();
          if (applyModuleTheme) {
            try {
              applyModuleTheme(moduleId, moduleEntry.node, target);
            } catch (error) {
              debugLog("Failed to apply popup module theme.", {
                moduleId,
                message: error && error.message ? error.message : String(error)
              });
            }
          }
          feedbackModules.appendChild(moduleEntry.node);
          moduleIds.push(moduleId);
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

    function openFeedbackPopup(target, anchorPoint = null) {
      const popup = ensureFeedbackPopup();
      activeFeedbackTarget = target;
      activeFeedbackAnchor = anchorPoint && typeof anchorPoint === "object"
        ? anchorPoint
        : null;
      popup.classList.remove("lexishift-open");
      renderFeedbackModules(target);
      const placement = positionFeedbackPopup();
      debugLog("Opening feedback popup.", {
        top: popup.style.top,
        left: popup.style.left,
        verticalPlacement: placement ? placement.vertical : "",
        horizontalPlacement: placement ? placement.horizontal : "",
        moduleCount: feedbackModules ? feedbackModules.childElementCount : 0,
        target: summarizeTarget(target)
      });
      cancelFrame(feedbackOpenFrame);
      feedbackOpenFrame = requestAnimationFrame(() => {
        feedbackOpenFrame = null;
        if (activeFeedbackTarget === target) {
          popup.classList.add("lexishift-open");
          popup.setAttribute("aria-hidden", "false");
        }
      });
      attachFeedbackKeyListener();
      attachFeedbackCloseListener();
    }

    function closeFeedbackPopup() {
      if (!feedbackPopup) {
        return;
      }
      feedbackPopup.classList.remove("lexishift-open");
      feedbackPopup.setAttribute("aria-hidden", "true");
      cancelFrame(feedbackOpenFrame);
      cancelFrame(feedbackPositionFrame);
      feedbackOpenFrame = null;
      feedbackPositionFrame = null;
      activeFeedbackTarget = null;
      activeFeedbackAnchor = null;
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
        const pointerAnchor = Number.isFinite(Number(event.clientX))
          && Number.isFinite(Number(event.clientY))
          && (Number(event.clientX) !== 0 || Number(event.clientY) !== 0)
          ? { clientX: Number(event.clientX), clientY: Number(event.clientY) }
          : null;
        openFeedbackPopup(target, pointerAnchor);
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
    createController,
    computePopupPlacement
  };
})();
