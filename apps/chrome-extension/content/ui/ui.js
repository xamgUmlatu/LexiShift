(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STYLE_ID = "lexishift-style";
  let clickListenerAttached = false;
  const scriptModule = root.uiJapaneseScriptModule && typeof root.uiJapaneseScriptModule === "object"
    ? root.uiJapaneseScriptModule
    : null;
  const quickDefinitionModule = root.uiQuickDefinitionModule && typeof root.uiQuickDefinitionModule === "object"
    ? root.uiQuickDefinitionModule
    : null;
  const popupLayoutStyles = typeof root.uiPopupLayoutStyles?.styles === "string"
    ? root.uiPopupLayoutStyles.styles
    : "";
  const dictionaryDisclosureStyles = typeof root.uiQuickDefinitionDictionarySections?.styles === "string"
    ? root.uiQuickDefinitionDictionarySections.styles
    : "";
  const feedbackHistoryModule = root.uiFeedbackHistoryModule && typeof root.uiFeedbackHistoryModule === "object"
    ? root.uiFeedbackHistoryModule
    : null;
  const encounterHistoryModule = root.uiEncounterHistoryModule && typeof root.uiEncounterHistoryModule === "object"
    ? root.uiEncounterHistoryModule
    : null;
  const popupModulesRegistry = root.popupModulesRegistry && typeof root.popupModulesRegistry === "object"
    ? root.popupModulesRegistry
    : null;
  const popupHelpers = root.uiPopupHelpers && typeof root.uiPopupHelpers === "object"
    ? root.uiPopupHelpers
    : {};
  const popupLocaleHelpers = root.uiPopupLocaleHelpers && typeof root.uiPopupLocaleHelpers === "object"
    ? root.uiPopupLocaleHelpers
    : {};
  const normalizeLanguage = typeof popupHelpers.normalizeLanguage === "function"
    ? popupHelpers.normalizeLanguage
    : (value) => String(value || "").trim().toLowerCase();
  const createLocaleManager = typeof popupLocaleHelpers.createLocaleManager === "function"
    ? popupLocaleHelpers.createLocaleManager
    : null;
  const createThemeManager = typeof popupHelpers.createThemeManager === "function"
    ? popupHelpers.createThemeManager
    : null;
  const resolveRuntimePopupModuleOrderHelper = typeof popupHelpers.resolveRuntimePopupModuleOrder === "function"
    ? popupHelpers.resolveRuntimePopupModuleOrder
    : null;
  const popupHistoryStore = root.popupModuleHistoryStore && typeof root.popupModuleHistoryStore === "object"
    ? root.popupModuleHistoryStore
    : null;
  const wordInfoApi = root.wordInfoApi && typeof root.wordInfoApi === "object"
    ? root.wordInfoApi
    : null;
  const lemmatize = root.lemmatizer && typeof root.lemmatizer.lemmatize === "function"
    ? root.lemmatizer.lemmatize
    : null;
  const popupModuleRegistryFactory = root.uiPopupModuleRegistry
    && typeof root.uiPopupModuleRegistry.createRegistry === "function"
    ? root.uiPopupModuleRegistry.createRegistry
    : null;
  const RUNTIME_THEME_MODULE_ID_MAP = Object.freeze({
    "quick-definition": "quick-definition",
    "japanese-script": "ja-script-forms",
    "feedback-history": "feedback-history",
    "encounter-history": "encounter-history"
  });
  const PREF_TO_RUNTIME_MODULE_ID_MAP = Object.freeze({
    "quick-definition": "quick-definition",
    "ja-script-forms": "japanese-script",
    "feedback-history": "feedback-history",
    "encounter-history": "encounter-history"
  });
  const DEFAULT_RUNTIME_MODULE_ORDER = Object.freeze([
    "quick-definition",
    "japanese-script",
    "feedback-history",
    "encounter-history"
  ]);
  const POPUP_UI_SUPPORTED_LOCALES = Object.freeze(["en", "ja", "zh", "de"]);
  let activePopupModulePrefs = { byId: {}, order: [] };
  let activePopupProfileId = "default";
  let activeTargetLanguage = "en";
  const popupLocaleManager = createLocaleManager
    ? createLocaleManager({
        supportedLocales: POPUP_UI_SUPPORTED_LOCALES,
        initialUiLanguage: "system"
      })
    : {
        t: (key, _substitutions, fallback) => String(fallback || key || ""),
        setPopupUiLanguage: () => {},
        resolveActivePopupLocale: () => "en",
        getActiveUiLanguage: () => "system"
      };

  function resolveActivePopupLocale() {
    return popupLocaleManager.resolveActivePopupLocale();
  }

  function t(key, substitutions, fallback) {
    return popupLocaleManager.t(key, substitutions, fallback);
  }

  function setPopupUiLanguage(uiLanguageSetting) {
    popupLocaleManager.setPopupUiLanguage(uiLanguageSetting);
  }

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

  function resolveTargetLanguage(target) {
    const pair = target && target.dataset ? String(target.dataset.languagePair || "") : "";
    return targetLanguageFromPair(pair) || activeTargetLanguage || "en";
  }

  const popupThemeManager = createThemeManager
    ? createThemeManager({
        popupModulesRegistry,
        getActivePopupModulePrefs: () => activePopupModulePrefs,
        runtimeThemeModuleIdMap: RUNTIME_THEME_MODULE_ID_MAP
      })
    : {
        applyPopupModuleTheme: () => {},
        clearPopupModuleTheme: () => {}
      };

  function applyPopupModuleTheme(runtimeModuleId, node) {
    popupThemeManager.applyPopupModuleTheme(runtimeModuleId, node);
  }

  function isPopupModuleEnabled(moduleId, targetLanguage) {
    if (!popupModulesRegistry || typeof popupModulesRegistry.isEnabledForTarget !== "function") {
      return false;
    }
    return popupModulesRegistry.isEnabledForTarget(
      activePopupModulePrefs,
      moduleId,
      normalizeLanguage(targetLanguage)
    );
  }

  function historyModuleContext() {
    return {
      historyStore: popupHistoryStore,
      profileId: activePopupProfileId,
      lemmatize,
      t,
      locale: resolveActivePopupLocale()
    };
  }

  function wordInfoModuleContext() {
    return {
      profileId: activePopupProfileId,
      t,
      locale: resolveActivePopupLocale(),
      wordInfo: wordInfoApi,
      wordInfoApi
    };
  }

  const popupModuleDescriptorsById = {
    "quick-definition": {
      id: "quick-definition",
      build: (target, debugLog) => {
        if (!quickDefinitionModule || typeof quickDefinitionModule.build !== "function") {
          return null;
        }
        const targetLanguage = resolveTargetLanguage(target);
        if (!isPopupModuleEnabled("quick-definition", targetLanguage)) {
          return null;
        }
        return quickDefinitionModule.build(target, debugLog, wordInfoModuleContext());
      }
    },
    "japanese-script": {
      id: "japanese-script",
      build: (target, debugLog) => {
        if (!scriptModule || typeof scriptModule.build !== "function") {
          return null;
        }
        const targetLanguage = resolveTargetLanguage(target);
        if (!isPopupModuleEnabled("ja-script-forms", targetLanguage)) {
          return null;
        }
        return scriptModule.build(target, debugLog, {
          t,
          locale: resolveActivePopupLocale()
        });
      }
    },
    "feedback-history": {
      id: "feedback-history",
      build: (target, debugLog) => {
        if (!feedbackHistoryModule || typeof feedbackHistoryModule.build !== "function") {
          return null;
        }
        const targetLanguage = resolveTargetLanguage(target);
        if (!isPopupModuleEnabled("feedback-history", targetLanguage)) {
          return null;
        }
        return feedbackHistoryModule.build(target, debugLog, historyModuleContext());
      }
    },
    "encounter-history": {
      id: "encounter-history",
      build: (target, debugLog) => {
        if (!encounterHistoryModule || typeof encounterHistoryModule.build !== "function") {
          return null;
        }
        const targetLanguage = resolveTargetLanguage(target);
        if (!isPopupModuleEnabled("encounter-history", targetLanguage)) {
          return null;
        }
        return encounterHistoryModule.build(target, debugLog, historyModuleContext());
      }
    }
  };

  function resolveRuntimePopupModuleOrder() {
    const configuredOrder = activePopupModulePrefs
      && typeof activePopupModulePrefs === "object"
      && Array.isArray(activePopupModulePrefs.order)
      ? activePopupModulePrefs.order
      : [];
    if (resolveRuntimePopupModuleOrderHelper) {
      return resolveRuntimePopupModuleOrderHelper({
        configuredOrder,
        prefToRuntimeModuleIdMap: PREF_TO_RUNTIME_MODULE_ID_MAP,
        defaultRuntimeModuleOrder: DEFAULT_RUNTIME_MODULE_ORDER,
        descriptorsById: popupModuleDescriptorsById
      });
    }
    return DEFAULT_RUNTIME_MODULE_ORDER.filter((runtimeModuleId) => popupModuleDescriptorsById[runtimeModuleId]);
  }

  function resolvePopupModuleDescriptors() {
    return resolveRuntimePopupModuleOrder()
      .map((runtimeModuleId) => popupModuleDescriptorsById[runtimeModuleId])
      .filter((descriptor) => descriptor && typeof descriptor === "object");
  }

  const popupModuleRegistry = popupModuleRegistryFactory
    ? popupModuleRegistryFactory({
        resolveModules: resolvePopupModuleDescriptors
      })
    : null;
  const feedbackPopupFactory = root.uiFeedbackPopupController
    && typeof root.uiFeedbackPopupController.createController === "function"
    ? root.uiFeedbackPopupController.createController
    : null;
  const feedbackController = feedbackPopupFactory
    ? feedbackPopupFactory({
        popupModuleRegistry,
        applyModuleTheme: applyPopupModuleTheme,
        summarizeTarget: scriptModule && typeof scriptModule.summarizeTarget === "function"
          ? scriptModule.summarizeTarget
          : undefined
      })
    : {
        closeFeedbackPopup: () => {},
        attachFeedbackListener: () => {},
        setDebugEnabled: () => {},
        setFeedbackSoundEnabled: () => {}
      };

  function ensureStyle(color, srsColor) {
    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement("style");
      style.id = STYLE_ID;
      const parent = document.head || document.documentElement;
      if (parent) {
        parent.appendChild(style);
      }
    }
    const srs = srsColor || color;
    style.textContent = `
      :root{--lexishift-highlight-color:${color};--lexishift-srs-highlight-color:${srs};}
      .lexishift-replacement{cursor:pointer;transition:color 120ms ease;}
      .lexishift-replacement.lexishift-highlight{color:var(--lexishift-highlight-color);}
      .lexishift-replacement.lexishift-highlight.lexishift-srs{color:var(--lexishift-srs-highlight-color);}
      ${popupLayoutStyles}
      .lexishift-script-module-row{display:grid;grid-template-columns:auto 1fr;column-gap:8px;align-items:start;}
      .lexishift-script-module-row + .lexishift-script-module-row{margin-top:4px;}
      .lexishift-script-module-label{font-size:10px;line-height:1.3;letter-spacing:0.06em;
        text-transform:uppercase;color:var(--lexishift-module-label, rgba(247,244,239,0.72));}
      .lexishift-script-module-value{font-size:13px;line-height:1.35;font-weight:600;word-break:break-word;}
      .lexishift-popup-module-toggle{display:inline-flex;align-items:center;justify-content:flex-start;
        width:100%;padding:0;border:0;background:transparent;color:inherit;cursor:pointer;
        font-size:12px;line-height:1.35;font-weight:700;letter-spacing:0.03em;}
      .lexishift-popup-module-toggle-centered{justify-content:center;text-align:center;}
      .lexishift-popup-module-toggle:disabled{opacity:0.65;cursor:default;}
      .lexishift-popup-module-details{display:flex;flex-direction:column;gap:4px;margin-top:6px;}
      .lexishift-popup-module-details.hidden{display:none;}
      .lexishift-popup-module-line{font-size:11px;line-height:1.35;
        color:var(--lexishift-module-line, rgba(247,244,239,0.9));}
      .lexishift-popup-module-quote{padding-left:6px;
        border-left:2px solid var(--lexishift-module-quote-border, rgba(247,244,239,0.35));
        font-style:italic;color:var(--lexishift-module-quote-text, rgba(247,244,239,0.86));}
      .lexishift-definition-module{display:flex;flex-direction:column;min-width:180px;overflow:hidden;}
      .lexishift-definition-header{display:flex;align-items:center;justify-content:space-between;
        gap:8px;margin-bottom:5px;}
      .lexishift-definition-word{min-width:0;font-size:14px;line-height:1.2;font-weight:800;
        word-break:break-word;}
      .lexishift-definition-pos{flex:0 0 auto;padding:2px 6px;border-radius:999px;
        background:var(--lexishift-module-quote-border, rgba(247,244,239,0.18));
        color:var(--lexishift-module-label, rgba(247,244,239,0.78));
        font-size:10px;line-height:1.2;font-weight:700;text-transform:uppercase;}
      .lexishift-definition-pos:empty{display:none;}
      .lexishift-definition-body{display:flex;min-height:0;flex-direction:column;gap:5px;
        overflow-y:auto;overscroll-behavior:contain;scrollbar-gutter:stable;padding-right:2px;}
      .lexishift-definition-source{margin-top:-2px;font-size:9px;line-height:1.3;font-weight:700;
        letter-spacing:0.035em;color:var(--lexishift-module-label, rgba(247,244,239,0.68));}
      ${dictionaryDisclosureStyles}
      .lexishift-definition-status{font-size:11px;line-height:1.35;
        color:var(--lexishift-module-line, rgba(247,244,239,0.88));}
      .lexishift-definition-senses,.lexishift-definition-glosses{margin:0;padding-left:18px;}
      .lexishift-definition-sense,.lexishift-definition-gloss-item{padding-left:2px;}
      .lexishift-definition-sense + .lexishift-definition-sense,
      .lexishift-definition-gloss-item + .lexishift-definition-gloss-item{margin-top:6px;}
      .lexishift-definition-sense::marker,.lexishift-definition-gloss-item::marker{
        color:var(--lexishift-module-label, rgba(247,244,239,0.68));font-size:10px;font-weight:800;}
      .lexishift-definition-sense-glosses{font-size:12px;line-height:1.4;font-weight:650;
        color:var(--lexishift-module-text, #f7f4ef);white-space:pre-line;}
      .lexishift-definition-orthography-note{display:flex;align-items:baseline;gap:5px;
        margin-top:2px;font-size:11px;line-height:1.4;
        color:var(--lexishift-module-line, rgba(247,244,239,0.9));}
      .lexishift-definition-orthography-form{flex:0 0 auto;font-weight:750;
        color:var(--lexishift-module-text, #f7f4ef);}
      .lexishift-definition-orthography-text{min-width:0;}
      .lexishift-definition-gloss{font-size:12px;line-height:1.35;font-weight:650;
        color:var(--lexishift-module-text, #f7f4ef);white-space:pre-line;}
      .lexishift-definition-labels{display:flex;gap:4px;flex-wrap:wrap;margin-top:3px;}
      .lexishift-definition-label{padding:1px 5px;border-radius:999px;
        background:var(--lexishift-module-quote-border, rgba(247,244,239,0.14));
        color:var(--lexishift-module-label, rgba(247,244,239,0.78));
        font-size:9px;line-height:1.35;font-weight:700;}
      .lexishift-definition-detail,.lexishift-definition-example{font-size:11px;line-height:1.35;
        color:var(--lexishift-module-line, rgba(247,244,239,0.86));}
      .lexishift-definition-example{font-style:italic;}
      .lexishift-definition-structured-senses{display:flex;flex-direction:column;gap:7px;}
      .lexishift-definition-structured-sense + .lexishift-definition-structured-sense{
        padding-top:6px;border-top:1px solid var(--lexishift-module-quote-border, rgba(247,244,239,0.16));}
      .lexishift-definition-structured{max-height:270px;overflow-y:auto;overscroll-behavior:contain;
        padding-right:3px;font-size:11px;line-height:1.5;color:var(--lexishift-module-line, rgba(247,244,239,0.92));}
      .lexishift-yomitan-element{box-sizing:border-box;}
      .lexishift-yomitan-element.lexishift-yomitan-role-headword{margin-bottom:5px;font-size:12px;font-weight:750;
        color:var(--lexishift-module-text, #f7f4ef);}
      .lexishift-yomitan-role-major-section + .lexishift-yomitan-role-major-section{
        margin-top:7px;padding-top:6px;border-top:1px solid var(--lexishift-module-quote-border, rgba(247,244,239,0.16));}
      .lexishift-yomitan-role-sense{margin-top:5px;}
      .lexishift-yomitan-role-sense-number,.lexishift-yomitan-role-subsense-number{
        display:inline-block;min-width:1.45em;margin-right:3px;font-weight:800;
        color:var(--lexishift-module-text, #f7f4ef);}
      .lexishift-yomitan-role-subsense{margin:3px 0 0 12px;}
      .lexishift-yomitan-role-definition{color:var(--lexishift-module-text, #f7f4ef);}
      .lexishift-yomitan-role-part-of-speech-group{display:inline-block;margin:0 4px 2px 0;
        color:var(--lexishift-module-label, rgba(247,244,239,0.75));font-size:10px;font-weight:700;}
      .lexishift-yomitan-role-example{margin:2px 0 0 10px;color:var(--lexishift-module-label, rgba(247,244,239,0.78));
        font-size:10px;font-style:italic;}
      .lexishift-yomitan-role-note{margin:3px 0 0 10px;color:var(--lexishift-module-label, rgba(247,244,239,0.82));}
      .lexishift-yomitan-role-reference,.lexishift-yomitan-reference-link{
        color:var(--lexishift-module-label, rgba(247,244,239,0.8));}
      .lexishift-yomitan-reference-link{text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px;}
      .lexishift-yomitan-role-source{color:var(--lexishift-module-label, rgba(247,244,239,0.68));font-size:9px;}
      .lexishift-yomitan-role-reading-list,.lexishift-yomitan-role-related-terms{margin:3px 0;padding-left:17px;}
      .lexishift-yomitan-style-bold{font-weight:800;}
      .lexishift-yomitan-style-italic{font-style:italic;}
      .lexishift-yomitan-style-super{font-size:0.72em;vertical-align:super;}
      .lexishift-yomitan-style-sub{font-size:0.72em;vertical-align:sub;}
      .lexishift-yomitan-style-underline{text-decoration:underline;}
      .lexishift-yomitan-image-fallback{display:inline-block;margin:0 2px;font-weight:800;
        color:var(--lexishift-module-text, #f7f4ef);}
      .lexishift-definition-structured-truncated{text-align:center;color:var(--lexishift-module-label, rgba(247,244,239,0.68));}
      .lexishift-definition-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:1px;}
      .lexishift-definition-link{display:inline-flex;align-items:center;padding:3px 7px;border:1px solid rgba(247,244,239,0.2);border-radius:4px;
        background:linear-gradient(180deg,rgba(255,255,255,0.055),rgba(0,0,0,0.035));box-shadow:inset 0 1px 0 rgba(255,255,255,0.07),0 1px 0 rgba(0,0,0,0.13);font-size:11px;line-height:1.3;font-weight:700;color:inherit;text-decoration:none;}
      .lexishift-definition-link:hover{border-color:rgba(247,244,239,0.32);background:linear-gradient(180deg,rgba(255,255,255,0.075),rgba(0,0,0,0.025));}.lexishift-definition-link:focus-visible{outline:2px solid currentColor;outline-offset:2px;}
      @media (prefers-reduced-motion: reduce){
        .lexishift-definition-dictionary-arrow,.lexishift-definition-dictionary-panel{transition:none;}
      }
      .lexishift-feedback-bar{display:flex;gap:6px;align-items:center;padding:6px 8px;
        flex:0 0 auto;border-radius:999px;background:rgba(28,26,23,0.9);box-shadow:0 10px 24px rgba(0,0,0,0.18);}
      .lexishift-feedback-option{width:22px;height:22px;border-radius:999px;border:0;cursor:pointer;
        display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:11px;font-weight:700;
        transition:transform 120ms ease, box-shadow 120ms ease;}
      .lexishift-feedback-option.lexishift-selected{transform:scale(1.15);
        box-shadow:0 0 0 3px rgba(255,255,255,0.45);}
      .lexishift-feedback-option[data-rating="again"]{background:#D64545;}
      .lexishift-feedback-option[data-rating="hard"]{background:#E07B39;}
      .lexishift-feedback-option[data-rating="good"]{background:#E0B84B;color:#2c2a26;}
      .lexishift-feedback-option[data-rating="easy"]{background:#2F74D0;}
    `;
  }

  function applyHighlightToDom(enabled) {
    const highlight = enabled !== false;
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      if (highlight) {
        node.classList.add("lexishift-highlight");
      } else {
        node.classList.remove("lexishift-highlight");
      }
      if (node.dataset.origin === "srs") {
        node.classList.add("lexishift-srs");
      } else {
        node.classList.remove("lexishift-srs");
      }
    });
  }

  function clearReplacements() {
    feedbackController.closeFeedbackPopup();
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      const original = node.dataset.original || node.textContent || "";
      node.replaceWith(document.createTextNode(original));
    });
  }

  function attachClickListener() {
    if (clickListenerAttached) {
      return;
    }
    document.addEventListener("click", (event) => {
      const target = event.target && event.target.closest ? event.target.closest(".lexishift-replacement") : null;
      if (!target) {
        return;
      }
      feedbackController.closeFeedbackPopup();
      const state = target.dataset.state || "replacement";
      if (state === "replacement") {
        target.textContent = target.dataset.original || target.textContent;
        target.dataset.state = "original";
      } else {
        target.textContent = target.dataset.displayReplacement || target.dataset.replacement || target.textContent;
        target.dataset.state = "replacement";
      }
    });
    clickListenerAttached = true;
  }

  function attachFeedbackListener(handler, options = {}) {
    feedbackController.attachFeedbackListener(handler, options);
  }

  function setPopupModulePrefs(prefs, metadata = {}) {
    activePopupModulePrefs = prefs && typeof prefs === "object"
      ? prefs
      : { byId: {}, order: [] };
    if (metadata && metadata.profileId !== undefined) {
      const profileId = String(metadata.profileId || "").trim();
      activePopupProfileId = profileId || "default";
    }
    if (metadata && metadata.targetLanguage !== undefined) {
      activeTargetLanguage = normalizeLanguage(metadata.targetLanguage) || activeTargetLanguage;
    }
    setPopupUiLanguage(
      metadata && metadata.uiLanguage !== undefined
        ? metadata.uiLanguage
        : popupLocaleManager.getActiveUiLanguage()
    );
  }

  function setDebugEnabled(enabled) {
    feedbackController.setDebugEnabled(enabled === true);
  }

  function setFeedbackSoundEnabled(enabled) {
    feedbackController.setFeedbackSoundEnabled(enabled);
  }

  root.ui = {
    ensureStyle,
    applyHighlightToDom,
    clearReplacements,
    attachClickListener,
    attachFeedbackListener,
    setPopupModulePrefs,
    setDebugEnabled,
    setFeedbackSoundEnabled
  };
})();
