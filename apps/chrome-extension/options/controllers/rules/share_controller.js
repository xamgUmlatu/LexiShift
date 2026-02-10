(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const rulesManager = opts.rulesManager && typeof opts.rulesManager === "object"
      ? opts.rulesManager
      : null;
    const translate = typeof opts.t === "function"
      ? opts.t
      : ((_key, _substitutions, fallback) => fallback || "");
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const updateRulesSourceUI = typeof opts.updateRulesSourceUI === "function"
      ? opts.updateRulesSourceUI
      : (() => {});
    const updateRulesMeta = typeof opts.updateRulesMeta === "function"
      ? opts.updateRulesMeta
      : (() => {});
    const errorMessage = typeof opts.errorMessage === "function"
      ? opts.errorMessage
      : ((err, _fallbackKey, fallbackText) => (err && err.message) || fallbackText || "");
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const rulesInput = elements.rulesInput || null;
    const rulesFileInput = elements.rulesFileInput || null;
    const fileStatus = elements.fileStatus || null;
    const shareCodeInput = elements.shareCodeInput || null;
    const shareCodeCjk = elements.shareCodeCjk || null;

    async function saveRules() {
      if (!rulesManager || !rulesInput) {
        return;
      }
      if (rulesInput.disabled) {
        setStatus(
          translate("status_switch_edit_json", null, "Switch to Edit JSON to save changes."),
          colors.ERROR
        );
        return;
      }
      try {
        const { rules, updatedAt } = await rulesManager.saveFromEditor(rulesInput.value);
        updateRulesSourceUI("editor");
        updateRulesMeta(rules, updatedAt);
        setStatus(translate("status_rules_saved", null, "Rules saved."), colors.SUCCESS);
      } catch (err) {
        setStatus(errorMessage(err, "status_invalid_json", "Invalid JSON file."), colors.ERROR);
      }
    }

    async function importFromFile() {
      if (!rulesManager || !rulesFileInput || !rulesInput) {
        return;
      }
      const file = rulesFileInput.files && rulesFileInput.files[0];
      if (!file) {
        setStatus(translate("status_choose_json_file", null, "Choose a JSON file first."), colors.ERROR);
        return;
      }
      try {
        const { rules, updatedAt, fileName } = await rulesManager.importFromFile(file);
        rulesInput.value = JSON.stringify(rules, null, 2);
        updateRulesSourceUI("file");
        updateRulesMeta(rules, updatedAt);
        if (fileStatus) {
          fileStatus.textContent = translate("file_status_last_imported", fileName, `Last imported: ${fileName}`);
        }
        setStatus(translate("status_imported_rules", String(rules.length), `Imported ${rules.length} rules.`), colors.SUCCESS);
      } catch (err) {
        setStatus(errorMessage(err, "status_invalid_json", "Invalid JSON file."), colors.ERROR);
      }
    }

    function exportToFile() {
      if (!rulesManager) {
        return;
      }
      rulesManager.exportToFile();
      setStatus(translate("status_exported_rules", null, "Exported rules."), colors.SUCCESS);
    }

    function generateShareCode() {
      if (!rulesManager || !shareCodeInput || !shareCodeCjk || !rulesInput) {
        return;
      }
      try {
        const code = rulesManager.generateShareCode(shareCodeCjk.checked, rulesInput.value, rulesInput.disabled);
        shareCodeInput.value = code;
        setStatus(
          translate(
            "status_generated_code",
            String(shareCodeInput.value.length),
            `Code generated (${shareCodeInput.value.length} chars).`
          ),
          colors.SUCCESS
        );
      } catch (err) {
        setStatus(
          err && err.message ? err.message : translate("status_generate_failed", null, "Failed to generate code."),
          colors.ERROR
        );
      }
    }

    async function importShareCode() {
      if (!rulesManager || !shareCodeInput || !shareCodeCjk || !rulesInput) {
        return;
      }
      try {
        const { rules, updatedAt } = await rulesManager.importShareCode(shareCodeInput.value, shareCodeCjk.checked);
        rulesInput.value = JSON.stringify(rules, null, 2);
        updateRulesSourceUI("editor");
        updateRulesMeta(rules, updatedAt);
        setStatus(translate("status_code_imported", null, "Code imported."), colors.SUCCESS);
      } catch (err) {
        setStatus(
          err && err.message ? err.message : translate("status_invalid_code", null, "Invalid code."),
          colors.ERROR
        );
      }
    }

    function copyShareCode() {
      if (!shareCodeInput || !shareCodeInput.value) {
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(shareCodeInput.value).then(() => {
          setStatus(translate("status_copied", null, "Copied."), colors.SUCCESS);
        });
        return;
      }
      shareCodeInput.select();
      document.execCommand("copy");
      setStatus(translate("status_copied", null, "Copied."), colors.SUCCESS);
    }

    return {
      saveRules,
      importFromFile,
      exportToFile,
      generateShareCode,
      importShareCode,
      copyShareCode
    };
  }

  root.optionsRulesShare = {
    createController
  };
})();
