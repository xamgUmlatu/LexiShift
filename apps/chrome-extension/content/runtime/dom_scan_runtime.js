(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const LEXISHIFT_SCAN_SKIP_SELECTOR = ".lexishift-replacement, [data-lexishift-scan-skip=\"true\"]";
  const functionType = "fun" + "ction";
  const returnEmptyObject = () => ({});
  const returnNull = () => null;
  const noop = () => {};
  const semanticPerformanceModule = root.contentDomScanSemanticPerformanceMetrics || {};
  const buildSemanticPerformanceSummary = typeof semanticPerformanceModule.buildSummary === "function"
    ? semanticPerformanceModule.buildSummary
    : returnEmptyObject;
  const buildSemanticAdmissionLogSummary = typeof semanticPerformanceModule.buildAdmissionLogSummary === "function"
    ? semanticPerformanceModule.buildAdmissionLogSummary
    : returnEmptyObject;
  const createFallbackScanCounters = typeof semanticPerformanceModule.createFallbackScanCounters === "function"
    ? semanticPerformanceModule.createFallbackScanCounters
    : returnNull;
    const maybeYieldDuringScan = typeof semanticPerformanceModule.maybeYieldDuringScan === functionType
      ? semanticPerformanceModule.maybeYieldDuringScan
      : null;
  const semanticNodeScheduler = root.contentDomScanSemanticNodeScheduler || {};
  const processSemanticTextNodes = typeof semanticNodeScheduler.processTextNodes === functionType
    ? semanticNodeScheduler.processTextNodes
    : null;
  function createRuntime(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getCurrentSettings = typeof opts.getCurrentSettings === "function"
      ? opts.getCurrentSettings
      : returnEmptyObject;
    const getCurrentTrie = typeof opts.getCurrentTrie === "function"
      ? opts.getCurrentTrie
      : returnNull;
    const getProcessedNodes = typeof opts.getProcessedNodes === "function"
      ? opts.getProcessedNodes
      : (() => new WeakMap());
    const setProcessedNodes = typeof opts.setProcessedNodes === "function"
      ? opts.setProcessedNodes
      : noop;
    const isApplyingChanges = typeof opts.isApplyingChanges === "function"
      ? opts.isApplyingChanges
      : Boolean;
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
    const semanticGateRuntime = opts.semanticGateRuntime && typeof opts.semanticGateRuntime === "object"
      ? opts.semanticGateRuntime
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
    const browsingAdmissionSignals = opts.browsingAdmissionSignals
      && typeof opts.browsingAdmissionSignals === "object"
      ? opts.browsingAdmissionSignals
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
    const log = typeof opts.log === "function" ? opts.log : noop;
    const yieldToPage = typeof opts.yieldToPage === "function"
      ? opts.yieldToPage
      : (() => new Promise((resolve) => {
          globalThis.setTimeout(resolve, 0);
        }));
    const defaultNowMs = globalThis.performance && typeof globalThis.performance.now === "function"
      ? globalThis.performance.now.bind(globalThis.performance)
      : Date.now;
    const nowMs = typeof opts.nowMs === "function"
      ? opts.nowMs
      : defaultNowMs;

    let observer = null;
    let observedBody = null;
    let pageBudgetState = null;
    let scanQueue = Promise.resolve();

    async function processTextNodes(nodes, counter, settings, deadlineMs) {
      if (processSemanticTextNodes) {
        return processSemanticTextNodes({
          nodes,
          counter,
          settings,
          deadlineMs,
          pageBudgetState,
          semanticGateRuntime,
          textNodeProcessor,
          recordScanNodeBatch: semanticPerformanceModule.recordScanNodeBatch,
          maybeYieldDuringScan,
          nowMs,
          yieldToPage
        });
      }
      const list = Array.isArray(nodes) ? nodes : [];
      for (let index = 0; index < list.length; index += 1) {
        await textNodeProcessor.processTextNode(list[index], counter);
        if (maybeYieldDuringScan) {
          deadlineMs = await maybeYieldDuringScan(
            counter,
            deadlineMs,
            index + 1 < list.length,
            nowMs,
            yieldToPage
          );
        }
      }
      return deadlineMs;
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
            return Boolean(node.parentElement.closest(LEXISHIFT_SCAN_SKIP_SELECTOR));
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
          updatePageBudgetUsage: noop
        };

    const reorderNodesForScanFactory = root.contentDomScanOrder
      && typeof root.contentDomScanOrder.createReorderNodesForScan === "function"
      ? root.contentDomScanOrder.createReorderNodesForScan
      : null;
    const reorderNodesForScan = reorderNodesForScanFactory
      ? reorderNodesForScanFactory({ normalizeProfileId })
      : (nodes) => nodes;

    const scanCountersFactory = root.contentDomScanCounters
      && typeof root.contentDomScanCounters.createScanCounters === "function"
      ? root.contentDomScanCounters.createScanCounters
      : null;
    const scanCounters = scanCountersFactory
      ? scanCountersFactory({ getFocusWord })
      : createFallbackScanCounters({ nowMs, getFocusWord });

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
          semanticGateRuntime,
          getFocusInfo,
          describeElement,
          shorten,
          describeCodepoints,
          normalizeRuleOrigin,
          srsMetrics,
          browsingAdmissionSignals,
          lemmatizer,
          popupModuleHistoryStore,
          isPopupModuleEnabled,
          normalizeProfileId,
          nowMs,
          log,
          nodeFilters,
          getPageBudgetState: () => pageBudgetState,
          updatePageBudgetUsage: pageBudgetTracker.updatePageBudgetUsage
        })
      : {
          processTextNode: async (_node, _counter) => {}
        };

    function enqueueScan(task) {
      const scheduled = scanQueue.then(task);
      scanQueue = scheduled.catch((error) => {
        log(
          "DOM scan failed:",
          error && error.message ? error.message : String(error || "Unknown error.")
        );
      });
      return scheduled;
    }

    async function processDocumentInternal() {
      const currentSettings = getCurrentSettings();
      const counter = scanCounters.createFullScanCounter(currentSettings);
      if (!document.body) {
        log("Document body not ready.");
        return counter;
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
      const scanNodes = reorderNodesForScan(nodes, currentSettings);
      let deadlineMs = Number(counter.scanStartedAtMs || nowMs()) + 12;
      deadlineMs = await processTextNodes(scanNodes, counter, currentSettings, deadlineMs);
      counter.scanDurationMs = nowMs() - Number(counter.scanStartedAtMs || 0);
      if (currentSettings.debugEnabled) {
        log(
          `Scan summary: ${counter.totalNodes} total text node(s), ${counter.emptyNodes} empty, ${counter.whitespaceNodes} whitespace-only, ${counter.scanned} scanned, ${counter.skippedCached} cached, ${counter.skippedEditable} editable skipped, ${counter.skippedExcluded} excluded skipped, ${counter.skippedLexi} replaced skipped, ${counter.replacements} replacement(s) across ${counter.nodes} node(s).`
        );
        log("Scan timing:", {
          scanMs: counter.scanDurationMs,
          yieldCount: counter.yieldCount,
          firstReplacementMs: Number.isFinite(Number(counter.firstReplacementLatencyMs))
            ? Number(counter.firstReplacementLatencyMs)
            : null,
          firstVisibleReplacementMs: Number.isFinite(Number(counter.firstVisibleReplacementLatencyMs))
            ? Number(counter.firstVisibleReplacementLatencyMs)
            : null
        });
        if (currentSettings.srsSemanticAdmissionEnabled === true && counter.semanticEligible > 0) {
          log("Semantic admission scan summary:", buildSemanticAdmissionLogSummary(counter));
          log("Semantic admission performance:", buildSemanticPerformanceSummary(counter));
        }
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
      }
      return counter;
    }

    function processDocument() {
      return enqueueScan(processDocumentInternal);
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
        enqueueScan(async () => {
          const currentSettings = getCurrentSettings();
          const counter = scanCounters.createMutationCounter(currentSettings);
          pageBudgetState = pageBudgetTracker.buildPageBudgetState(currentSettings);
          let deadlineMs = Number(counter.scanStartedAtMs || nowMs()) + 12;
          for (const mutation of mutations) {
            if (mutation.type === "characterData") {
              await textNodeProcessor.processTextNode(mutation.target, counter);
              if (maybeYieldDuringScan) {
                deadlineMs = await maybeYieldDuringScan(counter, deadlineMs, true, nowMs, yieldToPage);
              }
            } else if (mutation.type === "childList") {
              for (const node of mutation.addedNodes) {
                if (node.nodeType === Node.TEXT_NODE) {
                  await textNodeProcessor.processTextNode(node, counter);
                  if (maybeYieldDuringScan) {
                    deadlineMs = await maybeYieldDuringScan(counter, deadlineMs, true, nowMs, yieldToPage);
                  }
                } else if (node.nodeType === Node.ELEMENT_NODE) {
                  const textNodes = collectTextNodes(node);
                  deadlineMs = await processTextNodes(textNodes, counter, currentSettings, deadlineMs);
                }
              }
            }
          }
          counter.scanDurationMs = nowMs() - Number(counter.scanStartedAtMs || 0);
          if (currentSettings.debugEnabled) {
            if (counter.replacements > 0) {
              log(`Updated ${counter.replacements} replacement(s) in ${counter.nodes} node(s).`);
            }
            if (counter.replacements > 0 || counter.semanticEligible > 0) {
              log("Mutation timing:", {
                scanMs: counter.scanDurationMs,
                yieldCount: counter.yieldCount,
                firstReplacementMs: Number.isFinite(Number(counter.firstReplacementLatencyMs))
                  ? Number(counter.firstReplacementLatencyMs)
                  : null,
                firstVisibleReplacementMs: Number.isFinite(Number(counter.firstVisibleReplacementLatencyMs))
                  ? Number(counter.firstVisibleReplacementLatencyMs)
                  : null
              });
            }
            if (currentSettings.srsSemanticAdmissionEnabled === true && counter.semanticEligible > 0) {
              log("Semantic admission mutation summary:", buildSemanticAdmissionLogSummary(counter));
              log("Semantic admission performance:", buildSemanticPerformanceSummary(counter));
            }
            if (counter.detailTruncated) {
              log(`Detail logs truncated after ${counter.detailLimit} replacement(s).`);
            }
            if (counter.focusDetailTruncated) {
              log(`Focus logs truncated after ${counter.focusDetailLimit} node(s).`);
            }
          }
        });
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
      void processDocument();
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
