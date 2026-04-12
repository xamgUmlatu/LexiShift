(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STORAGE_KEY = "srsRuntimeLastState";

  function hasLocalStorageApi() {
    return Boolean(globalThis.chrome && chrome.storage && chrome.storage.local);
  }

  function sanitizeState(state) {
    if (!state || typeof state !== "object") {
      return null;
    }
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
      semantic_fallback_replaces: Number.isFinite(Number(state.semantic_fallback_replaces))
        ? Number(state.semantic_fallback_replaces)
        : 0,
      semantic_fallback_abstains: Number.isFinite(Number(state.semantic_fallback_abstains))
        ? Number(state.semantic_fallback_abstains)
        : 0,
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
      chrome.storage.local.get({ [STORAGE_KEY]: null }, (items) => {
        resolve(sanitizeState(items[STORAGE_KEY]));
      });
    });
  }

  root.srsRuntimeDiagnostics = {
    storageKey: STORAGE_KEY,
    saveLastState,
    loadLastState
  };
})();
