class HelperManager {
  constructor(i18n, logger) {
    this.i18n = i18n;
    this.logger = logger || console.log;
  }

  normalizeProfileId(profileId) {
    const normalized = String(profileId || "").trim();
    return normalized || "default";
  }

  normalizeSrsSizing(sizingOrTopN, options) {
    const rawSizing = (sizingOrTopN && typeof sizingOrTopN === "object")
      ? sizingOrTopN
      : {};
    const rawTopN = Number.parseInt(
      rawSizing.bootstrapTopN !== undefined ? rawSizing.bootstrapTopN : sizingOrTopN,
      10
    );
    const bootstrapTopN = Number.isFinite(rawTopN) ? Math.max(200, rawTopN) : 800;
    const rawInitial = Number.parseInt(
      rawSizing.initialActiveCount !== undefined
        ? rawSizing.initialActiveCount
        : (options && options.initialActiveCount),
      10
    );
    const initialActiveCount = Number.isFinite(rawInitial)
      ? Math.max(1, Math.min(rawInitial, bootstrapTopN))
      : Math.min(40, bootstrapTopN);
    const rawHint = Number.parseInt(
      rawSizing.maxActiveItemsHint !== undefined
        ? rawSizing.maxActiveItemsHint
        : (options && options.maxActiveItemsHint),
      10
    );
    const maxActiveItemsHint = Number.isFinite(rawHint) ? Math.max(1, rawHint) : null;
    return { bootstrapTopN, initialActiveCount, maxActiveItemsHint };
  }

  getClient() {
    const transport = globalThis.LexiShift && globalThis.LexiShift.helperTransportExtension;
    const Client = globalThis.LexiShift && globalThis.LexiShift.helperClient;
    if (!Client || !transport) return null;
    return new Client(transport);
  }

  async getStatus() {
    const client = this.getClient();
    if (!client) {
      return {
        ok: false,
        message: this.i18n.t("status_helper_missing", null, "Helper unavailable."),
        lastRun: ""
      };
    }
    try {
      const response = await client.getStatus();
      if (!response || response.ok === false) {
        const msg = response && response.error && response.error.message
          ? response.error.message
          : this.i18n.t("status_helper_failed", null, "Helper error.");
        return { ok: false, message: msg, lastRun: "" };
      }
      const data = response.data || {};
      const lastRun = data.last_run_at || "";
      const lastError = data.last_error;
      if (lastError) {
        return {
          ok: true,
          message: this.i18n.t("status_helper_error", null, "Helper error."),
          lastRun
        };
      }
      return {
        ok: true,
        message: this.i18n.t("status_helper_ok", null, "Helper connected."),
        lastRun
      };
    } catch (err) {
      this.logger("Helper status failed.", err);
      return {
        ok: false,
        message: this.i18n.t("status_helper_failed", null, "Helper error."),
        lastRun: ""
      };
    }
  }

  async getProfiles() {
    const client = this.getClient();
    if (!client || typeof client.getProfiles !== "function") {
      return {
        ok: false,
        data: null,
        error: {
          code: "helper_missing",
          message: this.i18n.t("status_helper_missing", null, "Helper unavailable.")
        }
      };
    }
    try {
      const response = await client.getProfiles();
      if (!response || response.ok === false) {
        return {
          ok: false,
          data: null,
          error: {
            code: (response && response.error && response.error.code) || "helper_error",
            message: (response && response.error && response.error.message)
              || this.i18n.t("status_helper_failed", null, "Helper error.")
          }
        };
      }
      return { ok: true, data: response.data || null, error: null };
    } catch (err) {
      return {
        ok: false,
        data: null,
        error: {
          code: "helper_error",
          message: err && err.message
            ? err.message
            : this.i18n.t("status_helper_failed", null, "Helper error.")
        }
      };
    }
  }

  async getSrsRuntimeDiagnostics(pair, options) {
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
  }

  async testConnection() {
    const client = this.getClient();
    if (!client) return this.i18n.t("status_helper_missing", null, "Helper unavailable.");
    try {
      const response = await client.hello();
      if (!response || response.ok === false) {
        const msg = response && response.error && response.error.message
          ? response.error.message
          : this.i18n.t("status_helper_failed", null, "Helper error.");
        return this.i18n.t("status_helper_test_failed", msg, `Connection failed: ${msg}`);
      }
      const version = (response.data && response.data.helper_version) || "";
      return this.i18n.t("status_helper_test_ok", version, version ? `Helper connected (v${version}).` : "Helper connected.");
    } catch (err) {
      this.logger("Helper test failed.", err);
      const msg = err && err.message ? err.message : this.i18n.t("status_helper_failed", null, "Helper error.");
      return this.i18n.t("status_helper_test_failed", msg, `Connection failed: ${msg}`);
    }
  }

  async openDataDir() {
    const client = this.getClient();
    if (!client) return this.i18n.t("status_helper_missing", null, "Helper unavailable.");
    try {
      const response = await client.openDataDir();
      if (!response || response.ok === false) {
        const msg = response && response.error && response.error.message
          ? response.error.message
          : this.i18n.t("status_helper_open_failed", null, "Failed to open folder.");
        return this.i18n.t("status_helper_open_failed", msg, `Open failed: ${msg}`);
      }
      const opened = response.data && response.data.opened ? response.data.opened : "";
      return this.i18n.t("status_helper_opened", opened, opened ? `Opened: ${opened}` : "Opened.");
    } catch (err) {
      this.logger("Open helper data dir failed.", err);
      const msg = err && err.message ? err.message : this.i18n.t("status_helper_open_failed", null, "Failed to open folder.");
      return this.i18n.t("status_helper_open_failed", msg, `Open failed: ${msg}`);
    }
  }

