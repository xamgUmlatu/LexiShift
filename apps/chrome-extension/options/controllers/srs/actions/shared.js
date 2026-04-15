(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createShared(options) {
    const opts = options && typeof options === "object" ? options : {};
    const output = opts.output || null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const buildPreflightBlockedLines = typeof opts.buildPreflightBlockedLines === "function"
      ? opts.buildPreflightBlockedLines
      : (_options) => [];
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          ERROR: "#b42318"
        };
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    function setOutputText(text) {
      if (!output) {
        return;
      }
      output.textContent = text;
    }

    async function markRulesetUpdatedNow() {
      await new Promise((resolve) => {
        chrome.storage.local.set(
          { srsRulesetUpdatedAt: new Date().toISOString() },
          () => resolve()
        );
      });
    }

    async function preflightSrsPairResources(pair, profileId, actionLabel, options) {
      const preflightOptions = options && typeof options === "object" ? options : {};
      const setPreflightOutputText = typeof preflightOptions.setOutputText === "function"
        ? preflightOptions.setOutputText
        : setOutputText;
      if (!helperManager || typeof helperManager.getSrsRuntimeDiagnostics !== "function") {
        return true;
      }
      const diagnostics = await helperManager.getSrsRuntimeDiagnostics(pair, { profileId });
      const helperData = diagnostics && diagnostics.helper && typeof diagnostics.helper === "object"
        ? diagnostics.helper
        : null;
      if (!helperData) {
        return true;
      }
      const ignoredMissingInputTypes = Array.isArray(preflightOptions.ignoredMissingInputTypes)
        ? new Set(
            preflightOptions.ignoredMissingInputTypes
              .map((value) => String(value || "").trim())
              .filter((value) => value)
          )
        : null;
      const missingInputs = Array.isArray(helperData.missing_inputs)
        ? helperData.missing_inputs.filter((entry) => {
            if (!ignoredMissingInputTypes || !ignoredMissingInputTypes.size) {
              return true;
            }
            const type = entry && entry.type ? String(entry.type).trim() : "";
            return !ignoredMissingInputTypes.has(type);
          })
        : [];
      if (!missingInputs.length) {
        return true;
      }
      const lines = buildPreflightBlockedLines({
        actionLabel,
        pair,
        profileId,
        helperData: {
          ...helperData,
          missing_inputs: missingInputs
        }
      });
      setPreflightOutputText(lines.join("\n"));
      setStatus(
        `Missing resources for ${pair}. Add the required files and try again.`,
        colors.ERROR
      );
      log("SRS preflight failed due to missing resources", {
        pair,
        profileId,
        helper: helperData
      });
      return false;
    }

    return {
      setOutputText,
      markRulesetUpdatedNow,
      preflightSrsPairResources
    };
  }

  root.optionsSrsActionsShared = {
    createShared
  };
})();
