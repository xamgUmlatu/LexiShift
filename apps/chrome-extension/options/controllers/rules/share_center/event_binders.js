(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function bindEvents(options) {
    const opts = options && typeof options === "object" ? options : {};
    const parentInputs = opts.parentInputs && typeof opts.parentInputs === "object" ? opts.parentInputs : {};
    const staticLeafInputs = opts.staticLeafInputs && typeof opts.staticLeafInputs === "object" ? opts.staticLeafInputs : {};
    const staticTargets = opts.staticTargets && typeof opts.staticTargets === "object" ? opts.staticTargets : {};
    const applyParentToggle = typeof opts.applyParentToggle === "function" ? opts.applyParentToggle : (() => {});
    const updateAllParentStates = typeof opts.updateAllParentStates === "function" ? opts.updateAllParentStates : (() => {});
    const updateSummary = typeof opts.updateSummary === "function" ? opts.updateSummary : (() => {});
    const onLeafChanged = typeof opts.onLeafChanged === "function" ? opts.onLeafChanged : (() => {});
    const setExportMode = typeof opts.setExportMode === "function" ? opts.setExportMode : (() => {});
    const openModal = typeof opts.openModal === "function" ? opts.openModal : (() => {});
    const closeModal = typeof opts.closeModal === "function" ? opts.closeModal : (() => {});
    const closeAllModals = typeof opts.closeAllModals === "function" ? opts.closeAllModals : (() => {});
    const setOutputStatus = typeof opts.setOutputStatus === "function" ? opts.setOutputStatus : (() => {});
    const setImportFileName = typeof opts.setImportFileName === "function" ? opts.setImportFileName : (() => {});
    const generateShareCode = typeof opts.generateShareCode === "function" ? opts.generateShareCode : (() => Promise.resolve());
    const importShareCode = typeof opts.importShareCode === "function" ? opts.importShareCode : (() => Promise.resolve());
    const setExportStatus = typeof opts.setExportStatus === "function" ? opts.setExportStatus : (() => {});
    const setImportStatus = typeof opts.setImportStatus === "function" ? opts.setImportStatus : (() => {});
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const tr = typeof opts.tr === "function" ? opts.tr : ((key, fallback) => String(fallback || key || ""));
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : { DEFAULT: "#6c675f", ERROR: "#b42318" };

    const openExportButton = opts.openExportButton || null;
    const openImportButton = opts.openImportButton || null;
    const exportBackdrop = opts.exportBackdrop || null;
    const exportCloseButton = opts.exportCloseButton || null;
    const importBackdrop = opts.importBackdrop || null;
    const importCloseButton = opts.importCloseButton || null;
    const exportModeFullInput = opts.exportModeFullInput || null;
    const exportModeCustomInput = opts.exportModeCustomInput || null;
    const importFileInput = opts.importFileInput || null;
    const importButton = opts.importButton || null;
    const generateButton = opts.generateButton || null;
    const importStatusOutput = opts.importStatusOutput || null;

    Object.entries(parentInputs).forEach(([parentId, input]) => {
      if (!input) {
        return;
      }
      input.addEventListener("change", () => {
        applyParentToggle(parentId, input.checked === true);
        updateAllParentStates();
        updateSummary();
      });
    });

    Object.entries(staticLeafInputs).forEach(([leafId, input]) => {
      if (!input) {
        return;
      }
      const entry = {
        id: leafId,
        kind: "static",
        input,
        meta: staticTargets[leafId]
      };
      input.addEventListener("change", () => {
        onLeafChanged(entry);
      });
    });

    if (exportModeFullInput) {
      exportModeFullInput.addEventListener("change", () => {
        if (exportModeFullInput.checked === true) {
          setExportMode("full");
        }
      });
    }
    if (exportModeCustomInput) {
      exportModeCustomInput.addEventListener("change", () => {
        if (exportModeCustomInput.checked === true) {
          setExportMode("custom");
        }
      });
    }

    if (openExportButton) {
      openExportButton.addEventListener("click", () => {
        updateSummary();
        openModal("export");
      });
    }
    if (openImportButton) {
      openImportButton.addEventListener("click", () => {
        setOutputStatus(importStatusOutput, "", colors.DEFAULT);
        if (importFileInput) {
          importFileInput.value = "";
        }
        setImportFileName("");
        openModal("import");
      });
    }
    if (exportCloseButton) {
      exportCloseButton.addEventListener("click", () => {
        closeModal("export");
      });
    }
    if (importCloseButton) {
      importCloseButton.addEventListener("click", () => {
        closeModal("import");
      });
    }
    if (exportBackdrop) {
      exportBackdrop.addEventListener("click", (event) => {
        if (event.target === exportBackdrop) {
          closeModal("export");
        }
      });
    }
    if (importBackdrop) {
      importBackdrop.addEventListener("click", (event) => {
        if (event.target === importBackdrop) {
          closeModal("import");
        }
      });
    }
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeAllModals();
      }
    });

    if (generateButton) {
      generateButton.addEventListener("click", () => {
        generateShareCode().catch((error) => {
          const message = error && error.message ? error.message : tr("share_center_error_export_failed", "Failed to export file.");
          setExportStatus(message, colors.ERROR);
          log("Share center generate failed.", error);
        });
      });
    }
    if (importButton) {
      importButton.addEventListener("click", () => {
        importShareCode().catch((error) => {
          const message = error && error.message ? error.message : tr("share_center_error_import_failed", "Failed to import file.");
          setImportStatus(message, colors.ERROR);
          log("Share center import failed.", error);
        });
      });
    }
    if (importFileInput) {
      importFileInput.addEventListener("change", () => {
        const file = importFileInput.files && importFileInput.files[0];
        setImportFileName(file ? file.name : "");
      });
    }
  }

  root.optionsShareCenterEventBinders = {
    bindEvents
  };
})();
