(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const STYLE_ID = "lexishift-style";
  let clickListenerAttached = false;

  function ensureStyle(color) {
    let style = document.getElementById(STYLE_ID);
    if (!style) {
      style = document.createElement("style");
      style.id = STYLE_ID;
      const parent = document.head || document.documentElement;
      if (parent) {
        parent.appendChild(style);
      }
    }
    style.textContent = `:root{--lexishift-highlight-color:${color};}.lexishift-replacement{cursor:pointer;transition:color 120ms ease;}.lexishift-replacement.lexishift-highlight{color:var(--lexishift-highlight-color);}`;
  }

  function applyHighlightToDom(enabled) {
    const highlight = enabled !== false;
    document.querySelectorAll(".lexishift-replacement").forEach((node) => {
      if (highlight) {
        node.classList.add("lexishift-highlight");
      } else {
        node.classList.remove("lexishift-highlight");
      }
    });
  }

  function clearReplacements() {
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
      const state = target.dataset.state || "replacement";
      if (state === "replacement") {
        target.textContent = target.dataset.original || target.textContent;
        target.dataset.state = "original";
      } else {
        target.textContent = target.dataset.replacement || target.textContent;
        target.dataset.state = "replacement";
      }
    });
    clickListenerAttached = true;
  }

  root.ui = { ensureStyle, applyHighlightToDom, clearReplacements, attachClickListener };
})();
