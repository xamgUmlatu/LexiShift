(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const DEFAULT_TIMEOUT_MS = 4000;

  class HelperClient {
    constructor(transport) {
      this._transport = transport;
    }

    async send(type, payload = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
      if (!this._transport || typeof this._transport.send !== "function") {
        return { ok: false, error: { code: "transport_missing", message: "No helper transport configured." } };
      }
      return this._transport.send(type, payload, timeoutMs);
    }

    hello() {
      return this.send("hello");
    }

    getStatus() {
      return this.send("status");
    }

    getSnapshot(pair, profileId) {
      return this.send("get_snapshot", { pair, profile_id: profileId });
    }

    getRuleset(pair, profileId) {
      return this.send("get_ruleset", { pair, profile_id: profileId });
    }

    getSrsDiagnostics(pair, profileId) {
      return this.send("srs_diagnostics", { pair, profile_id: profileId });
    }

    getProfiles() {
      return this.send("profiles_get");
    }

    openDataDir() {
      return this.send("open_data_dir");
    }

    recordFeedback(payload) {
      return this.send("record_feedback", payload);
    }

    recordExposure(payload) {
      return this.send("record_exposure", payload);
    }

    triggerRulegen(payload, timeoutMs) {
      return this.send("trigger_rulegen", payload, timeoutMs);
    }

    initializeSrs(payload, timeoutMs) {
      return this.send("srs_initialize", payload, timeoutMs);
    }

    planSrsSet(payload, timeoutMs) {
      return this.send("srs_plan_set", payload, timeoutMs);
    }

    refreshSrsSet(payload, timeoutMs) {
      return this.send("srs_refresh", payload, timeoutMs);
    }

    resetSrs(payload) {
      return this.send("srs_reset", payload);
    }
  }

  root.helperClient = HelperClient;
})();
