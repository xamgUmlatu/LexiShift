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

    function handleStorageChange(changes, area) {
      if (area !== "local") {
        return;
      }
      const currentSettings = getCurrentSettings();
      const nextSettings = { ...currentSettings };
      let needsRebuild = false;
      let needsHighlight = false;

      if (changes.enabled) {
        nextSettings.enabled = changes.enabled.newValue;
        needsRebuild = true;
      }
      if (changes.rules) {
        nextSettings.rules = changes.rules.newValue;
        needsRebuild = true;
      }
      if (changes.highlightEnabled) {
        nextSettings.highlightEnabled = changes.highlightEnabled.newValue;
        needsHighlight = true;
      }
      if (changes.highlightColor) {
        nextSettings.highlightColor = changes.highlightColor.newValue;
        needsHighlight = true;
      }
      if (changes.maxOnePerTextBlock) {
        nextSettings.maxOnePerTextBlock = changes.maxOnePerTextBlock.newValue;
        needsRebuild = true;
      }
      if (changes.allowAdjacentReplacements) {
        nextSettings.allowAdjacentReplacements = changes.allowAdjacentReplacements.newValue;
        needsRebuild = true;
      }
      if (changes.maxReplacementsPerPage) {
        nextSettings.maxReplacementsPerPage = changes.maxReplacementsPerPage.newValue;
        needsRebuild = true;
      }
      if (changes.maxReplacementsPerLemmaPerPage) {
        nextSettings.maxReplacementsPerLemmaPerPage = changes.maxReplacementsPerLemmaPerPage.newValue;
        needsRebuild = true;
      }
      if (changes.srsEnabled) {
        nextSettings.srsEnabled = changes.srsEnabled.newValue;
        needsRebuild = true;
      }
      if (changes.srsPair) {
        nextSettings.srsPair = changes.srsPair.newValue;
        needsRebuild = true;
      }
      if (changes.srsProfileId) {
        nextSettings.srsProfileId = changes.srsProfileId.newValue;
        needsRebuild = true;
      }
      if (changes.srsMaxActive) {
        nextSettings.srsMaxActive = changes.srsMaxActive.newValue;
        needsRebuild = true;
      }
      if (changes.srsSoundEnabled) {
        nextSettings.srsSoundEnabled = changes.srsSoundEnabled.newValue;
        if (setFeedbackSoundEnabled) {
          setFeedbackSoundEnabled(nextSettings.srsSoundEnabled);
        }
      }
      if (changes.srsHighlightColor) {
        nextSettings.srsHighlightColor = changes.srsHighlightColor.newValue;
        needsHighlight = true;
      }
      if (changes.srsFeedbackSrsEnabled) {
        nextSettings.srsFeedbackSrsEnabled = changes.srsFeedbackSrsEnabled.newValue;
      }
      if (changes.srsFeedbackRulesEnabled) {
        nextSettings.srsFeedbackRulesEnabled = changes.srsFeedbackRulesEnabled.newValue;
      }
      if (changes.srsFeedbackSrsEnabled || changes.srsFeedbackRulesEnabled) {
        const merged = { ...getCurrentSettings(), ...nextSettings };
        setCurrentSettings(merged);
        const feedbackOrigins = merged.srsFeedbackSrsEnabled === false ? [] : [ruleOriginSrs];
        if (attachFeedbackListener) {
          attachFeedbackListener((payload) => onFeedback(payload, getFocusWord(getCurrentSettings())), {
            allowOrigins: feedbackOrigins
          });
        }
      }
      if (changes.srsExposureLoggingEnabled) {
        nextSettings.srsExposureLoggingEnabled = changes.srsExposureLoggingEnabled.newValue;
        const merged = { ...getCurrentSettings(), ...nextSettings };
        setCurrentSettings(merged);
        if (merged.debugEnabled) {
          log(
            `SRS exposure logging ${merged.srsExposureLoggingEnabled === false ? "disabled" : "enabled"}.`
          );
        }
      }
      if (changes.srsRulesetUpdatedAt) {
        nextSettings.srsRulesetUpdatedAt = changes.srsRulesetUpdatedAt.newValue;
        needsRebuild = true;
      }
      if (changes.targetDisplayScript) {
        nextSettings.targetDisplayScript = changes.targetDisplayScript.newValue;
        needsRebuild = true;
      }
      if (changes.debugEnabled) {
        nextSettings.debugEnabled = changes.debugEnabled.newValue;
        const merged = { ...getCurrentSettings(), ...nextSettings };
        setCurrentSettings(merged);
        if (setDebugEnabled) {
          setDebugEnabled(merged.debugEnabled === true);
        }
        log("Debug logging enabled.");
      }
      if (changes.debugFocusWord) {
        nextSettings.debugFocusWord = changes.debugFocusWord.newValue;
        const merged = { ...getCurrentSettings(), ...nextSettings };
        setCurrentSettings(merged);
        const focusWord = getFocusWord(merged);
        if (focusWord) {
          log(`Debug focus word set to "${focusWord}".`);
        } else {
          log("Debug focus word cleared.");
        }
      }

      if (needsHighlight) {
        const merged = { ...getCurrentSettings(), ...nextSettings };
        setCurrentSettings(merged);
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
