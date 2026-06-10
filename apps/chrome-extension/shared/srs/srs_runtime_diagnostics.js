(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STORAGE_KEY = "srsRuntimeLastState";
  const DEBUG_ENABLED_KEY = "debugEnabled";

  function hasLocalStorageApi() {
    return Boolean(globalThis.chrome && chrome.storage && chrome.storage.local);
  }

  function sanitizeState(state) {
    if (!state || typeof state !== "object") {
      return null;
    }
    const normalizeTiming = (value) => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value))
      ? Number(value)
      : null;
    const normalizeCountMap = (value) => {
      const source = value && typeof value === "object" ? value : {};
      const result = {};
      for (const key of Object.keys(source).sort()) {
        const normalizedKey = String(key || "").trim();
        const count = Number(source[key]);
        if (!normalizedKey || !Number.isFinite(count) || count <= 0) continue;
        result[normalizedKey] = count;
      }
      return result;
    };
    return {
      ts: state.ts ? String(state.ts) : new Date().toISOString(),
      pair: state.pair ? String(state.pair) : "",
      profile_id: state.profile_id ? String(state.profile_id) : "",
      srs_enabled: state.srs_enabled === true,
      rules_source: state.rules_source ? String(state.rules_source) : "",
      rules_enabled_total: Number.isFinite(Number(state.rules_enabled_total))
        ? Number(state.rules_enabled_total)
        : 0,
      rules_local_enabled: Number.isFinite(Number(state.rules_local_enabled))
        ? Number(state.rules_local_enabled)
        : 0,
      rules_srs_enabled: Number.isFinite(Number(state.rules_srs_enabled))
        ? Number(state.rules_srs_enabled)
        : 0,
      active_rules_total: Number.isFinite(Number(state.active_rules_total))
        ? Number(state.active_rules_total)
        : 0,
      active_rules_srs: Number.isFinite(Number(state.active_rules_srs))
        ? Number(state.active_rules_srs)
        : 0,
      semantic_admission_enabled: state.semantic_admission_enabled === true,
      semantic_runtime_capability: state.semantic_runtime_capability
        ? String(state.semantic_runtime_capability)
        : "unavailable",
      semantic_runtime_reason_code: state.semantic_runtime_reason_code
        ? String(state.semantic_runtime_reason_code)
        : "no_semantic_rules",
      semantic_pointer_rule_count: Number.isFinite(Number(state.semantic_pointer_rule_count))
        ? Number(state.semantic_pointer_rule_count)
        : 0,
      semantic_ready_rule_count: Number.isFinite(Number(state.semantic_ready_rule_count))
        ? Number(state.semantic_ready_rule_count)
        : 0,
      semantic_fallback_policy: state.semantic_fallback_policy
        ? String(state.semantic_fallback_policy)
        : "legacy_on_unavailable",
      semantic_inventory_loaded: state.semantic_inventory_loaded === true,
      semantic_inventory_source: state.semantic_inventory_source
        ? String(state.semantic_inventory_source)
        : "none",
      semantic_inventory_error: state.semantic_inventory_error
        ? String(state.semantic_inventory_error)
        : "",
      semantic_matches_eligible: Number.isFinite(Number(state.semantic_matches_eligible))
        ? Number(state.semantic_matches_eligible)
        : 0,
      semantic_matches_ready: Number.isFinite(Number(state.semantic_matches_ready))
        ? Number(state.semantic_matches_ready)
        : 0,
      semantic_policy_replaces: Number.isFinite(Number(state.semantic_policy_replaces))
        ? Number(state.semantic_policy_replaces)
        : 0,
      semantic_policy_abstains: Number.isFinite(Number(state.semantic_policy_abstains))
        ? Number(state.semantic_policy_abstains)
        : 0,
      semantic_policy_soft_affordances: Number.isFinite(Number(state.semantic_policy_soft_affordances))
        ? Number(state.semantic_policy_soft_affordances)
        : 0,
      semantic_fallback_replaces: Number.isFinite(Number(state.semantic_fallback_replaces))
        ? Number(state.semantic_fallback_replaces)
        : 0,
      semantic_fallback_abstains: Number.isFinite(Number(state.semantic_fallback_abstains))
        ? Number(state.semantic_fallback_abstains)
        : 0,
      semantic_fallback_soft_affordances: Number.isFinite(
        Number(state.semantic_fallback_soft_affordances)
      )
        ? Number(state.semantic_fallback_soft_affordances)
        : 0,
      semantic_fallback_reason_counts: normalizeCountMap(state.semantic_fallback_reason_counts),
      semantic_policy_decision_total: Number.isFinite(Number(state.semantic_policy_decision_total))
        ? Number(state.semantic_policy_decision_total)
        : 0,
      semantic_fallback_decision_total: Number.isFinite(Number(state.semantic_fallback_decision_total))
        ? Number(state.semantic_fallback_decision_total)
        : 0,
      semantic_overall_decision_total: Number.isFinite(Number(state.semantic_overall_decision_total))
        ? Number(state.semantic_overall_decision_total)
        : 0,
      semantic_policy_abstain_rate: normalizeTiming(state.semantic_policy_abstain_rate),
      semantic_fallback_abstain_rate: normalizeTiming(state.semantic_fallback_abstain_rate),
      semantic_overall_abstain_rate: normalizeTiming(state.semantic_overall_abstain_rate),
      semantic_decision_policy_id: state.semantic_decision_policy_id
        ? String(state.semantic_decision_policy_id)
        : "",
      semantic_debug_decision_override: state.semantic_debug_decision_override
        ? String(state.semantic_debug_decision_override)
        : "",
      semantic_debug_override_applied: Number.isFinite(Number(state.semantic_debug_override_applied))
        ? Number(state.semantic_debug_override_applied)
        : 0,
      semantic_inventory_lookup_calls: Number.isFinite(Number(state.semantic_inventory_lookup_calls))
        ? Number(state.semantic_inventory_lookup_calls)
        : 0,
      semantic_inventory_lookup_latency_ms_total: normalizeTiming(
        state.semantic_inventory_lookup_latency_ms_total
      ),
      semantic_inventory_lookup_latency_ms_max: normalizeTiming(state.semantic_inventory_lookup_latency_ms_max),
      semantic_inventory_lookup_latency_ms_avg: normalizeTiming(state.semantic_inventory_lookup_latency_ms_avg),
      semantic_helper_batch_calls: Number.isFinite(Number(state.semantic_helper_batch_calls))
        ? Number(state.semantic_helper_batch_calls)
        : 0,
      semantic_helper_request_count: Number.isFinite(Number(state.semantic_helper_request_count))
        ? Number(state.semantic_helper_request_count)
        : 0,
      semantic_helper_batch_min_size: normalizeTiming(state.semantic_helper_batch_min_size),
      semantic_helper_batch_max_size: Number.isFinite(Number(state.semantic_helper_batch_max_size))
        ? Number(state.semantic_helper_batch_max_size)
        : 0,
      semantic_helper_batch_avg_size: normalizeTiming(state.semantic_helper_batch_avg_size),
      semantic_helper_latency_ms_total: normalizeTiming(state.semantic_helper_latency_ms_total),
      semantic_helper_latency_ms_max: normalizeTiming(state.semantic_helper_latency_ms_max),
      semantic_helper_latency_ms_avg: normalizeTiming(state.semantic_helper_latency_ms_avg),
      semantic_scan_node_batch_calls: Number.isFinite(Number(state.semantic_scan_node_batch_calls))
        ? Number(state.semantic_scan_node_batch_calls)
        : 0,
      semantic_scan_node_count: Number.isFinite(Number(state.semantic_scan_node_count))
        ? Number(state.semantic_scan_node_count)
        : 0,
      semantic_scan_node_batch_min_size: normalizeTiming(state.semantic_scan_node_batch_min_size),
      semantic_scan_node_batch_max_size: Number.isFinite(Number(state.semantic_scan_node_batch_max_size))
        ? Number(state.semantic_scan_node_batch_max_size)
        : 0,
      semantic_scan_node_batch_avg_size: normalizeTiming(state.semantic_scan_node_batch_avg_size),
      semantic_scan_node_concurrent_batches: Number.isFinite(
        Number(state.semantic_scan_node_concurrent_batches)
      )
        ? Number(state.semantic_scan_node_concurrent_batches)
        : 0,
      semantic_scan_node_serial_batches: Number.isFinite(Number(state.semantic_scan_node_serial_batches))
        ? Number(state.semantic_scan_node_serial_batches)
        : 0,
      semantic_scan_node_serial_budget_batches: Number.isFinite(
        Number(state.semantic_scan_node_serial_budget_batches)
      )
        ? Number(state.semantic_scan_node_serial_budget_batches)
        : 0,
      semantic_context_cache_container_builds: Number.isFinite(
        Number(state.semantic_context_cache_container_builds)
      )
        ? Number(state.semantic_context_cache_container_builds)
        : 0,
      semantic_context_cache_record_reuses: Number.isFinite(Number(state.semantic_context_cache_record_reuses))
        ? Number(state.semantic_context_cache_record_reuses)
        : 0,
      semantic_context_cache_usable_reuses: Number.isFinite(Number(state.semantic_context_cache_usable_reuses))
        ? Number(state.semantic_context_cache_usable_reuses)
        : 0,
      semantic_context_cache_bypasses: Number.isFinite(Number(state.semantic_context_cache_bypasses))
        ? Number(state.semantic_context_cache_bypasses)
        : 0,
      apply_total_ms: normalizeTiming(state.apply_total_ms),
      active_rules_resolve_ms: normalizeTiming(state.active_rules_resolve_ms),
      helper_rules_resolve_ms: normalizeTiming(state.helper_rules_resolve_ms),
      srs_gate_ms: normalizeTiming(state.srs_gate_ms),
      semantic_inventory_resolve_ms: normalizeTiming(state.semantic_inventory_resolve_ms),
      runtime_apply_ms: normalizeTiming(state.runtime_apply_ms),
      scan_ms: normalizeTiming(state.scan_ms),
      first_replacement_latency_ms: normalizeTiming(state.first_replacement_latency_ms),
      first_visible_replacement_latency_ms: normalizeTiming(state.first_visible_replacement_latency_ms),
      srs_stats: state.srs_stats && typeof state.srs_stats === "object"
        ? state.srs_stats
        : null,
      helper_rules_error: state.helper_rules_error ? String(state.helper_rules_error) : "",
      page_url: state.page_url ? String(state.page_url) : "",
      frame_type: state.frame_type ? String(state.frame_type) : ""
    };
  }

  function saveLastState(state) {
    return new Promise((resolve) => {
      const payload = sanitizeState(state);
      if (!payload || !hasLocalStorageApi()) {
        resolve(null);
        return;
      }
      chrome.storage.local.set({ [STORAGE_KEY]: payload }, () => resolve(payload));
    });
  }

  function loadLastState() {
    return new Promise((resolve) => {
      if (!hasLocalStorageApi()) {
        resolve(null);
        return;
      }
      chrome.storage.local.get({ [DEBUG_ENABLED_KEY]: false, [STORAGE_KEY]: null }, (items) => {
        if (items[DEBUG_ENABLED_KEY] !== true) {
          resolve(null);
          return;
        }
        resolve(sanitizeState(items[STORAGE_KEY]));
      });
    });
  }

  function clearLastState() {
    return new Promise((resolve) => {
      if (!hasLocalStorageApi() || typeof chrome.storage.local.remove !== "function") {
        resolve();
        return;
      }
      chrome.storage.local.remove(STORAGE_KEY, () => resolve());
    });
  }

  root.srsRuntimeDiagnostics = {
    storageKey: STORAGE_KEY,
    saveLastState,
    loadLastState,
    clearLastState
  };
})();
