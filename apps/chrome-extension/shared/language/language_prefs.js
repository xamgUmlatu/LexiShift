(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const DEFAULT_SOURCE = "en";
  const DEFAULT_TARGET = "en";
  const DEFAULT_PAIR = "en-en";

  function normalizeLang(value, fallback) {
    const raw = String(value || "").trim().toLowerCase();
    if (!raw) {
      return fallback;
    }
    return raw;
  }

  function buildPair(source, target) {
    return `${source}-${target}`;
  }

  function normalizeLanguagePrefs(settings = {}) {
    const sourceLanguage = normalizeLang(settings.sourceLanguage, DEFAULT_SOURCE);
    const targetLanguage = normalizeLang(settings.targetLanguage, DEFAULT_TARGET);
    const srsPairAuto = settings.srsPairAuto === true;
    return { sourceLanguage, targetLanguage, srsPairAuto };
  }

  function resolveLanguagePair(settings = {}) {
    const { sourceLanguage, targetLanguage, srsPairAuto } = normalizeLanguagePrefs(settings);
    if (srsPairAuto) {
      return buildPair(sourceLanguage, targetLanguage);
    }
    const explicit = String(settings.srsPair || "").trim().toLowerCase();
    if (explicit) {
      return explicit;
    }
    return buildPair(sourceLanguage, targetLanguage) || DEFAULT_PAIR;
  }

  function applyLanguagePrefs(settings = {}) {
    const prefs = normalizeLanguagePrefs(settings);
    const resolvedPair = resolveLanguagePair({ ...settings, ...prefs });
    return { ...settings, ...prefs, srsPair: resolvedPair };
  }

  root.languagePrefs = {
    normalizeLanguagePrefs,
    resolveLanguagePair,
    applyLanguagePrefs
  };
})();
