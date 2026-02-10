(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function bind(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.t === "function"
      ? opts.t
      : ((_key, _subs, fallback) => fallback || "");
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const i18n = opts.i18n && typeof opts.i18n === "object" ? opts.i18n : null;
    const ui = opts.ui && typeof opts.ui === "object"
      ? opts.ui
      : {
          COLORS: {
            SUCCESS: "#3c5a2a",
            ERROR: "#b42318",
            DEFAULT: "#6c675f"
          }
        };
    const saveLanguageSettings = typeof opts.saveLanguageSettings === "function"
      ? opts.saveLanguageSettings
      : (() => Promise.resolve());
    const applyTargetLanguagePrefsLocalization = typeof opts.applyTargetLanguagePrefsLocalization === "function"
      ? opts.applyTargetLanguagePrefsLocalization
      : (() => {});
    const renderSrsProfileStatus = typeof opts.renderSrsProfileStatus === "function"
      ? opts.renderSrsProfileStatus
      : (() => {});
    const updateTargetLanguagePrefsModalVisibility = typeof opts.updateTargetLanguagePrefsModalVisibility === "function"
      ? opts.updateTargetLanguagePrefsModalVisibility
      : (() => {});
    const setTargetLanguagePrefsModalOpen = typeof opts.setTargetLanguagePrefsModalOpen === "function"
      ? opts.setTargetLanguagePrefsModalOpen
      : (() => {});
    const targetLanguageModalController = opts.targetLanguageModalController
      && typeof opts.targetLanguageModalController === "object"
      ? opts.targetLanguageModalController
      : null;
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const languageSelect = elements.languageSelect || null;
    const sourceLanguageInput = elements.sourceLanguageInput || null;
    const targetLanguageInput = elements.targetLanguageInput || null;
    const targetLanguageGearButton = elements.targetLanguageGearButton || null;
    const jaPrimaryDisplayScriptInput = elements.jaPrimaryDisplayScriptInput || null;
    const targetLanguagePrefsModalBackdrop = elements.targetLanguagePrefsModalBackdrop || null;
    const targetLanguagePrefsModalOkButton = elements.targetLanguagePrefsModalOkButton || null;

    if (languageSelect) {
      languageSelect.addEventListener("change", () => {
        const value = languageSelect.value || "system";
        chrome.storage.local.set({ uiLanguage: value }, () => {
          Promise.resolve(i18n && typeof i18n.load === "function" ? i18n.load(value) : undefined).finally(() => {
            applyTargetLanguagePrefsLocalization();
            renderSrsProfileStatus();
            setStatus(translate("status_language_updated", null, "Language updated."), ui.COLORS.SUCCESS);
          });
        });
      });
    }

    applyTargetLanguagePrefsLocalization();

    if (sourceLanguageInput) {
      sourceLanguageInput.addEventListener("change", saveLanguageSettings);
    }
    if (targetLanguageInput) {
      targetLanguageInput.addEventListener("change", () => {
        if (String(targetLanguageInput.value || "").trim().toLowerCase() !== "ja") {
          setTargetLanguagePrefsModalOpen(false);
        }
        updateTargetLanguagePrefsModalVisibility(targetLanguageInput.value || "");
        saveLanguageSettings();
      });
    }
    if (targetLanguageGearButton && targetLanguageModalController && typeof targetLanguageModalController.toggle === "function") {
      targetLanguageGearButton.addEventListener("click", () => {
        targetLanguageModalController.toggle();
      });
    }
    if (jaPrimaryDisplayScriptInput) {
      jaPrimaryDisplayScriptInput.addEventListener("change", () => {
        saveLanguageSettings();
      });
    }
    if (targetLanguagePrefsModalBackdrop
      && targetLanguageModalController
      && typeof targetLanguageModalController.handleBackdropClick === "function") {
      targetLanguagePrefsModalBackdrop.addEventListener("click", (event) => {
        targetLanguageModalController.handleBackdropClick(event);
      });
    }
    if (targetLanguagePrefsModalOkButton
      && targetLanguageModalController
      && typeof targetLanguageModalController.handleOkClick === "function") {
      targetLanguagePrefsModalOkButton.addEventListener("click", () => {
        targetLanguageModalController.handleOkClick();
      });
    }
    if (targetLanguageModalController && typeof targetLanguageModalController.handleKeydown === "function") {
      document.addEventListener("keydown", (event) => {
        targetLanguageModalController.handleKeydown(event);
      });
    }
  }

  root.optionsEventGeneralLanguageBindings = {
    bind
  };
})();
