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

    function dispatchPreflightBlocked(detail) {
      if (
        !globalThis.document
        || typeof globalThis.document.dispatchEvent !== "function"
        || typeof globalThis.CustomEvent !== "function"
      ) {
        return;
      }
      globalThis.document.dispatchEvent(new globalThis.CustomEvent(
        "lexishift:srs-preflight-blocked",
        { detail }
      ));
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
      const runtimeOptions = options && typeof options === "object" ? options : {};
      const ignoredMissingInputTypes = new Set(
        Array.isArray(runtimeOptions.ignoredMissingInputTypes)
          ? runtimeOptions.ignoredMissingInputTypes.map((value) => String(value || "").trim()).filter(Boolean)
          : []
      );
      const setOutputTextOverride = typeof runtimeOptions.setOutputText === "function"
        ? runtimeOptions.setOutputText
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
      const missingInputs = Array.isArray(helperData.missing_inputs)
        ? helperData.missing_inputs.filter((entry) => {
            const type = entry && entry.type ? String(entry.type).trim() : "";
            return !ignoredMissingInputTypes.has(type);
          })
        : [];
      if (!missingInputs.length) {
        return true;
      }
      const helperDataForOutput = {
        ...helperData,
        missing_inputs: missingInputs
      };
      const lines = buildPreflightBlockedLines({
        actionLabel,
        pair,
        profileId,
        helperData: helperDataForOutput
      });
      dispatchPreflightBlocked({
        actionLabel,
        pair,
        profileId,
        missingInputs,
        helperData: helperDataForOutput
      });
      setOutputTextOverride(lines.join("\n"));
      setStatus(
        `Missing resources for ${pair}. Add the required files and try again.`,
        colors.ERROR
      );
      log("SRS preflight failed due to missing resources", {
        pair,
        profileId,
        helper: helperDataForOutput
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
