(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRouter(options) {
    const opts = options && typeof options === "object" ? options : {};
    const defaults = opts.defaults && typeof opts.defaults === "object" ? opts.defaults : {};
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const getCurrentSettings = typeof opts.getCurrentSettings === "function"
      ? opts.getCurrentSettings
      : (() => ({}));
    const setCurrentSettings = typeof opts.setCurrentSettings === "function"
      ? opts.setCurrentSettings
      : (() => {});
    const getFocusWord = typeof opts.getFocusWord === "function"
      ? opts.getFocusWord
      : ((_settings) => "");
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const setDebugEnabled = typeof opts.setDebugEnabled === "function"
      ? opts.setDebugEnabled
      : null;
    const setFeedbackSoundEnabled = typeof opts.setFeedbackSoundEnabled === "function"
      ? opts.setFeedbackSoundEnabled
      : null;
    const ensureStyle = typeof opts.ensureStyle === "function"
      ? opts.ensureStyle
      : null;
    const applyHighlightToDom = typeof opts.applyHighlightToDom === "function"
      ? opts.applyHighlightToDom
      : null;
    const attachFeedbackListener = typeof opts.attachFeedbackListener === "function"
      ? opts.attachFeedbackListener
      : null;
    const onFeedback = typeof opts.onFeedback === "function"
      ? opts.onFeedback
      : (() => {});
    const applySettings = typeof opts.applySettings === "function"
      ? opts.applySettings
      : (() => {});

    const rebuildKeys = [
      "enabled",
      "rules",
      "maxOnePerTextBlock",
      "allowAdjacentReplacements",
      "maxReplacementsPerPage",
      "maxReplacementsPerLemmaPerPage",
      "srsEnabled",
      "srsPair",
      "srsProfileId",
      "srsMaxActive",
      "srsRulesetUpdatedAt",
      "targetDisplayScript"
    ];
    const highlightKeys = [
      "highlightEnabled",
      "highlightColor",
      "srsHighlightColor"
    ];

    function mergeSettings(nextSettings) {
      const merged = { ...getCurrentSettings(), ...nextSettings };
      setCurrentSettings(merged);
      return merged;
    }

    function applyChangedKey(nextSettings, changes, key) {
      if (!changes[key]) {
        return false;
      }
      nextSettings[key] = changes[key].newValue;
      return true;
    }

    function configureFeedbackListener(nextSettings) {
      const merged = mergeSettings(nextSettings);
      const feedbackOrigins = merged.srsFeedbackSrsEnabled === false ? [] : [ruleOriginSrs];
      if (attachFeedbackListener) {
        attachFeedbackListener((payload) => onFeedback(payload, getFocusWord(getCurrentSettings())), {
          allowOrigins: feedbackOrigins
        });
      }
    }

    function applyHighlightSettings(nextSettings) {
      const merged = mergeSettings(nextSettings);
      if (ensureStyle) {
        ensureStyle(
          merged.highlightColor || defaults.highlightColor,
          merged.srsHighlightColor || merged.highlightColor || defaults.highlightColor
        );
      }
      if (applyHighlightToDom) {
        applyHighlightToDom(merged.highlightEnabled);
      }
    }

    function handleStorageChange(changes, area) {
      if (area !== "local") {
        return;
      }
      const currentSettings = getCurrentSettings();
      const nextSettings = { ...currentSettings };
      let needsRebuild = false;
      let needsHighlight = false;

      for (const key of rebuildKeys) {
        if (applyChangedKey(nextSettings, changes, key)) {
          needsRebuild = true;
        }
      }
      for (const key of highlightKeys) {
        if (applyChangedKey(nextSettings, changes, key)) {
          needsHighlight = true;
        }
      }

      if (changes.srsSoundEnabled) {
        nextSettings.srsSoundEnabled = changes.srsSoundEnabled.newValue;
        if (setFeedbackSoundEnabled) {
          setFeedbackSoundEnabled(nextSettings.srsSoundEnabled);
        }
      }
      if (changes.srsFeedbackSrsEnabled) {
        nextSettings.srsFeedbackSrsEnabled = changes.srsFeedbackSrsEnabled.newValue;
      }
      if (changes.srsFeedbackRulesEnabled) {
        nextSettings.srsFeedbackRulesEnabled = changes.srsFeedbackRulesEnabled.newValue;
      }
      if (changes.srsFeedbackSrsEnabled || changes.srsFeedbackRulesEnabled) {
        configureFeedbackListener(nextSettings);
      }

      if (changes.srsExposureLoggingEnabled) {
        nextSettings.srsExposureLoggingEnabled = changes.srsExposureLoggingEnabled.newValue;
        const merged = mergeSettings(nextSettings);
        if (merged.debugEnabled) {
          log(
            `SRS exposure logging ${merged.srsExposureLoggingEnabled === false ? "disabled" : "enabled"}.`
          );
        }
      }

      if (changes.debugEnabled) {
        nextSettings.debugEnabled = changes.debugEnabled.newValue;
        const merged = mergeSettings(nextSettings);
        if (setDebugEnabled) {
          setDebugEnabled(merged.debugEnabled === true);
        }
        log("Debug logging enabled.");
      }
      if (changes.debugFocusWord) {
        nextSettings.debugFocusWord = changes.debugFocusWord.newValue;
        const merged = mergeSettings(nextSettings);
        const focusWord = getFocusWord(merged);
        if (focusWord) {
          log(`Debug focus word set to "${focusWord}".`);
        } else {
          log("Debug focus word cleared.");
        }
      }

      if (needsHighlight) {
        applyHighlightSettings(nextSettings);
      }
      if (needsRebuild) {
        applySettings(nextSettings);
      }
    }

    return {
      handleStorageChange
    };
  }

  root.contentSettingsChangeRouter = {
    createRouter
  };
})();
