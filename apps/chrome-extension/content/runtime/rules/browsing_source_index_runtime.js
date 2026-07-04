(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getCurrentSettings = typeof opts.getCurrentSettings === "function"
      ? opts.getCurrentSettings
      : (() => ({}));
    const getHelperClient = typeof opts.getHelperClient === "function"
      ? opts.getHelperClient
      : (() => null);
    const helperRulesRuntime = opts.helperRulesRuntime || null;
    const normalizeProfileId = typeof opts.normalizeProfileId === "function"
      ? opts.normalizeProfileId
      : ((value) => String(value || "").trim() || "default");
    const clearSeen = typeof opts.clearSeen === "function" ? opts.clearSeen : (() => {});
    const mineBrowsingPage = typeof opts.mineBrowsingPage === "function"
      ? opts.mineBrowsingPage
      : (() => {});
    const afterRefresh = typeof opts.afterRefresh === "function" ? opts.afterRefresh : (() => {});
    const isTopFrameWindow = typeof opts.isTopFrameWindow === "function"
      ? opts.isTopFrameWindow
      : (() => true);
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    let sourceRules = [];
    let sourceIndexToken = 0;
    let refreshPending = false;

    function debugLog(settings, message, details) {
      if (settings && settings.debugEnabled) {
        log(message, details);
      }
    }

    function sourceRuleKey(rule) {
      const metadata = rule && rule.metadata && typeof rule.metadata === "object"
        ? rule.metadata
        : {};
      const wordPackage = metadata.word_package && typeof metadata.word_package === "object"
        ? metadata.word_package
        : {};
      const surface = String(wordPackage.surface || (rule && rule.replacement) || "").trim();
      const reading = String(wordPackage.reading || "").trim();
      return [
        String(rule && rule.source_phrase || "").trim().toLowerCase(),
        surface,
        reading
      ].join("|");
    }

    function sourceRulesFor(activeRules) {
      const merged = [];
      const seen = new Set();
      for (const rule of []
        .concat(Array.isArray(sourceRules) ? sourceRules : [])
        .concat(Array.isArray(activeRules) ? activeRules : [])) {
        const key = sourceRuleKey(rule);
        if (!key || seen.has(key)) {
          continue;
        }
        seen.add(key);
        merged.push(rule);
      }
      return merged;
    }

    async function refresh(reason) {
      const settings = getCurrentSettings();
      const pair = String(settings && settings.srsPair || "").trim().toLowerCase();
      const profileId = normalizeProfileId(settings && settings.srsProfileId);
      const topFrame = isTopFrameWindow();
      const helperClient = getHelperClient();
      const hasResolver = Boolean(
        helperRulesRuntime
        && typeof helperRulesRuntime.resolveBrowsingSourceIndex === "function"
      );
      const enabled = Boolean(
        settings
        && settings.srsEnabled === true
        && settings.srsBrowsingAdmissionSignalsEnabled === true
        && topFrame
        && pair
        && pair !== "all"
      );
      const token = (sourceIndexToken += 1);
      const refreshReason = reason || "browsing source index loaded";
      let shouldMineBrowsingPage = false;
      refreshPending = true;
      const refreshDetails = {
        reason: reason || "",
        pair,
        profileId,
        enabled,
        srsEnabled: Boolean(settings && settings.srsEnabled === true),
        browsingEnabled: Boolean(settings && settings.srsBrowsingAdmissionSignalsEnabled === true),
        topFrame,
        hasHelperClient: Boolean(helperClient),
        hasResolver
      };
      try {
        debugLog(settings, "Browsing source index refresh:", refreshDetails);
        if (!enabled || !helperClient || !hasResolver) {
          sourceRules = [];
          debugLog(settings, "Browsing source index unavailable:", refreshDetails);
          return { sourceRuleCount: 0, source: "none" };
        }
        const sourceIndexOptions = settings.srsBrowsingSourceIndexOptions
          && typeof settings.srsBrowsingSourceIndexOptions === "object"
          ? settings.srsBrowsingSourceIndexOptions
          : {};
        const result = await helperRulesRuntime.resolveBrowsingSourceIndex(
          pair,
          profileId,
          sourceIndexOptions
        );
        if (token !== sourceIndexToken) {
          return { sourceRuleCount: sourceRules.length, source: "stale" };
        }
        sourceRules = Array.isArray(result.rules) ? result.rules.slice() : [];
        debugLog(
          settings,
          `Browsing source index ready: ${sourceRules.length} rule(s) from ${String(result.source || "none")}.`,
          { error: result.error ? String(result.error) : "" }
        );
        debugLog(settings, "Browsing source index ready:", {
          ...refreshDetails,
          source: String(result.source || ""),
          sourceRuleCount: sourceRules.length,
          error: result.error ? String(result.error) : ""
        });
        shouldMineBrowsingPage = sourceRules.length > 0;
        return { sourceRuleCount: sourceRules.length, source: String(result.source || "") };
      } finally {
        if (token === sourceIndexToken) {
          refreshPending = false;
          if (shouldMineBrowsingPage) {
            clearSeen();
            mineBrowsingPage(refreshReason);
          }
          afterRefresh(refreshReason);
        }
      }
    }

    return {
      isRefreshPending: () => refreshPending,
      refresh,
      sourceRulesFor
    };
  }

  root.contentBrowsingSourceIndexRuntime = {
    createController
  };
})();
