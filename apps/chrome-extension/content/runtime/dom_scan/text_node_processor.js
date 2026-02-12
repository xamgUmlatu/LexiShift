(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

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

    function processTextNode(node, counter) {
      if (!node || !node.nodeValue) {
        if (counter) counter.emptyNodes += 1;
        return;
      }
      const currentSettings = getCurrentSettings();
      const currentTrie = getCurrentTrie();
      const processedNodes = getProcessedNodes();
      if (!currentTrie || !currentSettings.enabled || !processedNodes || !buildReplacementFragment) {
        return;
      }
      if (counter) {
        counter.totalNodes += 1;
      }
      if (/^\s+$/.test(node.nodeValue)) {
        if (counter) {
          counter.whitespaceNodes += 1;
        }
        processedNodes.set(node, node.nodeValue);
        return;
      }
      const focusWord = counter ? counter.focusWord : "";
      const focusEnabled = Boolean(focusWord);
      const focusInfo = focusEnabled
        ? getFocusInfo(node.nodeValue, focusWord)
        : { substring: false, token: false, index: -1 };
      if (counter && focusInfo.substring) {
        counter.focusSubstringNodes += 1;
      }
      if (counter && focusInfo.token) {
        counter.focusTokenNodes += 1;
      }
      if (isEditable(node)) {
        if (counter) {
          counter.skippedEditable += 1;
          if (focusInfo.substring) {
            counter.focusSkippedEditable += 1;
          }
        }
        return;
      }
      if (isExcluded(node)) {
        if (counter) {
          counter.skippedExcluded += 1;
          if (focusInfo.substring) {
            counter.focusSkippedExcluded += 1;
          }
        }
        return;
      }
      if (isLexiShiftNode(node)) {
        if (counter) {
          counter.skippedLexi += 1;
          if (focusInfo.substring) {
            counter.focusSkippedLexi += 1;
          }
        }
        return;
      }
      const last = processedNodes.get(node);
      if (last === node.nodeValue) {
        if (counter) {
          counter.skippedCached += 1;
          if (focusInfo.substring) {
            counter.focusSkippedCached += 1;
          }
        }
        return;
      }
      if (counter) counter.scanned += 1;
      if (focusEnabled && focusInfo.substring && !focusInfo.token && counter) {
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
      const pageBudgetState = getPageBudgetState();
      const originResolver = (rule) => {
        return String(rule && rule.metadata ? rule.metadata.lexishift_origin : "");
      };
      const result = buildReplacementFragment(
        node.nodeValue,
        currentTrie,
        currentSettings,
        (textNode) => {
          processedNodes.set(textNode, textNode.nodeValue);
        },
        originResolver,
        pageBudgetState
      );
      if (result) {
        const parent = node.parentNode;
        if (parent) {
          parent.replaceChild(result.fragment, node);
          if (pageBudgetState) {
            updatePageBudgetUsage(pageBudgetState, Array.isArray(result.budgetKeys) ? result.budgetKeys : []);
          }
          if (srsMetrics
            && currentSettings.srsExposureLoggingEnabled !== false
            && result.details
            && result.details.length
          ) {
            const exposures = result.details.map((detail) =>
              srsMetrics.buildExposure(
                detail,
                normalizeRuleOrigin(detail.origin),
                window.location ? window.location.href : "",
                lemmatizer ? lemmatizer.lemmatize : null
              )
            );
            srsMetrics.recordExposureBatch(exposures).then((saved) => {
              if (currentSettings.debugEnabled && saved && saved.length) {
                log(`Recorded ${saved.length} exposure(s).`);
              }
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
                ts: new Date().toISOString()
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
          if (counter) {
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
        if (focusEnabled && focusInfo.token && counter) {
          counter.focusUnmatched += 1;
          if (currentSettings.debugEnabled && counter.focusDetailLogs < counter.focusDetailLimit) {
            const parent = node.parentElement;
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
        processedNodes.set(node, node.nodeValue);
      }
    }

    return {
      processTextNode
    };
  }

  root.contentDomScanTextNodeProcessor = {
    createTextNodeProcessor
  };
})();
