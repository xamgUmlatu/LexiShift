(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function buildTokenOffsets(tokens) {
    const offsets = [];
    let cursor = 0;
    for (const token of tokens || []) {
      offsets.push(cursor);
      cursor += String(token && token.text ? token.text : "").length;
    }
    return offsets;
  }

  function normalizeResolvedContext(value, fallback) {
    if (!value || typeof value !== "object") return fallback;
    const contextText = String(value.contextText || value.context_text || "");
    const matchStart = Number(value.matchStart !== undefined ? value.matchStart : value.match_start);
    const matchEnd = Number(value.matchEnd !== undefined ? value.matchEnd : value.match_end);
    if (
      !contextText
      || !Number.isFinite(matchStart)
      || !Number.isFinite(matchEnd)
      || matchStart < 0
      || matchEnd <= matchStart
      || matchEnd > contextText.length
    ) {
      return fallback;
    }
    return { contextText, matchStart, matchEnd };
  }

  function resolveContextWithResolver(resolver, payload, fallback, log) {
    if (typeof resolver !== "function") return fallback;
    let candidate = null;
    try {
      candidate = resolver(payload);
    } catch (error) {
      if (typeof log === "function") log("Failed to resolve widened semantic context:", error);
    }
    return normalizeResolvedContext(candidate, fallback);
  }

  function createRequestMatch(options) {
    const opts = options && typeof options === "object" ? options : {};
    const descriptor = opts.descriptor && typeof opts.descriptor === "object" ? opts.descriptor : {};
    const match = descriptor.match && typeof descriptor.match === "object" ? descriptor.match : {};
    const tokens = Array.isArray(opts.tokens) ? opts.tokens : [];
    const wordPositions = Array.isArray(opts.wordPositions) ? opts.wordPositions : [];
    const tokenOffsets = buildTokenOffsets(tokens);
    const startTokenIdx = Number(wordPositions[match.startWordIndex]);
    const endTokenIdx = Number(wordPositions[match.endWordIndex]);
    const start = Number.isFinite(startTokenIdx) ? Number(tokenOffsets[startTokenIdx] || 0) : 0;
    const endStart = Number.isFinite(endTokenIdx) ? Number(tokenOffsets[endTokenIdx] || 0) : start;
    const endToken = tokens[endTokenIdx] && typeof tokens[endTokenIdx] === "object"
      ? tokens[endTokenIdx]
      : { text: "" };
    const fallbackContext = {
      contextText: String(opts.text || ""),
      matchStart: start,
      matchEnd: endStart + String(endToken.text || "").length
    };
    const sourcePhrase = String(match.rule && match.rule.source_phrase || "").trim();
    const resolvedContext = resolveContextWithResolver(
      opts.semanticContextResolver,
      {
        match,
        matchId: descriptor.matchId,
        sourcePhrase,
        text: fallbackContext.contextText,
        tokens,
        wordPositions,
        tokenOffsets,
        matchStart: fallbackContext.matchStart,
        matchEnd: fallbackContext.matchEnd
      },
      fallbackContext,
      opts.log
    );
    return {
      match_id: descriptor.matchId,
      source_phrase: sourcePhrase,
      context_text: resolvedContext.contextText,
      match_start: resolvedContext.matchStart,
      match_end: resolvedContext.matchEnd,
      semantic_admission: descriptor.admission,
      document_url: globalThis.location && globalThis.location.href ? globalThis.location.href : "",
      page_language: document && document.documentElement ? String(document.documentElement.lang || "") : ""
    };
  }

  root.contentSemanticRequestContext = {
    createRequestMatch
  };
})();
