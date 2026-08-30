(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function normalizePairKey(pairKey) {
    return String(pairKey || "").trim().toLowerCase();
  }

  function currentStoryCard(profile) {
    const source = profile && typeof profile === "object" ? profile : null;
    const exists = Boolean(source && (source.srsStoryExists === true || source.srsEnabled === true));
    return {
      exists,
      shouldShow: exists,
      badgeKey: "badge_srs_active_story",
      badgeFallback: "Active"
    };
  }

  function collapseStoryCard(card) {
    if (!card) {
      return;
    }
    if ("open" in card) {
      card.open = false;
    }
    if (typeof card.querySelectorAll !== "function") {
      return;
    }
    card.querySelectorAll("details").forEach((details) => {
      if ("open" in details) {
        details.open = false;
      }
    });
  }

  function switchableStoryCards(options) {
    const opts = options && typeof options === "object" ? options : {};
    const currentPairKey = normalizePairKey(opts.currentPairKey);
    const entries = Array.isArray(opts.entries) ? opts.entries : [];
    return entries
      .map((entry) => {
        if (!entry || typeof entry !== "object") {
          return null;
        }
        const pairKey = normalizePairKey(entry.pairKey);
        if (!pairKey) {
          return null;
        }
        const isSelected = currentPairKey
          ? pairKey === currentPairKey
          : entry.isActive === true;
        if (isSelected) {
          return null;
        }
        return {
          pairKey,
          canSwitch: true,
          creationIndex: entry.creationIndex,
          srsMaxActive: entry.srsMaxActive
        };
      })
      .filter(Boolean);
  }

  root.optionsSrsStoryViewModel = {
    collapseStoryCard,
    currentStoryCard,
    normalizePairKey,
    switchableStoryCards
  };
})();
