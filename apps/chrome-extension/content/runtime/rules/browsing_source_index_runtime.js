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
    const log = typeof opts.log === "function" ? opts.log : (() => {});

    let sourceRules = [];
    let sourceIndexToken = 0;

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
      const enabled = Boolean(
        settings
        && settings.srsBrowsingAdmissionSignalsEnabled === true
        && pair
        && pair !== "all"
      );
      const token = (sourceIndexToken += 1);
      if (
        !enabled
        || !getHelperClient()
        || !helperRulesRuntime
        || typeof helperRulesRuntime.resolveBrowsingSourceIndex !== "function"
      ) {
        sourceRules = [];
        return;
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
        return;
      }
      sourceRules = Array.isArray(result.rules) ? result.rules.slice() : [];
      if (settings.debugEnabled && result.error) {
        log("Browsing source index load issue.", result.error);
      }
      if (sourceRules.length) {
        clearSeen();
        mineBrowsingPage(reason || "browsing source index loaded");
      }
    }

    return {
      refresh,
      sourceRulesFor
    };
  }

  root.contentBrowsingSourceIndexRuntime = {
    createController
  };
})();
