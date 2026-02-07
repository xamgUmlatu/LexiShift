class HelperManager {
  constructor(i18n, logger) {
    this.i18n = i18n;
    this.logger = logger || console.log;
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

  async runRulegenPreview(pair, maxActive) {
    const client = this.getClient();
    if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));

    const startedAt = Date.now();
    const rulegenResponse = await client.triggerRulegen({
      pair: pair,
      // Preview mode should not mutate helper-side SRS state.
      initialize_if_empty: false,
      persist_store: false,
      persist_outputs: false,
      update_status: false,
      debug: true,
      debug_sample_size: 10,
      max_active: maxActive
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
      helperCache.saveSnapshot(pair, snapshot);
    }

    if (!snapshot) throw new Error(this.i18n.t("status_srs_rulegen_failed", null, "Rule preview failed."));
    return { rulegenData, snapshot, duration };
  }

  async initializeSrsSet(pair, setTopN, options) {
    const client = this.getClient();
    if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
    const sizing = this.normalizeSrsSizing(setTopN, options);
    const opts = options && typeof options === "object" ? options : {};
    const strategy = typeof opts.strategy === "string" && opts.strategy ? opts.strategy : "profile_bootstrap";
    const objective = typeof opts.objective === "string" && opts.objective ? opts.objective : "bootstrap";
    const trigger = typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_initialize_button";
    const profileContext = opts.profileContext && typeof opts.profileContext === "object"
      ? opts.profileContext
      : {};

    const response = await client.initializeSrs({
      pair,
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
    const strategy = typeof opts.strategy === "string" && opts.strategy ? opts.strategy : "profile_bootstrap";
    const objective = typeof opts.objective === "string" && opts.objective ? opts.objective : "bootstrap";
    const trigger = typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_plan_button";
    const profileContext = opts.profileContext && typeof opts.profileContext === "object"
      ? opts.profileContext
      : {};
    const response = await client.planSrsSet({
      pair,
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

  async resetSrs(pair) {
    const client = this.getClient();
    if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));

    this.logger(`[HelperManager] resetSrs called for ${pair}`);
    const response = await client.resetSrs({ pair });

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
        await helperCache.clearPair(pair);
      } else if (helperCache) {
        if (typeof helperCache.deleteSnapshot === "function") {
          await helperCache.deleteSnapshot(pair);
        }
        if (typeof helperCache.deleteRuleset === "function") {
          await helperCache.deleteRuleset(pair);
        }
      }
    } catch (err) {
      this.logger("Failed clearing helper cache for reset pair.", err);
    }

    return response.data;
  }
}
