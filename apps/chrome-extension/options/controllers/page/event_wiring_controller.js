(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const i18n = opts.i18n && typeof opts.i18n === "object" ? opts.i18n : null;
    const ui = opts.ui && typeof opts.ui === "object"
      ? opts.ui
      : {
          COLORS: {
            SUCCESS: "#3c5a2a",
            ERROR: "#b42318",
            DEFAULT: "#6c675f"
          },
          LINKS: {
            app: "",
            plugin: ""
          }
        };
    const rulesShareController = opts.rulesShareController && typeof opts.rulesShareController === "object"
      ? opts.rulesShareController
      : null;
    const profileBackgroundController = opts.profileBackgroundController && typeof opts.profileBackgroundController === "object"
      ? opts.profileBackgroundController
      : null;
    const srsActionsController = opts.srsActionsController && typeof opts.srsActionsController === "object"
      ? opts.srsActionsController
      : null;
    const helperActionsController = opts.helperActionsController && typeof opts.helperActionsController === "object"
      ? opts.helperActionsController
      : null;
    const targetLanguageModalController = opts.targetLanguageModalController && typeof opts.targetLanguageModalController === "object"
      ? opts.targetLanguageModalController
      : null;
    const updateRulesSourceUI = typeof opts.updateRulesSourceUI === "function"
      ? opts.updateRulesSourceUI
      : (() => {});
    const saveDisplaySettings = typeof opts.saveDisplaySettings === "function"
      ? opts.saveDisplaySettings
      : (() => {});
    const saveReplacementSettings = typeof opts.saveReplacementSettings === "function"
      ? opts.saveReplacementSettings
      : (() => {});
    const saveSrsSettings = typeof opts.saveSrsSettings === "function"
      ? opts.saveSrsSettings
      : (() => Promise.resolve());
    const saveLanguageSettings = typeof opts.saveLanguageSettings === "function"
      ? opts.saveLanguageSettings
      : (() => Promise.resolve());
    const saveSrsProfileId = typeof opts.saveSrsProfileId === "function"
      ? opts.saveSrsProfileId
      : (() => Promise.resolve());
    const refreshSrsProfiles = typeof opts.refreshSrsProfiles === "function"
      ? opts.refreshSrsProfiles
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
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const generalBindings = root.optionsEventGeneralBindings && typeof root.optionsEventGeneralBindings.bind === "function"
      ? root.optionsEventGeneralBindings
      : { bind() {} };
    const profileBackgroundBindings = root.optionsEventProfileBackgroundBindings
      && typeof root.optionsEventProfileBackgroundBindings.bind === "function"
      ? root.optionsEventProfileBackgroundBindings
      : { bind() {} };
    const srsBindings = root.optionsEventSrsBindings && typeof root.optionsEventSrsBindings.bind === "function"
      ? root.optionsEventSrsBindings
      : { bind() {} };

    let bound = false;

    function bindAsyncListener(element, eventName, action, config) {
      if (!element) {
        return;
      }
      const options = config && typeof config === "object" ? config : {};
      const fallbackMessageResolver = typeof options.fallbackMessage === "function"
        ? options.fallbackMessage
        : () => String(options.fallbackMessage || "Action failed.");
      const logMessage = String(options.logMessage || "Action failed.");
      const onError = typeof options.onError === "function"
        ? options.onError
        : (message) => setStatus(message, ui.COLORS.ERROR);
      element.addEventListener(eventName, () => {
        Promise.resolve()
          .then(() => action())
          .catch((err) => {
            const fallbackMessage = fallbackMessageResolver();
            const message = err && err.message ? err.message : fallbackMessage;
            onError(message, err);
            log(logMessage, err);
          });
      });
    }

    function bind() {
      if (bound) {
        return;
      }
      bound = true;

      generalBindings.bind({
        t: translate,
        setStatus,
        i18n,
        ui,
        rulesShareController,
        targetLanguageModalController,
        updateRulesSourceUI,
        saveDisplaySettings,
        saveReplacementSettings,
        saveLanguageSettings,
        applyTargetLanguagePrefsLocalization,
        renderSrsProfileStatus,
        updateTargetLanguagePrefsModalVisibility,
        setTargetLanguagePrefsModalOpen,
        elements
      });

      profileBackgroundBindings.bind({
        bindAsyncListener,
        profileBackgroundController,
        elements
      });

      srsBindings.bind({
        t: translate,
        bindAsyncListener,
        helperActionsController,
        srsActionsController,
        saveSrsSettings,
        saveSrsProfileId,
        refreshSrsProfiles,
        elements
      });
    }

    return {
      bind
    };
  }

  root.optionsEventWiring = {
    createController
  };
})();
