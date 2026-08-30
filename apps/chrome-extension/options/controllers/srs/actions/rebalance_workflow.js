(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRebalanceWorkflows(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const resolvePair = typeof opts.resolvePair === "function" ? opts.resolvePair : (() => "en-en");
    const syncSelectedProfile = typeof opts.syncSelectedProfile === "function"
      ? opts.syncSelectedProfile
      : ((items) => Promise.resolve({ items, profileId: "default" }));
    const resolvePlanningState = typeof opts.resolvePlanningState === "function"
      ? opts.resolvePlanningState
      : (() => null);
    const preflightSrsPairResources = typeof opts.preflightSrsPairResources === "function"
      ? opts.preflightSrsPairResources
      : (() => Promise.resolve(true));
    const buildRebalanceResultOutput = typeof opts.buildRebalanceResultOutput === "function"
      ? opts.buildRebalanceResultOutput
      : (() => "");
    const rebalancePreviewButton = opts.rebalancePreviewButton || null;
    const rebalanceApplyButton = opts.rebalanceApplyButton || null;
    const setOutputText = typeof opts.setOutputText === "function" ? opts.setOutputText : (() => {});
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const confirmFn = typeof opts.confirmFn === "function" ? opts.confirmFn : (message) => globalThis.confirm(message);
    const markRulesetUpdatedNow = typeof opts.markRulesetUpdatedNow === "function"
      ? opts.markRulesetUpdatedNow
      : (() => Promise.resolve());
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };

    async function previewRebalance() {
      if (!rebalancePreviewButton) {
        return;
      }
      const srsPair = resolvePair();
      rebalancePreviewButton.disabled = true;
      setOutputText(translate(
        "status_srs_rebalance_preview_running",
        [srsPair],
        `Preparing preference retune preview for ${srsPair}…`
      ));

      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
        const canProceed = await preflightSrsPairResources(
          srsPair,
          synced.profileId,
          "preference retune preview"
        );
        if (!canProceed) {
          return;
        }
        const planningState = resolvePlanningState(synced.items, srsPair, synced.profileId);
        const profileContext = planningState.profileContext;
        const result = await helperManager.planSrsRebalance(srsPair, {
          profileId: synced.profileId,
          strategy: "profile_growth",
          objective: "rebalance",
          maxActiveItems: planningState.profile.srsMaxActive || settingsManager.defaults.srsMaxActive || 40,
          trigger: "options_rebalance_preview_button",
          profileContext
        });
        setOutputText(buildRebalanceResultOutput({
          translate,
          srsPair,
          profileId: result.profile_id || synced.profileId,
          payload: result,
          mode: "preview"
        }));
        setStatus(
          result.plan && result.plan.can_execute === true
            ? translate("status_srs_rebalance_ready", [srsPair], `Preference retune preview ready for ${srsPair}.`)
            : translate("status_srs_rebalance_blocked", [srsPair], `Preference retune is not ready for ${srsPair}.`),
          result.plan && result.plan.can_execute === true ? colors.SUCCESS : colors.DEFAULT
        );
        log("SRS rebalance preview", {
          pair: srsPair,
          result,
          profileContext,
          requestProfileContextMeta: planningState.contextMeta
        });
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_rebalance_preview_failed", null, "Preference retune preview failed.");
        setOutputText(msg);
        setStatus(msg, colors.ERROR);
        log("SRS rebalance preview failed.", err);
      } finally {
        rebalancePreviewButton.disabled = false;
      }
    }

    async function applyRebalance() {
      if (!rebalanceApplyButton) {
        return;
      }
      const srsPair = resolvePair();
      rebalanceApplyButton.disabled = true;
      setOutputText(translate(
        "status_srs_rebalance_apply_running",
        [srsPair],
        `Preparing preference retune for ${srsPair}…`
      ));

      try {
        const items = await settingsManager.load();
        const synced = await syncSelectedProfile(items);
        const canProceed = await preflightSrsPairResources(
          srsPair,
          synced.profileId,
          "preference retune"
        );
        if (!canProceed) {
          return;
        }
        const planningState = resolvePlanningState(synced.items, srsPair, synced.profileId);
        const profileContext = planningState.profileContext;
        const requestOptions = {
          profileId: synced.profileId,
          strategy: "profile_growth",
          objective: "rebalance",
          maxActiveItems: planningState.profile.srsMaxActive || settingsManager.defaults.srsMaxActive || 40,
          profileContext
        };
        const previewResult = await helperManager.planSrsRebalance(srsPair, {
          ...requestOptions,
          trigger: "options_rebalance_apply_preview"
        });
        setOutputText(buildRebalanceResultOutput({
          translate,
          srsPair,
          profileId: previewResult.profile_id || synced.profileId,
          payload: previewResult,
          mode: "preview"
        }));
        if (!previewResult.plan || previewResult.plan.can_execute !== true) {
          setStatus(
            translate("status_srs_rebalance_blocked", [srsPair], `Preference retune is not ready for ${srsPair}.`),
            colors.DEFAULT
          );
          return;
        }
        const summary = previewResult.summary && typeof previewResult.summary === "object"
          ? previewResult.summary
          : {};
        const keepCount = Number(summary.proposed_keep_count || 0);
        const parkCount = Number(summary.proposed_park_count || 0);
        const activateCount = Number(summary.proposed_activate_count || 0);
        const confirmMessage = [
          translate(
            "confirm_srs_rebalance_title",
            [srsPair],
            `Retune active words for ${srsPair} using current preferences?`
          ),
          translate(
            "confirm_srs_rebalance_body_counts",
            [keepCount, parkCount, activateCount],
            `${keepCount} protected words will stay active, ${parkCount} low-commitment words will move out of active practice, and ${activateCount} words will move in. Review history will be preserved.`
          )
        ].join("\n\n");
        if (!confirmFn(confirmMessage)) {
          setStatus(
            translate("status_srs_rebalance_cancelled", [srsPair], `Preference retune cancelled for ${srsPair}.`),
            colors.DEFAULT
          );
          return;
        }
        const result = await helperManager.applySrsRebalance(srsPair, {
          ...requestOptions,
          trigger: "options_rebalance_apply_button"
        });
        setOutputText(buildRebalanceResultOutput({
          translate,
          srsPair,
          profileId: result.profile_id || synced.profileId,
          payload: result,
          mode: "apply"
        }));
        if (result.applied && result.rulegen && result.rulegen.published !== false) {
          await markRulesetUpdatedNow();
        }
        setStatus(
          result.applied
            ? translate("status_srs_rebalance_applied", [srsPair], `Preference retune applied for ${srsPair}.`)
            : translate("status_srs_rebalance_noop", [srsPair], `Preference retune for ${srsPair} did not need active-word changes.`),
          result.applied ? colors.SUCCESS : colors.DEFAULT
        );
        log("SRS rebalance apply", {
          pair: srsPair,
          result,
          profileContext,
          requestProfileContextMeta: planningState.contextMeta
        });
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_rebalance_apply_failed", null, "Preference retune failed.");
        setOutputText(msg);
        setStatus(msg, colors.ERROR);
        log("SRS rebalance apply failed.", err);
      } finally {
        rebalanceApplyButton.disabled = false;
      }
    }

    return {
      previewRebalance,
      applyRebalance
    };
  }

  root.optionsSrsRebalanceWorkflow = {
    createRebalanceWorkflows
  };
})();
