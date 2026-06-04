(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function resolveTranslate(translate) {
    return typeof translate === "function"
      ? translate
      : ((_key, _subs, fallback) => fallback || "");
  }

  function normalizeHelperErrorMessage(error, options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = resolveTranslate(opts.translate);
    const fallbackKey = String(opts.fallbackKey || "status_helper_failed");
    const fallbackText = String(opts.fallbackText || "Helper error.");
    const fallback = translate(fallbackKey, null, fallbackText);

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
      || lowerMessage.includes("native messaging not available")
      || lowerMessage.includes("helper bridge unavailable")
      || lowerMessage.includes("could not establish connection")
      || lowerMessage.includes("receiving end does not exist")
    ) {
      return translate("status_helper_missing", null, "Helper unavailable.");
    }

    if (
      code === "timeout"
      || lowerMessage.includes("timed out")
      || lowerMessage.includes("did not respond in time")
    ) {
      return translate(
        "status_helper_timeout",
        null,
        "The helper did not respond in time."
      );
    }

    if (
      code === "native_host_exited"
      || lowerMessage.includes("native host has exited")
      || lowerMessage.includes("helper exited unexpectedly")
    ) {
      return translate(
        "status_helper_native_host_exited",
        null,
        "The helper exited unexpectedly."
      );
    }

    if (
      code === "native_forbidden"
      || lowerMessage.includes("access to the specified native messaging host is forbidden")
      || lowerMessage.includes("native messaging access is blocked")
    ) {
      return translate(
        "status_helper_native_messaging_forbidden",
        null,
        "The browser blocked access to the helper."
      );
    }

    if (
      code === "native_error"
      || code === "bridge_error"
      || code === "native_exception"
      || lowerMessage.includes("error when communicating with the native messaging host")
      || lowerMessage.includes("could not communicate with the helper")
    ) {
      return translate(
        "status_helper_native_messaging_failed",
        null,
        "Could not communicate with the helper."
      );
    }

    return rawMessage || fallback;
  }

  function normalizeHelperThrownErrorMessage(error, options) {
    if (error && typeof error === "object") {
      return normalizeHelperErrorMessage(
        {
          code: error.code || "",
          message: error.message || String(error)
        },
        options
      );
    }
    return normalizeHelperErrorMessage(
      {
        code: "",
        message: String(error || "")
      },
      options
    );
  }

  root.helperErrorCopy = {
    normalizeHelperErrorMessage,
    normalizeHelperThrownErrorMessage
  };
})();
