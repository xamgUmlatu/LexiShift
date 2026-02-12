(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function bind(options) {
    const opts = options && typeof options === "object" ? options : {};
    const rulesBindings = root.optionsEventGeneralRulesBindings
      && typeof root.optionsEventGeneralRulesBindings.bind === "function"
      ? root.optionsEventGeneralRulesBindings
      : { bind() {} };
    const displayBindings = root.optionsEventGeneralDisplayBindings
      && typeof root.optionsEventGeneralDisplayBindings.bind === "function"
      ? root.optionsEventGeneralDisplayBindings
      : { bind() {} };
    const languageBindings = root.optionsEventGeneralLanguageBindings
      && typeof root.optionsEventGeneralLanguageBindings.bind === "function"
      ? root.optionsEventGeneralLanguageBindings
      : { bind() {} };
    const integrationsBindings = root.optionsEventGeneralIntegrationsBindings
      && typeof root.optionsEventGeneralIntegrationsBindings.bind === "function"
      ? root.optionsEventGeneralIntegrationsBindings
      : { bind() {} };

    rulesBindings.bind({
      t: opts.t,
      setStatus: opts.setStatus,
      ui: opts.ui,
      rulesShareController: opts.rulesShareController,
      updateRulesSourceUI: opts.updateRulesSourceUI,
      elements: opts.elements
    });

    displayBindings.bind({
      t: opts.t,
      setStatus: opts.setStatus,
      ui: opts.ui,
      saveDisplaySettings: opts.saveDisplaySettings,
      saveReplacementSettings: opts.saveReplacementSettings,
      elements: opts.elements
    });

    languageBindings.bind({
      t: opts.t,
      setStatus: opts.setStatus,
      i18n: opts.i18n,
      ui: opts.ui,
      saveLanguageSettings: opts.saveLanguageSettings,
      applyTargetLanguagePrefsLocalization: opts.applyTargetLanguagePrefsLocalization,
      renderSrsProfileStatus: opts.renderSrsProfileStatus,
      renderProfileBackgroundStatus: opts.renderProfileBackgroundStatus,
      updateTargetLanguagePrefsModalVisibility: opts.updateTargetLanguagePrefsModalVisibility,
      setTargetLanguagePrefsModalOpen: opts.setTargetLanguagePrefsModalOpen,
      targetLanguageModalController: opts.targetLanguageModalController,
      elements: opts.elements
    });

    integrationsBindings.bind({
      ui: opts.ui,
      elements: opts.elements
    });
  }

  root.optionsEventGeneralBindings = {
    bind
  };
})();
