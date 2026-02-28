(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRenderers(options) {
    const opts = options && typeof options === "object" ? options : {};
    const shareCenterRowFactory = root.optionsShareCenterRowFactory;
    if (!shareCenterRowFactory || typeof shareCenterRowFactory.createDynamicLeafRow !== "function") {
      throw new Error("Share Center row factory is missing.");
    }
    const createDynamicLeafRow = shareCenterRowFactory.createDynamicLeafRow;
    const srsPairItemsRoot = opts.srsPairItemsRoot || null;
    const rulesetItemsRoot = opts.rulesetItemsRoot || null;
    const moduleItemsRoot = opts.moduleItemsRoot || null;
    const dynamicLeafState = opts.dynamicLeafState instanceof Map ? opts.dynamicLeafState : new Map();
    const getDynamicSrsPairIds = typeof opts.getDynamicSrsPairIds === "function" ? opts.getDynamicSrsPairIds : (() => []);
    const setDynamicSrsPairIds = typeof opts.setDynamicSrsPairIds === "function" ? opts.setDynamicSrsPairIds : (() => {});
    const getDynamicRulesetIds = typeof opts.getDynamicRulesetIds === "function" ? opts.getDynamicRulesetIds : (() => []);
    const setDynamicRulesetIds = typeof opts.setDynamicRulesetIds === "function" ? opts.setDynamicRulesetIds : (() => {});
    const getDynamicModuleIds = typeof opts.getDynamicModuleIds === "function" ? opts.getDynamicModuleIds : (() => []);
    const setDynamicModuleIds = typeof opts.setDynamicModuleIds === "function" ? opts.setDynamicModuleIds : (() => {});
    const clearDynamicLeafsByKind = typeof opts.clearDynamicLeafsByKind === "function"
      ? opts.clearDynamicLeafsByKind
      : (() => {});
    const resolveProfileSrsPairs = typeof opts.resolveProfileSrsPairs === "function"
      ? opts.resolveProfileSrsPairs
      : (() => ({ currentPair: "", pairs: [] }));
    const resolveProfileModules = typeof opts.resolveProfileModules === "function"
      ? opts.resolveProfileModules
      : (() => ({ targetLanguage: "en", modules: [] }));
    const joinPath = typeof opts.joinPath === "function" ? opts.joinPath : ((parts) => (Array.isArray(parts) ? parts.join(" > ") : ""));
    const labels = opts.labels && typeof opts.labels === "object" ? opts.labels : {};
    const tr = typeof opts.tr === "function" ? opts.tr : ((key, fallback) => String(fallback || key || ""));
    const colors = opts.colors && typeof opts.colors === "object" ? opts.colors : { DEFAULT: "#6c675f" };
    const setSrsPairStatus = typeof opts.setSrsPairStatus === "function" ? opts.setSrsPairStatus : (() => {});
    const setRulesetStatus = typeof opts.setRulesetStatus === "function" ? opts.setRulesetStatus : (() => {});
    const setModuleStatus = typeof opts.setModuleStatus === "function" ? opts.setModuleStatus : (() => {});
    const onLeafChanged = typeof opts.onLeafChanged === "function" ? opts.onLeafChanged : (() => {});
    const normalizePath = typeof opts.normalizePath === "function"
      ? opts.normalizePath
      : ((value) => String(value || "").trim());
    const pathBasename = typeof opts.pathBasename === "function"
      ? opts.pathBasename
      : ((value) => String(value || ""));
    const isObject = typeof opts.isObject === "function"
      ? opts.isObject
      : ((value) => Boolean(value) && typeof value === "object" && !Array.isArray(value));
    const getSelectedRulesetPath = typeof opts.getSelectedRulesetPath === "function"
      ? opts.getSelectedRulesetPath
      : (() => "");
    const setSelectedRulesetPath = typeof opts.setSelectedRulesetPath === "function"
      ? opts.setSelectedRulesetPath
      : (() => {});

    function renderSrsPairItems(items, profileId) {
      if (!srsPairItemsRoot) {
        return;
      }
      const previouslyCheckedPairs = new Set();
      dynamicLeafState.forEach((entry) => {
        if (!entry || entry.kind !== "srs_pair_item") {
          return;
        }
        if (entry.input && entry.input.checked && entry.meta && entry.meta.srsPair) {
          previouslyCheckedPairs.add(String(entry.meta.srsPair));
        }
      });

      clearDynamicLeafsByKind("srs_pair_item");
      setDynamicSrsPairIds([]);
      srsPairItemsRoot.innerHTML = "";

      const pairData = resolveProfileSrsPairs(items, profileId);
      const pairs = Array.isArray(pairData.pairs) ? pairData.pairs : [];

      if (!pairs.length) {
        const empty = document.createElement("p");
        empty.className = "hint";
        empty.textContent = tr("share_center_empty_srs_pairs", "No SRS pair data available for this profile.");
        srsPairItemsRoot.appendChild(empty);
        setSrsPairStatus(
          tr(
            "share_center_status_no_srs_pairs_profile",
            `No non-empty SRS pair data on profile ${profileId}.`,
            [profileId]
          ),
          colors.DEFAULT
        );
        return;
      }

      const firstPair = String(pairs[0] && pairs[0].pair || "").trim();
      const nextLeafIds = [];
      pairs.forEach((pairEntry) => {
        const pair = String(pairEntry.pair || "").trim();
        if (!pair) {
          return;
        }
        const leafId = `srs-pair::${encodeURIComponent(pair)}`;
        const meta = {
          id: leafId,
          kind: "srs_pair_item",
          label: pair,
          path: joinPath([labels.profile, labels.srsData, pair]),
          groups: [labels.srsData],
          scope: "srs_pair",
          enabled: true,
          srsPair: pair
        };
        const hintParts = [];
        if (pairEntry.hasProfileData) {
          hintParts.push(tr("share_center_hint_profile_pair_data", "Profile pair data"));
        }
        if (pairEntry.hasSignalsData) {
          hintParts.push(tr("share_center_hint_signals", "Signals"));
        }
        if (pairEntry.hasImportedHelperData) {
          hintParts.push(tr("share_center_hint_imported_helper_snapshot", "Imported helper snapshot"));
        }
        if (pairEntry.isCurrent) {
          hintParts.push(tr("share_center_hint_current_pair", "Current pair"));
        }
        const checked = previouslyCheckedPairs.has(pair)
          || (!previouslyCheckedPairs.size && pairEntry.isCurrent)
          || (!previouslyCheckedPairs.size && !pairEntry.isCurrent && pair === firstPair);
        const row = createDynamicLeafRow(meta, {
          checked,
          hint: hintParts.join(" • ") || tr("share_center_hint_srs_pair_data_available", "SRS pair data available."),
          badge: pairEntry.isCurrent ? tr("share_center_badge_current", "Current") : null
        });
        const entry = {
          id: leafId,
          kind: "srs_pair_item",
          input: row.input,
          meta
        };
        row.input.addEventListener("change", () => {
          onLeafChanged(entry);
        });
        srsPairItemsRoot.appendChild(row.label);
        dynamicLeafState.set(leafId, entry);
        nextLeafIds.push(leafId);
      });
      setDynamicSrsPairIds(nextLeafIds);

      setSrsPairStatus(
        tr(
          "share_center_status_srs_pairs_profile",
          `${pairs.length} SRS pair${pairs.length === 1 ? "" : "s"} with data on profile ${profileId}.`,
          [String(pairs.length), profileId]
        ),
        colors.DEFAULT
      );
    }

    function renderRulesetItems(profileId, manualState, cache) {
      if (!rulesetItemsRoot) {
        return;
      }
      const previouslyCheckedPaths = new Set();
      dynamicLeafState.forEach((entry) => {
        if (!entry || entry.kind !== "ruleset_item") {
          return;
        }
        if (entry.input && entry.input.checked && entry.meta && entry.meta.rulesetPath) {
          previouslyCheckedPaths.add(String(entry.meta.rulesetPath));
        }
      });

      clearDynamicLeafsByKind("ruleset_item");
      setDynamicRulesetIds([]);
      rulesetItemsRoot.innerHTML = "";

      const entries = [];
      const seen = new Set();
      const enabledByPath = isObject(manualState && manualState.enabledByPath)
        ? manualState.enabledByPath
        : {};
      (Array.isArray(manualState.order) ? manualState.order : []).forEach((rawPath) => {
        const pathKey = normalizePath(rawPath);
        if (!pathKey || seen.has(pathKey)) {
          return;
        }
        seen.add(pathKey);
        const cacheEntry = cache[pathKey];
        const rules = cacheEntry && Array.isArray(cacheEntry.rules) ? cacheEntry.rules : [];
        const rulesCountRaw = cacheEntry
          ? (Number.isFinite(Number(cacheEntry.rulesCount)) ? Number(cacheEntry.rulesCount) : rules.length)
          : 0;
        const rulesCount = Math.max(0, rulesCountRaw);
        const exportable = rulesCount > 0;
        entries.push({
          path: pathKey,
          displayPath: cacheEntry && cacheEntry.displayPath ? cacheEntry.displayPath : pathKey,
          rulesCount,
          exportable,
          profileEnabled: enabledByPath[pathKey] !== false
        });
      });

      if (!entries.length) {
        const empty = document.createElement("p");
        empty.className = "hint";
        empty.textContent = tr("share_center_empty_rulesets", "No profile rulesets available.");
        rulesetItemsRoot.appendChild(empty);
        setRulesetStatus(
          tr(
            "share_center_status_no_rulesets_profile",
            `No exportable rulesets for profile ${profileId}.`,
            [profileId]
          ),
          colors.DEFAULT
        );
        return;
      }

      const firstExportablePath = (() => {
        for (const entry of entries) {
          if (entry.exportable) {
            return entry.path;
          }
        }
        return "";
      })();

      const nextLeafIds = [];
      const selectedPath = getSelectedRulesetPath();
      entries.forEach((rulesetEntry) => {
        const pathKey = normalizePath(rulesetEntry.path);
        const leafId = `ruleset::${encodeURIComponent(pathKey)}`;
        const label = pathBasename(rulesetEntry.displayPath);
        const exportable = rulesetEntry.exportable === true;
        const meta = {
          id: leafId,
          kind: "ruleset_item",
          label,
          path: joinPath([labels.profile, labels.rulesets, label]),
          groups: [labels.rulesets],
          scope: exportable ? "ruleset" : null,
          enabled: exportable,
          reason: exportable ? "" : tr("share_center_reason_rules_not_loaded", "Rules not loaded"),
          rulesetPath: pathKey,
          rulesetName: label,
          rulesCount: rulesetEntry.rulesCount,
          profileEnabled: rulesetEntry.profileEnabled
        };
        const checked = exportable && (
          previouslyCheckedPaths.has(pathKey)
          || (!previouslyCheckedPaths.size && selectedPath === pathKey)
          || (!previouslyCheckedPaths.size && !selectedPath && pathKey === firstExportablePath)
        );
        const profileEnabledText = rulesetEntry.profileEnabled
          ? tr("share_center_hint_enabled_in_profile", "Enabled in profile")
          : tr("share_center_hint_disabled_in_profile", "Disabled in profile");
        const pathText = normalizePath(rulesetEntry.displayPath);
        const hint = exportable
          ? `${tr("share_center_hint_rules_count", `${rulesetEntry.rulesCount} rules`, [String(rulesetEntry.rulesCount)])} • ${profileEnabledText}${pathText && pathText !== label ? ` • ${pathText}` : ""}`
          : `${tr("share_center_hint_rules_not_loaded_path", "Rules not loaded yet for this path")}${pathText && pathText !== label ? ` • ${pathText}` : ""}`;
        const row = createDynamicLeafRow(meta, {
          checked,
          hint,
          isPending: exportable !== true,
          isDisabled: exportable !== true,
          badge: exportable
            ? (rulesetEntry.profileEnabled
              ? tr("share_center_badge_enabled", "Enabled")
              : tr("share_center_badge_disabled", "Disabled"))
            : tr("share_center_badge_unavailable", "Unavailable")
        });
        const entry = {
          id: leafId,
          kind: "ruleset_item",
          input: row.input,
          meta
        };
        row.input.addEventListener("change", () => {
          onLeafChanged(entry);
        });
        rulesetItemsRoot.appendChild(row.label);
        dynamicLeafState.set(leafId, entry);
        nextLeafIds.push(leafId);
        if (row.input.checked && exportable) {
          setSelectedRulesetPath(pathKey);
        }
      });
      setDynamicRulesetIds(nextLeafIds);
      const exportableCount = entries.filter((entry) => entry.exportable).length;
      setRulesetStatus(
        tr(
          "share_center_status_rulesets_profile",
          `${entries.length} ruleset${entries.length === 1 ? "" : "s"} on profile ${profileId}; ${exportableCount} exportable now.`,
          [String(entries.length), profileId, String(exportableCount)]
        ),
        colors.DEFAULT
      );
    }

    function renderModuleItems(items, profileId) {
      if (!moduleItemsRoot) {
        return;
      }
      const previouslyCheckedModuleIds = new Set();
      dynamicLeafState.forEach((entry) => {
        if (!entry || entry.kind !== "module_item") {
          return;
        }
        if (entry.input && entry.input.checked && entry.meta && entry.meta.moduleId) {
          previouslyCheckedModuleIds.add(String(entry.meta.moduleId));
        }
      });

      clearDynamicLeafsByKind("module_item");
      setDynamicModuleIds([]);
      moduleItemsRoot.innerHTML = "";

      const moduleData = resolveProfileModules(items, profileId);
      const modules = Array.isArray(moduleData.modules) ? moduleData.modules : [];
      const targetLanguage = String(moduleData.targetLanguage || "en");

      if (!modules.length) {
        const empty = document.createElement("p");
        empty.className = "hint";
        empty.textContent = tr("share_center_empty_modules", "No modules available for this profile/language.");
        moduleItemsRoot.appendChild(empty);
        setModuleStatus(
          tr(
            "share_center_status_no_modules_profile",
            `No modules available for profile ${profileId} (${targetLanguage}).`,
            [profileId, targetLanguage]
          ),
          colors.DEFAULT
        );
        return;
      }

      const nextLeafIds = [];
      modules.forEach((moduleEntry) => {
        const moduleId = String(moduleEntry.moduleId || "").trim();
        if (!moduleId) {
          return;
        }
        const leafId = `module::${moduleId}`;
        const label = String(moduleEntry.label || moduleId);
        const meta = {
          id: leafId,
          kind: "module_item",
          label,
          path: joinPath([labels.profile, labels.modules, label]),
          groups: [labels.modules],
          scope: "module_item",
          enabled: true,
          moduleId,
          moduleEnabledInProfile: moduleEntry.enabledInProfile === true,
          moduleTargetLanguage: targetLanguage
        };
        const enabledInProfile = moduleEntry.enabledInProfile === true;
        const row = createDynamicLeafRow(meta, {
          checked: previouslyCheckedModuleIds.has(moduleId),
          hint: moduleEntry.description
            ? `${moduleEntry.description} • ${enabledInProfile
              ? tr("share_center_hint_enabled_in_profile", "Enabled in profile")
              : tr("share_center_hint_disabled_in_profile", "Disabled in profile")}`
            : (
                enabledInProfile
                  ? tr("share_center_hint_enabled_in_this_profile", "Enabled in this profile.")
                  : tr("share_center_hint_disabled_in_this_profile", "Disabled in this profile.")
              )
        });
        const entry = {
          id: leafId,
          kind: "module_item",
          input: row.input,
          meta
        };
        row.input.addEventListener("change", () => {
          onLeafChanged(entry);
        });
        moduleItemsRoot.appendChild(row.label);
        dynamicLeafState.set(leafId, entry);
        nextLeafIds.push(leafId);
      });
      setDynamicModuleIds(nextLeafIds);

      setModuleStatus(
        tr(
          "share_center_status_modules_profile",
          `${modules.length} module${modules.length === 1 ? "" : "s"} for profile ${profileId} (${targetLanguage}).`,
          [String(modules.length), profileId, targetLanguage]
        ),
        colors.DEFAULT
      );
    }

    return {
      renderSrsPairItems,
      renderRulesetItems,
      renderModuleItems
    };
  }

  root.optionsShareCenterRenderers = {
    createRenderers
  };
})();
