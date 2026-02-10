class LocalizationService {
  constructor() {
    this.messages = null;
    this.activeLocale = "system";
    this.supportedLocales = ["ja", "zh", "de"];
  }

  t(key, substitutions, fallback) {
    if (this.messages && this.messages[key] && this.messages[key].message) {
      return this.formatMessage(this.messages[key].message, substitutions);
    }
    if (globalThis.chrome && chrome.i18n) {
      const message = chrome.i18n.getMessage(key, substitutions);
      if (message) {
        return message;
      }
    }
    return fallback || key;
  }

  formatMessage(message, substitutions) {
    if (!substitutions) {
      return message;
    }
    const values = Array.isArray(substitutions) ? substitutions : [substitutions];
    return message.replace(/\$([1-9]\d*)/g, (match, index) => {
      const value = values[Number(index) - 1];
      return value !== undefined ? String(value) : match;
    });
  }

  apply() {
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      const key = node.getAttribute("data-i18n");
      if (!key) return;
      const message = this.t(key, null, "");
      if (message) {
        node.textContent = message;
      }
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
      const key = node.getAttribute("data-i18n-placeholder");
      if (!key) return;
      const message = this.t(key, null, "");
      if (message) {
        node.setAttribute("placeholder", message);
      }
    });
    const title = this.t("options_title", null, "");
    if (title) {
      document.title = title;
    }
  }

  resolveLocale(value) {
    if (!value || value === "system") {
      const systemLocale = (globalThis.chrome && chrome.i18n && chrome.i18n.getUILanguage())
        || navigator.language
        || "en";
      value = systemLocale;
    }
    const normalized = value.toLowerCase();
    for (const lang of this.supportedLocales) {
      if (normalized.startsWith(lang)) return lang;
    }
    return "en";
  }

  async load(locale) {
    this.activeLocale = locale || "system";
    if (this.activeLocale === "system") {
      this.messages = null;
      this.apply();
      return;
    }
    const resolved = this.resolveLocale(this.activeLocale);
    try {
      const url = chrome.runtime.getURL(`_locales/${resolved}/messages.json`);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to load locale: ${resolved}`);
      }
      this.messages = await response.json();
    } catch (err) {
      this.messages = null;
    }
    this.apply();
  }
}