  async runRulegenPreview(pair, options) {
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
    return { rulegenData, snapshot, duration };
  }

  async runSampledRulegenPreview(pair, sampleCount = 5, options) {
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
    return { rulegenData, snapshot, duration };
  }

  async initializeSrsSet(pair, setTopN, options) {
    const client = this.getClient();
    if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
    const sizing = this.normalizeSrsSizing(setTopN, options);
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeProfileId(opts.profileId);
    const strategy = typeof opts.strategy === "string" && opts.strategy ? opts.strategy : "profile_bootstrap";
    const objective = typeof opts.objective === "string" && opts.objective ? opts.objective : "bootstrap";
    const trigger = typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_initialize_button";
    const profileContext = opts.profileContext && typeof opts.profileContext === "object"
      ? opts.profileContext
      : {};

    const response = await client.initializeSrs({
      pair,
      profile_id: profileId,
      set_top_n: sizing.bootstrapTopN,
      bootstrap_top_n: sizing.bootstrapTopN,
      initial_active_count: sizing.initialActiveCount,
      max_active_items_hint: sizing.maxActiveItemsHint,
      replace_pair: false,
      strategy,
      objective,
      trigger,
      profile_context: profileContext
    }, 30000);
    if (!response || response.ok === false) {
      throw new Error(
        response && response.error && response.error.message
          ? response.error.message
          : this.i18n.t("status_srs_set_init_failed", null, "S initialization failed.")
      );
    }
    return response.data || {};
  }

  async planSrsSet(pair, setTopN, options) {
    const client = this.getClient();
    if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
    const sizing = this.normalizeSrsSizing(setTopN, options);
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeProfileId(opts.profileId);
    const strategy = typeof opts.strategy === "string" && opts.strategy ? opts.strategy : "profile_bootstrap";
    const objective = typeof opts.objective === "string" && opts.objective ? opts.objective : "bootstrap";
    const trigger = typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_plan_button";
    const profileContext = opts.profileContext && typeof opts.profileContext === "object"
      ? opts.profileContext
      : {};
    const response = await client.planSrsSet({
      pair,
      profile_id: profileId,
      strategy,
      objective,
      set_top_n: sizing.bootstrapTopN,
      bootstrap_top_n: sizing.bootstrapTopN,
      initial_active_count: sizing.initialActiveCount,
      max_active_items_hint: sizing.maxActiveItemsHint,
      trigger,
      profile_context: profileContext
    }, 15000);
    if (!response || response.ok === false) {
      throw new Error(
        response && response.error && response.error.message
          ? response.error.message
          : this.i18n.t("status_srs_set_init_failed", null, "S planning failed.")
      );
    }
    return response.data || {};
  }

  async refreshSrsSet(pair, options) {
    const client = this.getClient();
    if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeProfileId(opts.profileId);
    const response = await client.refreshSrsSet({
      pair,
      profile_id: profileId,
      set_top_n: Number.parseInt(opts.setTopN, 10) || 2000,
      feedback_window_size: Number.parseInt(opts.feedbackWindowSize, 10) || 100,
      max_active_items: Number.isFinite(Number(opts.maxActiveItems))
        ? Number(opts.maxActiveItems)
        : undefined,
      max_new_items: Number.isFinite(Number(opts.maxNewItems))
        ? Number(opts.maxNewItems)
        : undefined,
      persist_store: opts.persistStore !== false,
      trigger: typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_refresh_button",
      profile_context: opts.profileContext && typeof opts.profileContext === "object"
        ? opts.profileContext
        : undefined
    }, 30000);
    if (!response || response.ok === false) {
      throw new Error(
        response && response.error && response.error.message
          ? response.error.message
          : this.i18n.t("status_srs_set_init_failed", null, "SRS refresh failed.")
      );
    }
    return response.data || {};
  }

  async resetSrs(pair, options) {
    const client = this.getClient();
    if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
    const opts = options && typeof options === "object" ? options : {};
    const profileId = this.normalizeProfileId(opts.profileId);

    this.logger(`[HelperManager] resetSrs called for ${pair} (profile=${profileId})`);
    const response = await client.resetSrs({ pair, profile_id: profileId });

    this.logger(`[HelperManager] resetSrs response:`, response);

    if (!response || response.ok === false) {
      throw new Error(
        response && response.error && response.error.message
          ? response.error.message
          : this.i18n.t("status_srs_reset_failed", null, "SRS reset failed.")
      );
    }

    const helperCache = globalThis.LexiShift && globalThis.LexiShift.helperCache;
    try {
      if (helperCache && typeof helperCache.clearPair === "function") {
        await helperCache.clearPair(pair, { profileId });
      } else if (helperCache) {
        if (typeof helperCache.deleteSnapshot === "function") {
          await helperCache.deleteSnapshot(pair, { profileId });
        }
        if (typeof helperCache.deleteRuleset === "function") {
          await helperCache.deleteRuleset(pair, { profileId });
        }
      }
    } catch (err) {
      this.logger("Failed clearing helper cache for reset pair.", err);
    }

    return response.data;
  }
}
