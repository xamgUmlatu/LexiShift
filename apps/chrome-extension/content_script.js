(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const defaults = root.defaults || {
    enabled: true,
    rules: [],
    highlightEnabled: true,
    highlightColor: "#9AA0A6",
    maxOnePerTextBlock: false,
    allowAdjacentReplacements: true,
    debugEnabled: false,
    debugFocusWord: ""
  };

  if (!root.tokenizer || !root.matcher || !root.replacements || !root.ui || !root.utils) {
    console.warn("[LexiShift] Content modules not loaded.");
    return;
  }

  const { textHasToken } = root.tokenizer;
  const { buildTrie, normalizeRules } = root.matcher;
  const { buildReplacementFragment } = root.replacements;
  const { ensureStyle, applyHighlightToDom, clearReplacements, attachClickListener } = root.ui;
  const { describeElement, shorten, describeCodepoints, countOccurrences, collectTextNodes } = root.utils;

  let processedNodes = new WeakMap();
  let currentSettings = { ...defaults };
  let currentTrie = null;
  let observer = null;
  let applyingChanges = false;
  let observedBody = null;

  function log(...args) {
    if (!currentSettings.debugEnabled) {
      return;
    }
    console.log("[LexiShift]", ...args);
  }

  function getFrameInfo() {
    let frameType = "top";
    try {
      if (window.top && window.top !== window) {
        frameType = "iframe";
      }
    } catch (error) {
      frameType = "iframe";
    }
    let topHref = "";
    try {
      topHref = window.top ? window.top.location.href : "";
    } catch (error) {
      topHref = "[cross-origin]";
    }
    return {
      frameType,
      href: window.location ? window.location.href : "",
      topHref
    };
  }

  function getFocusWord(settings) {
    const raw = settings && settings.debugFocusWord ? String(settings.debugFocusWord).trim() : "";
    return raw ? raw.toLowerCase() : "";
  }

  function getFocusInfo(text, focusWord) {
    if (!focusWord || !text) {
      return { substring: false, token: false, index: -1 };
    }
    const lower = text.toLowerCase();
    const index = lower.indexOf(focusWord);
    if (index === -1) {
      return { substring: false, token: false, index: -1 };
    }
    return { substring: true, token: textHasToken(text, focusWord), index };
  }

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

  function processTextNode(node, counter) {
    if (!node || !node.nodeValue) {
      if (counter) counter.emptyNodes += 1;
      return;
    }
    if (!currentTrie || !currentSettings.enabled) {
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
    const result = buildReplacementFragment(node.nodeValue, currentTrie, currentSettings, (textNode) => {
      processedNodes.set(textNode, textNode.nodeValue);
    });
    if (result) {
      const parent = node.parentNode;
      if (parent) {
        parent.replaceChild(result.fragment, node);
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
      if (applyingChanges) {
        return;
      }
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
    if (!currentSettings.enabled || !currentTrie) {
      return;
    }
    processedNodes = new WeakMap();
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

  function applySettings(settings) {
    currentSettings = { ...defaults, ...settings };
    processedNodes = new WeakMap();
    const normalizedRules = normalizeRules(currentSettings.rules);
    const enabledRules = normalizedRules.filter((rule) => rule.enabled !== false);
    const focusWord = getFocusWord(currentSettings);
    const focusRules = focusWord
      ? enabledRules.filter((rule) => String(rule.source_phrase || "").toLowerCase() === focusWord)
      : [];
    log("Settings loaded.", {
      enabled: currentSettings.enabled,
      rules: normalizedRules.length,
      enabledRules: enabledRules.length,
      highlightEnabled: currentSettings.highlightEnabled,
      highlightColor: currentSettings.highlightColor,
      maxOnePerTextBlock: currentSettings.maxOnePerTextBlock,
      allowAdjacentReplacements: currentSettings.allowAdjacentReplacements,
      debugEnabled: currentSettings.debugEnabled,
      debugFocusWord: focusWord || ""
    });
    if (currentSettings.debugEnabled) {
      log("Context info:", Object.assign({ readyState: document.readyState }, getFrameInfo()));
      if (document.body) {
        log("Body info:", {
          childElements: document.body.childElementCount,
          textLength: document.body.innerText ? document.body.innerText.length : 0
        });
      }
    }
    if (!normalizedRules.length) {
      log("No rules loaded.");
    }
    if (focusWord && !focusRules.length) {
      log(`No enabled rule found for focus word "${focusWord}".`);
    }
    ensureStyle(currentSettings.highlightColor || defaults.highlightColor);
    attachClickListener();
    applyHighlightToDom(currentSettings.highlightEnabled);

    applyingChanges = true;
    try {
      clearReplacements();
      if (!currentSettings.enabled) {
        currentTrie = null;
        log("Replacements are disabled.");
        return;
      }
      currentTrie = buildTrie(normalizedRules);
      processDocument();
    } finally {
      applyingChanges = false;
    }
  }

  function loadSettings() {
    return new Promise((resolve) => {
      chrome.storage.local.get(defaults, (items) => resolve(items));
    });
  }

  async function boot() {
    const settings = await loadSettings();
    applySettings(settings);
    observeChanges();
    window.addEventListener("load", () => {
      ensureObserver();
      rescanDocument("window load");
    });
    setTimeout(() => {
      ensureObserver();
      rescanDocument("post-load timeout");
    }, 1500);
  }

  boot();

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") {
      return;
    }
    const nextSettings = { ...currentSettings };
    let needsRebuild = false;
    let needsHighlight = false;

    if (changes.enabled) {
      nextSettings.enabled = changes.enabled.newValue;
      needsRebuild = true;
    }
    if (changes.rules) {
      nextSettings.rules = changes.rules.newValue;
      needsRebuild = true;
    }
    if (changes.highlightEnabled) {
      nextSettings.highlightEnabled = changes.highlightEnabled.newValue;
      needsHighlight = true;
    }
    if (changes.highlightColor) {
      nextSettings.highlightColor = changes.highlightColor.newValue;
      needsHighlight = true;
    }
    if (changes.maxOnePerTextBlock) {
      nextSettings.maxOnePerTextBlock = changes.maxOnePerTextBlock.newValue;
      needsRebuild = true;
    }
    if (changes.allowAdjacentReplacements) {
      nextSettings.allowAdjacentReplacements = changes.allowAdjacentReplacements.newValue;
      needsRebuild = true;
    }
    if (changes.debugEnabled) {
      nextSettings.debugEnabled = changes.debugEnabled.newValue;
      currentSettings = { ...currentSettings, ...nextSettings };
      log("Debug logging enabled.");
    }
    if (changes.debugFocusWord) {
      nextSettings.debugFocusWord = changes.debugFocusWord.newValue;
      currentSettings = { ...currentSettings, ...nextSettings };
      const focusWord = getFocusWord(currentSettings);
      if (focusWord) {
        log(`Debug focus word set to "${focusWord}".`);
      } else {
        log("Debug focus word cleared.");
      }
    }

    if (needsHighlight) {
      currentSettings = { ...currentSettings, ...nextSettings };
      ensureStyle(currentSettings.highlightColor || defaults.highlightColor);
      applyHighlightToDom(currentSettings.highlightEnabled);
    }
    if (needsRebuild) {
      applySettings(nextSettings);
    }
  });
})();
