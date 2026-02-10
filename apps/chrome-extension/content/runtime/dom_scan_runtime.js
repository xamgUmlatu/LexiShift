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
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    let observer = null;
    let observedBody = null;
    let pageBudgetState = null;

    function isEditable(node) {
      if (!node || !node.parentElement) {
        return false;
      }
      const parent = node.parentElement;
      if (parent.isContentEditable) {
        return true;
      }
      const tag = parent.tagName;
      return tag === "INPUT" || tag === "TEXTAREA";
    }

    function isExcluded(node) {
      if (!node || !node.parentElement) {
        return true;
      }
      const tag = node.parentElement.tagName;
      return tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT";
    }

    function isLexiShiftNode(node) {
      if (!node || !node.parentElement) {
        return false;
      }
      return Boolean(node.parentElement.closest(".lexishift-replacement"));
    }

    function toBudgetLimit(value, fallback) {
      const parsed = Number.parseInt(value, 10);
      if (!Number.isFinite(parsed)) {
        return Math.max(0, fallback || 0);
      }
      return Math.max(0, parsed);
    }

    function getBudgetLemmaKey(value) {
      return String(value || "").trim().toLowerCase();
    }

    function buildPageBudgetState(settings) {
      const maxTotal = toBudgetLimit(settings.maxReplacementsPerPage, 0);
      const maxPerLemma = toBudgetLimit(settings.maxReplacementsPerLemmaPerPage, 0);
      if (maxTotal <= 0 && maxPerLemma <= 0) {
        return null;
      }
      const state = {
        maxTotal,
        maxPerLemma,
        usedTotal: 0,
        usedByLemma: Object.create(null)
      };
      const existing = document.querySelectorAll(".lexishift-replacement");
      for (const span of existing) {
        const key = getBudgetLemmaKey(span.dataset.replacement || span.textContent || "");
        if (!key) {
          continue;
        }
        state.usedTotal += 1;
        state.usedByLemma[key] = Number(state.usedByLemma[key] || 0) + 1;
      }
      return state;
    }

    function updatePageBudgetUsage(state, replacements) {
      if (!state || !replacements || !replacements.length) {
        return;
      }
      for (const replacement of replacements) {
        const key = getBudgetLemmaKey(replacement);
        if (!key) {
          continue;
        }
        state.usedTotal += 1;
        state.usedByLemma[key] = Number(state.usedByLemma[key] || 0) + 1;
      }
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
      const originResolver = (rule) => {
        return String(rule && rule.metadata ? rule.metadata.lexishift_origin : "");
      };
      const result = buildReplacementFragment(node.nodeValue, currentTrie, currentSettings, (textNode) => {
        processedNodes.set(textNode, textNode.nodeValue);
      }, originResolver, pageBudgetState);
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

    function processDocument() {
      const currentSettings = getCurrentSettings();
      const counter = {
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
        detailLimit: 40,
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
        focusDetailLimit: 30,
        focusDetailTruncated: false
      };
      if (!document.body) {
        log("Document body not ready.");
        return;
      }
      pageBudgetState = buildPageBudgetState(currentSettings);
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
        processTextNode(node, counter);
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
        const counter = {
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
          detailLimit: 20,
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
          focusDetailLimit: 15,
          focusDetailTruncated: false
        };
        pageBudgetState = buildPageBudgetState(currentSettings);
        for (const mutation of mutations) {
          if (mutation.type === "characterData") {
            processTextNode(mutation.target, counter);
          } else if (mutation.type === "childList") {
            mutation.addedNodes.forEach((node) => {
              if (node.nodeType === Node.TEXT_NODE) {
                processTextNode(node, counter);
              } else if (node.nodeType === Node.ELEMENT_NODE) {
                const textNodes = collectTextNodes(node);
                for (const textNode of textNodes) {
                  processTextNode(textNode, counter);
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
