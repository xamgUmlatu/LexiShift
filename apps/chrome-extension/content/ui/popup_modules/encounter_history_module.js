(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

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

  function formatLastSeen(value) {
    const ts = String(value || "").trim();
    if (!ts) {
      return "";
    }
    const date = new Date(ts);
    if (Number.isNaN(date.getTime())) {
      return "";
    }
    return date.toLocaleString();
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
        debugLog("Skipping encounter-history module: target payload missing.");
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
    toggleButton.textContent = "Encounter history";
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
        toggleButton.textContent = "Encounter history";
        return;
      }
      const summaryCount = Number(moduleEl.dataset.encounterCount || 0);
      toggleButton.textContent = summaryCount > 0
        ? `Encounter history (${summaryCount})`
        : "Encounter history";
    }

    async function ensureLoaded() {
      if (loaded) {
        return;
      }
      toggleButton.disabled = true;
      toggleButton.textContent = "Encounter history (loading...)";
      try {
        const history = await historyStore.getHistoryForWord({
          profile_id: profileId,
          language_pair: payload.languagePair,
          lemma
        });
        details.textContent = "";
        const encounterCount = Number(history && history.encounter_count ? history.encounter_count : 0);
        const lastSeen = formatLastSeen(history && history.last_seen ? history.last_seen : "");
        const excerpt = String(history && history.last_sentence_excerpt ? history.last_sentence_excerpt : "").trim();
        moduleEl.dataset.encounterCount = String(encounterCount);

        if (!encounterCount) {
          const empty = document.createElement("div");
          empty.className = "lexishift-popup-module-line";
          empty.textContent = "No encounters yet.";
          details.appendChild(empty);
          loaded = true;
          return;
        }

        const rows = [
          `Encounters: ${encounterCount}`,
          lastSeen ? `Last seen: ${lastSeen}` : ""
        ].filter(Boolean);
        for (const text of rows) {
          const row = document.createElement("div");
          row.className = "lexishift-popup-module-line";
          row.textContent = text;
          details.appendChild(row);
        }
        if (excerpt) {
          const excerptRow = document.createElement("div");
          excerptRow.className = "lexishift-popup-module-line lexishift-popup-module-quote";
          excerptRow.textContent = excerpt;
          details.appendChild(excerptRow);
        }
        loaded = true;
      } catch (error) {
        details.textContent = "";
        const failed = document.createElement("div");
        failed.className = "lexishift-popup-module-line";
        failed.textContent = "Failed to load encounter history.";
        details.appendChild(failed);
        if (typeof debugLog === "function") {
          debugLog("Failed to load encounter-history module.", {
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

  root.uiEncounterHistoryModule = {
    build
  };
})();
