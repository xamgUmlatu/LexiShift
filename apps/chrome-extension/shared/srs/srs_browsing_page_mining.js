(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const sourceMining = root.srsBrowsingSourceMining || {};

  const SIDE_TARGET = "target";
  const OBSERVATION_TARGET_SURFACE = "target_surface";
  const DEFAULT_MAX_RUBY_TARGETS_PER_SCAN = 80;
  const DEFAULT_MAX_COUNT_PER_TARGET = 5;
  const JAPANESE_RE = /[\u3040-\u30ff\u3400-\u9fff]/;
  const KANA_RE = /^[\u3040-\u30ffー・]+$/;

  function targetLanguageFromPair(pair) {
    const parts = String(pair || "").trim().toLowerCase().split("-", 2);
    return parts.length === 2 ? parts[1] : "";
  }

  function normalizeText(value) {
    return String(value || "").replace(/\s+/g, "").trim();
  }

  function nodeTextExcludingRubyText(node) {
    if (!node) {
      return "";
    }
    if (node.nodeType === 3) {
      return node.nodeValue || "";
    }
    if (node.nodeType !== 1) {
      return "";
    }
    const tag = String(node.tagName || "").trim().toLowerCase();
    if (tag === "rt" || tag === "rp") {
      return "";
    }
    let text = "";
    for (const child of Array.from(node.childNodes || [])) {
      text += nodeTextExcludingRubyText(child);
    }
    return text;
  }

  function rubyReadingText(ruby) {
    if (!ruby || typeof ruby.querySelectorAll !== "function") {
      return "";
    }
    return Array.from(ruby.querySelectorAll("rt"))
      .map((node) => String(node.textContent || ""))
      .join("");
  }

  function extractRubyPair(ruby) {
    const surface = normalizeText(nodeTextExcludingRubyText(ruby));
    const reading = normalizeText(rubyReadingText(ruby));
    return isValidRubyPair(surface, reading) ? { surface, reading } : null;
  }

  function isValidRubyPair(surface, reading) {
    if (!surface || !reading) {
      return false;
    }
    if (surface.length > 12 || reading.length > 24) {
      return false;
    }
    if (!JAPANESE_RE.test(surface) || !KANA_RE.test(reading)) {
      return false;
    }
    return surface !== reading;
  }

  function collectRubyPairs(rootNode, options) {
    const opts = options && typeof options === "object" ? options : {};
    const queryRoot = rootNode && typeof rootNode.querySelectorAll === "function"
      ? rootNode
      : globalThis.document;
    if (!queryRoot || typeof queryRoot.querySelectorAll !== "function") {
      return [];
    }
    const maxTargets = Math.max(
      1,
      Number(opts.maxRubyTargetsPerScan || DEFAULT_MAX_RUBY_TARGETS_PER_SCAN)
    );
    const pairs = [];
    for (const ruby of Array.from(queryRoot.querySelectorAll("ruby"))) {
      if (pairs.length >= maxTargets) {
        break;
      }
      if (opts.includeInvisible !== true && !isVisibleElement(ruby)) {
        continue;
      }
      const pair = extractRubyPair(ruby);
      if (pair) {
        pairs.push(pair);
      }
    }
    return pairs;
  }

  function buildRubyTargetSignals(pairs, settings, options) {
    const opts = options && typeof options === "object" ? options : {};
    const pair = String(settings && settings.srsPair || "").trim().toLowerCase();
    if (!pair || pair === "all" || targetLanguageFromPair(pair) !== "ja") {
      return [];
    }
    const maxCount = Math.max(1, Number(opts.maxCountPerTarget || DEFAULT_MAX_COUNT_PER_TARGET));
    const counts = new Map();
    for (const item of Array.isArray(pairs) ? pairs : []) {
      const surface = normalizeText(item && (item.surface || item.target_lemma || item.lemma));
      const reading = normalizeText(item && (item.reading || item.target_reading));
      if (!isValidRubyPair(surface, reading)) {
        continue;
      }
      const targetKey = `${surface}|${reading}`;
      counts.set(targetKey, {
        surface,
        reading,
        count: Math.min(maxCount, Number(counts.get(targetKey)?.count || 0) + 1)
      });
    }
    return Array.from(counts.values()).map((row) => ({
      language_pair: pair,
      lemma: row.surface,
      target_key: `${row.surface}|${row.reading}`,
      target_reading: row.reading,
      side: SIDE_TARGET,
      count: row.count,
      reading_confidence: 1,
      source_mapping_confidence: 1,
      observation_source: OBSERVATION_TARGET_SURFACE
    }));
  }

  function sourceMiningOptionsFromSettings(settings) {
    const value = settings && (
      settings.srsBrowsingSourceMiningOptions
      || settings.srsBrowsingAdmissionSourceMiningOptions
    );
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
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

  function createMiner(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getCurrentSettings = typeof opts.getCurrentSettings === "function"
      ? opts.getCurrentSettings
      : (() => ({}));
    const browsingAdmissionSignals = opts.browsingAdmissionSignals
      && typeof opts.browsingAdmissionSignals === "object"
      ? opts.browsingAdmissionSignals
      : null;
    const getCurrentRules = typeof opts.getCurrentRules === "function"
      ? opts.getCurrentRules
      : (() => []);
    const getSourceMiningRules = typeof opts.getSourceMiningRules === "function"
      ? opts.getSourceMiningRules
      : getCurrentRules;
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const seenSignalKeys = new Set();

    function clearSeen() {
      seenSignalKeys.clear();
    }

    function mineDocument(rootNode, reason) {
      const settings = getCurrentSettings();
      if (
        !settings
        || settings.srsBrowsingAdmissionSignalsEnabled !== true
        || targetLanguageFromPair(settings.srsPair) !== "ja"
        || !browsingAdmissionSignals
        || typeof browsingAdmissionSignals.recordExposureBatch !== "function"
      ) {
        return Promise.resolve({ status: "skipped", reason: "not_enabled" });
      }
      const targetRoot = rootNode || globalThis.document;
      const scanOptions = {
        ...opts,
        ...sourceMiningOptionsFromSettings(settings)
      };
      const pairs = collectRubyPairs(targetRoot, scanOptions);
      const sourceText = typeof sourceMining.collectVisibleSourceText === "function"
        ? sourceMining.collectVisibleSourceText(targetRoot, scanOptions)
        : "";
      const rules = getSourceMiningRules();
      const signals = buildRubyTargetSignals(pairs, settings, scanOptions)
        .concat(
          typeof sourceMining.buildSourceMappingSignals === "function"
            ? sourceMining.buildSourceMappingSignals(sourceText, rules, settings, scanOptions)
            : []
        )
        .filter((signal) => {
          const seenKey = `${signal.side || ""}|${signal.target_key || ""}`;
          if (seenSignalKeys.has(seenKey)) {
            return false;
          }
          seenSignalKeys.add(seenKey);
          return true;
        });
      if (!signals.length) {
        return Promise.resolve({ status: "empty", accepted: 0 });
      }
      if (settings.debugEnabled) {
        log(`Queued ${signals.length} browsing-admission page signal(s): ${String(reason || "scan")}.`);
      }
      return browsingAdmissionSignals.recordExposureBatch(signals, settings);
    }

    return {
      clearSeen,
      mineDocument
    };
  }

  root.srsBrowsingPageMining = {
    buildSourceMappingIndex: sourceMining.buildSourceMappingIndex,
    buildSourceMappingSignals: sourceMining.buildSourceMappingSignals,
    buildRubyTargetSignals,
    collectVisibleSourceText: sourceMining.collectVisibleSourceText,
    collectRubyPairs,
    countSourceTermOccurrences: sourceMining.countSourceTermOccurrences,
    createMiner,
    extractRubyPair,
    isValidRubyPair,
    sourceLanguageFromPair: sourceMining.sourceLanguageFromPair,
    targetLanguageFromPair
  };
})();
