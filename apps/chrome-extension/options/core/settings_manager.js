class SettingsManager {
  constructor() {
    const sharedDefaults = globalThis.LexiShift && globalThis.LexiShift.defaults;
    if (!sharedDefaults || typeof sharedDefaults !== "object") {
      throw new Error("[LexiShift][Options] Missing required shared defaults module.");
    }
    this.DEFAULT_PROFILE_ID = "default";
    this.defaults = sharedDefaults;
    this.currentRules = [];
  }

  async load() {
    return new Promise((resolve) => {
      chrome.storage.local.get(this.defaults, resolve);
    });
  }

  async save(data) {
    return new Promise((resolve) => {
      chrome.storage.local.set(data, resolve);
    });
  }
}

(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const installers = [
    ["optionsSettingsInstallBaseMethods", root.optionsSettingsInstallBaseMethods],
    ["optionsSettingsInstallLanguageMethods", root.optionsSettingsInstallLanguageMethods],
    ["optionsSettingsInstallUiPrefsMethods", root.optionsSettingsInstallUiPrefsMethods],
    ["optionsSettingsInstallSignalsMethods", root.optionsSettingsInstallSignalsMethods],
    ["optionsSettingsInstallSrsProfileMethods", root.optionsSettingsInstallSrsProfileMethods]
  ];
  for (const [name, install] of installers) {
    if (typeof install !== "function") {
      throw new Error(`[LexiShift][Options] Missing SettingsManager installer: ${name}`);
    }
    install(SettingsManager);
  }
})();
