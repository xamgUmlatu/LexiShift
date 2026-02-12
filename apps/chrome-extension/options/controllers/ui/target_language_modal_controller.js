(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const settingsManager = opts.settingsManager && typeof opts.settingsManager === "object"
      ? opts.settingsManager
      : null;
    const resolveTargetLanguage = typeof opts.resolveTargetLanguage === "function"
      ? opts.resolveTargetLanguage
      : (() => "en");
    const resolveSelectedProfileId = typeof opts.resolveSelectedProfileId === "function"
      ? opts.resolveSelectedProfileId
      : (() => "default");
    const optionsMainContent = opts.optionsMainContent || null;
    const triggerButton = opts.triggerButton || null;
    const modalBackdrop = opts.modalBackdrop || null;
    const modalRoot = opts.modalRoot || null;
    const modulesList = opts.modulesList || null;

    let isOpen = false;
    let lastFocusedElement = null;
    let activeTargetLanguage = "en";
    let activeProfileId = "default";
    let activeModulePrefs = { byId: {} };

    function getRegistry() {
      const registry = root.popupModulesRegistry;
      return registry && typeof registry === "object" ? registry : null;
    }

    function normalizeLanguage(value) {
      return String(value || "").trim().toLowerCase();
    }

    function supportsTargetLanguage(value) {
      const language = normalizeLanguage(value);
      const registry = getRegistry();
      if (!registry || typeof registry.resolveVisibleSettingModules !== "function") {
        return language === "ja";
      }
      const visibleModules = registry.resolveVisibleSettingModules(language);
      return Array.isArray(visibleModules) && visibleModules.length > 0;
    }

    function getVisibleModules(language) {
      const registry = getRegistry();
      if (!registry || typeof registry.resolveVisibleSettingModules !== "function") {
        return [];
      }
      const visible = registry.resolveVisibleSettingModules(language);
      return Array.isArray(visible) ? visible : [];
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

    function cloneModulePrefs(modulePrefs) {
      const source = modulePrefs && typeof modulePrefs === "object" ? modulePrefs : {};
      const byId = source.byId && typeof source.byId === "object" ? source.byId : {};
      const nextById = {};
      for (const [key, value] of Object.entries(byId)) {
        const entry = value && typeof value === "object" ? value : {};
        nextById[key] = {
          ...entry,
          config: entry.config && typeof entry.config === "object" ? { ...entry.config } : undefined
        };
      }
      return { byId: nextById };
    }

    function ensureModuleEntry(modulePrefs, moduleId) {
      if (!modulePrefs.byId || typeof modulePrefs.byId !== "object") {
        modulePrefs.byId = {};
      }
      if (!modulePrefs.byId[moduleId] || typeof modulePrefs.byId[moduleId] !== "object") {
        modulePrefs.byId[moduleId] = { enabled: true };
      }
      return modulePrefs.byId[moduleId];
    }

    function getModuleLabel(definition) {
      return translate(
        definition.labelKey,
        null,
        definition.labelFallback || definition.id
      );
    }

    function getModuleDescription(definition) {
      if (!definition) {
        return "";
      }
      const fallback = String(definition.descriptionFallback || "").trim();
      const key = String(definition.descriptionKey || "").trim();
      if (!key && !fallback) {
        return "";
      }
      return translate(key, null, fallback);
    }

    function getToggleStateLabel(enabled) {
      return translate(
        enabled ? "module_toggle_on" : "module_toggle_off",
        null,
        enabled ? "On" : "Off"
      );
    }

    function renderEnableToggle(definition, entry) {
      const enabled = entry.enabled !== false;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "language-module-enable-toggle";
      if (enabled) {
        button.classList.add("is-enabled");
      }
      button.dataset.action = "toggle-enable";
      button.dataset.moduleId = definition.id;
      button.dataset.field = "enabled";
      button.setAttribute("aria-pressed", enabled ? "true" : "false");
      button.setAttribute(
        "aria-label",
        `${getModuleLabel(definition)}: ${getToggleStateLabel(enabled)}`
      );

      const track = document.createElement("span");
      track.className = "language-module-enable-track";
      const thumb = document.createElement("span");
      thumb.className = "language-module-enable-thumb";
      track.appendChild(thumb);

      const text = document.createElement("span");
      text.className = "language-module-enable-text";
      text.textContent = getToggleStateLabel(enabled);

      button.appendChild(track);
      button.appendChild(text);
      return button;
    }

    function renderInnerSettingSelect(definition, entry, disabled) {
      const row = document.createElement("div");
      row.className = "language-module-inner-row";

      const label = document.createElement("label");
      const selectId = `module-select-${definition.id}`;
      label.setAttribute("for", selectId);
      label.className = "language-module-inner-label";
      label.textContent = getModuleLabel(definition);

      const select = document.createElement("select");
      select.className = "language-module-inner-select";
      select.id = selectId;
      select.dataset.moduleId = definition.id;
      select.dataset.field = "config.primary";
      select.disabled = disabled === true;
      const options = Array.isArray(definition.options) ? definition.options : [];
      for (const optionDef of options) {
        const optionEl = document.createElement("option");
        optionEl.value = String(optionDef.value || "");
        optionEl.textContent = translate(
          optionDef.labelKey,
          null,
          optionDef.labelFallback || optionEl.value
        );
        select.appendChild(optionEl);
      }
      const defaultValue = options.length ? String(options[0].value || "") : "";
      const configuredValue = entry
        && entry.config
        && typeof entry.config === "object"
        ? String(entry.config.primary || "")
        : "";
      select.value = configuredValue || defaultValue;

      row.appendChild(label);
      row.appendChild(select);
      return row;
    }

    function renderModuleCard(definition, entry, options) {
      const opts = options && typeof options === "object" ? options : {};
      const card = document.createElement("div");
      card.className = "language-module-card";

      const main = document.createElement("div");
      main.className = "language-module-main";

      const heading = document.createElement("div");
      heading.className = "language-module-heading";

      const title = document.createElement("h3");
      title.className = "language-module-title";
      title.textContent = getModuleLabel(definition);
      heading.appendChild(title);

      const subtitleText = getModuleDescription(definition);
      if (subtitleText) {
        const subtitle = document.createElement("p");
        subtitle.className = "language-module-subtitle";
        subtitle.textContent = subtitleText;
        heading.appendChild(subtitle);
      }

      main.appendChild(heading);
      if (opts.innerContent instanceof HTMLElement) {
        const innerWrap = document.createElement("div");
        innerWrap.className = "language-module-inner";
        innerWrap.appendChild(opts.innerContent);
        main.appendChild(innerWrap);
      }

      const controls = document.createElement("div");
      controls.className = "language-module-controls";
      controls.appendChild(renderEnableToggle(definition, entry));

      card.appendChild(main);
      card.appendChild(controls);
      return card;
    }

    function renderJapaneseScriptModule(definition, definitionsById, prefs) {
      const entry = ensureModuleEntry(prefs, definition.id);
      const selectDefinition = definitionsById["ja-primary-display-script"] || null;
      const selectEntry = selectDefinition
        ? ensureModuleEntry(prefs, selectDefinition.id)
        : null;
      const inner = selectDefinition && selectEntry
        ? renderInnerSettingSelect(selectDefinition, selectEntry, entry.enabled === false)
        : null;
      return renderModuleCard(definition, entry, {
        innerContent: inner
      });
    }

    function renderModuleControls(targetLanguage, modulePrefs) {
      if (!modulesList) {
        return;
      }
      modulesList.textContent = "";
      const language = normalizeLanguage(targetLanguage || resolveTargetLanguage());
      const visibleModules = getVisibleModules(language);
      if (!visibleModules.length) {
        const empty = document.createElement("p");
        empty.className = "hint";
        empty.textContent = translate(
          "hint_modules_unavailable",
          null,
          "No modules are available for this language."
        );
        modulesList.appendChild(empty);
        return;
      }

      const prefs = cloneModulePrefs(modulePrefs);
      const definitionsById = {};
      for (const definition of visibleModules) {
        definitionsById[definition.id] = definition;
      }
      for (const definition of visibleModules) {
        if (definition.id === "ja-primary-display-script") {
          continue;
        }
        if (definition.id === "ja-script-forms") {
          modulesList.appendChild(renderJapaneseScriptModule(definition, definitionsById, prefs));
          continue;
        }
        const entry = ensureModuleEntry(prefs, definition.id);
        modulesList.appendChild(renderModuleCard(definition, entry));
      }
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
      const modulePrefs = typeof settingsManager.getProfileModulePrefs === "function"
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
      }
      const updated = typeof settingsManager.updateProfileModulePrefs === "function"
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

    function handleModulesChange(event) {
      const target = event && event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const moduleId = String(target.dataset.moduleId || "").trim();
      const field = String(target.dataset.field || "").trim();
      if (!moduleId || !field) {
        return;
      }
      if (target instanceof HTMLSelectElement) {
        persistModuleChange(moduleId, field, target.value).catch(() => {});
      }
    }

    function handleModulesClick(event) {
      const eventTarget = event && event.target;
      if (!(eventTarget instanceof Node) || !modulesList) {
        return;
      }
      const button = eventTarget instanceof HTMLElement && typeof eventTarget.closest === "function"
        ? eventTarget.closest("button[data-action='toggle-enable']")
        : null;
      if (!(button instanceof HTMLButtonElement)) {
        return;
      }
      const moduleId = String(button.dataset.moduleId || "").trim();
      const field = String(button.dataset.field || "").trim();
      if (!moduleId || field !== "enabled") {
        return;
      }
      const currentlyEnabled = button.getAttribute("aria-pressed") === "true";
      persistModuleChange(moduleId, "enabled", !currentlyEnabled).catch(() => {});
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
      if (show) {
        refreshModulePrefs({ targetLanguage: language }).catch(() => {});
      }
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
      if (currentlyOpen) {
        refreshModulePrefs().catch(() => {});
      }
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

    if (modulesList) {
      modulesList.addEventListener("click", handleModulesClick);
      modulesList.addEventListener("change", handleModulesChange);
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
