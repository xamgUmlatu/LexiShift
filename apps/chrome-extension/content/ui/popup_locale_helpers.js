(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function normalizeUiLanguageSetting(value) {
    const normalized = String(value || "").trim().toLowerCase();
    return normalized || "system";
  }

  function resolveSystemLocale() {
    if (typeof chrome !== "undefined"
      && chrome.i18n
      && typeof chrome.i18n.getUILanguage === "function") {
      const uiLanguage = String(chrome.i18n.getUILanguage() || "").trim();
      if (uiLanguage) {
        return uiLanguage;
      }
    }
    return String(
      (typeof navigator !== "undefined" && navigator.language)
      || "en"
    ).trim() || "en";
  }

  function resolveUiLocale(uiLanguageSetting, supportedLocales) {
    const normalized = normalizeUiLanguageSetting(uiLanguageSetting);
    const candidate = normalized === "system"
      ? resolveSystemLocale().toLowerCase()
      : normalized;
    const locales = Array.isArray(supportedLocales) && supportedLocales.length
      ? supportedLocales
      : ["en"];
    for (const locale of locales) {
      if (candidate === locale || candidate.startsWith(`${locale}-`)) {
        return locale;
      }
    }
    return "en";
  }

  function formatPopupMessage(message, substitutions) {
    if (!substitutions) {
      return message;
    }
    const values = Array.isArray(substitutions) ? substitutions : [substitutions];
    return String(message).replace(/\$([1-9]\d*)/g, (match, index) => {
      const value = values[Number(index) - 1];
      return value !== undefined ? String(value) : match;
    });
  }

  function getChromeMessage(key, substitutions) {
    try {
      if (typeof chrome !== "undefined"
        && chrome.i18n
        && typeof chrome.i18n.getMessage === "function") {
        return String(chrome.i18n.getMessage(key, substitutions) || "");
      }
    } catch (_error) {
      // Ignore i18n runtime errors and fall back to defaults.
    }
    return "";
  }

  function createLocaleManager(options = {}) {
    const supportedLocales = Array.isArray(options.supportedLocales) && options.supportedLocales.length
      ? options.supportedLocales.map((entry) => String(entry || "").trim().toLowerCase()).filter(Boolean)
      : ["en"];
    let activeUiLanguage = normalizeUiLanguageSetting(options.initialUiLanguage || "system");
    let popupLocaleMessages = null;
    const popupLocaleMessagesByLocale = {};
    let popupLocaleLoadToken = 0;

    function t(key, substitutions, fallback) {
      if (popupLocaleMessages && popupLocaleMessages[key] && popupLocaleMessages[key].message) {
        return formatPopupMessage(popupLocaleMessages[key].message, substitutions);
      }
      const localized = getChromeMessage(key, substitutions);
      if (localized) {
        return localized;
      }
      return String(fallback || key || "");
    }

    function refreshPopupLocaleMessages() {
      const token = (popupLocaleLoadToken += 1);
      if (activeUiLanguage === "system") {
        popupLocaleMessages = null;
        return;
      }
      const locale = resolveUiLocale(activeUiLanguage, supportedLocales);
      if (popupLocaleMessagesByLocale[locale]) {
        popupLocaleMessages = popupLocaleMessagesByLocale[locale];
        return;
      }
      popupLocaleMessages = null;
      if (typeof chrome === "undefined"
        || !chrome.runtime
        || typeof chrome.runtime.getURL !== "function") {
        popupLocaleMessages = null;
        return;
      }
      const url = chrome.runtime.getURL(`_locales/${locale}/messages.json`);
      fetch(url)
        .then((response) => {
          if (!response || !response.ok) {
            throw new Error(`Failed to load locale: ${locale}`);
          }
          return response.json();
        })
        .then((messages) => {
          if (token !== popupLocaleLoadToken) {
            return;
          }
          if (!messages || typeof messages !== "object") {
            popupLocaleMessages = null;
            return;
          }
          popupLocaleMessagesByLocale[locale] = messages;
          popupLocaleMessages = messages;
        })
        .catch(() => {
          if (token !== popupLocaleLoadToken) {
            return;
          }
          popupLocaleMessages = null;
        });
    }

    function setPopupUiLanguage(uiLanguageSetting) {
      const normalized = normalizeUiLanguageSetting(uiLanguageSetting);
      const localeChanged = normalized !== activeUiLanguage;
      activeUiLanguage = normalized;
      if (localeChanged || (activeUiLanguage !== "system" && !popupLocaleMessages)) {
        refreshPopupLocaleMessages();
      }
    }

    function resolveActivePopupLocale() {
      if (activeUiLanguage === "system") {
        return resolveSystemLocale();
      }
      return resolveUiLocale(activeUiLanguage, supportedLocales);
    }

    return {
      t,
      setPopupUiLanguage,
      resolveActivePopupLocale,
      getActiveUiLanguage: () => activeUiLanguage
    };
  }

  root.uiPopupLocaleHelpers = {
    createLocaleManager
  };
})();
