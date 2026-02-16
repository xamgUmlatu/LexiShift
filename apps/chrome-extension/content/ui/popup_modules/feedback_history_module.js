(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function t(key, substitutions, fallback) {
    try {
      if (typeof chrome !== "undefined"
        && chrome.i18n
        && typeof chrome.i18n.getMessage === "function") {
        const message = chrome.i18n.getMessage(key, substitutions);
        if (message) {
          return message;
        }
      }
    } catch (_error) {
      // Ignore i18n runtime errors and return fallback.
    }
    return String(fallback || key || "");
  }

  function normalizePair(value) {
    return String(value || "").trim().toLowerCase();
  }

  function normalizeLemma(value) {
    return String(value || "").trim().toLowerCase();
  }

  function parseTargetPayload(target) {
    if (!target || !target.dataset) {
      return null;
    }
    const pair = normalizePair(target.dataset.languagePair);
    const replacement = String(target.dataset.replacement || target.dataset.displayReplacement || target.textContent || "").trim();
    if (!pair || !replacement) {
      return null;
    }
    return {
      languagePair: pair,
      replacement
    };
  }

  function parseFeedbackDigits(value) {
    return String(value || "")
      .split("")
      .filter((digit) => digit >= "1" && digit <= "4");
  }

  function summarizeDigits(digits) {
    const counts = { "1": 0, "2": 0, "3": 0, "4": 0 };
    for (const digit of digits) {
      if (counts[digit] !== undefined) {
        counts[digit] += 1;
      }
    }
    return counts;
  }

  function ratingLabel(digit, translate) {
    const tr = typeof translate === "function" ? translate : t;
    if (digit === "1") {
      return tr("popup_feedback_rating_again", null, "Again");
    }
    if (digit === "2") {
      return tr("popup_feedback_rating_hard", null, "Hard");
    }
    if (digit === "3") {
      return tr("popup_feedback_rating_good", null, "Good");
    }
    if (digit === "4") {
      return tr("popup_feedback_rating_easy", null, "Easy");
    }
    return digit;
  }

  function titleText(totalCount, translate) {
    const tr = typeof translate === "function" ? translate : t;
    const total = Number(totalCount || 0);
    if (total > 0) {
      return tr(
        "popup_feedback_history_count",
        [String(total)],
        `Feedback history (${total})`
      );
    }
    return tr("module_feedback_history", null, "Feedback history");
  }

  function build(target, debugLog, context) {
    const ctx = context && typeof context === "object" ? context : {};
    const translate = typeof ctx.t === "function" ? ctx.t : t;
    const historyStore = ctx.historyStore && typeof ctx.historyStore === "object"
      ? ctx.historyStore
      : null;
    if (!historyStore || typeof historyStore.getHistoryForWord !== "function") {
      return null;
    }
    const profileId = String(ctx.profileId || "default").trim() || "default";
    const lemmatize = typeof ctx.lemmatize === "function"
      ? ctx.lemmatize
      : null;
    const payload = parseTargetPayload(target);
    if (!payload) {
      if (typeof debugLog === "function") {
        debugLog("Skipping feedback-history module: target payload missing.");
      }
      return null;
    }
    const rawLemma = payload.replacement;
    const lemma = lemmatize
      ? normalizeLemma(lemmatize(rawLemma, payload.languagePair) || rawLemma)
      : normalizeLemma(rawLemma);
    if (!lemma) {
      return null;
    }

    const moduleEl = document.createElement("section");
    moduleEl.className = "lexishift-popup-module lexishift-history-module";
    const toggleButton = document.createElement("button");
    toggleButton.type = "button";
    toggleButton.className = "lexishift-popup-module-toggle lexishift-popup-module-toggle-centered";
    toggleButton.textContent = titleText(0, translate);
    const details = document.createElement("div");
    details.className = "lexishift-popup-module-details hidden";
    moduleEl.appendChild(toggleButton);
    moduleEl.appendChild(details);

    let loaded = false;
    let open = false;

    function setOpen(nextOpen) {
      open = nextOpen === true;
      details.classList.toggle("hidden", !open);
      toggleButton.setAttribute("aria-expanded", open ? "true" : "false");
      if (!loaded) {
        toggleButton.textContent = titleText(0, translate);
        return;
      }
      const summaryCount = Number(moduleEl.dataset.feedbackTotal || 0);
      toggleButton.textContent = titleText(summaryCount, translate);
    }

    async function ensureLoaded() {
      if (loaded) {
        return;
      }
      toggleButton.disabled = true;
      toggleButton.textContent = translate(
        "popup_feedback_history_loading",
        null,
        "Feedback history (loading...)"
      );
      try {
        const history = await historyStore.getHistoryForWord({
          profile_id: profileId,
          language_pair: payload.languagePair,
          lemma
        });
        details.textContent = "";
        const total = Number(history && history.feedback_total ? history.feedback_total : 0);
        const digits = parseFeedbackDigits(history && history.feedback_digits ? history.feedback_digits : "");
        const summary = summarizeDigits(digits);
        moduleEl.dataset.feedbackTotal = String(total);
        if (!digits.length) {
          const empty = document.createElement("div");
          empty.className = "lexishift-popup-module-line";
          empty.textContent = translate("popup_feedback_history_empty", null, "No feedback yet.");
          details.appendChild(empty);
          loaded = true;
          return;
        }
        const rows = [
          translate("popup_feedback_history_total", [String(total)], `Total: ${total}`),
          translate(
            "popup_feedback_history_breakdown_ah",
            [String(summary["1"]), String(summary["2"])],
            `Again: ${summary["1"]}  Hard: ${summary["2"]}`
          ),
          translate(
            "popup_feedback_history_breakdown_ge",
            [String(summary["3"]), String(summary["4"])],
            `Good: ${summary["3"]}  Easy: ${summary["4"]}`
          ),
          translate(
            "popup_feedback_history_recent",
            [digits.slice(-12).map((digit) => ratingLabel(digit, translate)).join(", ")],
            `Recent: ${digits.slice(-12).map((digit) => ratingLabel(digit, translate)).join(", ")}`
          )
        ];
        for (const text of rows) {
          const row = document.createElement("div");
          row.className = "lexishift-popup-module-line";
          row.textContent = text;
          details.appendChild(row);
        }
        loaded = true;
      } catch (error) {
        details.textContent = "";
        const failed = document.createElement("div");
        failed.className = "lexishift-popup-module-line";
        failed.textContent = translate(
          "popup_feedback_history_load_failed",
          null,
          "Failed to load feedback history."
        );
        details.appendChild(failed);
        if (typeof debugLog === "function") {
          debugLog("Failed to load feedback-history module.", {
            message: error && error.message ? error.message : String(error),
            languagePair: payload.languagePair,
            lemma
          });
        }
        loaded = true;
      } finally {
        toggleButton.disabled = false;
      }
    }

    toggleButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      Promise.resolve(ensureLoaded()).then(() => {
        setOpen(!open);
      });
    });

    setOpen(false);
    return moduleEl;
  }

  root.uiFeedbackHistoryModule = {
    build
  };
})();
