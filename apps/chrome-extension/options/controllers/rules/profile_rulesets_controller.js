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
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const listRoot = elements.profileRulesetsList || null;
    const statusOutput = elements.profileRulesetsStatus || null;
    const refreshButton = elements.profileRulesetsRefreshButton || null;

    function isObject(value) {
      return Boolean(value) && typeof value === "object" && !Array.isArray(value);
    }

    function normalizePath(value) {
      const normalized = String(value || "").trim();
      return normalized || "";
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
      return isObject(items && items.srsProfiles) ? items.srsProfiles : {};
    }

    function getProfileEntry(items, profileId) {
      const profilesRoot = getProfilesRoot(items);
      const resolvedProfileId = normalizeProfileId(profileId);
      return isObject(profilesRoot[resolvedProfileId]) ? profilesRoot[resolvedProfileId] : {};
    }

    function normalizeRulesArray(rules) {
      if (!Array.isArray(rules)) {
        return [];
      }
      return rules.filter((rule) => isObject(rule));
    }

    function normalizeRulesetCache(rawCache) {
      const raw = isObject(rawCache) ? rawCache : {};
      const normalized = {};
      Object.entries(raw).forEach(([rawPath, rawEntry]) => {
        const pathKey = normalizePath(rawPath);
        if (!pathKey || !isObject(rawEntry)) {
          return;
        }
        const rules = normalizeRulesArray(rawEntry.rules);
        normalized[pathKey] = {
          rules,
          rulesCount: Number.isFinite(Number(rawEntry.rulesCount))
            ? Number(rawEntry.rulesCount)
            : rules.length,
          exists: rawEntry.exists !== false,
          error: normalizePath(rawEntry.error),
          loadedAt: normalizePath(rawEntry.loadedAt),
          displayPath: normalizePath(rawEntry.displayPath) || pathKey
        };
      });
      return normalized;
    }

    function normalizeManualRulesetsState(rawState) {
      const raw = isObject(rawState) ? rawState : {};
      const rawOrder = Array.isArray(raw.order) ? raw.order : [];
      const rawEnabledByPath = isObject(raw.enabledByPath) ? raw.enabledByPath : {};
      const order = [];
      const seen = new Set();
      rawOrder.forEach((rawPath) => {
        const pathKey = normalizePath(rawPath);
        if (!pathKey || seen.has(pathKey)) {
          return;
        }
        seen.add(pathKey);
        order.push(pathKey);
      });
      const enabledByPath = {};
      order.forEach((pathKey) => {
        if (Object.prototype.hasOwnProperty.call(rawEnabledByPath, pathKey)) {
          enabledByPath[pathKey] = rawEnabledByPath[pathKey] !== false;
        }
      });
      return {
        order,
        enabledByPath
      };
    }

    function resolveExistingEnabled(state, pathKey, legacyPathKey) {
      if (Object.prototype.hasOwnProperty.call(state.enabledByPath, pathKey)) {
        return state.enabledByPath[pathKey] !== false;
      }
      if (legacyPathKey && Object.prototype.hasOwnProperty.call(state.enabledByPath, legacyPathKey)) {
        return state.enabledByPath[legacyPathKey] !== false;
      }
      return true;
    }

    function normalizeHelperRulesets(payload) {
      const rawItems = payload && Array.isArray(payload.rulesets) ? payload.rulesets : [];
      const items = [];
      const seen = new Set();
      rawItems.forEach((rawItem) => {
        const item = isObject(rawItem) ? rawItem : {};
        const pathKey = normalizePath(item.resolved_path || item.path);
        const displayPath = normalizePath(item.path) || pathKey;
        if (!pathKey || seen.has(pathKey)) {
          return;
        }
        seen.add(pathKey);
        const rules = normalizeRulesArray(item.rules);
        items.push({
          pathKey,
          displayPath,
          exists: item.exists === true,
          rules,
          rulesCount: Number.isFinite(Number(item.rules_count)) ? Number(item.rules_count) : rules.length,
          error: normalizePath(item.error)
        });
      });
      return items;
    }

    function mergeManualStateFromHelper(existingState, helperRulesets) {
      const order = [];
      const enabledByPath = {};
      helperRulesets.forEach((ruleset) => {
        order.push(ruleset.pathKey);
        enabledByPath[ruleset.pathKey] = resolveExistingEnabled(
          existingState,
          ruleset.pathKey,
          ruleset.displayPath
        );
      });
      return {
        order,
        enabledByPath
      };
    }

    function mergeCacheFromHelper(existingCache, helperRulesets) {
      const nextCache = {
        ...existingCache
      };
      const loadedAt = new Date().toISOString();
      helperRulesets.forEach((ruleset) => {
        nextCache[ruleset.pathKey] = {
          rules: ruleset.rules,
          rulesCount: ruleset.rulesCount,
          exists: ruleset.exists,
          error: ruleset.error,
          loadedAt,
          displayPath: ruleset.displayPath
        };
      });
      return nextCache;
    }

    function buildProfileRules(manualState, cache) {
      const rules = [];
      manualState.order.forEach((pathKey) => {
        if (manualState.enabledByPath[pathKey] === false) {
          return;
        }
        const entry = cache[pathKey];
        if (!entry || !Array.isArray(entry.rules)) {
          return;
        }
        entry.rules.forEach((rule) => {
          rules.push(rule);
        });
      });
      return rules;
    }

    function summarize(manualState, cache, profileRules) {
      const total = manualState.order.length;
      const enabled = manualState.order.filter((pathKey) => manualState.enabledByPath[pathKey] !== false).length;
      const missing = manualState.order.filter((pathKey) => cache[pathKey] && cache[pathKey].exists !== true).length;
      const rulesCount = Array.isArray(profileRules) ? profileRules.length : 0;
      let summary = `Enabled ${enabled}/${total} profile rulesets`;
      if (missing > 0) {
        summary += ` (${missing} missing)`;
      }
      summary += `, ${rulesCount} profile rules.`;
      return summary;
    }

    function setInlineStatus(message) {
      if (!statusOutput) {
        return;
      }
      statusOutput.textContent = message || "";
    }

    function pathBasename(path) {
      const normalized = normalizePath(path);
      if (!normalized) {
        return "(unknown)";
      }
      const slashIndex = Math.max(normalized.lastIndexOf("/"), normalized.lastIndexOf("\\"));
      return slashIndex >= 0 ? normalized.slice(slashIndex + 1) : normalized;
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
      const profileRules = buildProfileRules(manualState, cache);
      const profileRulesUpdatedAt = new Date().toISOString();
      await settingsManager.save({
        srsProfiles: nextProfiles,
        manualRulesetCacheByPath: cache,
        profileRules,
        profileRulesUpdatedAt
      });
      return {
        items: {
          ...(isObject(items) ? items : {}),
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
        title.textContent = pathBasename(cacheEntry && cacheEntry.displayPath ? cacheEntry.displayPath : pathKey);
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
      const activeRules = buildProfileRules(manualState, cache);
      setInlineStatus(summarize(manualState, cache, activeRules));
      if (refreshButton) {
        refreshButton.disabled = false;
        refreshButton.dataset.profileId = normalizeProfileId(profileId);
      }
    }

    async function setRulesetEnabled(pathKey, enabled) {
      if (!settingsManager) {
        return;
      }
      const normalizedPath = normalizePath(pathKey);
      if (!normalizedPath) {
        return;
      }
      const items = await settingsManager.load();
      const profileId = getSelectedProfileId(items);
      const profileEntry = getProfileEntry(items, profileId);
      const manualState = normalizeManualRulesetsState(profileEntry.manualRulesets);
      const cache = normalizeRulesetCache(items.manualRulesetCacheByPath);
      if (!manualState.order.includes(normalizedPath)) {
        manualState.order.push(normalizedPath);
      }
      manualState.enabledByPath[normalizedPath] = enabled === true;
      const persisted = await persistProfileRulesets(items, profileId, manualState, cache);
      renderRulesets(profileId, manualState, cache);
      const summary = summarize(manualState, cache, persisted.profileRules);
      setStatus(summary, colors.SUCCESS);
    }

    async function syncForProfile(options) {
      if (!settingsManager) {
        return null;
      }
      const localOptions = options && typeof options === "object" ? options : {};
      const items = isObject(localOptions.items) ? localOptions.items : await settingsManager.load();
      const profileId = normalizeProfileId(
        localOptions.profileId !== undefined ? localOptions.profileId : getSelectedProfileId(items)
      );
      const profileEntry = getProfileEntry(items, profileId);
      let manualState = normalizeManualRulesetsState(profileEntry.manualRulesets);
      let cache = normalizeRulesetCache(items.manualRulesetCacheByPath);
      let helperError = "";

      if (helperManager && typeof helperManager.getProfileRulesets === "function") {
        const helperResult = await helperManager.getProfileRulesets(profileId);
        if (helperResult && helperResult.ok) {
          const helperRulesets = normalizeHelperRulesets(helperResult.data);
          manualState = mergeManualStateFromHelper(manualState, helperRulesets);
          cache = mergeCacheFromHelper(cache, helperRulesets);
        } else {
          helperError = normalizePath(helperResult && helperResult.error && helperResult.error.message)
            || "Failed to load profile rulesets from helper.";
        }
      }

      const persisted = await persistProfileRulesets(items, profileId, manualState, cache);
      renderRulesets(profileId, manualState, cache);
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
          const message = error && error.message ? error.message : "Failed to refresh profile rulesets.";
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
