(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const RATING_LABELS = {
    "1": "Again",
    "2": "Hard",
    "3": "Good",
    "4": "Easy"
  };

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

  function build(target, debugLog, context) {
    const ctx = context && typeof context === "object" ? context : {};
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
    toggleButton.className = "lexishift-popup-module-toggle";
    toggleButton.textContent = "Feedback history";
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
        toggleButton.textContent = "Feedback history";
        return;
      }
      const summaryCount = Number(moduleEl.dataset.feedbackTotal || 0);
      toggleButton.textContent = summaryCount > 0
        ? `Feedback history (${summaryCount})`
        : "Feedback history";
    }

    async function ensureLoaded() {
      if (loaded) {
        return;
      }
      toggleButton.disabled = true;
      toggleButton.textContent = "Feedback history (loading...)";
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
          empty.textContent = "No feedback yet.";
          details.appendChild(empty);
          loaded = true;
          return;
        }
        const rows = [
          `Total: ${total}`,
          `Again: ${summary["1"]}  Hard: ${summary["2"]}`,
          `Good: ${summary["3"]}  Easy: ${summary["4"]}`,
          `Recent: ${digits.slice(-12).map((digit) => RATING_LABELS[digit] || digit).join(", ")}`
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
        failed.textContent = "Failed to load feedback history.";
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
