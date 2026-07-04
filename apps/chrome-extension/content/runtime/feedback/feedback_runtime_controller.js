(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const srsFeedback = opts.srsFeedback && typeof opts.srsFeedback === "object"
      ? opts.srsFeedback
      : null;
    const lemmatizer = opts.lemmatizer && typeof opts.lemmatizer === "object"
      ? opts.lemmatizer
      : null;
    const popupModuleHistoryStore = opts.popupModuleHistoryStore
      && typeof opts.popupModuleHistoryStore === "object"
      ? opts.popupModuleHistoryStore
      : null;
    const isPopupModuleEnabled = typeof opts.isPopupModuleEnabled === "function"
      ? opts.isPopupModuleEnabled
      : (_moduleId, _settings, _targetLanguage) => false;
    const helperFeedbackSyncModule = opts.helperFeedbackSyncModule && typeof opts.helperFeedbackSyncModule === "object"
      ? opts.helperFeedbackSyncModule
      : null;
    const getHelperClient = typeof opts.getHelperClient === "function"
      ? opts.getHelperClient
      : (() => null);
    const getCurrentSettings = typeof opts.getCurrentSettings === "function"
      ? opts.getCurrentSettings
      : (() => ({}));
    const normalizeProfileId = typeof opts.normalizeProfileId === "function"
      ? opts.normalizeProfileId
      : (value) => String(value || "").trim() || "default";
    const normalizeRuleOrigin = typeof opts.normalizeRuleOrigin === "function"
      ? opts.normalizeRuleOrigin
      : (origin) => String(origin || "").toLowerCase() === "srs" ? "srs" : "ruleset";
    const isTopFrameWindow = typeof opts.isTopFrameWindow === "function"
      ? opts.isTopFrameWindow
      : (() => true);
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const ruleOriginSrs = String(opts.ruleOriginSrs || "srs");
    const ruleOriginRuleset = String(opts.ruleOriginRuleset || "ruleset");
    const autoRefreshTimeoutMs = 60000;

    let feedbackSync = null;

    function targetLanguageFromPair(pair) {
      const normalized = String(pair || "").trim().toLowerCase();
      if (!normalized) {
        return "";
      }
      const parts = normalized.split("-", 2);
      if (parts.length < 2) {
        return "";
      }
      return String(parts[1] || "").trim().toLowerCase();
    }

    function normalizePositiveInt(value, fallback, minimum = 1) {
      const parsed = Number.parseInt(value, 10);
      if (!Number.isFinite(parsed)) {
        return Math.max(minimum, Number.parseInt(fallback, 10) || minimum);
      }
      return Math.max(minimum, parsed);
    }

    function buildAutoRefreshPayload(settings) {
      const current = settings && typeof settings === "object" ? settings : {};
      if (current.srsEnabled !== true || current.srsAutoRefreshEnabled === false) {
        return null;
      }
      const pair = String(current.srsPair || "").trim().toLowerCase();
      if (!pair || pair === "all") {
        return null;
      }
      const profileId = normalizeProfileId(current.srsProfileId);
      const profileContext = current.srsProfileContext && typeof current.srsProfileContext === "object"
        ? current.srsProfileContext
        : { pair, profile_id: profileId };
      const payload = {
        pair,
        profile_id: profileId,
        strategy: "profile_growth",
        max_active_items: normalizePositiveInt(current.srsMaxActive, 40, 1),
        auto_refresh_enabled: current.srsAutoRefreshEnabled !== false,
        auto_refresh_min_feedback_events: normalizePositiveInt(
          current.srsAutoRefreshMinFeedbackEvents,
          8,
          1
        ),
        auto_refresh_min_good_easy: normalizePositiveInt(
          current.srsAutoRefreshMinGoodEasy,
          6,
          1
        ),
        auto_refresh_repeat_min_good_easy: normalizePositiveInt(
          current.srsAutoRefreshRepeatMinGoodEasy,
          12,
          1
        ),
        auto_refresh_cooldown_minutes: normalizePositiveInt(
          current.srsAutoRefreshCooldownMinutes,
          90,
          0
        ),
        profile_context: profileContext,
        trigger: "auto_feedback_threshold"
      };
      const setTopN = Number.parseInt(current.srsBootstrapTopN, 10);
      if (Number.isFinite(setTopN)) {
        payload.set_top_n = Math.max(200, setTopN);
      }
      return payload;
    }

    async function maybeAutoRefreshAfterFeedbackFlush(meta) {
      const helperClient = getHelperClient();
      if (!helperClient || typeof helperClient.autoRefreshSrsSet !== "function") {
        return null;
      }
      const payload = buildAutoRefreshPayload(getCurrentSettings());
      if (!payload) {
        return null;
      }
      const response = await helperClient.autoRefreshSrsSet(payload, autoRefreshTimeoutMs);
      const settings = getCurrentSettings();
      if (settings && settings.debugEnabled) {
        log("SRS auto-refresh checked after feedback flush.", {
          reason: meta && meta.reason,
          handled: meta && meta.handled,
          response
        });
      }
      return response;
    }

    function ensureSync() {
      if (feedbackSync) {
        return feedbackSync;
      }
      if (!helperFeedbackSyncModule || typeof helperFeedbackSyncModule.create !== "function") {
        return null;
      }
      feedbackSync = helperFeedbackSyncModule.create({
        isFlushWorker: isTopFrameWindow(),
        sendFeedback: (payload) => {
          const helperClient = getHelperClient();
          if (helperClient && typeof helperClient.recordFeedback === "function") {
            return helperClient.recordFeedback(payload);
          }
          return Promise.resolve({
            ok: false,
            error: { code: "transport_missing", message: "Helper client unavailable." }
          });
        },
        maybeAutoRefresh: maybeAutoRefreshAfterFeedbackFlush,
        log: (...args) => {
          const settings = getCurrentSettings();
          if (settings && settings.debugEnabled) {
            log(...args);
          }
        }
      });
      feedbackSync.start();
      return feedbackSync;
    }

    function handleFeedback(payload, focusWord) {
      if (!payload || !payload.target) {
        return;
      }
      const settings = getCurrentSettings();
      const target = payload.target;
      const origin = normalizeRuleOrigin(target.dataset.origin || ruleOriginRuleset);
      if (origin !== ruleOriginSrs) {
        if (settings && settings.debugEnabled) {
          log(`Ignoring feedback for non-SRS replacement (${origin}).`);
        }
        return;
      }
      const entry = srsFeedback && typeof srsFeedback.buildEntryFromSpan === "function"
        ? srsFeedback.buildEntryFromSpan(target, payload.rating, window.location ? window.location.href : "")
        : {
            rating: payload.rating,
            lemma: String(target.dataset.replacement || target.textContent || ""),
            replacement: String(target.dataset.replacement || target.textContent || ""),
            original: String(target.dataset.original || ""),
            origin: origin,
            language_pair: target.dataset.languagePair || "",
            source_phrase: target.dataset.source || "",
            url: window.location ? window.location.href : ""
          };
      entry.profile_id = normalizeProfileId(settings.srsProfileId);
      const pair = String(entry.language_pair || settings.srsPair || "").trim().toLowerCase();
      const rawLemma = String(entry.lemma || entry.replacement || "").trim();
      const lemma = rawLemma && lemmatizer && typeof lemmatizer.lemmatize === "function"
        ? String(lemmatizer.lemmatize(rawLemma, pair) || rawLemma).trim().toLowerCase()
        : rawLemma.toLowerCase();
      const rating = String(entry.rating || payload.rating || "").trim().toLowerCase();
      const targetLanguage = targetLanguageFromPair(pair)
        || String(settings.targetLanguage || "").trim().toLowerCase();

      if (srsFeedback && typeof srsFeedback.recordFeedback === "function") {
        srsFeedback.recordFeedback(entry).then((saved) => {
          const latestSettings = getCurrentSettings();
          if (latestSettings && latestSettings.debugEnabled) {
            log("SRS feedback saved.", saved);
          }
        });
      }
      if (popupModuleHistoryStore
        && typeof popupModuleHistoryStore.recordFeedback === "function"
        && isPopupModuleEnabled("feedback-history", settings, targetLanguage)
        && pair
        && lemma
        && rating
      ) {
        popupModuleHistoryStore.recordFeedback({
          profile_id: entry.profile_id,
          language_pair: pair,
          lemma,
          replacement: String(entry.replacement || ""),
          rating,
          ts: entry.ts || new Date().toISOString(),
          word_package: entry.word_package || null
        }).catch((error) => {
          const latestSettings = getCurrentSettings();
          if (latestSettings && latestSettings.debugEnabled) {
            log("Failed to record feedback history.", error);
          }
        });
      }
      const sync = ensureSync();
      if (sync && typeof sync.enqueue === "function") {
        if (pair && pair !== "all" && lemma && rating) {
          sync.enqueue({
            pair,
            profile_id: normalizeProfileId(settings.srsProfileId),
            lemma,
            rating,
            source_type: "extension",
            ts: entry.ts || new Date().toISOString()
          }).catch((error) => {
            const latestSettings = getCurrentSettings();
            if (latestSettings && latestSettings.debugEnabled) {
              log("Failed to enqueue helper feedback.", error);
            }
          });
        }
      }
      if (settings && settings.debugEnabled) {
        log(
          `SRS feedback: ${entry.rating} for "${entry.replacement}" (${entry.language_pair || "unpaired"})`
        );
        if (focusWord && entry.replacement.toLowerCase() === focusWord) {
          log(`SRS feedback applied to focus word "${focusWord}".`);
        }
      }
    }

    function stop() {
      if (feedbackSync && typeof feedbackSync.stop === "function") {
        feedbackSync.stop();
      }
    }

    return {
      ensureSync,
      handleFeedback,
      stop
    };
  }

  root.contentFeedbackRuntimeController = {
    createController
  };
})();
