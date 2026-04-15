(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function stableArrayEquals(left, right) {
    const leftValues = Array.isArray(left) ? left : [];
    const rightValues = Array.isArray(right) ? right : [];
    if (leftValues.length !== rightValues.length) {
      return false;
    }
    return leftValues.every((value, index) => value === rightValues[index]);
  }

  function stableScalarEquals(left, right) {
    if (left === null || left === undefined || left === "") {
      return right === null || right === undefined || right === "";
    }
    if (right === null || right === undefined || right === "") {
      return false;
    }
    return Number.isFinite(Number(left)) && Number.isFinite(Number(right))
      ? Number(left) === Number(right)
      : left === right;
  }

  function clampNormalizedValue(value) {
    if (!Number.isFinite(Number(value))) {
      return null;
    }
    return Math.min(1, Math.max(0, Number(value)));
  }

  function normalizeInterestList(value) {
    const source = Array.isArray(value)
      ? value
      : String(value || "").split(",");
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

  function createResolver(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const parseInterestList = typeof opts.parseInterestList === "function"
      ? opts.parseInterestList
      : normalizeInterestList;
    const parseOptionalPercent = typeof opts.parseOptionalPercent === "function"
      ? opts.parseOptionalPercent
      : (() => null);
    const srsMaxActiveInput = opts.srsMaxActiveInput || null;
    const srsBootstrapTopNInput = opts.srsBootstrapTopNInput || null;
    const srsInitialActiveCountInput = opts.srsInitialActiveCountInput || null;
    const srsTopicInterestsInput = opts.srsTopicInterestsInput || null;
    const srsProficiencyEstimateInput = opts.srsProficiencyEstimateInput || null;
    const srsChallengeTargetInput = opts.srsChallengeTargetInput || null;

    function resolveInterests(storedSignals) {
      if (srsTopicInterestsInput) {
        return parseInterestList(srsTopicInterestsInput.value);
      }
      return normalizeInterestList(storedSignals.interests);
    }

    function resolveNormalizedValue(input, storedValue) {
      if (input) {
        return parseOptionalPercent(input.value);
      }
      return clampNormalizedValue(storedValue);
    }

    return function resolveEffectiveSrsPlanningState(items, pairKey, options) {
      if (!settingsManager) {
        return null;
      }
      const runtimeOptions = options && typeof options === "object" ? options : {};
      const storedProfile = settingsManager.getSrsProfile(items, pairKey, {
        profileId: runtimeOptions.profileId
      });
      const storedSignals = settingsManager.getSrsProfileSignals(items, pairKey, {
        profileId: storedProfile.profileId
      });
      const maxActiveRaw = srsMaxActiveInput ? parseInt(srsMaxActiveInput.value, 10) : NaN;
      const srsMaxActive = Number.isFinite(maxActiveRaw)
        ? Math.max(1, maxActiveRaw)
        : storedProfile.srsMaxActive;
      const sizing = settingsManager.resolveSrsSetSizing(
        {
          srsMaxActive,
          srsBootstrapTopN: srsBootstrapTopNInput ? srsBootstrapTopNInput.value : storedProfile.srsBootstrapTopN,
          srsInitialActiveCount: srsInitialActiveCountInput
            ? srsInitialActiveCountInput.value
            : storedProfile.srsInitialActiveCount
        },
        settingsManager.defaults
      );
      const interests = resolveInterests(storedSignals);
      const proficiencyEstimate = resolveNormalizedValue(
        srsProficiencyEstimateInput,
        storedSignals.proficiency && storedSignals.proficiency.estimated_value
      );
      const challengeTarget = resolveNormalizedValue(
        srsChallengeTargetInput,
        storedSignals.difficultyPreferences && storedSignals.difficultyPreferences.target_challenge_center
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
      const effectiveDifficultyPreferences = (
        storedSignals.difficultyPreferences && typeof storedSignals.difficultyPreferences === "object"
      )
        ? { ...storedSignals.difficultyPreferences }
        : {};
      if (proficiencyEstimate === null) {
        delete effectiveProficiency.estimated_value;
      } else {
        effectiveProficiency.estimated_value = Number(proficiencyEstimate.toFixed(2));
      }
      if (challengeTarget === null) {
        delete effectiveDifficultyPreferences.target_challenge_center;
      } else {
        effectiveDifficultyPreferences.target_challenge_center = Number(challengeTarget.toFixed(2));
      }
      const effectiveSignals = {
        ...storedSignals,
        interests,
        proficiency: effectiveProficiency,
        difficultyPreferences: effectiveDifficultyPreferences
      };
      const pendingOverrides = [];
      if (!stableScalarEquals(storedProfile.srsMaxActive, effectiveProfile.srsMaxActive)) {
        pendingOverrides.push("max_active_items");
      }
      if (!stableScalarEquals(storedProfile.srsBootstrapTopN, effectiveProfile.srsBootstrapTopN)) {
        pendingOverrides.push("bootstrap_top_n");
      }
      if (!stableScalarEquals(storedProfile.srsInitialActiveCount, effectiveProfile.srsInitialActiveCount)) {
        pendingOverrides.push("initial_active_count");
      }
      if (!stableArrayEquals(storedSignals.interests, effectiveSignals.interests)) {
        pendingOverrides.push("interests");
      }
      if (
        !stableScalarEquals(
          storedSignals.proficiency && storedSignals.proficiency.estimated_value,
          effectiveSignals.proficiency && effectiveSignals.proficiency.estimated_value
        )
      ) {
        pendingOverrides.push("proficiency_estimate");
      }
      if (
        !stableScalarEquals(
          storedSignals.difficultyPreferences && storedSignals.difficultyPreferences.target_challenge_center,
          effectiveSignals.difficultyPreferences
          && effectiveSignals.difficultyPreferences.target_challenge_center
        )
      ) {
        pendingOverrides.push("challenge_target");
      }
      return {
        profileId: storedProfile.profileId,
        profile: effectiveProfile,
        signals: effectiveSignals,
        profileContext: settingsManager.composeSrsPlanContext(pairKey, effectiveProfile, effectiveSignals, {
          profileId: storedProfile.profileId
        }),
        contextMeta: {
          source: pendingOverrides.length ? "current_form" : "saved_profile",
          pendingOverrides
        }
      };
    };
  }

  root.optionsSrsPlanningState = {
    createResolver
  };
})();
