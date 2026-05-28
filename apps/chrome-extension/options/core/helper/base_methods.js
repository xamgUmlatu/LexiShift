(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const helperErrorCopy = root.helperErrorCopy;

  if (
    !helperErrorCopy
    || typeof helperErrorCopy.normalizeHelperErrorMessage !== "function"
    || typeof helperErrorCopy.normalizeHelperThrownErrorMessage !== "function"
  ) {
    throw new Error("[LexiShift][Options] Missing shared helper error copy.");
  }

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
      return helperErrorCopy.normalizeHelperErrorMessage(error, {
        translate: this.i18n && typeof this.i18n.t === "function"
          ? this.i18n.t.bind(this.i18n)
          : null,
        fallbackKey,
        fallbackText
      });
    };

    proto.normalizeHelperThrownErrorMessage = function normalizeHelperThrownErrorMessage(
      error,
      fallbackKey = "status_helper_failed",
      fallbackText = "Helper error."
    ) {
      return helperErrorCopy.normalizeHelperThrownErrorMessage(error, {
        translate: this.i18n && typeof this.i18n.t === "function"
          ? this.i18n.t.bind(this.i18n)
          : null,
        fallbackKey,
        fallbackText
      });
    };

    proto.getStatus = async function getStatus(profileId) {
      const client = this.getClient();
      if (!client) {
        return {
          ok: false,
          message: this.i18n.t("status_helper_missing", null, "Helper unavailable."),
          lastRun: ""
        };
      }
      try {
        const response = await client.getStatus(this.normalizeProfileId(profileId));
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

    proto.openResourceSettings = async function openResourceSettings(pair, options) {
      const client = this.getClient();
      if (!client || typeof client.openResourceSettings !== "function") {
        return this.i18n.t("status_helper_missing", null, "Helper unavailable.");
      }
      const opts = options && typeof options === "object" ? options : {};
      const payload = {
        pair: String(pair || "").trim(),
        profile_id: this.normalizeProfileId(opts.profileId),
        missing_inputs: Array.isArray(opts.missingInputs) ? opts.missingInputs : []
      };
      try {
        const response = await client.openResourceSettings(payload);
        if (!response || response.ok === false) {
          const msg = this.normalizeHelperErrorMessage(
            response && response.error,
            "status_helper_open_resource_settings_failed",
            "Failed to open LexiShift resource settings."
          );
          return this.i18n.t(
            "status_helper_open_resource_settings_failed",
            msg,
            `Open failed: ${msg}`
          );
        }
        return this.i18n.t(
          "status_helper_open_resource_settings_opened",
          null,
          "Opened LexiShift resource settings."
        );
      } catch (err) {
        this.logger("Open LexiShift resource settings failed.", err);
        const msg = this.normalizeHelperThrownErrorMessage(
          err,
          "status_helper_open_resource_settings_failed",
          "Failed to open LexiShift resource settings."
        );
        return this.i18n.t(
          "status_helper_open_resource_settings_failed",
          msg,
          `Open failed: ${msg}`
        );
      }
    };
  }

  root.installHelperBaseMethods = installHelperBaseMethods;
})();
