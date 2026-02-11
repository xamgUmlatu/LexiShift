(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STYLE_ID = "lexishift-style";
  let clickListenerAttached = false;
  const scriptModule = root.uiJapaneseScriptModule && typeof root.uiJapaneseScriptModule === "object"
    ? root.uiJapaneseScriptModule
    : null;
  const popupModuleRegistryFactory = root.uiPopupModuleRegistry
    && typeof root.uiPopupModuleRegistry.createRegistry === "function"
    ? root.uiPopupModuleRegistry.createRegistry
    : null;
  const popupModuleRegistry = popupModuleRegistryFactory
    ? popupModuleRegistryFactory({
        modules: [
          {
            id: "japanese-script",
            build: (target, debugLog) => {
              if (!scriptModule || typeof scriptModule.build !== "function") {
                return null;
              }
              return scriptModule.build(target, debugLog);
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
        buildJapaneseScriptModule: (target, debugLog) => {
          if (!scriptModule || typeof scriptModule.build !== "function") {
            return null;
          }
          return scriptModule.build(target, debugLog);
        },
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
      .lexishift-script-module-heading{display:block;font-size:10px;line-height:1.2;
        letter-spacing:0.06em;text-transform:uppercase;color:rgba(247,244,239,0.72);margin-bottom:6px;}
      .lexishift-script-module-row{display:grid;grid-template-columns:auto 1fr;column-gap:8px;align-items:start;}
      .lexishift-script-module-row + .lexishift-script-module-row{margin-top:4px;}
      .lexishift-script-module-label{font-size:10px;line-height:1.3;letter-spacing:0.06em;
        text-transform:uppercase;color:rgba(247,244,239,0.72);}
      .lexishift-script-module-value{font-size:13px;line-height:1.35;font-weight:600;word-break:break-word;}
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
    setDebugEnabled,
    setFeedbackSoundEnabled
  };
})();
