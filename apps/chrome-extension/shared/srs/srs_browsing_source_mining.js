(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const sourceMorphology = root.srsBrowsingSourceMorphology || {};
  const normalizeSourceTerm = sourceMorphology.normalizeSourceTerm;
  const sourceTermTokens = sourceMorphology.sourceTermTokens;
  const sourceTermVariants = sourceMorphology.sourceTermVariants;

  if (
    typeof normalizeSourceTerm !== "function"
    || typeof sourceTermTokens !== "function"
    || typeof sourceTermVariants !== "function"
  ) {
    console.warn("[LexiShift] Browsing source morphology module not loaded.");
    return;
  }

  const SIDE_SOURCE = "source";
  const OBSERVATION_SOURCE_MAPPING = "source_mapping";
  const DEFAULT_MAX_SOURCE_TEXT_CHARS = 60000;
  const DEFAULT_MAX_SOURCE_TERMS_PER_SCAN = 80;
  const DEFAULT_MAX_SOURCE_COUNT_PER_TARGET = 3;
  const DEFAULT_SOURCE_SINGLE_WORD_CONFIDENCE = 0.58;
  const DEFAULT_SOURCE_PHRASE_CONFIDENCE = 0.72;
  const DEFAULT_SOURCE_FANOUT_PENALTY = 0.12;
  const DEFAULT_SOURCE_MIN_CONFIDENCE = 0.35;
  const DEFAULT_SOURCE_MAX_CONFIDENCE = 0.8;
  const SOURCE_TEXT_SKIP_TAGS = new Set([
    "script", "style", "noscript", "textarea", "select", "option", "template", "svg", "canvas"
  ]);

  function sourceLanguageFromPair(pair) {
    const parts = String(pair || "").trim().toLowerCase().split("-", 2);
    return parts.length === 2 ? parts[0] : "";
  }

  function targetLanguageFromPair(pair) {
    const parts = String(pair || "").trim().toLowerCase().split("-", 2);
    return parts.length === 2 ? parts[1] : "";
  }

  function normalizeTargetText(value) {
    return String(value || "").replace(/\s+/g, "").trim();
  }

  function optionNumber(options, key, fallback, min, max) {
    const opts = options && typeof options === "object" ? options : {};
    const value = Number(opts[key]);
    const safe = Number.isFinite(value) ? value : fallback;
    return Math.max(min, Math.min(max, safe));
  }

  function isVisibleElement(element) {
    if (!element) {
      return false;
    }
    if (typeof globalThis.getComputedStyle === "function") {
      const style = globalThis.getComputedStyle(element);
      if (style) {
        const display = String(style.display || "").trim().toLowerCase();
        const visibility = String(style.visibility || "").trim().toLowerCase();
        if (display === "none" || visibility === "hidden" || visibility === "collapse") {
          return false;
        }
      }
    }
    if (typeof element.getClientRects === "function" && element.getClientRects().length === 0) {
      return false;
    }
    return true;
  }

  function collectVisibleSourceText(rootNode, options) {
    const opts = options && typeof options === "object" ? options : {};
    const maxChars = Math.max(1000, Number(opts.maxSourceTextChars || DEFAULT_MAX_SOURCE_TEXT_CHARS));
    const queryRoot = rootNode && rootNode.body
      ? rootNode.body
      : (rootNode || (globalThis.document && globalThis.document.body) || globalThis.document);
    if (!queryRoot) {
      return "";
    }
    const parts = [];
    let totalChars = 0;

    function addText(value) {
      if (totalChars >= maxChars) {
        return;
      }
      const text = String(value || "").replace(/\s+/g, " ").trim();
      if (!text) {
        return;
      }
      const remaining = maxChars - totalChars;
      parts.push(text.slice(0, remaining));
      totalChars += Math.min(text.length, remaining);
    }

    function shouldSkipElement(element) {
      if (!element || element.nodeType !== 1) {
        return false;
      }
      const tag = String(element.tagName || "").trim().toLowerCase();
      if (SOURCE_TEXT_SKIP_TAGS.has(tag) || tag === "rt" || tag === "rp") {
        return true;
      }
      if (
        element.classList
        && typeof element.classList.contains === "function"
        && (
          element.classList.contains("lexishift-replacement")
          || element.classList.contains("lexishift-popup")
        )
      ) {
        return true;
      }
      if (
        typeof element.closest === "function"
        && element.closest(".lexishift-replacement, [data-lexishift-scan-skip=\"true\"]")
      ) {
        return true;
      }
      return opts.includeInvisible === true ? false : !isVisibleElement(element);
    }

    function fallbackVisit(node) {
      if (!node || totalChars >= maxChars) {
        return;
      }
      if (node.nodeType === 3) {
        const parent = node.parentElement || node.parentNode;
        if (!shouldSkipElement(parent)) {
          addText(node.nodeValue || "");
        }
        return;
      }
      if (node.nodeType !== 1 || shouldSkipElement(node)) {
        return;
      }
      for (const child of Array.from(node.childNodes || [])) {
        fallbackVisit(child);
        if (totalChars >= maxChars) {
          break;
        }
      }
    }

    if (
      queryRoot.ownerDocument
      && typeof queryRoot.ownerDocument.createTreeWalker === "function"
      && typeof globalThis.NodeFilter !== "undefined"
    ) {
      const walker = queryRoot.ownerDocument.createTreeWalker(
        queryRoot,
        globalThis.NodeFilter.SHOW_TEXT,
        {
          acceptNode(node) {
            const parent = node && (node.parentElement || node.parentNode);
            if (!parent || shouldSkipElement(parent)) {
              return globalThis.NodeFilter.FILTER_REJECT;
            }
            return String(node.nodeValue || "").trim()
              ? globalThis.NodeFilter.FILTER_ACCEPT
              : globalThis.NodeFilter.FILTER_REJECT;
          }
        }
      );
      let node = walker.nextNode();
      while (node && totalChars < maxChars) {
        addText(node.nodeValue || "");
        node = walker.nextNode();
      }
    } else {
      fallbackVisit(queryRoot);
    }
    return parts.join(" ");
  }

  function targetMetadataFromRule(rule) {
    const metadata = rule && rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {};
    const wordPackage = metadata.word_package && typeof metadata.word_package === "object"
      ? metadata.word_package
      : null;
    const scriptForms = wordPackage && wordPackage.script_forms && typeof wordPackage.script_forms === "object"
      ? wordPackage.script_forms
      : (metadata.script_forms && typeof metadata.script_forms === "object" ? metadata.script_forms : null);
    const morphology = metadata.morphology && typeof metadata.morphology === "object"
      ? metadata.morphology
      : null;
    const surface = normalizeTargetText(
      (wordPackage && wordPackage.surface)
        || (scriptForms && (scriptForms.kanji || scriptForms.surface))
        || (morphology && morphology.target_surface)
        || (rule && rule.replacement)
    );
    const reading = normalizeTargetText(
      (wordPackage && wordPackage.reading)
        || (scriptForms && scriptForms.kana)
        || ""
    );
    if (!surface) {
      return null;
    }
    return {
      surface,
      reading,
      targetKey: reading && reading !== surface ? `${surface}|${reading}` : surface,
      readingConfidence: reading ? 1 : 0.45
    };
  }

  function isSrsRuleForPair(rule, settings) {
    if (!rule || rule.enabled === false) {
      return false;
    }
    const metadata = rule.metadata && typeof rule.metadata === "object" ? rule.metadata : {};
    if (String(metadata.lexishift_origin || "").trim().toLowerCase() !== "srs") {
      return false;
    }
    const pair = String(settings && settings.srsPair || "").trim().toLowerCase();
    const rulePair = String(metadata.language_pair || pair).trim().toLowerCase();
    return Boolean(pair && pair !== "all" && rulePair === pair);
  }

  function sourceMappingConfidence(term, fanout, options, variantMultiplier) {
    const opts = options && typeof options === "object" ? options : {};
    const tokenCount = sourceTermTokens(term).length;
    const base = tokenCount > 1
      ? optionNumber(opts, "sourcePhraseConfidence", DEFAULT_SOURCE_PHRASE_CONFIDENCE, 0, 1)
      : optionNumber(
          opts,
          "sourceSingleWordConfidence",
          DEFAULT_SOURCE_SINGLE_WORD_CONFIDENCE,
          0,
          1
        );
    const fanoutPenalty = Math.max(0, Number(fanout || 1) - 1)
      * optionNumber(opts, "sourceFanoutPenalty", DEFAULT_SOURCE_FANOUT_PENALTY, 0, 1);
    const minConfidence = optionNumber(
      opts,
      "sourceMinConfidence",
      DEFAULT_SOURCE_MIN_CONFIDENCE,
      0,
      1
    );
    const maxConfidence = optionNumber(
      opts,
      "sourceMaxConfidence",
      DEFAULT_SOURCE_MAX_CONFIDENCE,
      minConfidence,
      1
    );
    const multiplier = Math.max(0, Math.min(1, Number(variantMultiplier || 1)));
    return Math.max(minConfidence, Math.min(maxConfidence, (base - fanoutPenalty) * multiplier));
  }

  function buildSourceMappingIndex(rules, settings, options) {
    const opts = options && typeof options === "object" ? options : {};
    const pair = String(settings && settings.srsPair || "").trim().toLowerCase();
    if (!pair || pair === "all" || sourceLanguageFromPair(pair) !== "en" || targetLanguageFromPair(pair) !== "ja") {
      return [];
    }
    const buckets = new Map();
    for (const rule of Array.isArray(rules) ? rules : []) {
      if (!isSrsRuleForPair(rule, settings)) {
        continue;
      }
      const target = targetMetadataFromRule(rule);
      if (!target) {
        continue;
      }
      for (const variant of sourceTermVariants(rule.source_phrase, opts)) {
        if (!buckets.has(variant.term)) {
          buckets.set(variant.term, new Map());
        }
        const targets = buckets.get(variant.term);
        const current = targets.get(target.targetKey);
        const previousMultiplier = Number(
          current && current.source_variant_confidence_multiplier || 0
        );
        const nextMultiplier = Number(variant.source_variant_confidence_multiplier || 1);
        if (!current || nextMultiplier > previousMultiplier) {
          targets.set(target.targetKey, {
            language_pair: pair,
            lemma: target.surface,
            target_key: target.targetKey,
            target_reading: target.reading,
            reading_confidence: target.readingConfidence,
            source_variant_kind: variant.source_variant_kind,
            source_variant_confidence_multiplier: nextMultiplier
          });
        }
      }
    }
    const maxSingleFanout = Math.max(1, Number(opts.maxSingleWordSourceFanout || 1));
    const maxPhraseFanout = Math.max(1, Number(opts.maxPhraseSourceFanout || 2));
    return Array.from(buckets.entries())
      .map(([term, targets]) => {
        const rows = Array.from(targets.values());
        const tokenCount = sourceTermTokens(term).length;
        const fanout = rows.length;
        const maxFanout = tokenCount > 1 ? maxPhraseFanout : maxSingleFanout;
        if (!fanout || fanout > maxFanout) {
          return null;
        }
        const variantMultiplier = rows.reduce(
          (best, row) => Math.max(best, Number(row.source_variant_confidence_multiplier || 1)),
          0
        );
        return {
          term,
          token_count: tokenCount,
          fanout,
          targets: rows,
          source_mapping_confidence: sourceMappingConfidence(term, fanout, opts, variantMultiplier)
        };
      })
      .filter(Boolean)
      .sort((left, right) => {
        if (right.term.length !== left.term.length) {
          return right.term.length - left.term.length;
        }
        return left.term.localeCompare(right.term);
      });
  }

  function countSourceTermOccurrences(normalizedText, term, maxCount) {
    const text = normalizeSourceTerm(normalizedText);
    const phrase = normalizeSourceTerm(term);
    if (!text || !phrase) {
      return 0;
    }
    const pattern = phrase
      .split(" ")
      .filter(Boolean)
      .map((token) => token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("\\s+");
    if (!pattern) {
      return 0;
    }
    const boundary = "[^0-9a-z]";
    const regex = new RegExp(`(^|${boundary})${pattern}(?=$|${boundary})`, "g");
    const cap = Math.max(1, Number(maxCount || DEFAULT_MAX_SOURCE_COUNT_PER_TARGET));
    let count = 0;
    while (count < cap && regex.exec(text)) {
      count += 1;
    }
    return count;
  }

  function buildSourceMappingSignals(sourceText, rules, settings, options) {
    const opts = options && typeof options === "object" ? options : {};
    const pair = String(settings && settings.srsPair || "").trim().toLowerCase();
    if (!pair || pair === "all" || sourceLanguageFromPair(pair) !== "en" || targetLanguageFromPair(pair) !== "ja") {
      return [];
    }
    const maxTerms = Math.max(1, Number(opts.maxSourceTermsPerScan || DEFAULT_MAX_SOURCE_TERMS_PER_SCAN));
    const maxCount = Math.max(1, Number(opts.maxSourceCountPerTarget || DEFAULT_MAX_SOURCE_COUNT_PER_TARGET));
    const normalizedText = normalizeSourceTerm(sourceText).slice(
      0,
      Math.max(1000, Number(opts.maxSourceTextChars || DEFAULT_MAX_SOURCE_TEXT_CHARS))
    );
    if (!normalizedText) {
      return [];
    }
    const signals = [];
    const byTarget = new Map();
    const targetOrder = [];
    const entries = buildSourceMappingIndex(rules, settings, opts);
    for (const entry of entries) {
      if (targetOrder.length >= maxTerms) {
        break;
      }
      const count = countSourceTermOccurrences(normalizedText, entry.term, maxCount);
      if (!count) {
        continue;
      }
      for (const target of entry.targets) {
        if (!byTarget.has(target.target_key) && targetOrder.length >= maxTerms) {
          break;
        }
        const current = byTarget.get(target.target_key);
        if (!current) {
          targetOrder.push(target.target_key);
          byTarget.set(target.target_key, {
            ...target,
            side: SIDE_SOURCE,
            count: 0,
            weighted_confidence_sum: 0,
            observation_source: OBSERVATION_SOURCE_MAPPING,
            source_mapping_confidence: 0
          });
        }
        const row = byTarget.get(target.target_key);
        row.count += count;
        row.weighted_confidence_sum += count * entry.source_mapping_confidence;
        row.reading_confidence = Math.max(
          Number(row.reading_confidence || 0),
          Number(target.reading_confidence || 0)
        );
      }
    }
    for (const targetKey of targetOrder) {
      const row = byTarget.get(targetKey);
      if (!row || row.count <= 0) {
        continue;
      }
      const confidence = row.weighted_confidence_sum / row.count;
      signals.push({
        language_pair: row.language_pair,
        lemma: row.lemma,
        target_key: row.target_key,
        target_reading: row.target_reading,
        reading_confidence: row.reading_confidence,
        side: row.side,
        count: row.count,
        observation_source: row.observation_source,
        source_mapping_confidence: Math.max(0, Math.min(1, confidence))
      });
    }
    return signals;
  }

  root.srsBrowsingSourceMining = {
    buildSourceMappingIndex,
    buildSourceMappingSignals,
    collectVisibleSourceText,
    countSourceTermOccurrences,
    normalizeSourceTerm,
    sourceLanguageFromPair,
    sourceTermVariants
  };
})();
