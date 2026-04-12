(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const DEFAULT_SEMANTIC_FALLBACK_POLICY = "legacy_on_unavailable";
  const FALLBACK_POLICIES = new Set([
    "legacy_on_unavailable",
    "abstain_on_unavailable",
    "soft_affordance_on_unavailable"
  ]);

  function createRuntime(options) {
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

    function isSemanticAdmissionEnabled(settings) {
      return Boolean(
        settings
        && settings.srsEnabled === true
        && settings.srsSemanticAdmissionEnabled === true
      );
    }

    function resolveFallbackPolicy(settings) {
      const normalized = String(
        settings && settings.srsSemanticAdmissionFallbackPolicy
          ? settings.srsSemanticAdmissionFallbackPolicy
          : DEFAULT_SEMANTIC_FALLBACK_POLICY
      ).trim() || DEFAULT_SEMANTIC_FALLBACK_POLICY;
      if (FALLBACK_POLICIES.has(normalized)) {
        return normalized;
      }
      return DEFAULT_SEMANTIC_FALLBACK_POLICY;
    }

    function resolveFallbackDecision(fallbackPolicy) {
      if (fallbackPolicy === "abstain_on_unavailable") {
        return "abstain";
      }
      if (fallbackPolicy === "soft_affordance_on_unavailable") {
        return "soft_affordance";
      }
      return "replace";
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
      return String(
        metadata && metadata.language_pair
          ? metadata.language_pair
          : settings && settings.srsPair
            ? settings.srsPair
            : ""
      ).trim().toLowerCase();
    }

    function shouldConsiderMatch(match, settings) {
      if (!match || !match.rule || getRuleOrigin(match.rule) !== ruleOriginSrs) {
        return false;
      }
      return Boolean(resolveSemanticAdmission(match) && isSemanticAdmissionEnabled(settings));
    }

    function buildTokenOffsets(tokens) {
      const offsets = [];
      let cursor = 0;
      for (const token of tokens || []) {
        offsets.push(cursor);
        cursor += String(token && token.text ? token.text : "").length;
      }
      return offsets;
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

    function createSummary(fallbackPolicy) {
      return {
        enabled: true,
        fallbackPolicy,
        eligible: 0,
        ready: 0,
        policyReplaces: 0,
        policyAbstains: 0,
        policySoftAffordances: 0,
        fallbackReplaces: 0,
        fallbackAbstains: 0,
        fallbackSoftAffordances: 0,
        inventorySource: "none",
        inventoryError: "",
        helperError: "",
        decisionPolicyId: ""
      };
    }

    function summarizeDecision(summary, decisionRecord, admission) {
      if (!summary || !decisionRecord) {
        return;
      }
      summary.eligible += 1;
      const status = String(admission && admission.status ? admission.status : "").trim();
      if (status === "ready") {
        summary.ready += 1;
      }
      const source = String(decisionRecord.decision_source || "");
      const decision = String(decisionRecord.decision || "");
      if (source === "policy") {
        if (decision === "replace") {
          summary.policyReplaces += 1;
        } else if (decision === "soft_affordance") {
          summary.policySoftAffordances += 1;
        } else {
          summary.policyAbstains += 1;
        }
        return;
      }
      if (decision === "replace") {
        summary.fallbackReplaces += 1;
      } else if (decision === "soft_affordance") {
        summary.fallbackSoftAffordances += 1;
      } else {
        summary.fallbackAbstains += 1;
      }
    }

    function buildRequestMatch(descriptor, text, tokens, wordPositions, tokenOffsets) {
      const startTokenIdx = Number(wordPositions[descriptor.match.startWordIndex]);
      const endTokenIdx = Number(wordPositions[descriptor.match.endWordIndex]);
      const start = Number.isFinite(startTokenIdx) ? Number(tokenOffsets[startTokenIdx] || 0) : 0;
      const endStart = Number.isFinite(endTokenIdx) ? Number(tokenOffsets[endTokenIdx] || 0) : start;
      const endToken = tokens[endTokenIdx] && typeof tokens[endTokenIdx] === "object"
        ? tokens[endTokenIdx]
        : { text: "" };
      return {
        match_id: descriptor.matchId,
        source_phrase: String(descriptor.match.rule && descriptor.match.rule.source_phrase || "").trim(),
        context_text: String(text || ""),
        match_start: start,
        match_end: endStart + String(endToken.text || "").length,
        semantic_admission: descriptor.admission,
        document_url: globalThis.location && globalThis.location.href ? globalThis.location.href : "",
        page_language: document && document.documentElement ? String(document.documentElement.lang || "") : ""
      };
    }

    async function admitMatches(context) {
      const ctx = context && typeof context === "object" ? context : {};
      const text = String(ctx.text || "");
      const tokens = Array.isArray(ctx.tokens) ? ctx.tokens : [];
      const wordPositions = Array.isArray(ctx.wordPositions) ? ctx.wordPositions : [];
      const matches = Array.isArray(ctx.matches) ? ctx.matches : [];
      const settings = ctx.settings && typeof ctx.settings === "object" ? ctx.settings : {};
      const decisionMap = new Map();

      if (!matches.length || !isSemanticAdmissionEnabled(settings)) {
        return {
          matches,
          decisionMap,
          summary: null
        };
      }

      const fallbackPolicy = resolveFallbackPolicy(settings);
      const summary = createSummary(fallbackPolicy);
      const profileId = normalizeProfileId(settings.srsProfileId);
      const tokenOffsets = buildTokenOffsets(tokens);
      const readyGroups = new Map();

      for (let index = 0; index < matches.length; index += 1) {
        const match = matches[index];
        if (!shouldConsiderMatch(match, settings)) {
          continue;
        }
        const admission = resolveSemanticAdmission(match);
        const descriptor = {
          match,
          admission,
          matchId: `semantic:${index}`,
          pair: resolvePairForMatch(match, settings)
        };
        const status = String(admission && admission.status ? admission.status : "").trim();
        if (status === "ready" && descriptor.pair) {
          descriptor.requestMatch = buildRequestMatch(
            descriptor,
            text,
            tokens,
            wordPositions,
            tokenOffsets
          );
          const key = `${descriptor.pair}::${profileId}`;
          if (!readyGroups.has(key)) {
            readyGroups.set(key, { pair: descriptor.pair, profileId, descriptors: [] });
          }
          readyGroups.get(key).descriptors.push(descriptor);
          continue;
        }
        const fallbackDecision = resolveFallbackDecision(fallbackPolicy);
        const decisionRecord = buildDecisionRecord(
          descriptor.matchId,
          descriptor.admission,
          fallbackDecision,
          "fallback_policy",
          [status ? `semantic_status_${status}` : "semantic_status_missing"]
        );
        decisionMap.set(match, decisionRecord);
        summarizeDecision(summary, decisionRecord, descriptor.admission);
      }

      for (const group of readyGroups.values()) {
        let inventoryResolution = null;
        if (helperRulesRuntime && typeof helperRulesRuntime.resolveSemanticInventory === "function") {
          inventoryResolution = await helperRulesRuntime.resolveSemanticInventory(
            group.pair,
            group.profileId
          );
        }
        const inventory = inventoryResolution && inventoryResolution.inventory
          && typeof inventoryResolution.inventory === "object"
          ? inventoryResolution.inventory
          : null;
        if (inventoryResolution && inventoryResolution.source && summary.inventorySource === "none") {
          summary.inventorySource = inventoryResolution.source;
        }
        if (!summary.inventoryError && inventoryResolution && inventoryResolution.error) {
          summary.inventoryError = String(inventoryResolution.error || "");
        }

        if (!inventory) {
          const fallbackDecision = resolveFallbackDecision(fallbackPolicy);
          const reasonCode = summary.inventoryError ? "semantic_inventory_unavailable" : "semantic_inventory_missing";
          for (const descriptor of group.descriptors) {
            const decisionRecord = buildDecisionRecord(
              descriptor.matchId,
              descriptor.admission,
              fallbackDecision,
              "fallback_policy",
              [reasonCode]
            );
            decisionMap.set(descriptor.match, decisionRecord);
            summarizeDecision(summary, decisionRecord, descriptor.admission);
          }
          continue;
        }

        if (!helperRulesRuntime || typeof helperRulesRuntime.semanticAdmitBatch !== "function") {
          const fallbackDecision = resolveFallbackDecision(fallbackPolicy);
          summary.helperError = "Helper semantic admission unavailable.";
          for (const descriptor of group.descriptors) {
            const decisionRecord = buildDecisionRecord(
              descriptor.matchId,
              descriptor.admission,
              fallbackDecision,
              "fallback_policy",
              ["decision_service_unavailable"]
            );
            decisionMap.set(descriptor.match, decisionRecord);
            summarizeDecision(summary, decisionRecord, descriptor.admission);
          }
          continue;
        }

        const response = await helperRulesRuntime.semanticAdmitBatch({
          schema_version: 1,
          pair: group.pair,
          profile_id: group.profileId,
          offset_encoding: "utf16_code_unit",
          fallback_policy: fallbackPolicy,
          surface_kind: "browser_page",
          matches: group.descriptors.map((descriptor) => descriptor.requestMatch)
        });
        const payload = response && response.response && typeof response.response === "object"
          ? response.response
          : null;
        const decisions = payload && Array.isArray(payload.decisions) ? payload.decisions : null;
        if (!summary.decisionPolicyId && payload && payload.decision_policy_id) {
          summary.decisionPolicyId = String(payload.decision_policy_id || "");
        }
        if (!summary.helperError && response && response.error) {
          summary.helperError = String(response.error || "");
        }

        if (!payload || !decisions) {
          const fallbackDecision = resolveFallbackDecision(fallbackPolicy);
          for (const descriptor of group.descriptors) {
            const decisionRecord = buildDecisionRecord(
              descriptor.matchId,
              descriptor.admission,
              fallbackDecision,
              "fallback_policy",
              [summary.helperError ? "decision_service_error" : "decision_response_missing"]
            );
            decisionMap.set(descriptor.match, decisionRecord);
            summarizeDecision(summary, decisionRecord, descriptor.admission);
          }
          continue;
        }

        const decisionsById = new Map();
        for (const decisionRecord of decisions) {
          if (!decisionRecord || typeof decisionRecord !== "object") {
            continue;
          }
          const matchId = String(decisionRecord.match_id || "").trim();
          if (!matchId) {
            continue;
          }
          decisionsById.set(matchId, {
            ...decisionRecord,
            match_id: matchId,
            decision: String(decisionRecord.decision || ""),
            decision_source: String(decisionRecord.decision_source || ""),
            reason_codes: Array.isArray(decisionRecord.reason_codes)
              ? decisionRecord.reason_codes.map((code) => String(code || "")).filter(Boolean)
              : []
          });
        }
        for (const descriptor of group.descriptors) {
          const decisionRecord = decisionsById.get(descriptor.matchId);
          if (!decisionRecord) {
            const fallbackDecision = resolveFallbackDecision(fallbackPolicy);
            const fallbackRecord = buildDecisionRecord(
              descriptor.matchId,
              descriptor.admission,
              fallbackDecision,
              "fallback_policy",
              ["decision_record_missing"]
            );
            decisionMap.set(descriptor.match, fallbackRecord);
            summarizeDecision(summary, fallbackRecord, descriptor.admission);
            continue;
          }
          decisionMap.set(descriptor.match, decisionRecord);
          summarizeDecision(summary, decisionRecord, descriptor.admission);
        }
      }

      const filteredMatches = matches.filter((match) => {
        const decisionRecord = decisionMap.get(match);
        if (!decisionRecord) {
          return true;
        }
        return String(decisionRecord.decision || "") === "replace";
      });

      if (settings.debugEnabled && summary.eligible > 0) {
        log("Semantic admission summary:", {
          eligible: summary.eligible,
          ready: summary.ready,
          policyReplaces: summary.policyReplaces,
          policyAbstains: summary.policyAbstains,
          fallbackReplaces: summary.fallbackReplaces,
          fallbackAbstains: summary.fallbackAbstains,
          inventorySource: summary.inventorySource,
          inventoryError: summary.inventoryError,
          helperError: summary.helperError,
          decisionPolicyId: summary.decisionPolicyId,
          retainedMatches: filteredMatches.length
        });
      }

      return {
        matches: filteredMatches,
        decisionMap,
        summary
      };
    }

    return {
      admitMatches
    };
  }

  root.contentSemanticGateRuntime = {
    createRuntime
  };
})();
