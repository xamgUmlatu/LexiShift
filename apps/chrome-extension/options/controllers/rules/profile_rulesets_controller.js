(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const helperErrorCopy = root.helperErrorCopy;

  if (
    !helperErrorCopy
    || typeof helperErrorCopy.normalizeHelperErrorMessage !== "function"
    || typeof helperErrorCopy.normalizeHelperThrownErrorMessage !== "function"
  ) {
    throw new Error("[LexiShift][Options] Missing shared helper error copy.");
  }

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const onRulesetsUpdated = typeof opts.onRulesetsUpdated === "function"
      ? opts.onRulesetsUpdated
      : (() => {});
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const listRoot = elements.profileRulesetsList || null;
    const statusOutput = elements.profileRulesetsStatus || null;
    const refreshButton = elements.profileRulesetsRefreshButton || null;
    const stateHelpers = root.optionsProfileRulesetsState && typeof root.optionsProfileRulesetsState === "object"
      ? root.optionsProfileRulesetsState
      : null;
    if (!stateHelpers) {
      throw new Error("Profile rulesets state helpers are missing.");
    }

    function normalizeProfileId(profileId) {
      if (settingsManager && typeof settingsManager.normalizeSrsProfileId === "function") {
        return settingsManager.normalizeSrsProfileId(profileId);
      }
      const normalized = String(profileId || "").trim();
      return normalized || "default";
    }

    function getSelectedProfileId(items) {
      if (settingsManager && typeof settingsManager.getSelectedSrsProfileId === "function") {
        return settingsManager.getSelectedSrsProfileId(items);
      }
      return normalizeProfileId(null);
    }

    function getProfilesRoot(items) {
      return stateHelpers.isObject(items && items.srsProfiles) ? items.srsProfiles : {};
    }

    function getProfileEntry(items, profileId) {
      const profilesRoot = getProfilesRoot(items);
      const resolvedProfileId = normalizeProfileId(profileId);
      return stateHelpers.isObject(profilesRoot[resolvedProfileId]) ? profilesRoot[resolvedProfileId] : {};
    }

    function setInlineStatus(message) {
      if (!statusOutput) {
        return;
      }
      statusOutput.textContent = message || "";
    }

    function normalizeHelperMessage(error, fallbackText) {
      return helperErrorCopy.normalizeHelperErrorMessage(error, {
        translate,
        fallbackText
      });
    }

    function normalizeThrownHelperMessage(error, fallbackText) {
      return helperErrorCopy.normalizeHelperThrownErrorMessage(error, {
        translate,
        fallbackText
      });
    }

    async function persistProfileRulesets(items, profileId, manualState, cache) {
      const resolvedProfileId = normalizeProfileId(profileId);
      const profilesRoot = getProfilesRoot(items);
      const profileEntry = getProfileEntry(items, resolvedProfileId);
      const nextProfiles = {
        ...profilesRoot,
        [resolvedProfileId]: {
          ...profileEntry,
          manualRulesets: {
            order: [...manualState.order],
            enabledByPath: {
              ...manualState.enabledByPath
            }
          }
        }
      };
      const profileRules = stateHelpers.buildProfileRules(manualState, cache);
      const profileRulesUpdatedAt = new Date().toISOString();
      await settingsManager.save({
        srsProfiles: nextProfiles,
        manualRulesetCacheByPath: cache,
        profileRules,
        profileRulesUpdatedAt
      });
      return {
        items: {
          ...(stateHelpers.isObject(items) ? items : {}),
          srsProfiles: nextProfiles,
          manualRulesetCacheByPath: cache,
          profileRules,
          profileRulesUpdatedAt
        },
        profileRules
      };
    }

    function renderRulesets(profileId, manualState, cache) {
      if (!listRoot) {
        return;
      }
      listRoot.innerHTML = "";
      if (!manualState.order.length) {
        const empty = document.createElement("p");
        empty.className = "hint";
        empty.textContent = "No profile rulesets available.";
        listRoot.appendChild(empty);
        setInlineStatus("No profile rulesets are linked to this profile.");
        return;
      }
      manualState.order.forEach((pathKey) => {
        const cacheEntry = cache[pathKey] || null;
        const row = document.createElement("label");
        row.className = "profile-ruleset-row";
        if (cacheEntry && cacheEntry.exists === false) {
          row.classList.add("is-missing");
        }
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = manualState.enabledByPath[pathKey] !== false;
        checkbox.addEventListener("change", () => {
          checkbox.disabled = true;
          setRulesetEnabled(pathKey, checkbox.checked)
            .catch((error) => {
              const message = error && error.message ? error.message : "Failed to update ruleset state.";
              setStatus(message, colors.ERROR);
              log("Profile ruleset toggle failed.", error);
            })
            .finally(() => {
              checkbox.disabled = false;
            });
        });
        const textWrap = document.createElement("span");
        textWrap.className = "profile-ruleset-text";
        const title = document.createElement("span");
        title.className = "profile-ruleset-label";
        title.textContent = stateHelpers.pathBasename(
          cacheEntry && cacheEntry.displayPath ? cacheEntry.displayPath : pathKey
        );
        const meta = document.createElement("span");
        meta.className = "profile-ruleset-meta";
        if (cacheEntry && cacheEntry.error) {
          meta.textContent = `Unavailable: ${cacheEntry.error}`;
        } else {
          const count = cacheEntry ? Number(cacheEntry.rulesCount || 0) : 0;
          meta.textContent = `${count} rules`;
        }
        const pathText = document.createElement("span");
        pathText.className = "profile-ruleset-path";
        pathText.textContent = cacheEntry && cacheEntry.displayPath ? cacheEntry.displayPath : pathKey;
        textWrap.appendChild(title);
        textWrap.appendChild(meta);
        textWrap.appendChild(pathText);
        row.appendChild(checkbox);
        row.appendChild(textWrap);
        listRoot.appendChild(row);
      });
      const activeRules = stateHelpers.buildProfileRules(manualState, cache);
      setInlineStatus(stateHelpers.summarize(manualState, cache, activeRules));
      if (refreshButton) {
        refreshButton.disabled = false;
        refreshButton.dataset.profileId = normalizeProfileId(profileId);
      }
    }

    async function setRulesetEnabled(pathKey, enabled) {
      if (!settingsManager) {
        return;
      }
      const normalizedPath = stateHelpers.normalizePath(pathKey);
      if (!normalizedPath) {
        return;
      }
      const items = await settingsManager.load();
      const profileId = getSelectedProfileId(items);
      const profileEntry = getProfileEntry(items, profileId);
      const manualState = stateHelpers.normalizeManualRulesetsState(profileEntry.manualRulesets);
      const cache = stateHelpers.normalizeRulesetCache(items.manualRulesetCacheByPath);
      if (!manualState.order.includes(normalizedPath)) {
        manualState.order.push(normalizedPath);
      }
      manualState.enabledByPath[normalizedPath] = enabled === true;
      const persisted = await persistProfileRulesets(items, profileId, manualState, cache);
      renderRulesets(profileId, manualState, cache);
      Promise.resolve(onRulesetsUpdated({
        items: persisted.items,
        profileId,
        manualState,
        cache
      })).catch((error) => {
        log("Profile rulesets update callback failed.", error);
      });
      const summary = stateHelpers.summarize(manualState, cache, persisted.profileRules);
      setStatus(summary, colors.SUCCESS);
    }

    async function syncForProfile(options) {
      if (!settingsManager) {
        return null;
      }
      const localOptions = options && typeof options === "object" ? options : {};
      const items = stateHelpers.isObject(localOptions.items) ? localOptions.items : await settingsManager.load();
      const profileId = normalizeProfileId(
        localOptions.profileId !== undefined ? localOptions.profileId : getSelectedProfileId(items)
      );
      const profileEntry = getProfileEntry(items, profileId);
      let manualState = stateHelpers.normalizeManualRulesetsState(profileEntry.manualRulesets);
      let cache = stateHelpers.normalizeRulesetCache(items.manualRulesetCacheByPath);
      let helperError = "";

      if (helperManager && typeof helperManager.getProfileRulesets === "function") {
        const helperResult = await helperManager.getProfileRulesets(profileId);
        if (helperResult && helperResult.ok) {
          const helperRulesets = stateHelpers.normalizeHelperRulesets(helperResult.data);
          manualState = stateHelpers.mergeManualStateFromHelper(manualState, helperRulesets);
          cache = stateHelpers.mergeCacheFromHelper(cache, helperRulesets);
        } else {
          helperError = normalizeHelperMessage(
            helperResult && helperResult.error,
            "Failed to load profile rulesets from helper."
          );
        }
      }

      const persisted = await persistProfileRulesets(items, profileId, manualState, cache);
      renderRulesets(profileId, manualState, cache);
      Promise.resolve(onRulesetsUpdated({
        items: persisted.items,
        profileId,
        manualState,
        cache
      })).catch((error) => {
        log("Profile rulesets update callback failed.", error);
      });
      if (helperError) {
        setInlineStatus(helperError);
      }
      return persisted.items;
    }

    async function refreshSelectedProfile() {
      const items = await settingsManager.load();
      const profileId = getSelectedProfileId(items);
      if (refreshButton) {
        refreshButton.disabled = true;
      }
      try {
        await syncForProfile({ items, profileId });
        setStatus(
          translate("status_srs_profile_refreshed", null, "Helper profiles refreshed."),
          colors.SUCCESS
        );
      } finally {
        if (refreshButton) {
          refreshButton.disabled = false;
        }
      }
    }

    if (refreshButton) {
      refreshButton.addEventListener("click", () => {
        refreshSelectedProfile().catch((error) => {
          const message = normalizeThrownHelperMessage(
            error,
            "Failed to refresh profile rulesets."
          );
          setStatus(message, colors.ERROR);
          setInlineStatus(message);
          log("Profile rulesets refresh failed.", error);
        });
      });
    }

    return {
      refreshSelectedProfile,
      syncForProfile
    };
  }

  root.optionsProfileRulesets = {
    createController
  };
})();
