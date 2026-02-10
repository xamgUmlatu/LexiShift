(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const { tokenize, normalize } = root.tokenizer || {};

  function buildTrie(rules) {
    const rootNode = { children: Object.create(null), bestRule: null };
    for (const rule of rules) {
      if (rule.enabled === false) {
        continue;
      }
      const words = tokenize(rule.source_phrase || "").filter((t) => t.kind === "word");
      if (!words.length) {
        continue;
      }
      let node = rootNode;
      for (const word of words) {
        const key = normalize(word.text);
        node.children[key] = node.children[key] || { children: Object.create(null), bestRule: null };
        node = node.children[key];
      }
      if (!node.bestRule || rule.priority > node.bestRule.priority) {
        node.bestRule = rule;
      }
    }
    return rootNode;
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

  function normalizeRules(rules) {
    return (rules || []).map((rule) => ({
      source_phrase: String(rule.source_phrase || ""),
      replacement: String(rule.replacement || ""),
      priority: Number.isFinite(rule.priority) ? rule.priority : 0,
      case_policy: rule.case_policy || "match",
      enabled: rule.enabled !== false,
      metadata: rule.metadata && typeof rule.metadata === "object"
        ? { ...rule.metadata }
        : null
    }));
  }

  root.matcher = { buildTrie, findLongestMatch, applyCase, normalizeRules };
})();
