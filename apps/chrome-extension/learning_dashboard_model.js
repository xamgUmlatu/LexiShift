(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const GLOSS_PREVIEW_LIMIT = 2;

  function normalizeText(value) {
    return String(value || "").trim();
  }

  function itemKey(item) {
    return normalizeText(item && (item.item_id || item.lemma || item.display));
  }

  function wordPackageForItem(item) {
    const advanced = item && item.advanced && typeof item.advanced === "object"
      ? item.advanced
      : {};
    const wordPackage = advanced.word_package && typeof advanced.word_package === "object"
      ? advanced.word_package
      : {};
    return wordPackage;
  }

  function firstSourcePhrase(item) {
    const summary = item && item.rule_summary && typeof item.rule_summary === "object"
      ? item.rule_summary
      : {};
    const phrases = Array.isArray(summary.source_phrases) ? summary.source_phrases : [];
    return normalizeText(phrases[0]);
  }

  function createWordInfoRequest({ item, pair, profileId }) {
    const sourcePhrase = firstSourcePhrase(item);
    return {
      profileId: normalizeText(profileId) || "default",
      pair: normalizeText(pair),
      lemma: normalizeText(item && item.lemma),
      display: normalizeText(item && item.display),
      origin: "srs",
      sourcePhrase,
      wordPackage: wordPackageForItem(item)
    };
  }

  function resolveGlossPreview(result) {
    const glosses = Array.isArray(result && result.glosses) ? result.glosses : [];
    const texts = [];
    for (const gloss of glosses) {
      const text = normalizeText(gloss && typeof gloss === "object" ? gloss.text : gloss);
      if (!text || texts.includes(text)) {
        continue;
      }
      texts.push(text);
      if (texts.length >= GLOSS_PREVIEW_LIMIT) {
        break;
      }
    }
    return texts.join(", ");
  }

  function resolvePosLabel(item, wordInfo) {
    const resultPos = wordInfo && wordInfo.pos && typeof wordInfo.pos === "object"
      ? normalizeText(wordInfo.pos.label || wordInfo.pos.canonical)
      : "";
    if (resultPos) {
      return resultPos;
    }
    return normalizeText(item && item.pos);
  }

  function resolveTopicLabel(item) {
    const packageValue = wordPackageForItem(item);
    const candidates = [
      item && item.topic,
      item && item.topic_label,
      packageValue.topic,
      packageValue.topic_label,
      packageValue.topic_family,
      packageValue.register
    ];
    for (const value of candidates) {
      const label = normalizeTopicText(value);
      if (label) {
        return label;
      }
    }
    const arrays = [
      item && item.topics,
      item && item.topic_hints,
      packageValue.topics,
      packageValue.topic_hints,
      packageValue.tags
    ];
    for (const value of arrays) {
      const label = firstTopicFromList(value);
      if (label) {
        return label;
      }
    }
    return "General";
  }

  function firstTopicFromList(value) {
    if (!Array.isArray(value)) {
      return "";
    }
    for (const item of value) {
      const label = normalizeTopicText(item);
      if (label) {
        return label;
      }
    }
    return "";
  }

  function normalizeTopicText(value) {
    const text = normalizeText(value);
    if (!text) {
      return "";
    }
    return text.replaceAll("_", " ").replace(/\b\w/g, (match) => match.toUpperCase());
  }

  function formatActivity(item) {
    const reviews = Number(item && item.review_count || 0);
    const seen = Number(item && item.exposures || 0);
    return `${reviews} ${reviews === 1 ? "review" : "reviews"} | ${seen} seen`;
  }

  function sourcePhraseSummary(item) {
    const summary = item && item.rule_summary && typeof item.rule_summary === "object"
      ? item.rule_summary
      : {};
    const phrases = Array.isArray(summary.source_phrases) ? summary.source_phrases : [];
    if (!phrases.length) {
      return "";
    }
    const suffix = summary.source_preview_truncated ? ", ..." : "";
    return `${phrases.join(", ")}${suffix}`;
  }

  function hasPublishedRules(item) {
    const summary = item && item.rule_summary && typeof item.rule_summary === "object"
      ? item.rule_summary
      : {};
    const count = Number(summary.enabled_rule_count || summary.rule_count || 0);
    return Number.isFinite(count) && count > 0 && Boolean(normalizeText(item && item.lemma));
  }

  root.learningDashboardModel = {
    createWordInfoRequest,
    firstSourcePhrase,
    formatActivity,
    hasPublishedRules,
    itemKey,
    normalizeText,
    resolveGlossPreview,
    resolvePosLabel,
    resolveTopicLabel,
    sourcePhraseSummary,
    wordPackageForItem
  };
})();
