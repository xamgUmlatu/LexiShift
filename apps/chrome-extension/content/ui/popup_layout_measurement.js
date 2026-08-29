(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function finiteDimension(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? Math.max(0, parsed) : 0;
  }

  function measureNaturalHeight(popup, modules) {
    if (!popup || typeof popup.getBoundingClientRect !== "function") {
      return 0;
    }
    const popupHeight = finiteDimension(popup.getBoundingClientRect().height);
    if (!modules || typeof modules.getBoundingClientRect !== "function") {
      return popupHeight;
    }
    const visibleModulesHeight = finiteDimension(modules.getBoundingClientRect().height);
    const naturalModulesHeight = finiteDimension(modules.scrollHeight);
    return popupHeight + Math.max(0, naturalModulesHeight - visibleModulesHeight);
  }

  root.uiPopupLayoutMeasurement = { measureNaturalHeight };
})();
