(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STYLE_ID = "lexishift-style";
  let clickListenerAttached = false;
  const scriptModule = root.uiJapaneseScriptModule && typeof root.uiJapaneseScriptModule === "object"
    ? root.uiJapaneseScriptModule
    : null;
  const feedbackHistoryModule = root.uiFeedbackHistoryModule && typeof root.uiFeedbackHistoryModule === "object"
    ? root.uiFeedbackHistoryModule
    : null;
  const encounterHistoryModule = root.uiEncounterHistoryModule && typeof root.uiEncounterHistoryModule === "object"
    ? root.uiEncounterHistoryModule
    : null;
  const popupModulesRegistry = root.popupModulesRegistry && typeof root.popupModulesRegistry === "object"
    ? root.popupModulesRegistry
    : null;
  const popupHistoryStore = root.popupModuleHistoryStore && typeof root.popupModuleHistoryStore === "object"
    ? root.popupModuleHistoryStore
    : null;
  const lemmatize = root.lemmatizer && typeof root.lemmatizer.lemmatize === "function"
    ? root.lemmatizer.lemmatize
    : null;
  const popupModuleRegistryFactory = root.uiPopupModuleRegistry
    && typeof root.uiPopupModuleRegistry.createRegistry === "function"
    ? root.uiPopupModuleRegistry.createRegistry
    : null;
  let activePopupModulePrefs = { byId: {} };
  let activePopupProfileId = "default";
  let activeTargetLanguage = "en";

  function normalizeLanguage(value) {
    return String(value || "").trim().toLowerCase();
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
      lemmatize
    };
  }

  const popupModuleRegistry = popupModuleRegistryFactory
    ? popupModuleRegistryFactory({
        modules: [
          {
            id: "japanese-script",
            build: (target, debugLog) => {
              if (!scriptModule || typeof scriptModule.build !== "function") {
                return null;
              }
              const targetLanguage = resolveTargetLanguage(target);
              if (!isPopupModuleEnabled("ja-script-forms", targetLanguage)) {
                return null;
              }
              return scriptModule.build(target, debugLog);
            }
          },
          {
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
          {
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
        ]
      })
    : null;
  const feedbackPopupFactory = root.uiFeedbackPopupController
    && typeof root.uiFeedbackPopupController.createController === "function"
    ? root.uiFeedbackPopupController.createController
    : null;
  const feedbackController = feedbackPopupFactory
    ? feedbackPopupFactory({
        popupModuleRegistry,
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
      .lexishift-feedback-popup{position:absolute;display:flex;flex-direction:column;gap:6px;
        align-items:flex-start;transform:translateY(6px) scale(0.92);opacity:0;
        transition:transform 140ms ease, opacity 140ms ease;z-index:2147483647;
        max-width:min(280px, calc(100vw - 16px));}
      .lexishift-feedback-popup.lexishift-open{transform:translateY(0) scale(1);opacity:1;}
      .lexishift-feedback-modules{display:flex;flex-direction:column;gap:6px;align-items:stretch;
        width:100%;}
      .lexishift-feedback-modules:empty{display:none;}
      .lexishift-popup-module{padding:8px 10px;border-radius:10px;background:rgba(28,26,23,0.94);
        color:#f7f4ef;box-shadow:0 10px 24px rgba(0,0,0,0.18);min-width:140px;
        max-width:min(280px, calc(100vw - 16px));}
      .lexishift-script-module-row{display:grid;grid-template-columns:auto 1fr;column-gap:8px;align-items:start;}
      .lexishift-script-module-row + .lexishift-script-module-row{margin-top:4px;}
      .lexishift-script-module-label{font-size:10px;line-height:1.3;letter-spacing:0.06em;
        text-transform:uppercase;color:rgba(247,244,239,0.72);}
      .lexishift-script-module-value{font-size:13px;line-height:1.35;font-weight:600;word-break:break-word;}
      .lexishift-popup-module-toggle{display:inline-flex;align-items:center;justify-content:flex-start;
        width:100%;padding:0;border:0;background:transparent;color:inherit;cursor:pointer;
        font-size:12px;line-height:1.35;font-weight:700;letter-spacing:0.03em;}
      .lexishift-popup-module-toggle-centered{justify-content:center;text-align:center;}
      .lexishift-popup-module-toggle:disabled{opacity:0.65;cursor:default;}
      .lexishift-popup-module-details{display:flex;flex-direction:column;gap:4px;margin-top:6px;}
      .lexishift-popup-module-details.hidden{display:none;}
      .lexishift-popup-module-line{font-size:11px;line-height:1.35;color:rgba(247,244,239,0.9);}
      .lexishift-popup-module-quote{padding-left:6px;border-left:2px solid rgba(247,244,239,0.35);
        font-style:italic;color:rgba(247,244,239,0.86);}
      .lexishift-feedback-bar{display:flex;gap:6px;align-items:center;padding:6px 8px;
        border-radius:999px;background:rgba(28,26,23,0.9);box-shadow:0 10px 24px rgba(0,0,0,0.18);}
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
      : { byId: {} };
    if (metadata && metadata.profileId !== undefined) {
      const profileId = String(metadata.profileId || "").trim();
      activePopupProfileId = profileId || "default";
    }
    if (metadata && metadata.targetLanguage !== undefined) {
      activeTargetLanguage = normalizeLanguage(metadata.targetLanguage) || activeTargetLanguage;
    }
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
