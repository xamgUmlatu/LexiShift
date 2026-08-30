(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const MAX_WORDS = 48;
  const MAX_CONTEXT_CHARS = 1200;
  const WORD_RE = /[\p{L}\p{M}\p{N}]+(?:['’][\p{L}\p{M}\p{N}]+)*/gu;
  const FALLBACK_STRONG_BOUNDARIES = new Set([".", "?", "!", "。", "？", "！", "…", "\u2029"]);
  const TRAILING_SENTENCE_CLOSERS = new Set([
    "\"", "'", "”", "’", "»", "›", ")", "]", "}", "）", "］", "｝", "」", "』", "】", "》", "〉"
  ]);
  const NON_TERMINAL_ABBREVIATIONS = new Set([
    "dr", "mr", "mrs", "ms", "prof", "rev", "hon", "pres", "gov", "sen", "rep",
    "gen", "lt", "col", "sgt", "capt", "cmdr", "fig", "eq", "no", "vs"
  ]);
  const segmenterCache = new Map();

  function normalizeLocale(value) {
    const locale = String(value || "").trim();
    return locale || undefined;
  }

  function createContextCache() {
    return {
      records: new WeakMap(),
      stats: {
        containerBuilds: 0,
        recordReuses: 0,
        usableReuses: 0,
        bypasses: 0
      }
    };
  }

  function normalizeContextCache(value, rawNodeFilters) {
    if (!value || typeof value !== "object" || !(value.records instanceof WeakMap)) {
      return null;
    }
    const policy = rawNodeFilters || null;
    if (!Object.prototype.hasOwnProperty.call(value, "nodeFilters")) {
      value.nodeFilters = policy;
    }
    if (value.nodeFilters !== policy) {
      if (value.stats && typeof value.stats === "object") value.stats.bypasses += 1;
      return null;
    }
    return value;
  }

  function getSegmenter(locale, granularity) {
    if (
      !globalThis.Intl
      || typeof globalThis.Intl.Segmenter !== "function"
    ) {
      return null;
    }
    const normalizedLocale = normalizeLocale(locale);
    const cacheKey = `${normalizedLocale || "default"}:${granularity}`;
    if (segmenterCache.has(cacheKey)) {
      return segmenterCache.get(cacheKey);
    }
    let segmenter = null;
    try {
      segmenter = new globalThis.Intl.Segmenter(normalizedLocale, { granularity });
    } catch (_error) {
      try {
        segmenter = new globalThis.Intl.Segmenter(undefined, { granularity });
      } catch (_fallbackError) {
        segmenter = null;
      }
    }
    segmenterCache.set(cacheKey, segmenter);
    return segmenter;
  }

  function findPreviousToken(text, endIndex) {
    let cursor = Math.max(0, endIndex);
    while (cursor > 0 && /\s/u.test(text[cursor - 1] || "")) cursor -= 1;
    while (cursor > 0 && TRAILING_SENTENCE_CLOSERS.has(text[cursor - 1])) cursor -= 1;
    if (cursor <= 0 || text[cursor - 1] !== ".") return "";
    cursor -= 1;
    const tokenEnd = cursor;
    while (cursor > 0 && /[\p{L}\p{M}]/u.test(text[cursor - 1] || "")) cursor -= 1;
    return text.slice(cursor, tokenEnd).toLocaleLowerCase();
  }

  function shouldMergeSegmentWithNext(text, segmentEnd) {
    return NON_TERMINAL_ABBREVIATIONS.has(findPreviousToken(text, segmentEnd));
  }

  function collectIntlSentenceRanges(text, locale) {
    const segmenter = getSegmenter(locale, "sentence");
    if (!segmenter) return null;
    const rawRanges = [];
    try {
      for (const entry of segmenter.segment(text)) {
        const start = Number(entry.index);
        const segment = String(entry.segment || "");
        if (!Number.isFinite(start) || !segment) continue;
        rawRanges.push({ start, end: start + segment.length });
      }
    } catch (_error) {
      return null;
    }
    if (!rawRanges.length) return null;
    const merged = [];
    for (let index = 0; index < rawRanges.length; index += 1) {
      const current = { ...rawRanges[index] };
      while (
        index + 1 < rawRanges.length
        && shouldMergeSegmentWithNext(text, current.end)
      ) {
        index += 1;
        current.end = rawRanges[index].end;
      }
      merged.push(current);
    }
    return merged;
  }

  function isEmbeddedPeriod(text, index) {
    const previous = text[index - 1] || "";
    const next = text[index + 1] || "";
    return /[\p{L}\p{M}\p{N}]/u.test(previous)
      && /[\p{L}\p{M}\p{N}]/u.test(next);
  }

  function isLowercaseInitialismContinuation(text, index) {
    const prefix = text.slice(Math.max(0, index - 8), index + 1);
    if (!/(?:\p{L}\.){2,}$/u.test(prefix)) return false;
    let cursor = index + 1;
    while (cursor < text.length && /\s/u.test(text[cursor] || "")) cursor += 1;
    return /\p{Ll}/u.test(text[cursor] || "");
  }

  function isFallbackBoundary(text, index) {
    const char = text[index];
    if (!FALLBACK_STRONG_BOUNDARIES.has(char)) return false;
    if (char !== ".") return true;
    if (isEmbeddedPeriod(text, index)) return false;
    if (NON_TERMINAL_ABBREVIATIONS.has(findPreviousToken(text, index + 1))) return false;
    return !isLowercaseInitialismContinuation(text, index);
  }

  function consumeBoundarySuffix(text, index) {
    let cursor = Math.max(0, index);
    while (cursor < text.length && FALLBACK_STRONG_BOUNDARIES.has(text[cursor])) cursor += 1;
    while (cursor < text.length && TRAILING_SENTENCE_CLOSERS.has(text[cursor])) cursor += 1;
    return cursor;
  }

  function collectFallbackSentenceRanges(text) {
    const ranges = [];
    let start = 0;
    let cursor = 0;
    while (cursor < text.length) {
      if (!isFallbackBoundary(text, cursor)) {
        cursor += 1;
        continue;
      }
      const end = consumeBoundarySuffix(text, cursor);
      ranges.push({ start, end });
      start = end;
      cursor = end;
    }
    if (start < text.length || !ranges.length) {
      ranges.push({ start, end: text.length });
    }
    return ranges;
  }

  function findContainingSentenceRange(ranges, matchStart, matchEnd, textLength) {
    const list = ranges || [];
    for (let index = 0; index < list.length; index += 1) {
      const range = list[index];
      if (range.start <= matchStart && range.end >= matchEnd) {
        return { ...range, index };
      }
    }
    return { start: 0, end: textLength, index: 0 };
  }

  function collectWordSpansWithSegmenter(text, start, end, locale) {
    const segmenter = getSegmenter(locale, "word");
    if (!segmenter) return null;
    const spans = [];
    try {
      for (const entry of segmenter.segment(text)) {
        if (entry.isWordLike !== true) continue;
        const wordStart = Number(entry.index);
        const wordEnd = wordStart + String(entry.segment || "").length;
        if (wordEnd > start && wordStart < end) spans.push({ start: wordStart, end: wordEnd });
        if (wordStart >= end) break;
      }
    } catch (_error) {
      return null;
    }
    return spans;
  }

  function collectWordSpansWithRegex(text, start, end) {
    const spans = [];
    const pattern = new RegExp(WORD_RE.source, "gu");
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

  function collectWordSpans(text, start, end, locale) {
    return collectWordSpansWithSegmenter(text, start, end, locale)
      || collectWordSpansWithRegex(text, start, end);
  }

  function clipToWordBudget(text, start, end, matchStart, matchEnd, locale) {
    const wordSpans = collectWordSpans(text, start, end, locale);
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

  function clipToCharacterBudget(start, end, matchStart, matchEnd) {
    if (end - start <= MAX_CONTEXT_CHARS) return { start, end };
    const matchLength = matchEnd - matchStart;
    const effectiveBudget = Math.max(MAX_CONTEXT_CHARS, matchLength);
    const sideBudget = Math.floor((effectiveBudget - matchLength) / 2);
    let clippedStart = Math.max(start, matchStart - sideBudget);
    let clippedEnd = Math.min(end, clippedStart + effectiveBudget);
    if (clippedEnd - clippedStart < effectiveBudget) {
      clippedStart = Math.max(start, clippedEnd - effectiveBudget);
    }
    return { start: clippedStart, end: clippedEnd };
  }

  function normalizeContextText(value) {
    return String(value || "").replace(/\u2029/g, "\n");
  }

  function trimContext(text, start, end, matchStart, matchEnd, sentenceRange) {
    let trimmedStart = start;
    let trimmedEnd = end;
    while (trimmedStart < matchStart && /\s/.test(text[trimmedStart] || "")) trimmedStart += 1;
    while (trimmedEnd > matchEnd && /\s/.test(text[trimmedEnd - 1] || "")) trimmedEnd -= 1;
    if (matchStart < trimmedStart || matchEnd > trimmedEnd || matchStart >= matchEnd) return null;
    return {
      contextText: normalizeContextText(text.slice(trimmedStart, trimmedEnd)),
      matchStart: matchStart - trimmedStart,
      matchEnd: matchEnd - trimmedStart,
      sentenceStart: Number(sentenceRange && sentenceRange.start || 0),
      sentenceEnd: Number(sentenceRange && sentenceRange.end || text.length),
      sentenceIndex: Number(sentenceRange && sentenceRange.index || 0)
    };
  }

  function clipContext(text, matchStart, matchEnd, options) {
    if (!text || matchStart < 0 || matchEnd <= matchStart || matchEnd > text.length) return null;
    const opts = options && typeof options === "object" ? options : {};
    const locale = normalizeLocale(opts.locale);
    const sentenceRanges = collectIntlSentenceRanges(text, locale)
      || collectFallbackSentenceRanges(text);
    const sentenceRange = findContainingSentenceRange(
      sentenceRanges,
      matchStart,
      matchEnd,
      text.length
    );
    let start = sentenceRange.start;
    let end = sentenceRange.end;
    if (end <= start || matchStart < start || matchEnd > end) {
      start = 0;
      end = text.length;
    }
    const wordClipped = clipToWordBudget(text, start, end, matchStart, matchEnd, locale);
    const clipped = clipToCharacterBudget(
      wordClipped.start,
      wordClipped.end,
      matchStart,
      matchEnd
    );
    return trimContext(
      text,
      clipped.start,
      clipped.end,
      matchStart,
      matchEnd,
      sentenceRange
    );
  }

  root.contentDomScanSemanticContextSupport = {
    clipContext,
    createContextCache,
    normalizeContextCache
  };
})();
