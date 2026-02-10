(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.t === "function"
      ? opts.t
      : ((_key, _subs, fallback) => fallback || "");
    const resolveTargetLanguage = typeof opts.resolveTargetLanguage === "function"
      ? opts.resolveTargetLanguage
      : (() => "en");
    const optionsMainContent = opts.optionsMainContent || null;
    const triggerButton = opts.triggerButton || null;
    const modalBackdrop = opts.modalBackdrop || null;
    const modalRoot = opts.modalRoot || null;

    let isOpen = false;
    let lastFocusedElement = null;

    function normalizeLanguage(value) {
      return String(value || "").trim().toLowerCase();
    }

    function supportsTargetLanguage(value) {
      return normalizeLanguage(value) === "ja";
    }

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

    function trapFocus(event) {
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

      if (!activeWithinModal) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
        return;
      }
      if (active === modalRoot) {
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

    function applyLocalization() {
      const label = translate(
        "title_language_specific_preferences",
        null,
        "Language-specific preferences"
      );
      if (triggerButton) {
        triggerButton.setAttribute("aria-label", label);
        triggerButton.setAttribute("title", label);
      }
    }

    function syncVisibility(targetLanguage) {
      const language = normalizeLanguage(
        targetLanguage !== undefined ? targetLanguage : resolveTargetLanguage()
      );
      const show = supportsTargetLanguage(language);
      if (triggerButton) {
        triggerButton.classList.toggle("hidden", !show);
        triggerButton.setAttribute("aria-expanded", show && isOpen ? "true" : "false");
      }
      if (!show) {
        isOpen = false;
      }
      const shouldShowModal = show && isOpen;
      if (modalBackdrop) {
        modalBackdrop.classList.toggle("hidden", !shouldShowModal);
        modalBackdrop.setAttribute("aria-hidden", shouldShowModal ? "false" : "true");
      }
      if (optionsMainContent) {
        if (shouldShowModal) {
          optionsMainContent.setAttribute("inert", "");
          optionsMainContent.setAttribute("aria-hidden", "true");
        } else {
          optionsMainContent.removeAttribute("inert");
          optionsMainContent.removeAttribute("aria-hidden");
        }
      }
      document.body.classList.toggle("modal-open", shouldShowModal);
    }

    function setOpen(open) {
      const wasOpen = isOpen === true;
      if (open === true && !wasOpen) {
        lastFocusedElement = document.activeElement instanceof HTMLElement
          ? document.activeElement
          : null;
      }
      isOpen = open === true;
      syncVisibility(resolveTargetLanguage());
      const currentlyOpen = isOpen === true;
      if (wasOpen && !currentlyOpen) {
        restoreFocusAfterClose();
      }
    }

    function toggle() {
      const targetLanguage = resolveTargetLanguage();
      if (!supportsTargetLanguage(targetLanguage)) {
        return false;
      }
      setOpen(!isOpen);
      return true;
    }

    function close() {
      setOpen(false);
    }

    function handleBackdropClick(event) {
      if (event && event.target === modalBackdrop) {
        close();
      }
    }

    function handleOkClick() {
      close();
    }

    function handleKeydown(event) {
      if (!isOpen) {
        return false;
      }
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return true;
      }
      trapFocus(event);
      return true;
    }

    function getIsOpen() {
      return isOpen;
    }

    return {
      applyLocalization,
      syncVisibility,
      setOpen,
      toggle,
      close,
      handleBackdropClick,
      handleOkClick,
      handleKeydown,
      supportsTargetLanguage,
      isOpen: getIsOpen
    };
  }

  root.optionsTargetLanguageModal = {
    createController
  };
})();
