(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const DEFAULT_SEMANTIC_FALLBACK_POLICY = "abstain_on_unavailable";
  const FALLBACK_POLICIES = new Set(["legacy_on_unavailable", "abstain_on_unavailable", "soft_affordance_on_unavailable"]);
  const DEBUG_DECISION_OVERRIDES = new Set(["replace", "abstain", "soft_affordance"]);
  const INVENTORY_RESOLUTION_CACHE_TTL_MS = 5 * 60 * 1000;
  const SEMANTIC_HELPER_BATCH_FIT_SCOPE = "per_match";
  const SEMANTIC_HELPER_MAX_REQUESTS_PER_BATCH = 32;
  const SEMANTIC_HELPER_BATCH_TIMEOUT_MS = 15000;
  const MAX_DEBUG_HELPER_BATCH_FLUSH_MS = 50;
  function createAdmitter(options) {
    const opts = options && typeof options === "object" ? options : {};
    const helperRulesRuntime = opts.helperRulesRuntime && typeof opts.helperRulesRuntime === "object"
      ? opts.helperRulesRuntime
      : null;
    const getRuleOrigin = typeof opts.getRuleOrigin === "function"
      ? opts.getRuleOrigin
      : (_rule) => String(opts.ruleOriginRuleset || "ruleset");
    const normalizeProfileId = typeof opts.normalizeProfileId === "function"
      ? opts.normalizeProfileId
      : (value) => String(value || "").trim() || "default";
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const nowMs = typeof opts.nowMs === "function"
      ? opts.nowMs
      : (() => (
          globalThis.performance && typeof globalThis.performance.now === "function"
            ? globalThis.performance.now()
            : Date.now()
        ));
    const createRequestMatch = opts.createRequestMatch;
    const createSummary = opts.createSummary;
    const finalizeSummary = opts.finalizeSummary;
    const summarizeHelperBatch = opts.summarizeHelperBatch;
    const summarizeInventoryLookup = opts.summarizeInventoryLookup;
    const summarizeDecision = opts.summarizeDecision;
    const inventoryResolutionCache = new Map();
    let queuedAdmissions = [];
    let queuedFlushScheduled = false;
    function isSemanticAdmissionEnabled(settings) {
      return Boolean(settings && settings.srsEnabled === true && settings.srsSemanticAdmissionEnabled === true);
    }
    function resolveFallbackPolicy(settings) {
      const normalized = String(settings && settings.srsSemanticAdmissionFallbackPolicy
        ? settings.srsSemanticAdmissionFallbackPolicy
        : DEFAULT_SEMANTIC_FALLBACK_POLICY).trim() || DEFAULT_SEMANTIC_FALLBACK_POLICY;
      return FALLBACK_POLICIES.has(normalized) ? normalized : DEFAULT_SEMANTIC_FALLBACK_POLICY;
    }
    function resolveFallbackDecision(fallbackPolicy) {
      if (fallbackPolicy === "abstain_on_unavailable") return "abstain";
      if (fallbackPolicy === "soft_affordance_on_unavailable") return "soft_affordance";
      return "replace";
    }
    function resolveDebugDecisionOverride(settings) {
      if (!settings || settings.debugEnabled !== true) return "";
      const normalized = String(settings.debugSemanticDecisionOverride || "").trim().toLowerCase();
      return DEBUG_DECISION_OVERRIDES.has(normalized) ? normalized : "";
    }
    function resolveDebugHelperBatchFlushMs(context) {
      const settings = context && context.settings && typeof context.settings === "object" ? context.settings : {};
      const parsed = Number.parseInt(settings.debugSemanticHelperBatchFlushMs, 10);
      return Number.isFinite(parsed) && parsed > 0 ? Math.min(MAX_DEBUG_HELPER_BATCH_FLUSH_MS, parsed) : 0;
    }
    function resolveSemanticAdmission(match) {
      const metadata = match && match.rule && match.rule.metadata && typeof match.rule.metadata === "object"
        ? match.rule.metadata
        : null;
      const admission = metadata && metadata.semantic_admission && typeof metadata.semantic_admission === "object"
        ? metadata.semantic_admission
        : null;
      return admission ? { ...admission } : null;
    }
    function resolvePairForMatch(match, settings) {
      const metadata = match && match.rule && match.rule.metadata && typeof match.rule.metadata === "object"
        ? match.rule.metadata
        : null;
      return String(metadata && metadata.language_pair ? metadata.language_pair : settings && settings.srsPair || "")
        .trim()
        .toLowerCase();
    }
    function shouldConsiderMatch(match, settings) {
      if (!match || !match.rule || getRuleOrigin(match.rule) !== ruleOriginSrs) return false;
      return Boolean(resolveSemanticAdmission(match) && isSemanticAdmissionEnabled(settings));
    }
    function buildDecisionRecord(matchId, admission, decision, decisionSource, reasonCodes) {
      const pointer = admission && typeof admission === "object" ? admission : {};
      return {
        match_id: String(matchId || ""),
        decision,
        decision_source: decisionSource,
        reason_codes: Array.isArray(reasonCodes) && reasonCodes.length
          ? reasonCodes.map((code) => String(code || "")).filter(Boolean)
          : ["semantic_runtime_unknown"],
        trigger_id: String(pointer.trigger_id || ""),
        sense_id: String(pointer.sense_id || ""),
        competition_set_id: String(pointer.competition_set_id || ""),
        phrase_set_id: String(pointer.phrase_set_id || "")
      };
    }
    function buildEffectiveDecisionRecord(decisionRecord, debugDecisionOverride) {
      if (!decisionRecord || !debugDecisionOverride) return decisionRecord;
      const originalDecision = String(decisionRecord.decision || "");
      const originalSource = String(decisionRecord.decision_source || "");
      const applied = originalDecision !== debugDecisionOverride;
      return {
        ...decisionRecord,
        effective_decision: applied ? debugDecisionOverride : originalDecision,
        effective_decision_source: applied ? "debug_override" : originalSource,
        debug_override: debugDecisionOverride,
        debug_original_decision: originalDecision,
        debug_original_decision_source: originalSource
      };
    }
    function createState(context, contextIndex, contextCount) {
      const ctx = context && typeof context === "object" ? context : {};
      const settings = ctx.settings && typeof ctx.settings === "object" ? ctx.settings : {};
      return {
        contextIndex,
        contextCount,
        text: String(ctx.text || ""),
        tokens: Array.isArray(ctx.tokens) ? ctx.tokens : [],
        wordPositions: Array.isArray(ctx.wordPositions) ? ctx.wordPositions : [],
        matches: Array.isArray(ctx.matches) ? ctx.matches : [],
        settings,
        semanticContextResolver: typeof ctx.semanticContextResolver === "function" ? ctx.semanticContextResolver : null,
        decisionMap: new Map(),
        debugDecisionOverride: resolveDebugDecisionOverride(settings),
        fallbackPolicy: resolveFallbackPolicy(settings),
        profileId: normalizeProfileId(settings.srsProfileId),
        summary: null
      };
    }
    function groupKeyForDescriptor(descriptor) {
      return JSON.stringify([
        descriptor.pair,
        descriptor.state.profileId,
        descriptor.state.fallbackPolicy
      ]);
    }
    function addReadyDescriptor(groups, descriptor) {
      const key = groupKeyForDescriptor(descriptor);
      if (!groups.has(key)) {
        groups.set(key, {
          pair: descriptor.pair,
          profileId: descriptor.state.profileId,
          fallbackPolicy: descriptor.state.fallbackPolicy,
          descriptors: []
        });
      }
      groups.get(key).descriptors.push(descriptor);
    }
    function groupStates(group) {
      return [...new Set(group.descriptors.map((descriptor) => descriptor.state))];
    }
    function setInventorySummary(group, inventoryResolution) {
      for (const state of groupStates(group)) {
        if (inventoryResolution && inventoryResolution.source && state.summary.inventorySource === "none") {
          state.summary.inventorySource = inventoryResolution.source;
        }
        if (!state.summary.inventoryError && inventoryResolution && inventoryResolution.error) {
          state.summary.inventoryError = String(inventoryResolution.error || "");
        }
      }
    }
    function setHelperSummary(group, payload, response) {
      for (const state of groupStates(group)) {
        if (!state.summary.decisionPolicyId && payload && payload.decision_policy_id) {
          state.summary.decisionPolicyId = String(payload.decision_policy_id || "");
        }
        if (!state.summary.helperError && response && response.error) {
          state.summary.helperError = String(response.error || "");
        }
      }
    }

    function inventoryResolutionCacheKey(pair, profileId) {
      const normalizedPair = String(pair || "").trim().toLowerCase();
      const normalizedProfileId = String(profileId || "").trim() || "default";
      return normalizedPair ? `${normalizedPair}::${normalizedProfileId}` : "";
    }

    function getCachedInventoryResolution(key) {
      if (!key || !inventoryResolutionCache.has(key)) return null;
      const entry = inventoryResolutionCache.get(key);
      const expiresAt = Number(entry && entry.expiresAt || 0);
      if (Number.isFinite(expiresAt) && expiresAt > 0 && expiresAt < nowMs()) {
        inventoryResolutionCache.delete(key);
        return null;
      }
      return entry;
    }

    function shouldCacheInventoryResolution(inventoryResolution) {
      return Boolean(
        inventoryResolution
        && inventoryResolution.inventory
        && typeof inventoryResolution.inventory === "object"
      );
    }

    async function resolveInventoryForGroup(group, metricSummary) {
      const cacheKey = inventoryResolutionCacheKey(group.pair, group.profileId);
      const cached = getCachedInventoryResolution(cacheKey);
      if (cached) {
        if (cached.promise && typeof cached.promise.then === "function") {
          return cached.promise;
        }
        return cached.resolution || null;
      }
      if (!helperRulesRuntime || typeof helperRulesRuntime.resolveSemanticInventory !== "function") {
        return null;
      }
      const startedAt = nowMs();
      const pending = {
        expiresAt: startedAt + INVENTORY_RESOLUTION_CACHE_TTL_MS,
        promise: Promise.resolve(helperRulesRuntime.resolveSemanticInventory(group.pair, group.profileId))
      };
      if (cacheKey) inventoryResolutionCache.set(cacheKey, pending);
      let inventoryResolution = null;
      try {
        inventoryResolution = await pending.promise;
      } catch (error) {
        if (cacheKey && inventoryResolutionCache.get(cacheKey) === pending) {
          inventoryResolutionCache.delete(cacheKey);
        }
        throw error;
      }
      summarizeInventoryLookup(metricSummary, nowMs() - startedAt);
      if (cacheKey && shouldCacheInventoryResolution(inventoryResolution)) {
        inventoryResolutionCache.set(cacheKey, {
          expiresAt: pending.expiresAt,
          resolution: inventoryResolution
        });
      } else if (cacheKey && inventoryResolutionCache.get(cacheKey) === pending) {
        inventoryResolutionCache.delete(cacheKey);
      }
      return inventoryResolution;
    }

    function chunkDescriptors(descriptors) {
      const list = Array.isArray(descriptors) ? descriptors : [];
      const chunkSize = Math.max(1, SEMANTIC_HELPER_MAX_REQUESTS_PER_BATCH);
      const chunks = [];
      for (let index = 0; index < list.length; index += chunkSize) {
        chunks.push(list.slice(index, index + chunkSize));
      }
      return chunks;
    }

    function addFallbackDecision(descriptor, decision, reasonCodes) {
      const decisionRecord = buildDecisionRecord(
        descriptor.matchId,
        descriptor.admission,
        decision,
        "fallback_policy",
        reasonCodes
      );
      descriptor.state.decisionMap.set(descriptor.match, decisionRecord);
      summarizeDecision(descriptor.state.summary, decisionRecord, descriptor.admission);
    }

    function finalizeState(state) {
      if (!state.summary) {
        return { matches: state.matches, decisionMap: state.decisionMap, summary: null };
      }
      let debugOverrideApplied = 0;
      if (state.debugDecisionOverride) {
        for (const [match, decisionRecord] of state.decisionMap.entries()) {
          const effectiveDecisionRecord = buildEffectiveDecisionRecord(decisionRecord, state.debugDecisionOverride);
          state.decisionMap.set(match, effectiveDecisionRecord);
          if (String(effectiveDecisionRecord.effective_decision || "") !== String(decisionRecord.decision || "")) {
            debugOverrideApplied += 1;
          }
        }
      }
      finalizeSummary(state.summary, state.debugDecisionOverride, debugOverrideApplied);
      const filteredMatches = state.matches.filter((match) => {
        const decisionRecord = state.decisionMap.get(match);
        return !decisionRecord || String(decisionRecord.effective_decision || decisionRecord.decision || "") === "replace";
      });
      if (state.settings.debugEnabled && state.summary.eligible > 0) {
        log("Semantic admission summary:", {
          eligible: state.summary.eligible,
          ready: state.summary.ready,
          policyReplaces: state.summary.policyReplaces,
          policyAbstains: state.summary.policyAbstains,
          fallbackReplaces: state.summary.fallbackReplaces,
          fallbackAbstains: state.summary.fallbackAbstains,
          policyAbstainRate: state.summary.policyAbstainRate,
          overallAbstainRate: state.summary.overallAbstainRate,
          inventorySource: state.summary.inventorySource,
          inventoryError: state.summary.inventoryError,
          helperError: state.summary.helperError,
          decisionPolicyId: state.summary.decisionPolicyId,
          debugDecisionOverride: state.summary.debugDecisionOverride,
          debugOverrideApplied: state.summary.debugOverrideApplied,
          retainedMatches: filteredMatches.length
        });
      }
      return { matches: filteredMatches, decisionMap: state.decisionMap, summary: state.summary };
    }

    async function admitContextBatch(contexts) {
      const states = (Array.isArray(contexts) ? contexts : []).map((context, index, list) =>
        createState(context, index, list.length)
      );
      const readyGroups = new Map();
      for (const state of states) {
        if (!state.matches.length || !isSemanticAdmissionEnabled(state.settings)) continue;
        state.summary = createSummary(state.fallbackPolicy);
        for (let index = 0; index < state.matches.length; index += 1) {
          const match = state.matches[index];
          if (!shouldConsiderMatch(match, state.settings)) continue;
          const admission = resolveSemanticAdmission(match);
          const descriptor = {
            state,
            match,
            admission,
            matchId: state.contextCount === 1 ? `semantic:${index}` : `semantic:${state.contextIndex}:${index}`,
            pair: resolvePairForMatch(match, state.settings)
          };
          const status = String(admission && admission.status ? admission.status : "").trim();
          if (status === "ready" && descriptor.pair) {
            descriptor.requestMatch = createRequestMatch({
              descriptor,
              text: state.text,
              tokens: state.tokens,
              wordPositions: state.wordPositions,
              semanticContextResolver: state.semanticContextResolver,
              log
            });
            addReadyDescriptor(readyGroups, descriptor);
          } else {
            addFallbackDecision(
              descriptor,
              resolveFallbackDecision(state.fallbackPolicy),
              [status ? `semantic_status_${status}` : "semantic_status_missing"]
            );
          }
        }
      }

      for (const group of readyGroups.values()) {
        const metricSummary = group.descriptors[0].state.summary;
        const inventoryResolution = await resolveInventoryForGroup(group, metricSummary);
        setInventorySummary(group, inventoryResolution);
        const inventory = inventoryResolution && inventoryResolution.inventory
          && typeof inventoryResolution.inventory === "object"
          ? inventoryResolution.inventory
          : null;
        const helperUnavailable = !helperRulesRuntime || typeof helperRulesRuntime.semanticAdmitBatch !== "function";
        if (!inventory || helperUnavailable) {
          const reasonCode = !inventory
            ? (metricSummary.inventoryError ? "semantic_inventory_unavailable" : "semantic_inventory_missing")
            : "decision_service_unavailable";
          if (inventory && helperUnavailable) {
            for (const state of groupStates(group)) state.summary.helperError = "Helper semantic admission unavailable.";
          }
          for (const descriptor of group.descriptors) {
            addFallbackDecision(descriptor, resolveFallbackDecision(descriptor.state.fallbackPolicy), [reasonCode]);
          }
          continue;
        }
        for (const descriptorChunk of chunkDescriptors(group.descriptors)) {
          const requestMatches = descriptorChunk.map((descriptor) => descriptor.requestMatch);
          const helperStartedAt = nowMs();
          const response = await helperRulesRuntime.semanticAdmitBatch({
            schema_version: 1,
            pair: group.pair,
            profile_id: group.profileId,
            offset_encoding: "utf16_code_unit",
            fallback_policy: group.fallbackPolicy,
            fit_scope: SEMANTIC_HELPER_BATCH_FIT_SCOPE,
            surface_kind: "browser_page",
            matches: requestMatches
          }, SEMANTIC_HELPER_BATCH_TIMEOUT_MS);
          summarizeHelperBatch(metricSummary, requestMatches.length, nowMs() - helperStartedAt);
          const payload = response && response.response && typeof response.response === "object" ? response.response : null;
          const decisions = payload && Array.isArray(payload.decisions) ? payload.decisions : null;
          setHelperSummary({ ...group, descriptors: descriptorChunk }, payload, response);
          const decisionsById = new Map((decisions || []).filter(Boolean).map((record) => [String(record.match_id || ""), record]));
          for (const descriptor of descriptorChunk) {
            const record = decisionsById.get(descriptor.matchId);
            if (!payload || !decisions || !record) {
              const reasonCode = !payload || !decisions
                ? (metricSummary.helperError ? "decision_service_error" : "decision_response_missing")
                : "decision_record_missing";
              addFallbackDecision(
                descriptor,
                resolveFallbackDecision(descriptor.state.fallbackPolicy),
                [reasonCode]
              );
              continue;
            }
            const decisionRecord = {
              ...record,
              match_id: descriptor.matchId,
              decision: String(record.decision || ""),
              decision_source: String(record.decision_source || ""),
              reason_codes: Array.isArray(record.reason_codes)
                ? record.reason_codes.map((code) => String(code || "")).filter(Boolean)
                : []
            };
            descriptor.state.decisionMap.set(descriptor.match, decisionRecord);
            summarizeDecision(descriptor.state.summary, decisionRecord, descriptor.admission);
          }
        }
      }
      return states.map(finalizeState);
    }
    function flushQueuedAdmissions() {
      const entries = queuedAdmissions;
      queuedAdmissions = [];
      queuedFlushScheduled = false;
      admitContextBatch(entries.map((entry) => entry.context)).then((results) => {
        results.forEach((result, index) => entries[index].resolve(result));
      }).catch((error) => {
        entries.forEach((entry) => entry.reject(error));
      });
    }
    function admitMatches(context) {
      return new Promise((resolve, reject) => {
        queuedAdmissions.push({ context, resolve, reject });
        if (!queuedFlushScheduled) {
          queuedFlushScheduled = true;
          const flushMs = resolveDebugHelperBatchFlushMs(context);
          if (flushMs > 0 && typeof globalThis.setTimeout === "function") globalThis.setTimeout(flushQueuedAdmissions, flushMs);
          else Promise.resolve().then(flushQueuedAdmissions);
        }
      });
    }
    return {
      admitContextBatch,
      admitMatches
    };
  }
  root.contentSemanticGateBatch = {
    createAdmitter
  };
})();
