(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createStatusHelpers(options) {
    const opts = options && typeof options === "object" ? options : {};
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : { DEFAULT: "#6c675f" };
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const statusOutput = opts.statusOutput || null;
    const rulesetStatus = opts.rulesetStatus || null;
    const srsPairStatus = opts.srsPairStatus || null;
    const moduleStatus = opts.moduleStatus || null;
    const exportStatusOutput = opts.exportStatusOutput || null;
    const importStatusOutput = opts.importStatusOutput || null;

    function setOutputStatus(output, message, color) {
      if (!output) {
        return;
      }
      output.textContent = message || "";
      output.style.color = color || colors.DEFAULT;
    }

    function setCardStatus(message, color) {
      setOutputStatus(statusOutput, message, color);
      if (message) {
        setStatus(message, color || colors.DEFAULT);
      }
    }

    function setRulesetStatus(message, color) {
      setOutputStatus(rulesetStatus, message, color);
    }

    function setSrsPairStatus(message, color) {
      setOutputStatus(srsPairStatus, message, color);
    }

    function setModuleStatus(message, color) {
      setOutputStatus(moduleStatus, message, color);
    }

    function setExportStatus(message, color) {
      setOutputStatus(exportStatusOutput, message, color);
      if (message) {
        setCardStatus(message, color);
      }
    }

    function setExportHint(message) {
      setOutputStatus(exportStatusOutput, message, colors.DEFAULT);
    }

    function setImportStatus(message, color) {
      setOutputStatus(importStatusOutput, message, color);
      if (message) {
        setCardStatus(message, color);
      }
    }

    return {
      setOutputStatus,
      setCardStatus,
      setRulesetStatus,
      setSrsPairStatus,
      setModuleStatus,
      setExportStatus,
      setExportHint,
      setImportStatus
    };
  }

  root.optionsShareCenterStatus = {
    createStatusHelpers
  };
})();
