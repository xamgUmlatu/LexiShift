(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setHelperStatus = typeof opts.setHelperStatus === "function"
      ? opts.setHelperStatus
      : (() => {});
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const debugHelperTestButton = elements.debugHelperTestButton || null;
    const debugHelperTestOutput = elements.debugHelperTestOutput || null;
    const debugOpenDataDirButton = elements.debugOpenDataDirButton || null;
    const debugOpenDataDirOutput = elements.debugOpenDataDirOutput || null;

    async function refreshStatus() {
      if (!helperManager || typeof helperManager.getStatus !== "function") {
        return;
      }
      setHelperStatus(translate("status_helper_connecting", null, "Connecting…"), "");
      const result = await helperManager.getStatus();
      setHelperStatus(result.message, result.lastRun);
    }

    async function testConnection() {
      if (!debugHelperTestButton || !debugHelperTestOutput) {
        return;
      }
      debugHelperTestButton.disabled = true;
      debugHelperTestOutput.textContent = translate("status_helper_connecting", null, "Connecting…");
      const message = await helperManager.testConnection();
      debugHelperTestOutput.textContent = message;
      debugHelperTestButton.disabled = false;
    }

    async function openDataDir() {
      if (!debugOpenDataDirButton || !debugOpenDataDirOutput) {
        return;
      }
      debugOpenDataDirButton.disabled = true;
      debugOpenDataDirOutput.textContent = translate("status_helper_connecting", null, "Connecting…");
      const message = await helperManager.openDataDir();
      debugOpenDataDirOutput.textContent = message;
      debugOpenDataDirButton.disabled = false;
    }

    return {
      refreshStatus,
      testConnection,
      openDataDir
    };
  }

  root.optionsHelperActions = {
    createController
  };
})();
