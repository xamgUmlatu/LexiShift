(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  root.uiPopupLayoutStyles = {
    styles: `
      .lexishift-feedback-popup{position:absolute;display:flex;flex-direction:column;gap:6px;
        align-items:flex-start;transform:translateY(6px) scale(0.92);opacity:0;
        transition:transform 140ms ease, opacity 140ms ease;z-index:2147483647;
        pointer-events:none;box-sizing:border-box;overflow:hidden;
        max-width:min(280px, calc(100vw - 16px));max-height:calc(100vh - 16px);}
      .lexishift-feedback-popup.lexishift-open{transform:translateY(0) scale(1);opacity:1;pointer-events:auto;}
      .lexishift-feedback-popup.lexishift-measuring{transform:none;transition:none;visibility:hidden;}
      .lexishift-feedback-modules{display:flex;flex:1 1 auto;flex-direction:column;gap:6px;align-items:stretch;
        width:100%;min-height:0;overflow-x:hidden;overflow-y:auto;overscroll-behavior:contain;}
      .lexishift-feedback-modules:empty{display:none;}
      .lexishift-popup-module{flex:0 1 auto;padding:8px 10px;border-radius:10px;
        background:var(--lexishift-module-bg, rgba(28,26,23,0.94));
        color:var(--lexishift-module-text, #f7f4ef);box-sizing:border-box;
        box-shadow:0 10px 24px var(--lexishift-module-shadow, rgba(0,0,0,0.18));
        min-width:140px;max-width:min(280px, calc(100vw - 16px));
        max-height:min(52vh, 420px);overflow:hidden;}
    `
  };
})();
