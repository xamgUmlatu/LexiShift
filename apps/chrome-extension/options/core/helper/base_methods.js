(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function installHelperBaseMethods(proto) {
    if (!proto || typeof proto !== "object") {
      return;
    }

    proto.normalizeProfileId = function normalizeProfileId(profileId) {
      const normalized = String(profileId || "").trim();
      return normalized || "default";
    };

    proto.normalizeSrsSizing = function normalizeSrsSizing(sizingOrTopN, options) {
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
    };

    proto.getClient = function getClient() {
      const transport = globalThis.LexiShift && globalThis.LexiShift.helperTransportExtension;
      const Client = globalThis.LexiShift && globalThis.LexiShift.helperClient;
      if (!Client || !transport) return null;
      return new Client(transport);
    };

    proto.normalizeHelperErrorMessage = function normalizeHelperErrorMessage(
      error,
      fallbackKey = "status_helper_failed",
      fallbackText = "Helper error."
    ) {
      const fallback = this.i18n.t(fallbackKey, null, fallbackText);
      if (!error || typeof error !== "object") {
        return fallback;
      }
      const code = String(error.code || "").trim().toLowerCase();
      const rawMessage = String(error.message || "").trim();
      const lowerMessage = rawMessage.toLowerCase();

      if (
        code === "helper_missing"
        || code === "transport_missing"
        || code === "bridge_unavailable"
        || code === "native_unavailable"
        || lowerMessage.includes("specified native messaging host not found")
        || lowerMessage.includes("no such native application")
      ) {
        return this.i18n.t("status_helper_missing", null, "Helper unavailable.");
      }
      if (code === "timeout" || lowerMessage.includes("timed out")) {
        return this.i18n.t(
          "status_helper_timeout",
          null,
          "The helper did not respond in time."
        );
      }
      if (
        code === "native_host_exited"
        || lowerMessage.includes("native host has exited")
      ) {
        return this.i18n.t(
          "status_helper_native_host_exited",
          null,
          "The helper exited unexpectedly."
        );
      }
      if (
        code === "native_forbidden"
        || lowerMessage.includes("access to the specified native messaging host is forbidden")
      ) {
        return this.i18n.t(
          "status_helper_native_messaging_forbidden",
          null,
          "The browser blocked access to the helper."
        );
      }
      if (
        lowerMessage.includes("error when communicating with the native messaging host")
        || code === "native_error"
        || code === "bridge_error"
        || code === "native_exception"
      ) {
        return this.i18n.t(
          "status_helper_native_messaging_failed",
          null,
          "Could not communicate with the helper."
        );
      }
      return rawMessage || fallback;
    };

    proto.normalizeHelperThrownErrorMessage = function normalizeHelperThrownErrorMessage(
      error,
      fallbackKey = "status_helper_failed",
      fallbackText = "Helper error."
    ) {
      if (error && typeof error === "object") {
        return this.normalizeHelperErrorMessage(
          {
            code: error.code || "",
            message: error.message || String(error)
          },
          fallbackKey,
          fallbackText
        );
      }
      return this.normalizeHelperErrorMessage(
        { code: "", message: String(error || "") },
        fallbackKey,
        fallbackText
      );
    };

    proto.getStatus = async function getStatus() {
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
          const msg = this.normalizeHelperErrorMessage(
            response && response.error,
            "status_helper_failed",
            "Helper error."
          );
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
          message: this.normalizeHelperThrownErrorMessage(
            err,
            "status_helper_failed",
            "Helper error."
          ),
          lastRun: ""
        };
      }
    };

    proto.getProfiles = async function getProfiles() {
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
              message: this.normalizeHelperErrorMessage(
                response && response.error,
                "status_helper_failed",
                "Helper error."
              )
            }
          };
        }
        return { ok: true, data: response.data || null, error: null };
      } catch (err) {
        return {
          ok: false,
          data: null,
          error: {
            code: (err && err.code) || "helper_error",
            message: this.normalizeHelperThrownErrorMessage(
              err,
              "status_helper_failed",
              "Helper error."
            )
          }
        };
      }
    };

    proto.getProfileRulesets = async function getProfileRulesets(profileId) {
      const client = this.getClient();
      if (!client || typeof client.getProfileRulesets !== "function") {
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
        const response = await client.getProfileRulesets(this.normalizeProfileId(profileId));
        if (!response || response.ok === false) {
          return {
            ok: false,
            data: null,
            error: {
              code: (response && response.error && response.error.code) || "helper_error",
              message: this.normalizeHelperErrorMessage(
                response && response.error,
                "status_helper_failed",
                "Helper error."
              )
            }
          };
        }
        return { ok: true, data: response.data || null, error: null };
      } catch (err) {
        return {
          ok: false,
          data: null,
          error: {
            code: (err && err.code) || "helper_error",
            message: this.normalizeHelperThrownErrorMessage(
              err,
              "status_helper_failed",
              "Helper error."
            )
          }
        };
      }
    };

    proto.testConnection = async function testConnection() {
      const client = this.getClient();
      if (!client) return this.i18n.t("status_helper_missing", null, "Helper unavailable.");
      try {
        const response = await client.hello();
        if (!response || response.ok === false) {
          const msg = this.normalizeHelperErrorMessage(
            response && response.error,
            "status_helper_failed",
            "Helper error."
          );
          return this.i18n.t("status_helper_test_failed", msg, `Connection failed: ${msg}`);
        }
        const version = (response.data && response.data.helper_version) || "";
        return this.i18n.t("status_helper_test_ok", version, version ? `Helper connected (v${version}).` : "Helper connected.");
      } catch (err) {
        this.logger("Helper test failed.", err);
        const msg = this.normalizeHelperThrownErrorMessage(
          err,
          "status_helper_failed",
          "Helper error."
        );
        return this.i18n.t("status_helper_test_failed", msg, `Connection failed: ${msg}`);
      }
    };

    proto.openDataDir = async function openDataDir() {
      const client = this.getClient();
      if (!client) return this.i18n.t("status_helper_missing", null, "Helper unavailable.");
      try {
        const response = await client.openDataDir();
        if (!response || response.ok === false) {
          const msg = this.normalizeHelperErrorMessage(
            response && response.error,
            "status_helper_open_failed",
            "Failed to open folder."
          );
          return this.i18n.t("status_helper_open_failed", msg, `Open failed: ${msg}`);
        }
        const opened = response.data && response.data.opened ? response.data.opened : "";
        return this.i18n.t("status_helper_opened", opened, opened ? `Opened: ${opened}` : "Opened.");
      } catch (err) {
        this.logger("Open helper data dir failed.", err);
        const msg = this.normalizeHelperThrownErrorMessage(
          err,
          "status_helper_open_failed",
          "Failed to open folder."
        );
        return this.i18n.t("status_helper_open_failed", msg, `Open failed: ${msg}`);
      }
    };
  }

  root.installHelperBaseMethods = installHelperBaseMethods;
})();
