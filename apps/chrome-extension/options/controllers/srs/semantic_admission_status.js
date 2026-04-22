(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createSupport(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const statusOutput = opts.statusOutput || null;
    const detailOutput = opts.detailOutput || null;
    const DISPLAY = {
      checking: [
        "status_srs_semantic_capability_checking",
        "Checking…",
        "hint_srs_semantic_capability_checking",
        "Checking semantic admission status…"
      ],
      active: [
        "status_srs_semantic_capability_active",
        "Automatic",
        "hint_srs_semantic_capability_active",
        "Helper-side sentence veto runs automatically for this pair/profile."
      ],
      published_unready: [
        "status_srs_semantic_capability_published_unready",
        "Not yet available",
        "hint_srs_semantic_capability_published_unready",
        "Semantic metadata is published, but this pair/profile has no ready coverage yet. LexiShift currently uses standard SRS replacements."
      ],
      unavailable: [
        "status_srs_semantic_capability_unavailable",
        "Unavailable",
        "hint_srs_semantic_capability_unavailable",
        "This pair/profile does not currently publish semantic admission coverage. LexiShift currently uses standard SRS replacements."
      ],
      error: [
        "status_srs_semantic_capability_error",
        "Needs repair",
        "hint_srs_semantic_capability_error",
        "Semantic admission data is present but inconsistent or unreadable. LexiShift currently uses standard SRS replacements until it is repaired."
      ],
      unknown: [
        "status_srs_semantic_capability_unknown",
        "Status unavailable",
        "hint_srs_semantic_capability_unknown",
        "Semantic admission status could not be checked right now."
      ]
    };

    function render(capability) {
      const key = Object.prototype.hasOwnProperty.call(DISPLAY, capability) ? capability : "unknown";
      const [statusKey, statusFallback, hintKey, hintFallback] = DISPLAY[key];
      if (statusOutput) {
        statusOutput.textContent = translate(statusKey, null, statusFallback);
      }
      if (detailOutput) {
        detailOutput.textContent = translate(hintKey, null, hintFallback);
      }
      return key;
    }

    function resolveCapability(diagnostics) {
      const payload = diagnostics && typeof diagnostics === "object" ? diagnostics : {};
      const helperData = payload.helper && typeof payload.helper === "object" ? payload.helper : null;
      const runtimeState = payload.runtime_state && typeof payload.runtime_state === "object"
        ? payload.runtime_state
        : null;
      return (
        (helperData && typeof helperData.semantic_runtime_capability === "string"
          ? helperData.semantic_runtime_capability
          : "")
        || (runtimeState && typeof runtimeState.semantic_runtime_capability === "string"
          ? runtimeState.semantic_runtime_capability
          : "")
        || "unknown"
      );
    }

    async function refresh(pairKey, profileId) {
      if (!statusOutput && !detailOutput) {
        return "unknown";
      }
      render("checking");
      if (!helperManager || typeof helperManager.getSrsRuntimeDiagnostics !== "function") {
        return render("unknown");
      }
      try {
        const diagnostics = await helperManager.getSrsRuntimeDiagnostics(pairKey, { profileId });
        return render(resolveCapability(diagnostics));
      } catch (_err) {
        return render("unknown");
      }
    }

    return {
      render,
      refresh
    };
  }

  root.optionsSrsSemanticAdmissionStatus = {
    createSupport
  };
})();
