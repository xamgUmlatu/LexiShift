(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const DEFAULT_STORY_FLOW_PROFICIENCY = "0";

  function normalizeInterestList(value) {
    const source = Array.isArray(value) ? value : String(value || "").split(",");
    const seen = new Set();
    return source
      .map((entry) => String(entry || "").trim())
      .filter((entry) => {
        if (!entry || seen.has(entry)) {
          return false;
        }
        seen.add(entry);
        return true;
      });
  }

  function setSelectValue(select, value, fallbackText) {
    if (!select) {
      return;
    }
    const nextValue = String(value || "").trim();
    if (!nextValue) {
      return;
    }
    const options = Array.from(select.options || []);
    if (!options.some((option) => option.value === nextValue)) {
      const option = globalThis.document.createElement("option");
      option.value = nextValue;
      option.textContent = fallbackText || nextValue;
      select.appendChild(option);
    }
    select.value = nextValue;
  }

  function copySelectOptions(source, target, fallbackValue) {
    if (!target) {
      return;
    }
    target.innerHTML = "";
    const options = source ? Array.from(source.options || []) : [];
    options.forEach((option) => {
      target.appendChild(option.cloneNode(true));
    });
    if (!target.options.length && fallbackValue) {
      setSelectValue(target, fallbackValue, fallbackValue);
    }
    const nextValue = source && source.value ? source.value : fallbackValue;
    setSelectValue(target, nextValue, nextValue);
  }

  const hasExplicitProficiencyValue = (input) => !(
    input && input.type === "range" && (input.dataset || {}).srsHasValue === "false"
  );

  function formatProficiencyValue(value, hasValue) {
    if (!hasValue) {
      return "Not set";
    }
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return "Not set";
    }
    return `${Math.round(Math.min(100, Math.max(0, numeric)))}%`;
  }

  function setProficiencyInput(input, value, hasValue) {
    if (!input) {
      return;
    }
    if (!input.dataset) {
      input.dataset = {};
    }
    input.value = hasValue ? String(value || DEFAULT_STORY_FLOW_PROFICIENCY) : DEFAULT_STORY_FLOW_PROFICIENCY;
    input.dataset.srsHasValue = hasValue ? "true" : "false";
  }

  function readStoryFlowValues(elements) {
    const source = elements && typeof elements === "object" ? elements : {};
    const proficiencyInput = source.modalProficiencyEstimateInput || null;
    return {
      sourceLanguage: source.modalSourceLanguageInput ? source.modalSourceLanguageInput.value : "",
      targetLanguage: source.modalTargetLanguageInput ? source.modalTargetLanguageInput.value : "",
      profileId: source.modalProfileIdInput ? source.modalProfileIdInput.value : "",
      proficiencyEstimate: proficiencyInput && hasExplicitProficiencyValue(proficiencyInput)
        ? proficiencyInput.value
        : "",
      interests: normalizeInterestList(source.modalTopicInterestsInput ? source.modalTopicInterestsInput.value : ""),
      maxActive: source.modalMaxActiveInput ? source.modalMaxActiveInput.value : "",
      initialActiveCount: source.modalInitialActiveCountInput ? source.modalInitialActiveCountInput.value : ""
    };
  }

  function readStoryContext(elements) {
    const source = elements && typeof elements === "object" ? elements : {};
    const profileId = source.mainProfileIdInput
      ? String(source.mainProfileIdInput.value || "default").trim() || "default"
      : "default";
    return {
      sourceLanguage: source.mainSourceLanguageInput ? String(source.mainSourceLanguageInput.value || "").trim() : "",
      targetLanguage: source.mainTargetLanguageInput ? String(source.mainTargetLanguageInput.value || "").trim() : "",
      profileId,
      srsEnabled: source.mainSrsEnabledInput ? source.mainSrsEnabledInput.checked === true : false
    };
  }

  function matchesStoryContext(values, context) {
    if (!context) return false;
    const profileId = String(values.profileId || "default").trim() || "default";
    return String(values.sourceLanguage || "").trim() === context.sourceLanguage
      && String(values.targetLanguage || "").trim() === context.targetLanguage
      && profileId === context.profileId;
  }

  function normalizeProfileId(settingsManager, profileId, items) {
    if (settingsManager && typeof settingsManager.normalizeSrsProfileId === "function") {
      return settingsManager.normalizeSrsProfileId(
        profileId || (typeof settingsManager.getSelectedSrsProfileId === "function"
          ? settingsManager.getSelectedSrsProfileId(items)
          : "default")
      );
    }
    return String(profileId || "default").trim() || "default";
  }

  function parsePercentValue(value) {
    const trimmed = String(value || "").trim();
    if (!trimmed) {
      return null;
    }
    const parsed = Number.parseFloat(trimmed);
    if (!Number.isFinite(parsed)) {
      return null;
    }
    return Math.min(100, Math.max(0, parsed)) / 100;
  }

  function buildPreviewPlanningState(settingsManager, values, items, pairKey) {
    if (!settingsManager) {
      return null;
    }
    const profileId = normalizeProfileId(settingsManager, values.profileId, items);
    const storedProfile = settingsManager.getSrsProfile(items, pairKey, { profileId });
    const storedSignals = settingsManager.getSrsProfileSignals(items, pairKey, {
      profileId: storedProfile.profileId || profileId
    });
    const maxActiveRaw = parseInt(values.maxActive, 10);
    const srsMaxActive = Number.isFinite(maxActiveRaw)
      ? Math.max(1, maxActiveRaw)
      : storedProfile.srsMaxActive;
    const sizing = settingsManager.resolveSrsSetSizing(
      {
        srsMaxActive,
        srsInitialActiveCount: values.initialActiveCount || storedProfile.srsInitialActiveCount
      },
      settingsManager.defaults
    );
    const effectiveProfile = {
      ...storedProfile,
      srsMaxActive,
      srsBootstrapTopN: sizing.srsBootstrapTopN,
      srsInitialActiveCount: sizing.srsInitialActiveCount
    };
    const effectiveProficiency = storedSignals.proficiency && typeof storedSignals.proficiency === "object"
      ? { ...storedSignals.proficiency }
      : {};
    const proficiencyEstimate = parsePercentValue(values.proficiencyEstimate);
    if (proficiencyEstimate === null) {
      delete effectiveProficiency.estimated_value;
    } else {
      effectiveProficiency.estimated_value = Number(proficiencyEstimate.toFixed(2));
    }
    const effectiveSignals = {
      ...storedSignals,
      interests: normalizeInterestList(values.interests),
      proficiency: effectiveProficiency
    };
    return {
      profileId: storedProfile.profileId || profileId,
      profile: effectiveProfile,
      signals: effectiveSignals,
      profileContext: settingsManager.composeSrsPlanContext(pairKey, effectiveProfile, effectiveSignals, {
        profileId: storedProfile.profileId || profileId
      }),
      contextMeta: {
        source: "story_setup_form",
        pendingOverrides: ["story_setup"]
      }
    };
  }

  function syncTopicChips(buttons, interests) {
    const selected = new Set(normalizeInterestList(interests));
    buttons.forEach((button) => {
      const topic = String(
        button.getAttribute("data-srs-story-topic-interest")
          || button.getAttribute("data-srs-topic-interest")
          || ""
      ).trim();
      const isSelected = Boolean(topic && selected.has(topic));
      if (button.classList && typeof button.classList.toggle === "function") {
        button.classList.toggle("is-selected", isSelected);
      }
      if (typeof button.setAttribute === "function") {
        button.setAttribute("aria-pressed", isSelected ? "true" : "false");
      }
    });
  }

  root.optionsSrsStoryFlowUtils = {
    buildPreviewPlanningState,
    copySelectOptions,
    DEFAULT_STORY_FLOW_PROFICIENCY,
    formatProficiencyValue,
    hasExplicitProficiencyValue,
    matchesStoryContext,
    normalizeInterestList,
    readStoryContext,
    readStoryFlowValues,
    setProficiencyInput,
    setSelectValue,
    syncTopicChips
  };
})();
