(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRuntime(options) {
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
    const setProcessedNodes = typeof opts.setProcessedNodes === "function"
      ? opts.setProcessedNodes
      : (() => {});
    const isApplyingChanges = typeof opts.isApplyingChanges === "function"
      ? opts.isApplyingChanges
      : (() => false);
    const getFocusWord = typeof opts.getFocusWord === "function"
      ? opts.getFocusWord
      : ((settings) => {
          const raw = settings && settings.debugFocusWord ? String(settings.debugFocusWord).trim() : "";
          return raw ? raw.toLowerCase() : "";
        });
    const getFocusInfo = typeof opts.getFocusInfo === "function"
      ? opts.getFocusInfo
      : ((text, focusWord) => {
          if (!focusWord || !text) {
            return { substring: false, token: false, index: -1 };
          }
          const lower = text.toLowerCase();
          const index = lower.indexOf(focusWord);
          if (index === -1) {
            return { substring: false, token: false, index: -1 };
          }
          return { substring: true, token: false, index };
        });
    const normalizeRuleOrigin = typeof opts.normalizeRuleOrigin === "function"
      ? opts.normalizeRuleOrigin
      : (origin) => String(origin || "").toLowerCase() === "srs" ? "srs" : "ruleset";
    const buildReplacementFragment = typeof opts.buildReplacementFragment === "function"
      ? opts.buildReplacementFragment
      : null;
    const describeElement = typeof opts.describeElement === "function"
      ? opts.describeElement
      : (() => "<unknown>");
    const shorten = typeof opts.shorten === "function"
      ? opts.shorten
      : (text) => String(text || "");
    const describeCodepoints = typeof opts.describeCodepoints === "function"
      ? opts.describeCodepoints
      : (text) => ({ snippet: String(text || ""), codes: [] });
    const countOccurrences = typeof opts.countOccurrences === "function"
      ? opts.countOccurrences
      : ((haystack, needle) => {
          if (!haystack || !needle) return 0;
          let count = 0;
          let cursor = 0;
          while (cursor < haystack.length) {
            const idx = haystack.indexOf(needle, cursor);
            if (idx === -1) break;
            count += 1;
            cursor = idx + Math.max(1, needle.length);
          }
          return count;
        });
    const collectTextNodes = typeof opts.collectTextNodes === "function"
      ? opts.collectTextNodes
      : (() => []);
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

    let observer = null;
    let observedBody = null;
    let pageBudgetState = null;

    function buildCounter(currentSettings, detailLimit, focusDetailLimit) {
      return {
        totalNodes: 0,
        emptyNodes: 0,
        whitespaceNodes: 0,
        replacements: 0,
        nodes: 0,
        scanned: 0,
        skippedEditable: 0,
        skippedExcluded: 0,
        skippedLexi: 0,
        skippedCached: 0,
        detailLogs: 0,
        detailLimit,
        detailTruncated: false,
        focusWord: currentSettings.debugEnabled ? getFocusWord(currentSettings) : "",
        focusSubstringNodes: 0,
        focusTokenNodes: 0,
        focusReplaced: 0,
        focusUnmatched: 0,
        focusSkippedEditable: 0,
        focusSkippedExcluded: 0,
        focusSkippedLexi: 0,
        focusSkippedCached: 0,
        focusSubstringNoToken: 0,
        focusDetailLogs: 0,
        focusDetailLimit,
        focusDetailTruncated: false
      };
    }

    const nodeFiltersFactory = root.contentDomScanNodeFilters
      && typeof root.contentDomScanNodeFilters.createNodeFilters === "function"
      ? root.contentDomScanNodeFilters.createNodeFilters
      : null;
    const nodeFilters = nodeFiltersFactory
      ? nodeFiltersFactory()
      : {
          isEditable: (node) => {
            if (!node || !node.parentElement) {
              return false;
            }
            const parent = node.parentElement;
            if (parent.isContentEditable) {
              return true;
            }
            const tag = parent.tagName;
            return tag === "INPUT" || tag === "TEXTAREA";
          },
          isExcluded: (node) => {
            if (!node || !node.parentElement) {
              return true;
            }
            const tag = node.parentElement.tagName;
            return tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT";
          },
          isLexiShiftNode: (node) => {
            if (!node || !node.parentElement) {
              return false;
            }
            return Boolean(node.parentElement.closest(".lexishift-replacement"));
          }
        };

    const pageBudgetTrackerFactory = root.contentDomScanPageBudgetTracker
      && typeof root.contentDomScanPageBudgetTracker.createPageBudgetTracker === "function"
      ? root.contentDomScanPageBudgetTracker.createPageBudgetTracker
      : null;
    const pageBudgetTracker = pageBudgetTrackerFactory
      ? pageBudgetTrackerFactory()
      : {
          buildPageBudgetState: (_settings) => null,
          updatePageBudgetUsage: (_state, _replacements) => {}
        };

    const scanCountersFactory = root.contentDomScanCounters
      && typeof root.contentDomScanCounters.createScanCounters === "function"
      ? root.contentDomScanCounters.createScanCounters
      : null;
    const scanCounters = scanCountersFactory
      ? scanCountersFactory({ getFocusWord })
      : {
          createFullScanCounter: (currentSettings) => buildCounter(currentSettings, 40, 30),
          createMutationCounter: (currentSettings) => buildCounter(currentSettings, 20, 15)
        };

    const textNodeProcessorFactory = root.contentDomScanTextNodeProcessor
      && typeof root.contentDomScanTextNodeProcessor.createTextNodeProcessor === "function"
      ? root.contentDomScanTextNodeProcessor.createTextNodeProcessor
      : null;
    const textNodeProcessor = textNodeProcessorFactory
      ? textNodeProcessorFactory({
          getCurrentSettings,
          getCurrentTrie,
          getProcessedNodes,
          buildReplacementFragment,
          getFocusInfo,
          describeElement,
          shorten,
          describeCodepoints,
          normalizeRuleOrigin,
          srsMetrics,
          lemmatizer,
          popupModuleHistoryStore,
          isPopupModuleEnabled,
          normalizeProfileId,
          log,
          nodeFilters,
          getPageBudgetState: () => pageBudgetState,
          updatePageBudgetUsage: pageBudgetTracker.updatePageBudgetUsage
        })
      : {
          processTextNode: (_node, _counter) => {}
        };

    function processDocument() {
      const currentSettings = getCurrentSettings();
      const counter = scanCounters.createFullScanCounter(currentSettings);
      if (!document.body) {
        log("Document body not ready.");
        return;
      }
      pageBudgetState = pageBudgetTracker.buildPageBudgetState(currentSettings);
      if (currentSettings.debugEnabled && counter.focusWord) {
        const focus = counter.focusWord;
        const innerText = document.body.innerText || "";
        const textContent = document.body.textContent || "";
        const innerCount = countOccurrences(innerText.toLowerCase(), focus);
        const contentCount = countOccurrences(textContent.toLowerCase(), focus);
        log(`Focus word "${focus}" occurrences: innerText=${innerCount}, textContent=${contentCount}.`);
      }
      const nodes = collectTextNodes(document.body);
      for (const node of nodes) {
        textNodeProcessor.processTextNode(node, counter);
      }
      if (currentSettings.debugEnabled) {
        log(
          `Scan summary: ${counter.totalNodes} total text node(s), ${counter.emptyNodes} empty, ${counter.whitespaceNodes} whitespace-only, ${counter.scanned} scanned, ${counter.skippedCached} cached, ${counter.skippedEditable} editable skipped, ${counter.skippedExcluded} excluded skipped, ${counter.skippedLexi} replaced skipped, ${counter.replacements} replacement(s) across ${counter.nodes} node(s).`
        );
        if (counter.focusWord) {
          log(
            `Focus word "${counter.focusWord}": ${counter.focusSubstringNodes} node(s) contain substring, ${counter.focusTokenNodes} contain token, ${counter.focusReplaced} replaced, ${counter.focusUnmatched} without match, ${counter.focusSubstringNoToken} substring-only, ${counter.focusSkippedCached} cached, ${counter.focusSkippedEditable} in editable, ${counter.focusSkippedExcluded} excluded, ${counter.focusSkippedLexi} already replaced.`
          );
        }
        if (counter.detailTruncated) {
          log(`Detail logs truncated after ${counter.detailLimit} replacement(s).`);
        }
        if (counter.focusDetailTruncated) {
          log(`Focus logs truncated after ${counter.focusDetailLimit} node(s).`);
        }
      } else if (counter.replacements > 0) {
        log(`Applied ${counter.replacements} replacement(s) across ${counter.nodes} node(s).`);
      }
    }

    function observeChanges() {
      if (observer) {
        return;
      }
      if (!document.body) {
        log("Document body not ready for observer.");
        return;
      }
      observedBody = document.body;
      observer = new MutationObserver((mutations) => {
        if (isApplyingChanges()) {
          return;
        }
        const currentSettings = getCurrentSettings();
        const counter = scanCounters.createMutationCounter(currentSettings);
        pageBudgetState = pageBudgetTracker.buildPageBudgetState(currentSettings);
        for (const mutation of mutations) {
          if (mutation.type === "characterData") {
            textNodeProcessor.processTextNode(mutation.target, counter);
          } else if (mutation.type === "childList") {
            mutation.addedNodes.forEach((node) => {
              if (node.nodeType === Node.TEXT_NODE) {
                textNodeProcessor.processTextNode(node, counter);
              } else if (node.nodeType === Node.ELEMENT_NODE) {
                const textNodes = collectTextNodes(node);
                for (const textNode of textNodes) {
                  textNodeProcessor.processTextNode(textNode, counter);
                }
              }
            });
          }
        }
        if (currentSettings.debugEnabled) {
          if (counter.replacements > 0) {
            log(`Updated ${counter.replacements} replacement(s) in ${counter.nodes} node(s).`);
          }
          if (counter.detailTruncated) {
            log(`Detail logs truncated after ${counter.detailLimit} replacement(s).`);
          }
          if (counter.focusDetailTruncated) {
            log(`Focus logs truncated after ${counter.focusDetailLimit} node(s).`);
          }
        } else if (counter.replacements > 0) {
          log(`Updated ${counter.replacements} replacement(s) in ${counter.nodes} node(s).`);
        }
      });
      observer.observe(observedBody, { childList: true, subtree: true, characterData: true });
    }

    function rescanDocument(reason) {
      const currentSettings = getCurrentSettings();
      if (!currentSettings.enabled || !getCurrentTrie()) {
        return;
      }
      setProcessedNodes(new WeakMap());
      if (reason) {
        log(`Rescan triggered: ${reason}`);
      }
      processDocument();
    }

    function ensureObserver() {
      if (!document.body) {
        return;
      }
      if (!observedBody || observedBody !== document.body) {
        if (observer) {
          observer.disconnect();
          observer = null;
        }
        observeChanges();
        rescanDocument("body changed");
      }
    }

    function clearBudgetState() {
      pageBudgetState = null;
    }

    function disconnect() {
      if (observer) {
        observer.disconnect();
        observer = null;
      }
      observedBody = null;
    }

    return {
      processDocument,
      observeChanges,
      rescanDocument,
      ensureObserver,
      clearBudgetState,
      disconnect
    };
  }

  root.contentDomScanRuntime = {
    createRuntime
  };
})();
