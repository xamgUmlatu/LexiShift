(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installHelperSrsSetMethods(proto) {
    if (!proto || typeof proto !== "object") {
      return;
    }

    proto.initializeSrsSet = async function initializeSrsSet(pair, setTopN, options) {
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
    };

    proto.planSrsSet = async function planSrsSet(pair, setTopN, options) {
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
    };

    proto.refreshSrsSet = async function refreshSrsSet(pair, options) {
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
    };

    proto.resetSrs = async function resetSrs(pair, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);

      this.logger(`[HelperManager] resetSrs called for ${pair} (profile=${profileId})`);
      const response = await client.resetSrs({ pair, profile_id: profileId });

      this.logger("[HelperManager] resetSrs response:", response);

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
    };
  }

  root.installHelperSrsSetMethods = installHelperSrsSetMethods;
})();
