(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createUiBridge(options) {
    const opts = options && typeof options === "object" ? options : {};
    const ui = opts.ui && typeof opts.ui === "object" ? opts.ui : null;

    function setStatus(message, color) {
      if (!ui || typeof ui.setStatus !== "function") {
        return;
      }
      ui.setStatus(message, color);
    }

    function setHelperStatus(status, lastSync) {
      if (!ui || typeof ui.setHelperStatus !== "function") {
        return;
      }
      ui.setHelperStatus(status, lastSync);
    }

    function updateRulesMeta(rules, updatedAt) {
      if (!ui || typeof ui.updateRulesMeta !== "function") {
        return;
      }
      ui.updateRulesMeta(rules, updatedAt);
    }

    function updateRulesSourceUI(source) {
      if (!ui || typeof ui.updateRulesSourceUI !== "function") {
        return;
      }
      ui.updateRulesSourceUI(source);
    }

    return {
      setStatus,
      setHelperStatus,
      updateRulesMeta,
      updateRulesSourceUI
    };
  }

  root.optionsUiBridge = {
    createUiBridge
  };
})();
