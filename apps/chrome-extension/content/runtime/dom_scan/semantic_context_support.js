(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const MAX_WORDS = 48;
  const WORD_RE = /[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*/g;
  const STRONG_BOUNDARIES = new Set([".", "?", "!"]);

  function findPreviousStrongBoundary(text, index) {
    for (let cursor = Math.max(0, index - 1); cursor >= 0; cursor -= 1) {
      if (STRONG_BOUNDARIES.has(text[cursor])) return cursor + 1;
    }
    return 0;
  }

  function findNextStrongBoundary(text, index) {
    for (let cursor = Math.max(0, index); cursor < text.length; cursor += 1) {
      if (STRONG_BOUNDARIES.has(text[cursor])) return cursor + 1;
    }
    return text.length;
  }

  function collectWordSpans(text, start, end) {
    const spans = [];
    const pattern = new RegExp(WORD_RE.source, "g");
    let match = pattern.exec(text);
    while (match) {
      const wordStart = match.index;
      const wordEnd = wordStart + match[0].length;
      if (wordEnd > start && wordStart < end) spans.push({ start: wordStart, end: wordEnd });
      if (wordStart >= end) break;
      match = pattern.exec(text);
    }
    return spans;
  }

  function clipToWordBudget(text, start, end, matchStart, matchEnd) {
    const wordSpans = collectWordSpans(text, start, end);
    if (wordSpans.length <= MAX_WORDS) return { start, end };
    let matchWordIndex = wordSpans.findIndex((span) => span.end > matchStart && span.start < matchEnd);
    if (matchWordIndex < 0) matchWordIndex = wordSpans.findIndex((span) => span.start >= matchStart);
    if (matchWordIndex < 0) matchWordIndex = Math.max(0, wordSpans.length - 1);
    const halfWindow = Math.floor(MAX_WORDS / 2);
    let firstWordIndex = Math.max(0, matchWordIndex - halfWindow);
    let lastWordIndex = Math.min(wordSpans.length, firstWordIndex + MAX_WORDS);
    if (lastWordIndex - firstWordIndex < MAX_WORDS) {
      firstWordIndex = Math.max(0, lastWordIndex - MAX_WORDS);
    }
    return {
      start: Math.max(start, wordSpans[firstWordIndex].start),
      end: Math.min(end, wordSpans[lastWordIndex - 1].end)
    };
  }

  function trimContext(text, start, end, matchStart, matchEnd) {
    let trimmedStart = start;
    let trimmedEnd = end;
    while (trimmedStart < matchStart && /\s/.test(text[trimmedStart] || "")) trimmedStart += 1;
    while (trimmedEnd > matchEnd && /\s/.test(text[trimmedEnd - 1] || "")) trimmedEnd -= 1;
    if (matchStart < trimmedStart || matchEnd > trimmedEnd || matchStart >= matchEnd) return null;
    return {
      contextText: text.slice(trimmedStart, trimmedEnd),
      matchStart: matchStart - trimmedStart,
      matchEnd: matchEnd - trimmedStart
    };
  }

  function clipContext(text, matchStart, matchEnd) {
    if (!text || matchStart < 0 || matchEnd <= matchStart || matchEnd > text.length) return null;
    let start = findPreviousStrongBoundary(text, matchStart);
    let end = findNextStrongBoundary(text, matchEnd);
    if (end <= start || matchStart < start || matchEnd > end) {
      start = 0;
      end = text.length;
    }
    const clipped = clipToWordBudget(text, start, end, matchStart, matchEnd);
    return trimContext(text, clipped.start, clipped.end, matchStart, matchEnd);
  }

  root.contentDomScanSemanticContextSupport = {
    clipContext
  };
})();
