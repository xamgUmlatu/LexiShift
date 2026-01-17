(() => {
  const TOKEN_RE = /[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*|\s+|[^\w\s]+/g;
  const WORD_RE = /^[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*$/;

  const DEFAULT_SETTINGS = {
    enabled: true,
    rules: []
  };

  const processedNodes = new WeakMap();

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

  function replaceText(text, trie) {
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
      return text;
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

    let output = "";
    let tokenCursor = 0;
    for (const match of matches) {
      const startTokenIdx = wordPositions[match.startWordIndex];
      const endTokenIdx = wordPositions[match.endWordIndex];
      for (let i = tokenCursor; i < startTokenIdx; i += 1) {
        output += tokens[i].text;
      }
      const sourceWords = wordTexts.slice(match.startWordIndex, match.endWordIndex + 1);
      const replacement = applyCase(match.rule.replacement, sourceWords, match.rule.case_policy || "match");
      output += replacement;
      tokenCursor = endTokenIdx + 1;
    }
    for (let i = tokenCursor; i < tokens.length; i += 1) {
      output += tokens[i].text;
    }
    return output;
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

  function processTextNode(node, trie) {
    if (!node || !node.nodeValue) {
      return;
    }
    if (isEditable(node) || isExcluded(node)) {
      return;
    }
    const last = processedNodes.get(node);
    if (last === node.nodeValue) {
      return;
    }
    const replaced = replaceText(node.nodeValue, trie);
    if (replaced !== node.nodeValue) {
      node.nodeValue = replaced;
    }
    processedNodes.set(node, node.nodeValue);
  }

  function processDocument(trie) {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      processTextNode(node, trie);
      node = walker.nextNode();
    }
  }

  function observeChanges(trie) {
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === "characterData") {
          processTextNode(mutation.target, trie);
        } else if (mutation.type === "childList") {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.TEXT_NODE) {
              processTextNode(node, trie);
            } else if (node.nodeType === Node.ELEMENT_NODE) {
              const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
              let textNode = walker.nextNode();
              while (textNode) {
                processTextNode(textNode, trie);
                textNode = walker.nextNode();
              }
            }
          });
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  function loadSettings() {
    return new Promise((resolve) => {
      chrome.storage.local.get(DEFAULT_SETTINGS, (items) => resolve(items));
    });
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

  async function boot() {
    const settings = await loadSettings();
    if (!settings.enabled) {
      return;
    }
    const trie = buildTrie(normalizeRules(settings.rules));
    processDocument(trie);
    observeChanges(trie);
  }

  boot();

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "local") {
      return;
    }
    if (changes.rules || changes.enabled) {
      boot();
    }
  });
})();
