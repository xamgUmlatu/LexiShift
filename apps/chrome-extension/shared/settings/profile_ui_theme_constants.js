(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  // Centralized ranges for options-page card color tuning.
  // Adjust these limits in one place if product requirements change.
  const CARD_THEME_LIMITS = Object.freeze({
    hueDeg: Object.freeze({
      min: -180,
      max: 180,
      step: 1,
      defaultValue: 0
    }),
    saturationPercent: Object.freeze({
      min: 70,
      max: 140,
      step: 1,
      defaultValue: 100
    }),
    brightnessPercent: Object.freeze({
      min: 80,
      max: 125,
      step: 1,
      defaultValue: 100
    })
  });

  root.profileUiTheme = {
    CARD_THEME_LIMITS
  };
})();
