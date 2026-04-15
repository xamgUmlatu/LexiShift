(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const RULEGEN_PREVIEW_TIMEOUT_MS = 60000;
  const LOG_PREFIX = "[LexiShift][Options][Diagnostics]";

  function debugLog(message, details = {}) {
    try {
      console.log(`${LOG_PREFIX} ${message}`, details);
    } catch (_error) {
      // Logging is best-effort.
    }
  }

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
          snapshot_target_count: 0
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
            result.helper_error = response && response.error && response.error.message
              ? response.error.message
              : this.i18n.t("status_helper_failed", null, "Helper error.");
          }
        } catch (err) {
          result.helper_error = err && err.message
            ? err.message
            : this.i18n.t("status_helper_failed", null, "Helper error.");
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
          }
        } catch (_err) {
          // Cache diagnostics are best-effort.
        }
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
      debugLog("rulegen preview started", {
        pair,
        profile_id: profileId
      });

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
      }, RULEGEN_PREVIEW_TIMEOUT_MS);

      if (!rulegenResponse || rulegenResponse.ok === false) {
        debugLog("rulegen preview failed", {
          pair,
          profile_id: profileId,
          duration_ms: Date.now() - startedAt,
          error: rulegenResponse && rulegenResponse.error && rulegenResponse.error.message
            ? rulegenResponse.error.message
            : "Rule preview failed."
        });
        throw new Error(
          rulegenResponse && rulegenResponse.error && rulegenResponse.error.message
            ? rulegenResponse.error.message
            : this.i18n.t("status_srs_rulegen_failed", null, "Rule preview failed.")
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
      debugLog("rulegen preview finished", {
        pair,
        profile_id: profileId,
        duration_ms: Date.now() - startedAt,
        targets: snapshot && snapshot.stats && Number.isFinite(Number(snapshot.stats.target_count))
          ? Number(snapshot.stats.target_count)
          : 0
      });
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
      debugLog("sampled rulegen preview started", {
        pair,
        profile_id: profileId,
        sample_count: normalizedCount,
        strategy,
        seed
      });

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
      }, RULEGEN_PREVIEW_TIMEOUT_MS);

      if (!rulegenResponse || rulegenResponse.ok === false) {
        debugLog("sampled rulegen preview failed", {
          pair,
          profile_id: profileId,
          sample_count: normalizedCount,
          strategy,
          duration_ms: Date.now() - startedAt,
          error: rulegenResponse && rulegenResponse.error && rulegenResponse.error.message
            ? rulegenResponse.error.message
            : "Rule preview failed."
        });
        throw new Error(
          rulegenResponse && rulegenResponse.error && rulegenResponse.error.message
            ? rulegenResponse.error.message
            : this.i18n.t("status_srs_rulegen_failed", null, "Rule preview failed.")
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
      debugLog("sampled rulegen preview finished", {
        pair,
        profile_id: profileId,
        sample_count: normalizedCount,
        strategy,
        duration_ms: Date.now() - startedAt,
        targets: snapshot && snapshot.stats && Number.isFinite(Number(snapshot.stats.target_count))
          ? Number(snapshot.stats.target_count)
          : 0
      });
      return { rulegenData, snapshot, duration };
    };
  }

  root.installHelperDiagnosticsMethods = installHelperDiagnosticsMethods;
})();
