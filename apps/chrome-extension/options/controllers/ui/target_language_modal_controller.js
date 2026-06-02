(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const isFn = (value) => typeof value === "function";

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const resolveTargetLanguage = isFn(opts.resolveTargetLanguage)
      ? opts.resolveTargetLanguage
      : (() => "en");
    const resolveSelectedProfileId = isFn(opts.resolveSelectedProfileId)
      ? opts.resolveSelectedProfileId
      : (() => "default");
    const optionsMainContent = opts.optionsMainContent || null;
    const triggerButton = opts.triggerButton || null;
    const modalBackdrop = opts.modalBackdrop || null;
    const modalRoot = opts.modalRoot || null;
    const modulesList = opts.modulesList || null;

    let isOpen = false;
    let activeTargetLanguage = "en";
    let activeProfileId = "default";
    let activeModulePrefs = { byId: {} };
    let openColorDrawerModuleId = "";

    const getRegistry = () => {
      const registry = root.popupModulesRegistry;
      return registry && typeof registry === "object" ? registry : null;
    };

    const utilsFactory = root.optionsTargetLanguageModalUtils
      && isFn(root.optionsTargetLanguageModalUtils.createHelpers)
      ? root.optionsTargetLanguageModalUtils.createHelpers
      : null;
    const modalUtils = utilsFactory
      ? utilsFactory({
          getRegistry,
          translate,
          getActiveModulePrefs: () => activeModulePrefs
        })
      : null;

    const normalizeLanguage = modalUtils && isFn(modalUtils.normalizeLanguage)
      ? modalUtils.normalizeLanguage
      : (value) => String(value || "").trim().toLowerCase();
    const supportsTargetLanguage = modalUtils && isFn(modalUtils.supportsTargetLanguage)
      ? modalUtils.supportsTargetLanguage
      : (value) => normalizeLanguage(value) === "ja";
    const getVisibleModules = modalUtils && isFn(modalUtils.getVisibleModules)
      ? modalUtils.getVisibleModules
      : (() => []);
    const getThemeDefaults = modalUtils && isFn(modalUtils.getThemeDefaults)
      ? modalUtils.getThemeDefaults
      : (() => ({
          hueDeg: 0,
          saturationPercent: 100,
          brightnessPercent: 100,
          transparencyPercent: 100
        }));
    const normalizeTheme = modalUtils && isFn(modalUtils.normalizeTheme)
      ? modalUtils.normalizeTheme
      : (theme) => (theme && typeof theme === "object" ? { ...theme } : getThemeDefaults());
    const supportsThemeTuning = modalUtils && isFn(modalUtils.supportsThemeTuning)
      ? modalUtils.supportsThemeTuning
      : () => false;
    const cloneModulePrefs = modalUtils && isFn(modalUtils.cloneModulePrefs)
      ? modalUtils.cloneModulePrefs
      : (modulePrefs) => (modulePrefs && typeof modulePrefs === "object" ? { ...modulePrefs } : { byId: {} });
    const ensureModuleEntry = modalUtils && isFn(modalUtils.ensureModuleEntry)
      ? modalUtils.ensureModuleEntry
      : (() => ({ enabled: true }));
    const normalizeCardModuleOrder = modalUtils && isFn(modalUtils.normalizeCardModuleOrder)
      ? modalUtils.normalizeCardModuleOrder
      : (orderIds) => (Array.isArray(orderIds) ? orderIds.map((value) => String(value || "").trim()).filter(Boolean) : []);
    const resolveOrderedCardDefinitions = modalUtils && isFn(modalUtils.resolveOrderedCardDefinitions)
      ? modalUtils.resolveOrderedCardDefinitions
      : (() => []);
    const getModuleLabel = modalUtils && isFn(modalUtils.getModuleLabel)
      ? modalUtils.getModuleLabel
      : (definition) => String(definition && definition.id || "");
    const getModuleDescription = modalUtils && isFn(modalUtils.getModuleDescription)
      ? modalUtils.getModuleDescription
      : (() => "");
    const getToggleStateLabel = modalUtils && isFn(modalUtils.getToggleStateLabel)
      ? modalUtils.getToggleStateLabel
      : (enabled) => (enabled ? "On" : "Off");
    const getThemeSliderDefinitions = modalUtils && isFn(modalUtils.getThemeSliderDefinitions)
      ? modalUtils.getThemeSliderDefinitions
      : (() => []);
    const formatThemeValue = modalUtils && isFn(modalUtils.formatThemeValue)
      ? modalUtils.formatThemeValue
      : (_key, value) => String(value || "");
    const resolveEntryTheme = modalUtils && isFn(modalUtils.resolveEntryTheme)
      ? modalUtils.resolveEntryTheme
      : (() => getThemeDefaults());
    const buildThemePreviewFilter = modalUtils && isFn(modalUtils.buildThemePreviewFilter)
      ? modalUtils.buildThemePreviewFilter
      : (() => "");
    const resolveThemeFromCardInputs = modalUtils && isFn(modalUtils.resolveThemeFromCardInputs)
      ? modalUtils.resolveThemeFromCardInputs
      : (() => getThemeDefaults());
    const applyThemePreviewToCard = modalUtils && isFn(modalUtils.applyThemePreviewToCard)
      ? modalUtils.applyThemePreviewToCard
      : (() => {});

    let moduleInteractions = null;
    const focusManagerFactory = root.optionsTargetLanguageModalFocus
      && isFn(root.optionsTargetLanguageModalFocus.createManager)
      ? root.optionsTargetLanguageModalFocus.createManager
      : null;
    const focusManager = focusManagerFactory
      ? focusManagerFactory({ modalRoot, triggerButton })
      : {
          markFocusBeforeOpen: () => {},
          restoreFocusAfterClose: () => {},
          trapFocus: () => {}
        };

    const rendererFactory = root.optionsTargetLanguageModalRenderer
      && isFn(root.optionsTargetLanguageModalRenderer.createRenderer)
      ? root.optionsTargetLanguageModalRenderer.createRenderer
      : null;
    const moduleRenderer = rendererFactory
      ? rendererFactory({
          modulesList,
          translate,
          normalizeLanguage,
          resolveTargetLanguage,
          getVisibleModules,
          cloneModulePrefs,
          ensureModuleEntry,
          resolveOrderedCardDefinitions,
          getModuleLabel,
          getModuleDescription,
          getToggleStateLabel,
          supportsThemeTuning,
          getThemeSliderDefinitions,
          formatThemeValue,
          resolveEntryTheme,
          buildThemePreviewFilter,
          applyThemePreviewToCard,
          getOpenColorDrawerModuleId: () => openColorDrawerModuleId,
          setOpenColorDrawerModuleId: (moduleId) => {
            openColorDrawerModuleId = String(moduleId || "").trim();
          },
          resetModuleDragState: () => {
            if (moduleInteractions && isFn(moduleInteractions.resetModuleDragState)) {
              moduleInteractions.resetModuleDragState();
            }
          }
        })
      : null;

    const renderModuleControls = (targetLanguage, modulePrefs) => {
      if (moduleRenderer && isFn(moduleRenderer.renderModuleControls)) {
        moduleRenderer.renderModuleControls(targetLanguage, modulePrefs);
      }
    };

    const syncOpenColorDrawerDomState = () => {
      if (moduleRenderer && isFn(moduleRenderer.syncOpenColorDrawerDomState)) {
        moduleRenderer.syncOpenColorDrawerDomState();
      }
    };

    const setOpenColorDrawer = (moduleId) => {
      openColorDrawerModuleId = String(moduleId || "").trim();
      syncOpenColorDrawerDomState();
    };

    function applyLocalization() {
      const label = translate(
        "button_modules",
        null,
        "Modules"
      );
      if (triggerButton) {
        triggerButton.textContent = label;
        triggerButton.setAttribute("aria-label", label);
        triggerButton.setAttribute("title", label);
      }
      if (modalRoot) {
        modalRoot.setAttribute("aria-label", label);
      }
      renderModuleControls(activeTargetLanguage, activeModulePrefs);
    }

    async function refreshModulePrefs(context) {
      if (!settingsManager || !modulesList) {
        return;
      }
      const localContext = context && typeof context === "object" ? context : {};
      const targetLanguage = normalizeLanguage(
        localContext.targetLanguage !== undefined
          ? localContext.targetLanguage
          : resolveTargetLanguage()
      );
      const items = localContext.items && typeof localContext.items === "object"
        ? localContext.items
        : await settingsManager.load();
      const profileId = String(
        localContext.profileId !== undefined
          ? localContext.profileId
          : resolveSelectedProfileId(items)
      ).trim() || "default";
      const modulePrefs = isFn(settingsManager.getProfileModulePrefs)
        ? settingsManager.getProfileModulePrefs(items, {
            profileId,
            targetLanguage
          })
        : { byId: {} };
      activeTargetLanguage = targetLanguage;
      activeProfileId = profileId;
      activeModulePrefs = cloneModulePrefs(modulePrefs);
      renderModuleControls(targetLanguage, activeModulePrefs);
    }

    async function persistModuleOrder(orderIds) {
      if (!settingsManager) {
        return;
      }
      const visibleModules = getVisibleModules(activeTargetLanguage);
      const cardDefinitions = modalUtils && isFn(modalUtils.resolveModuleCardDefinitions)
        ? modalUtils.resolveModuleCardDefinitions(visibleModules)
        : visibleModules;
      const normalizedOrder = normalizeCardModuleOrder(orderIds, cardDefinitions);
      if (!normalizedOrder.length) {
        return;
      }
      const currentOrder = normalizeCardModuleOrder(activeModulePrefs.order, cardDefinitions);
      if (normalizedOrder.join("|") === currentOrder.join("|")) {
        return;
      }
      const nextPrefs = cloneModulePrefs(activeModulePrefs);
      nextPrefs.order = normalizedOrder;
      const updated = isFn(settingsManager.updateProfileModulePrefs)
        ? await settingsManager.updateProfileModulePrefs(nextPrefs, {
            profileId: activeProfileId,
            targetLanguage: activeTargetLanguage
          })
        : null;
      if (updated && typeof updated === "object") {
        activeModulePrefs = cloneModulePrefs(updated);
      } else {
        activeModulePrefs = nextPrefs;
      }
      renderModuleControls(activeTargetLanguage, activeModulePrefs);
    }

    async function persistModuleChange(moduleId, field, value) {
      if (!settingsManager || !moduleId || !field) {
        return;
      }
      const nextPrefs = cloneModulePrefs(activeModulePrefs);
      const entry = ensureModuleEntry(nextPrefs, moduleId);
      if (field === "enabled") {
        entry.enabled = value === true;
      } else if (field === "config.primary") {
        if (!entry.config || typeof entry.config !== "object") {
          entry.config = {};
        }
        entry.config.primary = String(value || "");
      } else if (field === "config.theme") {
        if (!entry.config || typeof entry.config !== "object") {
          entry.config = {};
        }
        entry.config.theme = normalizeTheme(
          value && typeof value === "object" ? value : null,
          getThemeDefaults()
        );
      } else if (field.startsWith("config.theme.")) {
        const themeKey = String(field.slice("config.theme.".length) || "").trim();
        if (!themeKey) {
          return;
        }
        if (!entry.config || typeof entry.config !== "object") {
          entry.config = {};
        }
        const currentTheme = normalizeTheme(entry.config.theme, getThemeDefaults());
        currentTheme[themeKey] = Number.parseInt(value, 10);
        entry.config.theme = normalizeTheme(currentTheme, getThemeDefaults());
      }
      const updated = isFn(settingsManager.updateProfileModulePrefs)
        ? await settingsManager.updateProfileModulePrefs(nextPrefs, {
            profileId: activeProfileId,
            targetLanguage: activeTargetLanguage
          })
        : null;
      if (updated && typeof updated === "object") {
        activeModulePrefs = cloneModulePrefs(updated);
      } else {
        activeModulePrefs = nextPrefs;
      }
      renderModuleControls(activeTargetLanguage, activeModulePrefs);
    }

    const interactionsFactory = root.optionsTargetLanguageModalInteractions
      && isFn(root.optionsTargetLanguageModalInteractions.createInteractions)
      ? root.optionsTargetLanguageModalInteractions.createInteractions
      : null;
    moduleInteractions = interactionsFactory
      ? interactionsFactory({
          modulesList,
          persistModuleChange,
          persistModuleOrder,
          formatThemeValue,
          resolveThemeFromCardInputs,
          applyThemePreviewToCard,
          getOpenColorDrawerModuleId: () => openColorDrawerModuleId,
          setOpenColorDrawer
        })
      : {
          handleModulesChange: () => {},
          handleModulesInput: () => {},
          handleModulesDragStart: () => {},
          handleModulesDragOver: () => {},
          handleModulesDrop: () => {},
          handleModulesDragEnd: () => {},
          handleModulesClick: () => {},
          resetModuleDragState: () => {}
        };

    function syncVisibility(targetLanguage) {
      const language = normalizeLanguage(
        targetLanguage !== undefined ? targetLanguage : resolveTargetLanguage()
      );
      const show = supportsTargetLanguage(language);
      if (triggerButton) {
        triggerButton.hidden = !show;
        triggerButton.classList.toggle("hidden", !show);
        triggerButton.setAttribute("aria-expanded", show && isOpen ? "true" : "false");
      }
      if (!show) {
        isOpen = false;
        openColorDrawerModuleId = "";
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
      if (show) {
        refreshModulePrefs({ targetLanguage: language }).catch(() => {});
      }
    }

    function setOpen(open) {
      const wasOpen = isOpen === true;
      if (open === true && !wasOpen) {
        focusManager.markFocusBeforeOpen();
      }
      isOpen = open === true;
      if (!isOpen) {
        openColorDrawerModuleId = "";
        moduleInteractions.resetModuleDragState();
      }
      syncVisibility(resolveTargetLanguage());
      const currentlyOpen = isOpen === true;
      if (currentlyOpen) {
        refreshModulePrefs().catch(() => {});
      }
      if (wasOpen && !currentlyOpen) {
        focusManager.restoreFocusAfterClose();
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
      focusManager.trapFocus(event, isOpen);
      return true;
    }

    function getIsOpen() {
      return isOpen;
    }

    if (modulesList) {
      modulesList.addEventListener("click", moduleInteractions.handleModulesClick);
      modulesList.addEventListener("change", moduleInteractions.handleModulesChange);
      modulesList.addEventListener("input", moduleInteractions.handleModulesInput);
      modulesList.addEventListener("dragstart", moduleInteractions.handleModulesDragStart);
      modulesList.addEventListener("dragover", moduleInteractions.handleModulesDragOver);
      modulesList.addEventListener("drop", moduleInteractions.handleModulesDrop);
      modulesList.addEventListener("dragend", moduleInteractions.handleModulesDragEnd);
    }

    return {
      applyLocalization,
      refreshModulePrefs,
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
