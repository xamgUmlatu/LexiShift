(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createManager(options = {}) {
    const modalRoot = options.modalRoot || null;
    const triggerButton = options.triggerButton || null;
    let lastFocusedElement = null;

    function getFocusableElements() {
      if (!modalRoot) {
        return [];
      }
      const selector = [
        "button:not([disabled])",
        "select:not([disabled])",
        "input:not([disabled])",
        "textarea:not([disabled])",
        "a[href]",
        "[tabindex]:not([tabindex='-1'])"
      ].join(", ");
      return Array.from(modalRoot.querySelectorAll(selector)).filter((node) => {
        if (!(node instanceof HTMLElement)) {
          return false;
        }
        if (node.hidden) {
          return false;
        }
        const style = window.getComputedStyle(node);
        return style.display !== "none" && style.visibility !== "hidden";
      });
    }

    function markFocusBeforeOpen() {
      lastFocusedElement = document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    }

    function restoreFocusAfterClose() {
      const restoreTarget = (
        lastFocusedElement instanceof HTMLElement
        && document.contains(lastFocusedElement)
      )
        ? lastFocusedElement
        : triggerButton;
      lastFocusedElement = null;
      if (!(restoreTarget instanceof HTMLElement) || typeof restoreTarget.focus !== "function") {
        return;
      }
      window.requestAnimationFrame(() => {
        restoreTarget.focus();
      });
    }

    function trapFocus(event, isOpen) {
      if (!(event instanceof KeyboardEvent) || event.key !== "Tab" || !isOpen) {
        return;
      }
      const focusable = getFocusableElements();
      if (!focusable.length) {
        event.preventDefault();
        if (modalRoot && typeof modalRoot.focus === "function") {
          modalRoot.focus();
        }
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      const activeWithinModal = active instanceof Node
        && modalRoot
        && modalRoot.contains(active);

      if (!activeWithinModal || active === modalRoot) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
        return;
      }
      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
        return;
      }
      if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    }

    return {
      markFocusBeforeOpen,
      restoreFocusAfterClose,
      trapFocus
    };
  }

  root.optionsTargetLanguageModalFocus = {
    createManager
  };
})();
