(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function parseBoundedInt(rawValue, fallback, minimum) {
    const parsed = Number.parseInt(rawValue, 10);
    if (!Number.isFinite(parsed)) {
      return Math.max(minimum, Number.parseInt(fallback, 10) || minimum);
    }
    return Math.max(minimum, parsed);
  }

  function createSupport(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : { defaults: {} };
    const defaults = settingsManager.defaults || {};
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const enabledInput = elements.srsAutoRefreshEnabledInput || null;
    const minFeedbackInput = elements.srsAutoRefreshMinFeedbackInput || null;
    const minGoodEasyInput = elements.srsAutoRefreshMinGoodEasyInput || null;
    const repeatMinGoodEasyInput = elements.srsAutoRefreshRepeatMinGoodEasyInput || null;
    const cooldownInput = elements.srsAutoRefreshCooldownInput || null;

    function readSettings() {
      const minGoodEasy = parseBoundedInt(
        minGoodEasyInput ? minGoodEasyInput.value : undefined,
        defaults.srsAutoRefreshMinGoodEasy || 6,
        1
      );
      return {
        srsAutoRefreshEnabled: enabledInput ? enabledInput.checked : true,
        srsAutoRefreshMinFeedbackEvents: parseBoundedInt(
          minFeedbackInput ? minFeedbackInput.value : undefined,
          defaults.srsAutoRefreshMinFeedbackEvents || 8,
          1
        ),
        srsAutoRefreshMinGoodEasy: minGoodEasy,
        srsAutoRefreshRepeatMinGoodEasy: Math.max(
          minGoodEasy,
          parseBoundedInt(
            repeatMinGoodEasyInput ? repeatMinGoodEasyInput.value : undefined,
            defaults.srsAutoRefreshRepeatMinGoodEasy || 12,
            1
          )
        ),
        srsAutoRefreshCooldownMinutes: parseBoundedInt(
          cooldownInput ? cooldownInput.value : undefined,
          defaults.srsAutoRefreshCooldownMinutes || 90,
          0
        )
      };
    }

    function syncInputs(settings) {
      const source = settings && typeof settings === "object" ? settings : readSettings();
      if (minFeedbackInput) {
        minFeedbackInput.value = String(source.srsAutoRefreshMinFeedbackEvents);
      }
      if (minGoodEasyInput) {
        minGoodEasyInput.value = String(source.srsAutoRefreshMinGoodEasy);
      }
      if (repeatMinGoodEasyInput) {
        repeatMinGoodEasyInput.value = String(source.srsAutoRefreshRepeatMinGoodEasy);
      }
      if (cooldownInput) {
        cooldownInput.value = String(source.srsAutoRefreshCooldownMinutes);
      }
    }

    function composeRuntimeProfileContext(pairKey, profile, signals, profileId) {
      if (typeof settingsManager.composeSrsPlanContext === "function") {
        return settingsManager.composeSrsPlanContext(pairKey, profile, signals, {
          profileId
        });
      }
      return {
        pair: pairKey,
        profile_id: profileId || "default"
      };
    }

    return {
      composeRuntimeProfileContext,
      readSettings,
      syncInputs
    };
  }

  root.optionsSrsAutoRefreshSettings = {
    createSupport
  };
})();
