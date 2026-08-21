(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const semanticContextModule = root.contentDomScanSemanticContext || {};
  const createSemanticContextResolver = typeof semanticContextModule.createResolver === "function"
    ? semanticContextModule.createResolver
    : (() => null);
  const createSemanticContextCache = typeof semanticContextModule.createContextCache === "function"
    ? semanticContextModule.createContextCache
    : (() => null);
  const semanticPerformanceModule = root.contentDomScanSemanticPerformanceMetrics || {};
  const mergeSemanticSummary = typeof semanticPerformanceModule.mergeSummaryIntoCounter === "function"
    ? semanticPerformanceModule.mergeSummaryIntoCounter
    : ((_counter, _summary) => {});

  function createTextNodeProcessor(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getCurrentSettings = typeof opts.getCurrentSettings === "function"
      ? opts.getCurrentSettings
      : (() => ({}));
    const getCurrentTrie = typeof opts.getCurrentTrie === "function"
      ? opts.getCurrentTrie
      : (() => null);
    const getProcessedNodes = typeof opts.getProcessedNodes === "function"
      ? opts.getProcessedNodes
      : (() => new WeakMap());
    const buildReplacementFragment = typeof opts.buildReplacementFragment === "function"
      ? opts.buildReplacementFragment
      : null;
    const semanticGateRuntime = opts.semanticGateRuntime && typeof opts.semanticGateRuntime === "object"
      ? opts.semanticGateRuntime
      : null;
    const getFocusInfo = typeof opts.getFocusInfo === "function"
      ? opts.getFocusInfo
      : ((_text, _focusWord) => ({ substring: false, token: false, index: -1 }));
    const describeElement = typeof opts.describeElement === "function"
      ? opts.describeElement
      : (() => "<unknown>");
    const shorten = typeof opts.shorten === "function"
      ? opts.shorten
      : (text) => String(text || "");
    const describeCodepoints = typeof opts.describeCodepoints === "function"
      ? opts.describeCodepoints
      : (text) => ({ snippet: String(text || ""), codes: [] });
    const normalizeRuleOrigin = typeof opts.normalizeRuleOrigin === "function"
      ? opts.normalizeRuleOrigin
      : (origin) => String(origin || "").toLowerCase() === "srs" ? "srs" : "ruleset";
    const srsMetrics = opts.srsMetrics && typeof opts.srsMetrics === "object"
      ? opts.srsMetrics
      : null;
    const browsingAdmissionSignals = opts.browsingAdmissionSignals || null;
    const lemmatizer = opts.lemmatizer && typeof opts.lemmatizer === "object"
      ? opts.lemmatizer
      : null;
    const popupModuleHistoryStore = opts.popupModuleHistoryStore
      && typeof opts.popupModuleHistoryStore === "object"
      ? opts.popupModuleHistoryStore
      : null;
    const isPopupModuleEnabled = typeof opts.isPopupModuleEnabled === "function"
      ? opts.isPopupModuleEnabled
      : (_moduleId, _settings, _targetLanguage) => false;
    const normalizeProfileId = typeof opts.normalizeProfileId === "function"
      ? opts.normalizeProfileId
      : (value) => String(value || "").trim() || "default";
    const nowMs = typeof opts.nowMs === "function"
      ? opts.nowMs
      : (() => (
          globalThis.performance && typeof globalThis.performance.now === "function"
            ? globalThis.performance.now()
            : Date.now()
        ));
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const nodeFilters = opts.nodeFilters && typeof opts.nodeFilters === "object"
      ? opts.nodeFilters
      : {};
    const isEditable = typeof nodeFilters.isEditable === "function"
      ? nodeFilters.isEditable
      : ((_node) => false);
    const isExcluded = typeof nodeFilters.isExcluded === "function"
      ? nodeFilters.isExcluded
      : ((_node) => false);
    const isLexiShiftNode = typeof nodeFilters.isLexiShiftNode === "function"
      ? nodeFilters.isLexiShiftNode
      : ((_node) => false);
    const getPageBudgetState = typeof opts.getPageBudgetState === "function"
      ? opts.getPageBudgetState
      : (() => null);
    const updatePageBudgetUsage = typeof opts.updatePageBudgetUsage === "function"
      ? opts.updatePageBudgetUsage
      : ((_state, _replacements) => {});
    const semanticContextCaches = new WeakMap();
    const sentenceFallbackNodeIds = new WeakMap();
    let nextSentenceFallbackNodeId = 1;

    function getSemanticContextCache(counter) {
      if (!counter || typeof counter !== "object") return null;
      let cache = semanticContextCaches.get(counter);
      if (!cache) {
        cache = createSemanticContextCache();
        if (cache) semanticContextCaches.set(counter, cache);
      }
      if (cache && cache.stats && typeof cache.stats === "object") {
        counter.semanticContextCacheStats = cache.stats;
      }
      return cache;
    }

    function getSentenceFallbackKey(node) {
      if (!node || (typeof node !== "object" && typeof node !== "function")) {
        return "";
      }
      if (!sentenceFallbackNodeIds.has(node)) {
        sentenceFallbackNodeIds.set(node, nextSentenceFallbackNodeId);
        nextSentenceFallbackNodeId += 1;
      }
      return `text-node:${sentenceFallbackNodeIds.get(node)}`;
    }

    function mergeBudgetRejections(counter, value) {
      if (!counter || !value || typeof value !== "object") {
        return;
      }
      counter.replacementBudgetRejectedPage = Number(counter.replacementBudgetRejectedPage || 0)
        + Number(value.page || 0);
      counter.replacementBudgetRejectedSentence = Number(counter.replacementBudgetRejectedSentence || 0)
        + Number(value.sentence || 0);
      counter.replacementBudgetRejectedLemma = Number(counter.replacementBudgetRejectedLemma || 0)
        + Number(value.lemma || 0);
    }

    function targetLanguageFromPair(pair) {
      const normalized = String(pair || "").trim().toLowerCase();
      if (!normalized) {
        return "";
      }
      const parts = normalized.split("-", 2);
      if (parts.length < 2) {
        return "";
      }
      return String(parts[1] || "").trim().toLowerCase();
    }

    function isVisibleInViewport(element) {
      if (!element || typeof element.getBoundingClientRect !== "function") {
        return false;
      }
      let rect = null;
      try {
        rect = element.getBoundingClientRect();
      } catch (_error) {
        rect = null;
      }
      if (!rect) {
        return false;
      }
      const viewportWidth = Number(globalThis.innerWidth || 0);
      const viewportHeight = Number(globalThis.innerHeight || 0);
      if (!Number.isFinite(viewportWidth) || !Number.isFinite(viewportHeight) || viewportWidth <= 0 || viewportHeight <= 0) {
        return false;
      }
      return rect.bottom > 0
        && rect.top < viewportHeight
        && rect.right > 0
        && rect.left < viewportWidth;
    }

    async function processTextNode(node, counter, processOptions) {
      const runOptions = processOptions && typeof processOptions === "object" ? processOptions : {};
      const trackCounters = Boolean(counter && runOptions.countCounters !== false);
      const semanticDryRun = runOptions.semanticDryRun === true;
      if (!node || !node.nodeValue) {
        if (trackCounters) counter.emptyNodes += 1;
        return;
      }
      const currentSettings = getCurrentSettings();
      const currentTrie = getCurrentTrie();
      const processedNodes = getProcessedNodes();
      if (!currentTrie || !currentSettings.enabled || !processedNodes || !buildReplacementFragment) {
        return;
      }
      if (trackCounters) {
        counter.totalNodes += 1;
      }
      if (/^\s+$/.test(node.nodeValue)) {
        if (trackCounters) {
          counter.whitespaceNodes += 1;
        }
        processedNodes.set(node, node.nodeValue);
        return;
      }
      const focusWord = trackCounters ? counter.focusWord : "";
      const focusEnabled = Boolean(focusWord);
      const focusInfo = focusEnabled
        ? getFocusInfo(node.nodeValue, focusWord)
        : { substring: false, token: false, index: -1 };
      if (trackCounters && focusInfo.substring) {
        counter.focusSubstringNodes += 1;
      }
      if (trackCounters && focusInfo.token) {
        counter.focusTokenNodes += 1;
      }
      if (isEditable(node)) {
        if (trackCounters) {
          counter.skippedEditable += 1;
          if (focusInfo.substring) {
            counter.focusSkippedEditable += 1;
          }
        }
        return;
      }
      if (isExcluded(node)) {
        if (trackCounters) {
          counter.skippedExcluded += 1;
          if (focusInfo.substring) {
            counter.focusSkippedExcluded += 1;
          }
        }
        return;
      }
      if (isLexiShiftNode(node)) {
        if (trackCounters) {
          counter.skippedLexi += 1;
          if (focusInfo.substring) {
            counter.focusSkippedLexi += 1;
          }
        }
        return;
      }
      const last = processedNodes.get(node);
      if (last === node.nodeValue) {
        if (trackCounters) {
          counter.skippedCached += 1;
          if (focusInfo.substring) {
            counter.focusSkippedCached += 1;
          }
        }
        return;
      }
      if (trackCounters) counter.scanned += 1;
      if (focusEnabled && focusInfo.substring && !focusInfo.token && trackCounters) {
        counter.focusSubstringNoToken += 1;
        if (currentSettings.debugEnabled && counter.focusDetailLogs < counter.focusDetailLimit) {
          const parent = node.parentElement;
          const snippet = describeCodepoints(node.nodeValue, focusInfo.index, focusWord.length);
          log(
            `Focus substring "${focusWord}" found but not token in ${describeElement(parent)}: "${snippet.snippet}"`,
            snippet.codes
          );
          counter.focusDetailLogs += 1;
        } else if (currentSettings.debugEnabled) {
          counter.focusDetailTruncated = true;
        }
      }
      const pageBudgetState = semanticDryRun
        ? (runOptions.semanticPreflightBudget || null)
        : getPageBudgetState();
      const scanStartedAtMs = counter && Number.isFinite(Number(counter.scanStartedAtMs))
        ? Number(counter.scanStartedAtMs)
        : nowMs();
      if (counter && !Number.isFinite(Number(counter.scanStartedAtMs))) {
        counter.scanStartedAtMs = scanStartedAtMs;
      }
      const originResolver = (rule) => {
        return String(rule && rule.metadata ? rule.metadata.lexishift_origin : "");
      };
      const needsSentenceContext = Boolean(
        pageBudgetState
        && Number(pageBudgetState.maxPerSentence || 0) > 0
      );
      const semanticContextResolver = semanticGateRuntime || needsSentenceContext
        ? createSemanticContextResolver(node, {
            nodeFilters,
            cache: getSemanticContextCache(counter)
          })
        : null;
      const replacementOptions = {};
      if (semanticDryRun) {
        replacementOptions.dryRun = true;
      }
      if (runOptions.semanticResultOverride) {
        replacementOptions.semanticResultOverride = runOptions.semanticResultOverride;
      }
      if (needsSentenceContext) {
        replacementOptions.sentenceFallbackKey = getSentenceFallbackKey(node);
      }
      const result = await buildReplacementFragment(
        node.nodeValue,
        currentTrie,
        currentSettings,
        (textNode) => {
          processedNodes.set(textNode, textNode.nodeValue);
        },
        originResolver,
        pageBudgetState,
        semanticGateRuntime,
        semanticContextResolver,
        Object.keys(replacementOptions).length ? replacementOptions : null
      );
      if (counter && result && result.semanticSummary) {
        mergeSemanticSummary(counter, result.semanticSummary);
      }
      if (semanticDryRun) {
        return result;
      }
      if (trackCounters && result && result.budgetRejections) {
        mergeBudgetRejections(counter, result.budgetRejections);
      }
      if (result && result.fragment) {
        const parent = node.parentNode;
        if (parent) {
          if (trackCounters && !Number.isFinite(Number(counter.firstReplacementLatencyMs))) {
            counter.firstReplacementLatencyMs = nowMs() - scanStartedAtMs;
            if (currentSettings.debugEnabled) {
              log(`First replacement applied after ${Number(counter.firstReplacementLatencyMs).toFixed(1)} ms.`);
            }
          }
          if (
            trackCounters
            && !Number.isFinite(Number(counter.firstVisibleReplacementLatencyMs))
            && isVisibleInViewport(parent)
          ) {
            counter.firstVisibleReplacementLatencyMs = nowMs() - scanStartedAtMs;
            if (currentSettings.debugEnabled) {
              log(
                `First visible replacement applied after ${Number(counter.firstVisibleReplacementLatencyMs).toFixed(1)} ms.`
              );
            }
          }
          parent.replaceChild(result.fragment, node);
          if (pageBudgetState) {
            const budgetEntries = Array.isArray(result.budgetEntries)
              ? result.budgetEntries
              : (Array.isArray(result.budgetKeys) ? result.budgetKeys : []);
            updatePageBudgetUsage(pageBudgetState, budgetEntries);
          }
          const shouldRecordLocalExposure = currentSettings.srsExposureLoggingEnabled !== false;
          const shouldRecordBrowsingAdmission = currentSettings.srsBrowsingAdmissionSignalsEnabled === true
            && browsingAdmissionSignals && typeof browsingAdmissionSignals.recordExposureBatch === "function";
          if (srsMetrics && (shouldRecordLocalExposure || shouldRecordBrowsingAdmission) && result.details && result.details.length) {
            const exposures = result.details.map((detail) =>
              srsMetrics.buildExposure(
                detail,
                normalizeRuleOrigin(detail.origin),
                window.location ? window.location.href : "",
                lemmatizer ? lemmatizer.lemmatize : null
              )
            );
            srsMetrics.recordExposureBatch(exposures, {
              browsingAdmissionSignals, log, recordLocalExposureLog: shouldRecordLocalExposure, settings: currentSettings
            }).then((saved) => {
              if (currentSettings.debugEnabled && saved && saved.length) log(`Recorded ${saved.length} exposure(s).`);
            });
          }
          if (popupModuleHistoryStore
            && typeof popupModuleHistoryStore.recordEncounterBatch === "function"
            && result.details
            && result.details.length
          ) {
            const profileId = normalizeProfileId(currentSettings.srsProfileId);
            const encounters = [];
            for (const detail of result.details) {
              const origin = normalizeRuleOrigin(detail.origin);
              if (origin !== "srs") {
                continue;
              }
              const pair = String(detail.language_pair || currentSettings.srsPair || "").trim().toLowerCase();
              if (!pair) {
                continue;
              }
              const targetLanguage = targetLanguageFromPair(pair);
              if (!isPopupModuleEnabled("encounter-history", currentSettings, targetLanguage)) {
                continue;
              }
              const replacement = String(detail.replacement || "").trim();
              if (!replacement) {
                continue;
              }
              const lemma = lemmatizer && typeof lemmatizer.lemmatize === "function"
                ? String(lemmatizer.lemmatize(replacement, pair) || replacement).trim().toLowerCase()
                : replacement.toLowerCase();
              if (!lemma) {
                continue;
              }
              encounters.push({
                profile_id: profileId,
                language_pair: pair,
                lemma,
                replacement,
                sentence_excerpt: String(detail.context_excerpt || ""),
                ts: new Date().toISOString(),
                word_package: detail.word_package || null
              });
            }
            if (encounters.length) {
              popupModuleHistoryStore.recordEncounterBatch(encounters).then((saved) => {
                if (currentSettings.debugEnabled && saved && saved.length) {
                  log(`Recorded ${saved.length} encounter(s).`);
                }
              });
            }
          }
          if (trackCounters) {
            counter.replacements += result.replacements;
            counter.nodes += 1;
            if (currentSettings.debugEnabled && result.details && result.details.length) {
              for (const detail of result.details) {
                if (counter.detailLogs >= counter.detailLimit) {
                  counter.detailTruncated = true;
                  break;
                }
                log(`Replaced "${detail.original}" -> "${detail.replacement}" in ${describeElement(parent)}`);
                counter.detailLogs += 1;
              }
            }
            if (focusEnabled && focusInfo.token) {
              const matchedFocus = result.details
                ? result.details.some((detail) => String(detail.source || "").toLowerCase() === focusWord)
                : false;
              if (matchedFocus) {
                counter.focusReplaced += 1;
              } else {
                counter.focusUnmatched += 1;
                if (currentSettings.debugEnabled && counter.focusDetailLogs < counter.focusDetailLimit) {
                  log(
                    `Focus word "${focusWord}" found but no matching rule in ${describeElement(parent)}: "${shorten(
                      node.nodeValue,
                      140
                    )}"`
                  );
                  counter.focusDetailLogs += 1;
                } else if (currentSettings.debugEnabled) {
                  counter.focusDetailTruncated = true;
                }
              }
            }
          }
        }
      } else {
        if (focusEnabled && focusInfo.token && trackCounters) {
          counter.focusUnmatched += 1;
          const semanticFiltered = Boolean(
            result
            && result.semanticSummary
            && Number(result.semanticSummary.eligible || 0) > 0
          );
          if (currentSettings.debugEnabled && counter.focusDetailLogs < counter.focusDetailLimit) {
            const parent = node.parentElement;
            log(
              semanticFiltered
                ? `Focus word "${focusWord}" matched lexically but semantic admission kept original in ${describeElement(parent)}: "${shorten(
                  node.nodeValue,
                  140
                )}"`
                : `Focus word "${focusWord}" found but no matching rule in ${describeElement(parent)}: "${shorten(
                  node.nodeValue,
                  140
                )}"`
            );
            counter.focusDetailLogs += 1;
          } else if (currentSettings.debugEnabled) {
            counter.focusDetailTruncated = true;
          }
        }
        processedNodes.set(node, node.nodeValue);
      }
    }

    const preflightSemanticTextNode = (node, counter, preflightOptions) => {
      const options = preflightOptions && typeof preflightOptions === "object" ? preflightOptions : {};
      return processTextNode(node, counter, {
        semanticDryRun: true,
        countCounters: false,
        semanticPreflightBudget: options.semanticPreflightBudget || null
      });
    };

    return {
      processTextNode,
      preflightSemanticTextNode
    };
  }

  root.contentDomScanTextNodeProcessor = {
    createTextNodeProcessor
  };
})();
