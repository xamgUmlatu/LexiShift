(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installHelperDiagnosticsMethods(proto) {
    if (!proto || typeof proto !== "object") {
      return;
    }

    proto.getSrsRuntimeDiagnostics = async function getSrsRuntimeDiagnostics(pair, options) {
      const normalizedPair = String(pair || "").trim() || "en-ja";
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const result = {
        pair: normalizedPair,
        profile_id: profileId,
        helper: null,
        helper_error: null,
        cache: {
          ruleset_exists: false,
          ruleset_rules_count: 0,
          snapshot_exists: false,
          snapshot_target_count: 0,
          snapshot_generation_id: null,
          semantic_inventory_exists: false,
          semantic_inventory_schema_version: null,
          semantic_inventory_generation_id: null,
          semantic_inventory_competition_set_count: 0,
          semantic_inventory_phrase_set_count: 0,
          snapshot_semantic_generation_aligned: null
        },
        runtime_state: null
      };

      const client = this.getClient();
      if (client && typeof client.getSrsDiagnostics === "function") {
        try {
          const response = await client.getSrsDiagnostics(normalizedPair, profileId);
          if (response && response.ok !== false) {
            result.helper = response.data || null;
          } else {
            result.helper_error = this.normalizeHelperErrorMessage(
              response && response.error,
              "status_helper_failed",
              "Helper error."
            );
          }
        } catch (err) {
          result.helper_error = this.normalizeHelperThrownErrorMessage(
            err,
            "status_helper_failed",
            "Helper error."
          );
        }
      } else {
        result.helper_error = this.i18n.t("status_helper_missing", null, "Helper unavailable.");
      }

      const helperCache = globalThis.LexiShift && globalThis.LexiShift.helperCache;
      if (helperCache && typeof helperCache.loadRuleset === "function") {
        try {
          const cachedRuleset = await helperCache.loadRuleset(normalizedPair, { profileId });
          const rules = cachedRuleset && Array.isArray(cachedRuleset.rules)
            ? cachedRuleset.rules
            : [];
          result.cache.ruleset_exists = rules.length > 0;
          result.cache.ruleset_rules_count = rules.length;
        } catch (_err) {
          // Cache diagnostics are best-effort.
        }
      }
      if (helperCache && typeof helperCache.loadSnapshot === "function") {
        try {
          const cachedSnapshot = await helperCache.loadSnapshot(normalizedPair, { profileId });
          if (cachedSnapshot && typeof cachedSnapshot === "object") {
            const stats = cachedSnapshot.stats && typeof cachedSnapshot.stats === "object"
              ? cachedSnapshot.stats
              : {};
            const targetCount = Number.isFinite(Number(stats.target_count))
              ? Number(stats.target_count)
              : (Array.isArray(cachedSnapshot.targets) ? cachedSnapshot.targets.length : 0);
            result.cache.snapshot_exists = targetCount > 0;
            result.cache.snapshot_target_count = targetCount;
            result.cache.snapshot_generation_id = cachedSnapshot.generation_id
              ? String(cachedSnapshot.generation_id)
              : null;
          }
        } catch (_err) {
          // Cache diagnostics are best-effort.
        }
      }
      if (helperCache && typeof helperCache.loadSemanticInventory === "function") {
        try {
          const cachedInventory = await helperCache.loadSemanticInventory(normalizedPair, { profileId });
          if (cachedInventory && typeof cachedInventory === "object") {
            const competitionSets = cachedInventory.competition_sets && typeof cachedInventory.competition_sets === "object"
              ? cachedInventory.competition_sets
              : {};
            const phraseSets = cachedInventory.phrase_sets && typeof cachedInventory.phrase_sets === "object"
              ? cachedInventory.phrase_sets
              : {};
            result.cache.semantic_inventory_exists = true;
            result.cache.semantic_inventory_schema_version = Number.isFinite(
              Number(cachedInventory.schema_version)
            )
              ? Number(cachedInventory.schema_version)
              : null;
            result.cache.semantic_inventory_generation_id = cachedInventory.generation_id
              ? String(cachedInventory.generation_id)
              : null;
            result.cache.semantic_inventory_competition_set_count = Object.keys(competitionSets).length;
            result.cache.semantic_inventory_phrase_set_count = Object.keys(phraseSets).length;
          }
        } catch (_err) {
          // Cache diagnostics are best-effort.
        }
      }
      if (
        result.cache.snapshot_generation_id
        && result.cache.semantic_inventory_generation_id
      ) {
        result.cache.snapshot_semantic_generation_aligned = (
          result.cache.snapshot_generation_id === result.cache.semantic_inventory_generation_id
        );
      }

      const runtimeDiagnostics = globalThis.LexiShift && globalThis.LexiShift.srsRuntimeDiagnostics;
      if (runtimeDiagnostics && typeof runtimeDiagnostics.loadLastState === "function") {
        try {
          result.runtime_state = await runtimeDiagnostics.loadLastState();
        } catch (_err) {
          result.runtime_state = null;
        }
      }

      return result;
    };

    proto.runRulegenPreview = async function runRulegenPreview(pair, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);

      const startedAt = Date.now();
      const rulegenResponse = await client.triggerRulegen({
        pair: pair,
        profile_id: profileId,
        // Preview mode should not mutate helper-side SRS state.
        initialize_if_empty: false,
        persist_store: false,
        persist_outputs: false,
        update_status: false,
        debug: true,
        debug_sample_size: 10
      }, 15000);

      if (!rulegenResponse || rulegenResponse.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            rulegenResponse && rulegenResponse.error,
            "status_srs_rulegen_failed",
            "Rule preview failed."
          )
        );
      }

      const rulegenData = rulegenResponse.data || {};
      const duration = ((Date.now() - startedAt) / 1000).toFixed(1);
      const snapshot = rulegenData.snapshot || null;
      const helperCache = globalThis.LexiShift && globalThis.LexiShift.helperCache;

      if (snapshot && helperCache && typeof helperCache.saveSnapshot === "function") {
        helperCache.saveSnapshot(pair, snapshot, { profileId });
      }

      if (!snapshot) throw new Error(this.i18n.t("status_srs_rulegen_failed", null, "Rule preview failed."));
      return { rulegenData, snapshot, duration };
    };

    proto.runSampledRulegenPreview = async function runSampledRulegenPreview(pair, sampleCount = 5, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));

      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const strategy = typeof opts.strategy === "string" && opts.strategy
        ? opts.strategy
        : "weighted_priority";
      const seed = Number.isInteger(opts.seed) ? opts.seed : null;
      const requestedCount = Number.parseInt(sampleCount, 10);
      const normalizedCount = Number.isFinite(requestedCount)
        ? Math.max(1, Math.min(requestedCount, 200))
        : 5;

      const startedAt = Date.now();
      const rulegenResponse = await client.triggerRulegen({
        pair: pair,
        profile_id: profileId,
        // Preview mode should not mutate helper-side SRS state.
        initialize_if_empty: false,
        persist_store: false,
        persist_outputs: false,
        update_status: false,
        debug: true,
        debug_sample_size: 10,
        sample_count: normalizedCount,
        sample_strategy: strategy,
        sample_seed: seed
      }, 15000);

      if (!rulegenResponse || rulegenResponse.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            rulegenResponse && rulegenResponse.error,
            "status_srs_rulegen_failed",
            "Rule preview failed."
          )
        );
      }

      const rulegenData = rulegenResponse.data || {};
      const duration = ((Date.now() - startedAt) / 1000).toFixed(1);
      const snapshot = rulegenData.snapshot || null;
      const helperCache = globalThis.LexiShift && globalThis.LexiShift.helperCache;

      if (snapshot && helperCache && typeof helperCache.saveSnapshot === "function") {
        helperCache.saveSnapshot(pair, snapshot, { profileId });
      }

      if (!snapshot) throw new Error(this.i18n.t("status_srs_rulegen_failed", null, "Rule preview failed."));
      return { rulegenData, snapshot, duration };
    };

    proto.installSemanticPack = async function installSemanticPack(pair, options) {
      const client = this.getClient();
      if (!client || typeof client.installSemanticPack !== "function") {
        throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      }
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const semanticInventoryPath = String(opts.semanticInventoryPath || "").trim();
      const dataRoot = String(opts.dataRoot || "").trim();
      const allowDefaultDataRoot = opts.allowDefaultDataRoot === true;
      if (!dataRoot && !allowDefaultDataRoot) {
        throw new Error(
          this.i18n.t(
            "status_semantic_pack_data_root_required",
            null,
            "Data root is required unless default data root is enabled."
          )
        );
      }
      const response = await client.installSemanticPack({
        pair: pair,
        profile_id: profileId,
        semantic_inventory_path: semanticInventoryPath || undefined,
        pack_id: String(opts.packId || "en-es-active-only-combined-full-v1-tranche-004").trim()
          || "en-es-active-only-combined-full-v1-tranche-004",
        data_root: dataRoot || undefined,
        allow_default_data_root: allowDefaultDataRoot,
        dry_run: opts.dryRun === true,
        no_pack_copy: opts.copyPack === false
      }, 60000);
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_semantic_pack_install_failed",
            "Semantic pack install failed."
          )
        );
      }
      const helperCache = globalThis.LexiShift && globalThis.LexiShift.helperCache;
      if (helperCache && typeof helperCache.clearPair === "function") {
        await helperCache.clearPair(pair, { profileId });
      }
      return response.data || {};
    };
  }

  root.installHelperDiagnosticsMethods = installHelperDiagnosticsMethods;
})();
