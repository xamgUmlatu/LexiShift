class HelperManager {
  constructor(i18n, logger) {
    this.i18n = i18n;
    this.logger = logger || console.log;
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

  async runRulegenPreview(pair) {
    const client = this.getClient();
    if (!client) throw new Error(this.i18n.t("status_helper_missing", null, "Helper unavailable."));

    const startedAt = Date.now();
    const rulegenResponse = await client.triggerRulegen({
      pair: pair,
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

    // Fetch snapshot
    const response = await client.getSnapshot(pair);
    let snapshot = null;
    const helperCache = globalThis.LexiShift && globalThis.LexiShift.helperCache;

    if (response && response.ok !== false) {
      snapshot = response.data || {};
      if (helperCache && typeof helperCache.saveSnapshot === "function") {
        helperCache.saveSnapshot(pair, snapshot);
      }
    } else if (helperCache && typeof helperCache.loadSnapshot === "function") {
      snapshot = await helperCache.loadSnapshot(pair);
    }

    if (!snapshot) throw new Error(this.i18n.t("status_srs_rulegen_failed", null, "Rule preview failed."));
    return { rulegenData, snapshot, duration };
  }
}