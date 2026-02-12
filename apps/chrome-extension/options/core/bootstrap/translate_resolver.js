(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function resolveTranslate(value) {
    if (typeof value === "function") {
      return value;
    }
    return (_key, _subs, fallback) => fallback || "";
  }

  root.optionsTranslateResolver = {
    resolveTranslate
  };
})();
