(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installHelperSrsSetMethods(proto) {
    if (!proto || typeof proto !== "object") {
      return;
    }

    function applyBootstrapTopN(payload, sizing) {
      const rawTopN = sizing && Number.parseInt(sizing.bootstrapTopN, 10);
      if (!Number.isFinite(rawTopN)) {
        return payload;
      }
      payload.set_top_n = Math.max(200, rawTopN);
      payload.bootstrap_top_n = Math.max(200, rawTopN);
      return payload;
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

      const payload = applyBootstrapTopN({
        pair,
        profile_id: profileId,
        initial_active_count: sizing.initialActiveCount,
        max_active_items_hint: sizing.maxActiveItemsHint,
        replace_pair: false,
        strategy,
        objective,
        trigger,
        profile_context: profileContext
      }, sizing);
      const response = await client.initializeSrs(payload, 30000);
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_set_init_failed",
            "Practice setup failed."
          )
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
      const payload = applyBootstrapTopN({
        pair,
        profile_id: profileId,
        strategy,
        objective,
        initial_active_count: sizing.initialActiveCount,
        max_active_items_hint: sizing.maxActiveItemsHint,
        trigger,
        profile_context: profileContext
      }, sizing);
      const response = await client.planSrsSet(payload, 15000);
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_set_init_failed",
            "Practice setup failed."
          )
        );
      }
      return response.data || {};
    };

    proto.previewSrsAdmission = async function previewSrsAdmission(pair, setTopN, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const sizing = this.normalizeSrsSizing(setTopN, options);
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const strategy = typeof opts.strategy === "string" && opts.strategy ? opts.strategy : "profile_bootstrap";
      const objective = typeof opts.objective === "string" && opts.objective ? opts.objective : "bootstrap";
      const trigger = typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_admission_preview_button";
      const previewCount = Number.parseInt(opts.previewCount, 10);
      const previewSamplingMode = typeof opts.previewSamplingMode === "string" && opts.previewSamplingMode
        ? opts.previewSamplingMode
        : undefined;
      const previewSeed = Number.parseInt(opts.previewSeed, 10);
      const profileContext = opts.profileContext && typeof opts.profileContext === "object"
        ? opts.profileContext
        : {};
      const payload = applyBootstrapTopN({
        pair,
        profile_id: profileId,
        strategy,
        objective,
        initial_active_count: sizing.initialActiveCount,
        max_active_items_hint: sizing.maxActiveItemsHint,
        preview_count: Number.isFinite(previewCount) ? Math.max(1, Math.min(previewCount, 20)) : 10,
        preview_sampling_mode: previewSamplingMode,
        preview_seed: Number.isFinite(previewSeed) ? previewSeed : undefined,
        trigger,
        profile_context: profileContext
      }, sizing);
      const response = await client.previewSrsAdmission(payload, 60000);
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_admission_preview_failed",
            "Word sample failed."
          )
        );
      }
      return response.data || {};
    };

    proto.refreshSrsSet = async function refreshSrsSet(pair, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const allowedPos = Array.isArray(opts.allowedPos)
        ? opts.allowedPos.map((value) => String(value || "").trim()).filter((value) => value)
        : (typeof opts.allowedPos === "string"
          ? opts.allowedPos.split(",").map((value) => String(value || "").trim()).filter((value) => value)
          : undefined);
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
        allowed_pos: allowedPos && allowedPos.length ? allowedPos : undefined,
        persist_store: opts.persistStore !== false,
        strategy: typeof opts.strategy === "string" && opts.strategy ? opts.strategy : "profile_growth",
        trigger: typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_refresh_button",
        profile_context: opts.profileContext && typeof opts.profileContext === "object"
          ? opts.profileContext
          : undefined
      }, 30000);
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_refresh_failed",
            "Learning words refresh failed."
          )
        );
      }
      return response.data || {};
    };

    proto.listSrsItems = async function listSrsItems(pair, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const response = await client.listSrsItems(pair, profileId, {
        compact: opts.compact === true
      });
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_items_list_failed",
            "Failed to load learning words."
          )
        );
      }
      return response.data || {};
    };

    proto.getSrsItemRuleDetails = async function getSrsItemRuleDetails(pair, lemma, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const normalizedLemma = String(lemma || "").trim();
      if (!normalizedLemma) throw new Error("Missing SRS word.");
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const limit = Number.parseInt(opts.limit, 10);
      const response = await client.getSrsItemRuleDetails(
        pair,
        profileId,
        normalizedLemma,
        Number.isFinite(limit) ? limit : undefined
      );
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_rule_details_failed",
            "Failed to load rule details."
          )
        );
      }
      return response.data || {};
    };

    proto.lookupWordInfo = async function lookupWordInfo(request, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const apiFactory = globalThis.LexiShift && globalThis.LexiShift.wordInfoApi;
      if (!apiFactory || typeof apiFactory.create !== "function") {
        throw new Error("Word info API unavailable.");
      }
      const opts = options && typeof options === "object" ? options : {};
      const rawRequest = request && typeof request === "object" ? request : {};
      const profileId = this.normalizeProfileId(rawRequest.profileId || rawRequest.profile_id || opts.profileId);
      const api = apiFactory.create({ helperClient: client });
      const result = await api.lookup(
        {
          ...rawRequest,
          profileId
        },
        {
          timeoutMs: Number.parseInt(opts.timeoutMs, 10) || undefined
        }
      );
      if (!result || result.status === "error") {
        throw new Error(
          (result && result.error && result.error.message)
            || this.i18n.t("status_helper_failed", null, "Helper error.")
        );
      }
      return result;
    };

    proto.discardSrsItem = async function discardSrsItem(pair, lemma, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const normalizedLemma = String(lemma || "").trim();
      if (!normalizedLemma) throw new Error("Missing SRS word.");
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const response = await client.suppressSrsAdmission({
        pair,
        profile_id: profileId,
        lemma: normalizedLemma,
        reason: "user_blocked",
        note: typeof opts.note === "string" && opts.note
          ? opts.note
          : "srs_words_dashboard_discard"
      });
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_discard_failed",
            "Failed to discard learning word."
          )
        );
      }
      return response.data || {};
    };

    proto.planSrsRebalance = async function planSrsRebalance(pair, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const payload = {
        pair,
        profile_id: profileId,
        strategy: typeof opts.strategy === "string" && opts.strategy ? opts.strategy : "profile_growth",
        objective: typeof opts.objective === "string" && opts.objective ? opts.objective : "rebalance",
        max_active_items: Number.isFinite(Number(opts.maxActiveItems))
          ? Number(opts.maxActiveItems)
          : undefined,
        profile_context: opts.profileContext && typeof opts.profileContext === "object"
          ? opts.profileContext
          : undefined,
        trigger: typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_rebalance_preview_button"
      };
      const rawSetTopN = Number.parseInt(opts.setTopN, 10);
      if (Number.isFinite(rawSetTopN)) {
        payload.set_top_n = Math.max(200, rawSetTopN);
      }
      const response = await client.planSrsRebalance(payload, 30000);
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_rebalance_preview_failed",
            "Preference retune preview failed."
          )
        );
      }
      return response.data || {};
    };

    proto.applySrsRebalance = async function applySrsRebalance(pair, options) {
      const client = this.getClient();
      if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));
      const opts = options && typeof options === "object" ? options : {};
      const profileId = this.normalizeProfileId(opts.profileId);
      const payload = {
        pair,
        profile_id: profileId,
        strategy: typeof opts.strategy === "string" && opts.strategy ? opts.strategy : "profile_growth",
        objective: typeof opts.objective === "string" && opts.objective ? opts.objective : "rebalance",
        max_active_items: Number.isFinite(Number(opts.maxActiveItems))
          ? Number(opts.maxActiveItems)
          : undefined,
        profile_context: opts.profileContext && typeof opts.profileContext === "object"
          ? opts.profileContext
          : undefined,
        trigger: typeof opts.trigger === "string" && opts.trigger ? opts.trigger : "options_rebalance_apply_button"
      };
      const rawSetTopN = Number.parseInt(opts.setTopN, 10);
      if (Number.isFinite(rawSetTopN)) {
        payload.set_top_n = Math.max(200, rawSetTopN);
      }
      const response = await client.applySrsRebalance(payload, 30000);
      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_rebalance_apply_failed",
            "Preference retune failed."
          )
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
      const response = await client.resetSrs({
        pair,
        profile_id: profileId,
        preserve_lifecycle_metadata: opts.preserveLifecycleMetadata === true
      });

      this.logger("[HelperManager] resetSrs response:", response);

      if (!response || response.ok === false) {
        throw new Error(
          this.normalizeHelperErrorMessage(
            response && response.error,
            "status_srs_reset_failed",
            "This Vocabulary Practice deletion failed."
          )
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
