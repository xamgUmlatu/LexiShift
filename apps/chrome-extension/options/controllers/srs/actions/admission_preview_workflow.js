(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function generatePreviewSeed() {
    if (globalThis.crypto && typeof globalThis.crypto.getRandomValues === "function") {
      const buffer = new Uint32Array(1);
      globalThis.crypto.getRandomValues(buffer);
      return Number(buffer[0]);
    }
    return Math.floor(Math.random() * 2147483647);
  }

  function createAdmissionPreviewWorkflow(options) {
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
    const buildAdmissionPreviewOutput = typeof opts.buildAdmissionPreviewOutput === "function"
      ? opts.buildAdmissionPreviewOutput
      : (() => "");
    const admissionPreviewButton = opts.admissionPreviewButton || null;
    const setAdmissionPreviewOutputText = typeof opts.setAdmissionPreviewOutputText === "function"
      ? opts.setAdmissionPreviewOutputText
      : (() => {});
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    return async function previewAdmission(optionsArg) {
      const previewOptions = optionsArg && typeof optionsArg === "object" ? optionsArg : {};
      const outputWriter = typeof previewOptions.setOutputText === "function"
        ? previewOptions.setOutputText
        : setAdmissionPreviewOutputText;
      if (!admissionPreviewButton) {
        return;
      }
      const srsPair = String(previewOptions.pairKey || resolvePair() || "en-en").trim() || "en-en";
      const requestedPreviewCount = Number(previewOptions.previewCount);
      const previewCount = Number.isFinite(requestedPreviewCount) && requestedPreviewCount > 0
        ? Math.round(requestedPreviewCount)
        : 10;
      admissionPreviewButton.disabled = true;
      outputWriter(translate(
        "status_srs_admission_preview_running",
        [previewCount],
        `Sampling possible next words (${previewCount})…`
      ));

      try {
        const items = previewOptions.items && typeof previewOptions.items === "object"
          ? previewOptions.items
          : await settingsManager.load();
        const synced = previewOptions.skipSelectedProfileSync === true
          ? {
              items,
              profileId: String(
                previewOptions.profileId
                || (settingsManager && typeof settingsManager.getSelectedSrsProfileId === "function"
                  ? settingsManager.getSelectedSrsProfileId(items)
                  : "default")
              ).trim() || "default"
            }
          : await syncSelectedProfile(items);
        const profileId = String(previewOptions.profileId || synced.profileId || "default").trim() || "default";
        const canProceed = await preflightSrsPairResources(
          srsPair,
          profileId,
          "word sampling",
          { setOutputText: outputWriter }
        );
        if (!canProceed) {
          return;
        }
        const planningState = previewOptions.planningState && typeof previewOptions.planningState === "object"
          ? previewOptions.planningState
          : resolvePlanningState(synced.items, srsPair, profileId);
        const profileContext = planningState.profileContext;
        const previewSeed = generatePreviewSeed();
        const previewPayload = await helperManager.previewSrsAdmission(
          srsPair,
          {
            bootstrapTopN: planningState.profile.srsBootstrapTopN,
            initialActiveCount: planningState.profile.srsInitialActiveCount,
            maxActiveItemsHint: planningState.profile.srsMaxActive
          },
          {
            profileId,
            strategy: "profile_bootstrap",
            objective: "bootstrap",
            trigger: "options_admission_preview_button",
            previewCount,
            previewSamplingMode: "reserved_topic_lane",
            previewSeed,
            profileContext
          }
        );
        outputWriter(buildAdmissionPreviewOutput({
          translate,
          srsPair,
          profileId: previewPayload.profile_id || profileId,
          plan: previewPayload.plan || {},
          preview: previewPayload.preview || {},
          requestProfileContextMeta: planningState.contextMeta
        }));
        log("SRS admission preview", {
          pair: srsPair,
          profileId,
          previewSeed,
          requestProfileContext: profileContext,
          requestProfileContextMeta: planningState.contextMeta,
          preview: previewPayload.preview || null,
          plan: previewPayload.plan || null
        });
      } catch (err) {
        const msg = err && err.message
          ? err.message
          : translate("status_srs_admission_preview_failed", null, "Word sample failed.");
        outputWriter(msg);
        log("SRS admission preview failed.", err);
      } finally {
        admissionPreviewButton.disabled = false;
      }
    };
  }

  root.optionsSrsAdmissionPreviewWorkflow = {
    createAdmissionPreviewWorkflow
  };
})();
