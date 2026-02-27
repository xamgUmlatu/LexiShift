(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createModalHelpers(options) {
    const opts = options && typeof options === "object" ? options : {};
    const exportBackdrop = opts.exportBackdrop || null;
    const exportModal = opts.exportModal || null;
    const importBackdrop = opts.importBackdrop || null;
    const importModal = opts.importModal || null;
    const body = opts.body || null;

    function isModalOpen(backdrop) {
      return Boolean(backdrop) && !backdrop.classList.contains("hidden");
    }

    function syncBodyModalState() {
      const hasOpen = isModalOpen(exportBackdrop) || isModalOpen(importBackdrop);
      if (body && body.classList) {
        body.classList.toggle("modal-open", hasOpen);
      }
    }

    function openModal(kind) {
      if (kind === "export" && exportBackdrop) {
        exportBackdrop.classList.remove("hidden");
        exportBackdrop.setAttribute("aria-hidden", "false");
        if (exportModal) {
          exportModal.focus();
        }
      }
      if (kind === "import" && importBackdrop) {
        importBackdrop.classList.remove("hidden");
        importBackdrop.setAttribute("aria-hidden", "false");
        if (importModal) {
          importModal.focus();
        }
      }
      syncBodyModalState();
    }

    function closeModal(kind) {
      if (kind === "export" && exportBackdrop) {
        exportBackdrop.classList.add("hidden");
        exportBackdrop.setAttribute("aria-hidden", "true");
      }
      if (kind === "import" && importBackdrop) {
        importBackdrop.classList.add("hidden");
        importBackdrop.setAttribute("aria-hidden", "true");
      }
      syncBodyModalState();
    }

    function closeAllModals() {
      closeModal("export");
      closeModal("import");
    }

    return {
      openModal,
      closeModal,
      closeAllModals,
      isModalOpen,
      syncBodyModalState
    };
  }

  root.optionsShareCenterModal = {
    createModalHelpers
  };
})();
