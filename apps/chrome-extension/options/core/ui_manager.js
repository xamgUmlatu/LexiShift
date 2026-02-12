class UIManager {
  constructor() {
    this.dom = {};
    this.COLORS = {
      SUCCESS: "#3c5a2a",
      ERROR: "#b42318",
      DEFAULT: "#6c675f"
    };
    this.LINKS = {
      app: "https://lexishift.app/download",
      plugin: "https://lexishift.app/betterdiscord"
    };
    this.init();
  }

  init() {
    const ids = [
      "options-main-content",
      "enabled", "highlight-enabled", "highlight-color", "highlight-color-text",
      "max-one-per-block", "allow-adjacent", "max-replacements-per-page",
      "max-replacements-per-lemma-page", "debug-enabled", "debug-focus-word",
      "srs-enabled", "source-language", "target-language", "srs-max-active",
      "target-language-gear", "target-language-prefs-modal-backdrop",
      "target-language-prefs-modal", "target-language-prefs-modal-ok", "target-language-modules-list",
      "srs-profile-id", "srs-profile-refresh", "srs-profile-status",
      "profile-bg-backdrop-color",
      "profile-bg-enabled", "profile-bg-opacity", "profile-bg-opacity-value",
      "profile-bg-file", "profile-bg-remove", "profile-bg-apply",
      "profile-bg-status", "profile-bg-preview-wrap", "profile-bg-preview",
      "profile-card-theme-hue", "profile-card-theme-hue-value",
      "profile-card-theme-saturation", "profile-card-theme-saturation-value",
      "profile-card-theme-brightness", "profile-card-theme-brightness-value",
      "profile-card-theme-reset",
      "srs-bootstrap-top-n", "srs-initial-active-count",
      "srs-sound-enabled", "srs-highlight-color", "srs-highlight-color-text",
      "srs-feedback-srs-enabled", "srs-feedback-rules-enabled",
      "srs-exposure-logging-enabled",
      "srs-initialize-set", "srs-refresh-set", "srs-runtime-diagnostics",
      "srs-rulegen-sampled-preview",
      "srs-rulegen-output", "srs-reset", "helper-status",
      "helper-last-sync", "debug-helper-test",
      "debug-helper-test-output", "debug-open-data-dir",
      "debug-open-data-dir-output", "ui-language", "rules", "save",
      "status", "rules-file", "import-file", "export-file", "file-status",
      "rules-updated", "rules-count", "share-code", "share-code-cjk",
      "generate-code", "import-code", "copy-code", "open-desktop-app",
      "open-bd-plugin"
    ];

    ids.forEach((id) => {
      const prop = id.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
      this.dom[prop] = document.getElementById(id);
    });
    this.dom.rulesSourceInputs = Array.from(document.querySelectorAll("input[name='rules-source']"));
  }

  setStatus(message, color) {
    const el = this.dom.status;
    if (!el) return;
    el.textContent = message;
    el.style.color = color || this.COLORS.DEFAULT;
    if (message) {
      setTimeout(() => {
        if (el.textContent === message) {
          el.textContent = "";
        }
      }, 2000);
    }
  }

  formatTimestamp(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleString();
  }

  updateRulesMeta(rules, updatedAt) {
    if (this.dom.rulesCount) {
      this.dom.rulesCount.textContent = Array.isArray(rules) ? String(rules.length) : "0";
    }
    if (this.dom.rulesUpdated) {
      this.dom.rulesUpdated.textContent = this.formatTimestamp(updatedAt);
    }
  }

  updateRulesSourceUI(source) {
    this.dom.rulesSourceInputs.forEach((input) => {
      input.checked = input.value === source;
    });
    const isFile = source === "file";
    if (this.dom.rules) this.dom.rules.disabled = isFile;
    if (this.dom.save) this.dom.save.disabled = isFile;
  }

  setHelperStatus(status, lastSync) {
    if (this.dom.helperStatus) this.dom.helperStatus.textContent = status || "—";
    if (this.dom.helperLastSync) this.dom.helperLastSync.textContent = this.formatTimestamp(lastSync);
  }

  updateSrsInputs(profile) {
    if (this.dom.srsMaxActive) {
      this.dom.srsMaxActive.value = String(profile.srsMaxActive);
    }
    if (this.dom.srsBootstrapTopN) {
      this.dom.srsBootstrapTopN.value = String(profile.srsBootstrapTopN);
    }
    if (this.dom.srsInitialActiveCount) {
      this.dom.srsInitialActiveCount.value = String(profile.srsInitialActiveCount);
    }
    if (this.dom.srsSoundEnabled) {
      this.dom.srsSoundEnabled.checked = profile.srsSoundEnabled;
    }
    if (this.dom.srsHighlightColor) {
      this.dom.srsHighlightColor.value = profile.srsHighlightColor;
    }
    if (this.dom.srsHighlightColorText) {
      this.dom.srsHighlightColorText.value = profile.srsHighlightColor;
    }
    if (this.dom.srsFeedbackSrsEnabled) {
      this.dom.srsFeedbackSrsEnabled.checked = profile.srsFeedbackSrsEnabled;
    }
    if (this.dom.srsFeedbackRulesEnabled) {
      this.dom.srsFeedbackRulesEnabled.checked = profile.srsFeedbackRulesEnabled;
    }
    if (this.dom.srsExposureLoggingEnabled) {
      this.dom.srsExposureLoggingEnabled.checked = profile.srsExposureLoggingEnabled;
    }
  }

  updateProfileBackgroundInputs(prefs) {
    const source = prefs && typeof prefs === "object" ? prefs : {};
    const hasAsset = Boolean(String(source.backgroundAssetId || "").trim());
    const themePrefs = globalThis.LexiShift
      && globalThis.LexiShift.profileUiThemePrefs
      && typeof globalThis.LexiShift.profileUiThemePrefs === "object"
      ? globalThis.LexiShift.profileUiThemePrefs
      : {};
    const resolveCardThemeLimits = typeof themePrefs.resolveCardThemeLimits === "function"
      ? themePrefs.resolveCardThemeLimits
      : () => ({
          hueDeg: { min: -180, max: 180, step: 1, defaultValue: 0 },
          saturationPercent: { min: 70, max: 140, step: 1, defaultValue: 100 },
          brightnessPercent: { min: 80, max: 125, step: 1, defaultValue: 100 }
        });
    const normalizeCardThemePrefs = typeof themePrefs.normalizeCardThemePrefs === "function"
      ? themePrefs.normalizeCardThemePrefs
      : () => ({
          cardThemeHueDeg: 0,
          cardThemeSaturationPercent: 100,
          cardThemeBrightnessPercent: 100
        });
    const cardThemeLimits = resolveCardThemeLimits();
    const normalizedCardTheme = normalizeCardThemePrefs(source, {
      fallback: source
    });
    if (this.dom.profileBgBackdropColor) {
      this.dom.profileBgBackdropColor.value = String(source.backgroundBackdropColor || "#fbf7f0");
      this.dom.profileBgBackdropColor.disabled = false;
    }
    if (this.dom.profileBgEnabled) {
      this.dom.profileBgEnabled.checked = source.backgroundEnabled === true && hasAsset;
      this.dom.profileBgEnabled.disabled = false;
    }
    if (this.dom.profileBgOpacity) {
      const opacity = Number.isFinite(Number(source.backgroundOpacity))
        ? Number(source.backgroundOpacity)
        : 0.18;
      const percent = Math.round(Math.min(1, Math.max(0, opacity)) * 100);
      this.dom.profileBgOpacity.value = String(percent);
      this.dom.profileBgOpacity.disabled = false;
    }
    if (this.dom.profileBgOpacityValue) {
      const opacityValue = this.dom.profileBgOpacity
        ? Number(this.dom.profileBgOpacity.value || 18)
        : 18;
      this.dom.profileBgOpacityValue.textContent = `${Math.round(opacityValue)}%`;
    }
    if (this.dom.profileBgRemove) {
      this.dom.profileBgRemove.disabled = !hasAsset;
    }
    if (this.dom.profileBgApply) {
      this.dom.profileBgApply.disabled = !hasAsset;
    }
    if (this.dom.profileCardThemeHue) {
      const hue = Number.isFinite(Number(normalizedCardTheme.cardThemeHueDeg))
        ? Number(normalizedCardTheme.cardThemeHueDeg)
        : Number(cardThemeLimits.hueDeg.defaultValue);
      this.dom.profileCardThemeHue.min = String(cardThemeLimits.hueDeg.min);
      this.dom.profileCardThemeHue.max = String(cardThemeLimits.hueDeg.max);
      this.dom.profileCardThemeHue.step = String(cardThemeLimits.hueDeg.step || 1);
      this.dom.profileCardThemeHue.value = String(Math.round(hue));
      this.dom.profileCardThemeHue.disabled = false;
    }
    if (this.dom.profileCardThemeHueValue) {
      const hueValue = this.dom.profileCardThemeHue
        ? Number(this.dom.profileCardThemeHue.value || 0)
        : Number(cardThemeLimits.hueDeg.defaultValue);
      this.dom.profileCardThemeHueValue.textContent = `${Math.round(hueValue)}°`;
    }
    if (this.dom.profileCardThemeSaturation) {
      const saturation = Number.isFinite(Number(normalizedCardTheme.cardThemeSaturationPercent))
        ? Number(normalizedCardTheme.cardThemeSaturationPercent)
        : Number(cardThemeLimits.saturationPercent.defaultValue);
      this.dom.profileCardThemeSaturation.min = String(cardThemeLimits.saturationPercent.min);
      this.dom.profileCardThemeSaturation.max = String(cardThemeLimits.saturationPercent.max);
      this.dom.profileCardThemeSaturation.step = String(cardThemeLimits.saturationPercent.step || 1);
      this.dom.profileCardThemeSaturation.value = String(Math.round(saturation));
      this.dom.profileCardThemeSaturation.disabled = false;
    }
    if (this.dom.profileCardThemeSaturationValue) {
      const saturationValue = this.dom.profileCardThemeSaturation
        ? Number(this.dom.profileCardThemeSaturation.value || 100)
        : Number(cardThemeLimits.saturationPercent.defaultValue);
      this.dom.profileCardThemeSaturationValue.textContent = `${Math.round(saturationValue)}%`;
    }
    if (this.dom.profileCardThemeBrightness) {
      const brightness = Number.isFinite(Number(normalizedCardTheme.cardThemeBrightnessPercent))
        ? Number(normalizedCardTheme.cardThemeBrightnessPercent)
        : Number(cardThemeLimits.brightnessPercent.defaultValue);
      this.dom.profileCardThemeBrightness.min = String(cardThemeLimits.brightnessPercent.min);
      this.dom.profileCardThemeBrightness.max = String(cardThemeLimits.brightnessPercent.max);
      this.dom.profileCardThemeBrightness.step = String(cardThemeLimits.brightnessPercent.step || 1);
      this.dom.profileCardThemeBrightness.value = String(Math.round(brightness));
      this.dom.profileCardThemeBrightness.disabled = false;
    }
    if (this.dom.profileCardThemeBrightnessValue) {
      const brightnessValue = this.dom.profileCardThemeBrightness
        ? Number(this.dom.profileCardThemeBrightness.value || 100)
        : Number(cardThemeLimits.brightnessPercent.defaultValue);
      this.dom.profileCardThemeBrightnessValue.textContent = `${Math.round(brightnessValue)}%`;
    }
    if (this.dom.profileCardThemeReset) {
      this.dom.profileCardThemeReset.disabled = false;
    }
  }
}
