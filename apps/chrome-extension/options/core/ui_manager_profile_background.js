(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  root.optionsUiManagerProfileBackgroundMethods = {
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
            brightnessPercent: { min: 80, max: 125, step: 1, defaultValue: 100 },
            transparencyPercent: { min: 40, max: 100, step: 1, defaultValue: 100 }
          });
      const normalizeCardThemePrefs = typeof themePrefs.normalizeCardThemePrefs === "function"
        ? themePrefs.normalizeCardThemePrefs
        : () => ({
            cardThemeHueDeg: 0,
            cardThemeSaturationPercent: 100,
            cardThemeBrightnessPercent: 100,
            cardThemeTransparencyPercent: 100
          });
      const cardThemeLimits = resolveCardThemeLimits();
      const normalizedCardTheme = normalizeCardThemePrefs(source, {
        fallback: source
      });
      if (this.dom.profileBgBackdropColor) {
        this.dom.profileBgBackdropColor.value = String(source.backgroundBackdropColor || "#fbf7f0");
        this.dom.profileBgBackdropColor.disabled = false;
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
      if (this.dom.profileBgPositionReset) {
        this.dom.profileBgPositionReset.disabled = false;
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
      if (this.dom.profileCardThemeTransparency) {
        const transparency = Number.isFinite(Number(normalizedCardTheme.cardThemeTransparencyPercent))
          ? Number(normalizedCardTheme.cardThemeTransparencyPercent)
          : Number(cardThemeLimits.transparencyPercent.defaultValue);
        this.dom.profileCardThemeTransparency.min = String(cardThemeLimits.transparencyPercent.min);
        this.dom.profileCardThemeTransparency.max = String(cardThemeLimits.transparencyPercent.max);
        this.dom.profileCardThemeTransparency.step = String(cardThemeLimits.transparencyPercent.step || 1);
        this.dom.profileCardThemeTransparency.value = String(Math.round(transparency));
        this.dom.profileCardThemeTransparency.disabled = false;
      }
      if (this.dom.profileCardThemeTransparencyValue) {
        const transparencyValue = this.dom.profileCardThemeTransparency
          ? Number(this.dom.profileCardThemeTransparency.value || 100)
          : Number(cardThemeLimits.transparencyPercent.defaultValue);
        this.dom.profileCardThemeTransparencyValue.textContent = `${Math.round(transparencyValue)}%`;
      }
      if (this.dom.profileCardThemeReset) {
        this.dom.profileCardThemeReset.disabled = false;
      }
    }
  };
})();
