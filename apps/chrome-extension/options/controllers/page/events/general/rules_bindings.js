(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function bind(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const ui = opts.ui && typeof opts.ui === "object"
      ? opts.ui
      : {
          COLORS: {
            SUCCESS: "#3c5a2a",
            ERROR: "#b42318",
            DEFAULT: "#6c675f"
          }
        };
    const rulesShareController = opts.rulesShareController && typeof opts.rulesShareController === "object"
      ? opts.rulesShareController
      : null;
    const updateRulesSourceUI = typeof opts.updateRulesSourceUI === "function"
      ? opts.updateRulesSourceUI
      : (() => {});
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const saveButton = elements.saveButton || null;
    const importFileButton = elements.importFileButton || null;
    const exportFileButton = elements.exportFileButton || null;
    const rulesSourceInputs = Array.isArray(elements.rulesSourceInputs) ? elements.rulesSourceInputs : [];
    const generateCodeButton = elements.generateCodeButton || null;
    const importCodeButton = elements.importCodeButton || null;
    const copyCodeButton = elements.copyCodeButton || null;

    if (saveButton && rulesShareController && typeof rulesShareController.saveRules === "function") {
      saveButton.addEventListener("click", () => {
        rulesShareController.saveRules();
      });
    }
    if (importFileButton && rulesShareController && typeof rulesShareController.importFromFile === "function") {
      importFileButton.addEventListener("click", () => {
        rulesShareController.importFromFile();
      });
    }
    if (exportFileButton && rulesShareController && typeof rulesShareController.exportToFile === "function") {
      exportFileButton.addEventListener("click", () => {
        rulesShareController.exportToFile();
      });
    }

    rulesSourceInputs.forEach((input) => {
      input.addEventListener("change", () => {
        const selected = rulesSourceInputs.find((item) => item.checked);
        const value = selected ? selected.value : "editor";
        chrome.storage.local.set({ rulesSource: value }, () => {
          updateRulesSourceUI(value);
          setStatus(translate("status_rules_source_updated", null, "Rules source updated."), ui.COLORS.SUCCESS);
        });
      });
    });

    if (generateCodeButton && rulesShareController && typeof rulesShareController.generateShareCode === "function") {
      generateCodeButton.addEventListener("click", () => {
        rulesShareController.generateShareCode();
      });
    }
    if (importCodeButton && rulesShareController && typeof rulesShareController.importShareCode === "function") {
      importCodeButton.addEventListener("click", () => {
        rulesShareController.importShareCode();
      });
    }
    if (copyCodeButton && rulesShareController && typeof rulesShareController.copyShareCode === "function") {
      copyCodeButton.addEventListener("click", () => {
        rulesShareController.copyShareCode();
      });
    }
  }

  root.optionsEventGeneralRulesBindings = {
    bind
  };
})();
