(() => {
  const TOKEN_RE = /[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*|\s+|[^\w\s]+/g;
  const WORD_RE = /^[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*$/;
  const STYLE_ID = "lexishift-style";

  const DEFAULT_SETTINGS = {
    enabled: true,
    rules: [],
    highlightEnabled: true,
    highlightColor: "#9AA0A6",
    debugEnabled: false,
    debugFocusWord: ""
  };

  let processedNodes = new WeakMap();
  let currentSettings = { ...DEFAULT_SETTINGS };
  let currentTrie = null;
  let observer = null;
  let applyingChanges = false;
  let clickListenerAttached = false;
  let observedBody = null;

  function tokenize(text) {
    const tokens = [];
    const matches = text.matchAll(TOKEN_RE);
    for (const match of matches) {
      const chunk = match[0];
      let kind = "punct";
      if (WORD_RE.test(chunk)) {
        kind = "word";
      } else if (/^\s+$/.test(chunk)) {
        kind = "space";
      }
      tokens.push({ text: chunk, kind });
    }
    return tokens;
  }

  function normalize(word) {
    return word.toLowerCase();
  }

  function buildTrie(rules) {
    const root = { children: Object.create(null), bestRule: null };
    for (const rule of rules) {
      if (rule.enabled === false) {
        continue;
      }
      const words = tokenize(rule.source_phrase || "").filter((t) => t.kind === "word");
      if (!words.length) {
        continue;
      }
      let node = root;
      for (const word of words) {
        const key = normalize(word.text);
        node.children[key] = node.children[key] || { children: Object.create(null), bestRule: null };
        node = node.children[key];
      }
      if (!node.bestRule || rule.priority > node.bestRule.priority) {
        node.bestRule = rule;
      }
    }
    return root;
  }

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

  function textHasToken(text, token) {
    if (!text || !token) {
      return false;
    }
    const tokens = tokenize(text);
    return tokens.some((item) => item.kind === "word" && item.text.toLowerCase() === token);
  }

  function computeGapOk(tokens, wordPositions) {
    const gapOk = [];
    for (let i = 0; i < wordPositions.length - 1; i += 1) {
      const start = wordPositions[i] + 1;
      const end = wordPositions[i + 1];
      let ok = true;
      for (let j = start; j < end; j += 1) {
        if (tokens[j].kind !== "space") {
          ok = false;
          break;
        }
      }
      gapOk.push(ok);
    }
    return gapOk;
  }

  function applyCase(replacement, sourceWords, policy) {
    if (policy === "as-is") {
      return replacement;
    }
    if (policy === "lower") {
      return replacement.toLowerCase();
    }
    if (policy === "upper") {
      return replacement.toUpperCase();
    }
    if (policy === "title") {
      return replacement.replace(/\b\w/g, (m) => m.toUpperCase());
    }
    if (policy === "match") {
      const sourceText = sourceWords.join(" ");
      if (sourceText === sourceText.toUpperCase()) {
        return replacement.toUpperCase();
      }
      if (sourceWords.length && sourceWords[0][0] && sourceWords[0][0] === sourceWords[0][0].toUpperCase()) {
        return replacement.replace(/\b\w/g, (m) => m.toUpperCase());
      }
    }
    return replacement;
  }

  function findLongestMatch(trie, words, gapOk, startIndex) {
    let node = trie;
    let bestRule = null;
    let bestEnd = null;
    let bestPriority = -1;

    for (let idx = startIndex; idx < words.length; idx += 1) {
      if (idx > startIndex && !gapOk[idx - 1]) {
        break;
      }
      const normalized = normalize(words[idx]);
      node = node.children[normalized];
      if (!node) {
        break;
      }
      if (node.bestRule && node.bestRule.priority >= bestPriority) {
        if (node.bestRule.priority > bestPriority || bestEnd === null || idx > bestEnd) {
          bestRule = node.bestRule;
          bestEnd = idx;
          bestPriority = node.bestRule.priority;
        }
      }
    }

    if (!bestRule || bestEnd === null) {
      return null;
    }
    return { startWordIndex: startIndex, endWordIndex: bestEnd, rule: bestRule };
  }

  function createReplacementSpan(originalText, replacementText, highlightEnabled) {
    const span = document.createElement("span");
    span.className = "lexishift-replacement";
    if (highlightEnabled) {
      span.classList.add("lexishift-highlight");
    }
    span.textContent = replacementText;
    span.dataset.original = originalText;
    span.dataset.replacement = replacementText;
    span.dataset.state = "replacement";
    span.title = "Click to toggle original";
    return span;
  }

  function buildReplacementFragment(text, trie, settings, onTextNode) {
    const trackDetails = settings.debugEnabled === true;
    const details = trackDetails ? [] : null;
    const tokens = tokenize(text);
    const wordPositions = [];
    const wordTexts = [];
    tokens.forEach((token, idx) => {
      if (token.kind === "word") {
        wordPositions.push(idx);
        wordTexts.push(token.text);
      }
    });
    if (!wordPositions.length) {
      return null;
    }
    const gapOk = computeGapOk(tokens, wordPositions);
    const matches = [];
    let wordIndex = 0;
    while (wordIndex < wordTexts.length) {
      const match = findLongestMatch(trie, wordTexts, gapOk, wordIndex);
      if (match) {
        matches.push(match);
        wordIndex = match.endWordIndex + 1;
      } else {
        wordIndex += 1;
      }
    }

    if (!matches.length) {
      return null;
    }

    const fragment = document.createDocumentFragment();
    let tokenCursor = 0;
    for (const match of matches) {
      const startTokenIdx = wordPositions[match.startWordIndex];
      const endTokenIdx = wordPositions[match.endWordIndex];
      if (startTokenIdx > tokenCursor) {
        const chunk = tokens.slice(tokenCursor, startTokenIdx).map((t) => t.text).join("");
        if (chunk) {
          const textNode = document.createTextNode(chunk);
          fragment.appendChild(textNode);
          if (onTextNode) onTextNode(textNode);
        }
      }
      const sourceWords = wordTexts.slice(match.startWordIndex, match.endWordIndex + 1);
      const originalText = tokens.slice(startTokenIdx, endTokenIdx + 1).map((t) => t.text).join("");
      const replacementText = applyCase(match.rule.replacement, sourceWords, match.rule.case_policy || "match");
      fragment.appendChild(createReplacementSpan(originalText, replacementText, settings.highlightEnabled));
      if (details) {
        details.push({
          original: originalText,
          replacement: replacementText,
          source: match.rule.source_phrase || "",
          priority: match.rule.priority,
          case_policy: match.rule.case_policy || "match"
        });
      }
      tokenCursor = endTokenIdx + 1;
    }
    if (tokenCursor < tokens.length) {
      const tail = tokens.slice(tokenCursor).map((t) => t.text).join("");
      if (tail) {
        const textNode = document.createTextNode(tail);
        fragment.appendChild(textNode);
        if (onTextNode) onTextNode(textNode);
      }
    }
    return { fragment, replacements: matches.length, details };
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
    const focusInfo = focusEnabled ? getFocusInfo(node.nodeValue, focusWord) : { substring: false, token: false, index: -1 };
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
          `Focus substring \"${focusWord}\" found but not token in ${describeElement(parent)}: \"${snippet.snippet}\"`,
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
              log(
                `Replaced \"${detail.original}\" -> \"${detail.replacement}\" in ${describeElement(parent)}`
              );
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
                  `Focus word \"${focusWord}\" found but no matching rule in ${describeElement(parent)}: \"${shorten(node.nodeValue, 140)}\"`
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
          log(`Focus word \"${focusWord}\" found but no matching rule in ${describeElement(parent)}: \"${shorten(node.nodeValue, 140)}\"`);
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
      log(`Focus word \"${focus}\" occurrences: innerText=${innerCount}, textContent=${contentCount}.`);
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
          `Focus word \"${counter.focusWord}\": ${counter.focusSubstringNodes} node(s) contain substring, ${counter.focusTokenNodes} contain token, ${counter.focusReplaced} replaced, ${counter.focusUnmatched} without match, ${counter.focusSubstringNoToken} substring-only, ${counter.focusSkippedCached} cached, ${counter.focusSkippedEditable} in editable, ${counter.focusSkippedExcluded} excluded, ${counter.focusSkippedLexi} already replaced.`
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

  function ensureStyle(color) {
    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement("style");
      style.id = STYLE_ID;
      const parent = document.head || document.documentElement;
      if (parent) {
        parent.appendChild(style);
      }
    }
    style.textContent = `:root{--lexishift-highlight-color:${color};}.lexishift-replacement{cursor:pointer;transition:color 120ms ease;}.lexishift-replacement.lexishift-highlight{color:var(--lexishift-highlight-color);}`;
  }

  function applyHighlightToDom() {
    const highlight = currentSettings.highlightEnabled !== false;
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      if (highlight) {
        node.classList.add("lexishift-highlight");
      } else {
        node.classList.remove("lexishift-highlight");
      }
    });
  }

  function clearReplacements() {
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      const original = node.dataset.original || node.textContent || "";
      node.replaceWith(document.createTextNode(original));
    });
  }

  function attachClickListener() {
    if (clickListenerAttached) {
      return;
    }
    document.addEventListener("click", (event) => {
      const target = event.target && event.target.closest ? event.target.closest(".lexishift-replacement") : null;
      if (!target) {
        return;
      }
      const state = target.dataset.state || "replacement";
      if (state === "replacement") {
        target.textContent = target.dataset.original || target.textContent;
        target.dataset.state = "original";
      } else {
        target.textContent = target.dataset.replacement || target.textContent;
        target.dataset.state = "replacement";
      }
    });
    clickListenerAttached = true;
  }

  function describeElement(element) {
    if (!element || !element.tagName) {
      return "<unknown>";
    }
    const parts = [];
    let current = element;
    let depth = 0;
    while (current && depth < 3) {
      let label = current.tagName.toLowerCase();
      if (current.id) {
        label += `#${current.id}`;
      }
      const className = current.className && typeof current.className === "string" ? current.className.trim() : "";
      if (className) {
        const classes = className.split(/\\s+/).slice(0, 2).join(".");
        if (classes) {
          label += `.${classes}`;
        }
      }
      parts.unshift(label);
      current = current.parentElement;
      depth += 1;
    }
    return parts.join(" > ");
  }

  function shorten(text, maxLength) {
    const value = String(text || "");
    if (!maxLength || value.length <= maxLength) {
      return value;
    }
    return `${value.slice(0, maxLength - 3)}...`;
  }

  function describeCodepoints(text, index, length) {
    const value = String(text || "");
    if (!value) {
      return { snippet: "", codes: [] };
    }
    const safeIndex = Math.max(0, Number.isFinite(index) ? index : 0);
    const safeLength = Math.max(1, Number.isFinite(length) ? length : 1);
    const start = Math.max(0, safeIndex - 6);
    const end = Math.min(value.length, safeIndex + safeLength + 6);
    const snippet = value.slice(start, end);
    const codes = Array.from(snippet).map((ch) => {
      const hex = ch.codePointAt(0).toString(16).toUpperCase();
      return `${ch} U+${hex}`;
    });
    return { snippet, codes };
  }

  function countOccurrences(haystack, needle) {
    if (!needle) {
      return 0;
    }
    let count = 0;
    let index = 0;
    while (true) {
      const found = haystack.indexOf(needle, index);
      if (found === -1) {
        break;
      }
      count += 1;
      index = found + needle.length;
    }
    return count;
  }

  function collectTextNodes(root) {
    const nodes = [];
    if (!root) {
      return nodes;
    }
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      nodes.push(node);
      node = walker.nextNode();
    }
    return nodes;
  }

  function normalizeRules(rules) {
    return (rules || []).map((rule) => ({
      source_phrase: String(rule.source_phrase || ""),
      replacement: String(rule.replacement || ""),
      priority: Number.isFinite(rule.priority) ? rule.priority : 0,
      case_policy: rule.case_policy || "match",
      enabled: rule.enabled !== false
    }));
  }

  function applySettings(settings) {
    currentSettings = { ...DEFAULT_SETTINGS, ...settings };
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
      log(`No enabled rule found for focus word \"${focusWord}\".`);
    }
    ensureStyle(currentSettings.highlightColor || DEFAULT_SETTINGS.highlightColor);
    attachClickListener();
    applyHighlightToDom();

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
      chrome.storage.local.get(DEFAULT_SETTINGS, (items) => resolve(items));
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
        log(`Debug focus word set to \"${focusWord}\".`);
      } else {
        log("Debug focus word cleared.");
      }
    }

    if (needsHighlight) {
      currentSettings = { ...currentSettings, ...nextSettings };
      ensureStyle(currentSettings.highlightColor || DEFAULT_SETTINGS.highlightColor);
      applyHighlightToDom();
    }
    if (needsRebuild) {
      applySettings(nextSettings);
    }
  });
})();
