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
    }),
    transparencyPercent: Object.freeze({
      min: 40,
      max: 100,
      step: 1,
      defaultValue: 100
    })
  });

  const CARD_THEME_TOKEN_KEYS = Object.freeze([
    "--ls-card-surface",
    "--ls-card-border",
    "--ls-card-shadow",
    "--ls-card-accent-start",
    "--ls-card-accent-end",
    "--ls-modal-surface",
    "--ls-modal-border",
    "--ls-modal-shadow",
    "--ls-module-card-border",
    "--ls-module-card-bg-start",
    "--ls-module-card-bg-end",
    "--ls-module-card-shadow",
    "--ls-profile-panel-border",
    "--ls-profile-panel-bg",
    "--ls-profile-preview-border",
    "--ls-profile-preview-bg",
    "--ls-srs-preview-border",
    "--ls-srs-preview-bg",
    "--ls-helper-status-border",
    "--ls-helper-status-bg",
    "--ls-advanced-border",
    "--ls-advanced-bg"
  ]);

  root.profileUiTheme = {
    CARD_THEME_LIMITS,
    CARD_THEME_TOKEN_KEYS
  };
})();
