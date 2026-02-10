(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const profileSelect = opts.profileSelect || null;
    const setProfileStatusLocalized = typeof opts.setProfileStatusLocalized === "function"
      ? opts.setProfileStatusLocalized
      : (() => {});
    const onProfileLanguagePrefsSync = typeof opts.onProfileLanguagePrefsSync === "function"
      ? opts.onProfileLanguagePrefsSync
      : (() => Promise.resolve());
    const cacheTtlMs = Number.isFinite(Number(opts.cacheTtlMs))
      ? Math.max(0, Number(opts.cacheTtlMs))
      : 10_000;

    let helperProfilesCache = null;
    let helperProfilesCacheTs = 0;

    function resolveHelperProfileItems(payload) {
      const profiles = payload && Array.isArray(payload.profiles) ? payload.profiles : [];
      return profiles
        .map((profile) => {
          if (!profile || typeof profile !== "object") {
            return null;
          }
          const profileId = String(profile.profile_id || "").trim();
          if (!profileId) {
            return null;
          }
          return {
            profileId,
            name: String(profile.name || profileId).trim() || profileId
          };
        })
        .filter(Boolean);
    }

    function renderProfileControls(selectedProfileId, helperProfilesPayload) {
      const resolvedProfileId = String(selectedProfileId || "default").trim() || "default";
      const helperItems = resolveHelperProfileItems(helperProfilesPayload);
      const fallbackIds = [resolvedProfileId, "default"]
        .map((value) => String(value || "").trim())
        .filter(Boolean);
      const merged = [];
      const seen = new Set();
      for (const item of helperItems) {
        if (seen.has(item.profileId)) {
          continue;
        }
        seen.add(item.profileId);
        merged.push(item);
      }
      for (const profileId of fallbackIds) {
        if (seen.has(profileId)) {
          continue;
        }
        seen.add(profileId);
        merged.push({ profileId, name: profileId });
      }

      if (profileSelect) {
        const previousValue = profileSelect.value;
        profileSelect.innerHTML = "";
        merged.forEach((item) => {
          const option = document.createElement("option");
          option.value = item.profileId;
          option.textContent = `${item.name} (${item.profileId})`;
          profileSelect.appendChild(option);
        });
        const fallbackValue = merged.length ? merged[0].profileId : "default";
        const nextValue = merged.some((item) => item.profileId === resolvedProfileId)
          ? resolvedProfileId
          : (merged.some((item) => item.profileId === previousValue) ? previousValue : fallbackValue);
        profileSelect.value = nextValue || "default";
        profileSelect.disabled = merged.length === 0;
      }
      setProfileStatusLocalized(
        "status_profile_selected",
        [resolvedProfileId],
        `Selected profile: ${resolvedProfileId}.`
      );
    }

    async function fetchHelperProfiles(options) {
      if (!helperManager || typeof helperManager.getProfiles !== "function") {
        return null;
      }
      const localOptions = options && typeof options === "object" ? options : {};
      const force = localOptions.force === true;
      const now = Date.now();
      if (!force && helperProfilesCache && now - helperProfilesCacheTs < cacheTtlMs) {
        return helperProfilesCache;
      }
      const result = await helperManager.getProfiles();
      if (result && result.ok) {
        helperProfilesCache = result.data || null;
        helperProfilesCacheTs = now;
      }
      return result && result.ok ? (result.data || null) : null;
    }

    function clearCache() {
      helperProfilesCache = null;
      helperProfilesCacheTs = 0;
    }

    async function syncSelected(items, options) {
      if (!settingsManager) {
        return {
          items,
          profileId: "default",
          uiProfileId: "default",
          helperProfilesPayload: null
        };
      }
      const localOptions = options && typeof options === "object" ? options : {};
      const forceHelperRefresh = localOptions.forceHelperRefresh === true;
      let workingItems = items;
      let selectedSrsProfileId = settingsManager.getSelectedSrsProfileId(workingItems);
      let selectedUiProfileId = settingsManager.getSelectedUiProfileId(workingItems);
      // SRS profile selector is the user-facing source of truth for profile-scoped settings.
      let selectedProfileId = selectedSrsProfileId || selectedUiProfileId;
      const helperProfilesPayload = await fetchHelperProfiles({ force: forceHelperRefresh });
      const helperProfileItems = resolveHelperProfileItems(helperProfilesPayload);
      const helperProfileIds = helperProfileItems.map((item) => item.profileId);
      const hasSelectedProfile = helperProfileIds.length
        ? helperProfileIds.includes(selectedProfileId)
        : true;

      if (!hasSelectedProfile) {
        const nextProfileId = helperProfileIds.includes("default")
          ? "default"
          : (helperProfileIds[0] || settingsManager.DEFAULT_PROFILE_ID);
        if (nextProfileId && nextProfileId !== selectedProfileId) {
          await settingsManager.updateSelectedSrsProfileId(nextProfileId);
          await settingsManager.updateSelectedUiProfileId(nextProfileId);
          workingItems = await settingsManager.load();
          selectedSrsProfileId = settingsManager.getSelectedSrsProfileId(workingItems);
          selectedUiProfileId = settingsManager.getSelectedUiProfileId(workingItems);
          selectedProfileId = selectedSrsProfileId || selectedUiProfileId;
          await onProfileLanguagePrefsSync({
            items: workingItems,
            profileId: selectedSrsProfileId
          });
        }
      }

      if (selectedSrsProfileId !== selectedProfileId) {
        await settingsManager.updateSelectedSrsProfileId(selectedProfileId);
        workingItems = await settingsManager.load();
        selectedSrsProfileId = settingsManager.getSelectedSrsProfileId(workingItems);
        await onProfileLanguagePrefsSync({
          items: workingItems,
          profileId: selectedSrsProfileId
        });
      }
      if (selectedUiProfileId !== selectedProfileId) {
        await settingsManager.updateSelectedUiProfileId(selectedProfileId);
        workingItems = await settingsManager.load();
        selectedUiProfileId = settingsManager.getSelectedUiProfileId(workingItems);
      }

      renderProfileControls(selectedProfileId, helperProfilesPayload);
      return {
        items: workingItems,
        profileId: selectedSrsProfileId,
        uiProfileId: selectedUiProfileId,
        helperProfilesPayload
      };
    }

    return {
      clearCache,
      fetchHelperProfiles,
      syncSelected
    };
  }

  root.optionsSrsProfileSelector = {
    createController
  };
})();
