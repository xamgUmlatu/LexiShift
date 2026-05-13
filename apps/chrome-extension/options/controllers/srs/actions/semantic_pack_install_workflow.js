(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createSemanticPackInstallWorkflow(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const confirmFn = typeof opts.confirmFn === "function"
      ? opts.confirmFn
      : (message) => globalThis.confirm(message);
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const setOutputText = typeof opts.setOutputText === "function" ? opts.setOutputText : (() => {});
    const semanticPackInventoryPathInput = opts.semanticPackInventoryPathInput || null;
    const semanticPackIdInput = opts.semanticPackIdInput || null;
    const semanticPackDefaultDataRootInput = opts.semanticPackDefaultDataRootInput || null;
    const semanticPackDataRootInput = opts.semanticPackDataRootInput || null;
    const semanticPackInstallButton = opts.semanticPackInstallButton || null;
    const semanticPackInstallOutput = opts.semanticPackInstallOutput || null;
    const markRulesetUpdatedNow = typeof opts.markRulesetUpdatedNow === "function"
      ? opts.markRulesetUpdatedNow
      : (() => Promise.resolve());
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({
          items,
          profileId: "default"
        }));
    const refreshSemanticAdmissionStatus = typeof opts.refreshSemanticAdmissionStatus === "function"
      ? opts.refreshSemanticAdmissionStatus
      : (() => Promise.resolve());

    function setSemanticPackOutput(text) {
      if (semanticPackInstallOutput) {
        semanticPackInstallOutput.textContent = text || "";
        return;
      }
      setOutputText(text || "");
    }

    function renderSemanticPackInstallResult(result) {
      const summary = result && typeof result.summary === "object" ? result.summary : {};
      const paths = result && typeof result.target_paths === "object" ? result.target_paths : {};
      const ruleCount = Number(summary.rule_count || 0);
      const competitionCount = Number(summary.competition_set_count || 0);
      const profileId = String((result && result.profile_id) || "default");
      const packId = String(
        (result && result.pack_id) || "en-es-active-only-combined-full-v1-tranche-007"
      );
      const rulesetPath = String(paths.ruleset || "");
      return [
        translate(
          "status_semantic_pack_install_success",
          [packId, profileId, ruleCount, competitionCount],
          `Installed ${packId} for ${profileId}: ${ruleCount} rules, ${competitionCount} competition sets.`
        ),
        rulesetPath ? `ruleset: ${rulesetPath}` : ""
      ].filter((line) => line).join("\n");
    }

    async function installSemanticPack() {
      if (!semanticPackInstallButton) {
        return;
      }
      const srsPair = resolvePair();
      const semanticInventoryPath = semanticPackInventoryPathInput
        ? String(semanticPackInventoryPathInput.value || "").trim()
        : "";
      const packId = semanticPackIdInput ? String(semanticPackIdInput.value || "").trim() : "";
      const allowDefaultDataRoot = semanticPackDefaultDataRootInput
        ? semanticPackDefaultDataRootInput.checked === true
        : false;
      const dataRoot = semanticPackDataRootInput
        ? String(semanticPackDataRootInput.value || "").trim()
        : "";
      if (!dataRoot && !allowDefaultDataRoot) {
        const msg = translate(
          "status_semantic_pack_data_root_required",
          null,
          "Data root is required unless default data root is enabled."
        );
        setSemanticPackOutput(msg);
        setStatus(msg, colors.ERROR);
        return;
      }
      if (!helperManager || typeof helperManager.installSemanticPack !== "function") {
        const msg = translate("status_helper_missing", null, "Helper unavailable.");
        setSemanticPackOutput(msg);
        setStatus(msg, colors.ERROR);
        return;
      }

      const items = settingsManager && typeof settingsManager.load === "function"
        ? await settingsManager.load()
        : {};
      const synced = await syncSelectedProfile(items);
      if (!confirmFn(translate(
        "confirm_semantic_pack_install",
        [srsPair, synced.profileId],
        `Install semantic pack for ${srsPair} profile ${synced.profileId}? This overwrites the profile-local semantic publication files.`
      ))) {
        return;
      }

      semanticPackInstallButton.disabled = true;
      setSemanticPackOutput(translate(
        "status_semantic_pack_install_running",
        null,
        "Installing semantic pack…"
      ));
      try {
        const result = await helperManager.installSemanticPack(srsPair, {
          profileId: synced.profileId,
          semanticInventoryPath,
          packId,
          allowDefaultDataRoot,
          dataRoot
        });
        setSemanticPackOutput(renderSemanticPackInstallResult(result));
        await markRulesetUpdatedNow();
        await refreshSemanticAdmissionStatus(srsPair, synced.profileId);
        setStatus(
          translate("status_semantic_pack_install_ready", null, "Semantic pack installed."),
          colors.SUCCESS
        );
        log("Semantic pack installed", {
          pair: srsPair,
          profileId: synced.profileId,
          result
        });
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate(
              "status_semantic_pack_install_failed",
              null,
              "Semantic pack install failed."
            );
        setSemanticPackOutput(msg);
        setStatus(msg, colors.ERROR);
        log("Semantic pack install failed.", err);
      } finally {
        semanticPackInstallButton.disabled = false;
      }
    }

    return { installSemanticPack };
  }

  root.optionsSrsSemanticPackInstallWorkflow = {
    createSemanticPackInstallWorkflow
  };
})();
