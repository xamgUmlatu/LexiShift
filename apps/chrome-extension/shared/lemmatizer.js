(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function normalizeWord(word) {
    if (!word) return "";
    return String(word).trim();
  }

  function lemmatize(word, languagePair) {
    const raw = normalizeWord(word);
    if (!raw) return "";
    const pair = String(languagePair || "").toLowerCase();
    if (pair.startsWith("ja") || pair.includes("ja-") || pair.includes("-ja")) {
      return raw;
    }
    return raw.toLowerCase();
  }

  root.lemmatizer = { lemmatize };
})();
