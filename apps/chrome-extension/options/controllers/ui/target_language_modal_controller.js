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
    let openColorDrawerModuleId = "";
    let activeDragModuleId = "";

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

    function toFiniteNumber(value) {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    }

    function getThemeLimits() {
      const registry = getRegistry();
      if (registry && typeof registry.resolveModuleThemeLimits === "function") {
        return registry.resolveModuleThemeLimits();
      }
      return {
        hueDeg: { min: -180, max: 180, step: 1, defaultValue: 0 },
        saturationPercent: { min: 70, max: 450, step: 1, defaultValue: 100 },
        brightnessPercent: { min: 80, max: 200, step: 1, defaultValue: 100 },
        transparencyPercent: { min: 40, max: 100, step: 1, defaultValue: 100 }
      };
    }

    function getThemeDefaults() {
      const registry = getRegistry();
      if (registry && typeof registry.resolveModuleThemeDefaults === "function") {
        return registry.resolveModuleThemeDefaults();
      }
      const limits = getThemeLimits();
      return {
        hueDeg: Number(limits.hueDeg.defaultValue || 0),
        saturationPercent: Number(limits.saturationPercent.defaultValue || 100),
        brightnessPercent: Number(limits.brightnessPercent.defaultValue || 100),
        transparencyPercent: Number(limits.transparencyPercent.defaultValue || 100)
      };
    }

    function normalizeTheme(theme, fallbackTheme) {
      const registry = getRegistry();
      if (registry && typeof registry.normalizeModuleThemeConfig === "function") {
        return registry.normalizeModuleThemeConfig(theme, fallbackTheme);
      }
      const limits = getThemeLimits();
      const fallback = fallbackTheme && typeof fallbackTheme === "object"
        ? fallbackTheme
        : getThemeDefaults();
      function normalizeValue(limit, value, fallbackValue) {
        const lower = toFiniteNumber(limit.min);
        const upper = toFiniteNumber(limit.max);
        const defaultValue = toFiniteNumber(limit.defaultValue);
        const resolvedFallback = toFiniteNumber(fallbackValue);
        const parsed = Number.parseInt(value, 10);
        const base = Number.isFinite(parsed)
          ? parsed
          : (
              resolvedFallback !== null
                ? resolvedFallback
                : (defaultValue !== null ? defaultValue : 0)
            );
        const boundedLow = lower !== null ? Math.max(lower, base) : base;
        return upper !== null ? Math.min(upper, boundedLow) : boundedLow;
      }
      const source = theme && typeof theme === "object" ? theme : {};
      return {
        hueDeg: normalizeValue(limits.hueDeg, source.hueDeg, fallback.hueDeg),
        saturationPercent: normalizeValue(
          limits.saturationPercent,
          source.saturationPercent,
          fallback.saturationPercent
        ),
        brightnessPercent: normalizeValue(
          limits.brightnessPercent,
          source.brightnessPercent,
          fallback.brightnessPercent
        ),
        transparencyPercent: normalizeValue(
          limits.transparencyPercent,
          source.transparencyPercent,
          fallback.transparencyPercent
        )
      };
    }

    function supportsThemeTuning(definition) {
      if (!definition || !definition.id) {
        return false;
      }
      const registry = getRegistry();
      if (registry && typeof registry.supportsThemeTuning === "function") {
        return registry.supportsThemeTuning(definition.id);
      }
      return definition.themeEnabled === true;
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
      const order = Array.isArray(source.order)
        ? source.order.map((moduleId) => String(moduleId || "").trim()).filter(Boolean)
        : [];
      return { byId: nextById, order };
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

    function resolveModuleCardDefinitions(visibleModules) {
      if (!Array.isArray(visibleModules)) {
        return [];
      }
      return visibleModules.filter((definition) => definition && definition.id !== "ja-primary-display-script");
    }

    function normalizeCardModuleOrder(orderIds, definitions) {
      const ordered = [];
      const seen = new Set();
      const definitionIds = Array.isArray(definitions)
        ? definitions.map((definition) => String(definition && definition.id || "").trim()).filter(Boolean)
        : [];
      const allowed = new Set(definitionIds);
      const sourceIds = Array.isArray(orderIds) ? orderIds : [];
      for (const rawId of sourceIds) {
        const moduleId = String(rawId || "").trim();
        if (!moduleId || !allowed.has(moduleId) || seen.has(moduleId)) {
          continue;
        }
        seen.add(moduleId);
        ordered.push(moduleId);
      }
      for (const moduleId of definitionIds) {
        if (seen.has(moduleId)) {
          continue;
        }
        seen.add(moduleId);
        ordered.push(moduleId);
      }
      return ordered;
    }

    function resolveOrderedCardDefinitions(visibleModules, modulePrefs) {
      const cardDefinitions = resolveModuleCardDefinitions(visibleModules);
      const definitionsById = new Map(
        cardDefinitions.map((definition) => [String(definition.id || "").trim(), definition])
      );
      const normalizedOrder = normalizeCardModuleOrder(
        modulePrefs && typeof modulePrefs === "object" ? modulePrefs.order : null,
        cardDefinitions
      );
      return normalizedOrder
        .map((moduleId) => definitionsById.get(moduleId))
        .filter((definition) => Boolean(definition));
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

    function getThemeSliderDefinitions() {
      const limits = getThemeLimits();
      return [
        {
          key: "hueDeg",
          field: "config.theme.hueDeg",
          labelKey: "label_profile_card_theme_hue",
          labelFallback: "Hue",
          suffix: "°",
          limit: limits.hueDeg
        },
        {
          key: "saturationPercent",
          field: "config.theme.saturationPercent",
          labelKey: "label_profile_card_theme_saturation",
          labelFallback: "Saturation",
          suffix: "%",
          limit: limits.saturationPercent
        },
        {
          key: "brightnessPercent",
          field: "config.theme.brightnessPercent",
          labelKey: "label_profile_card_theme_brightness",
          labelFallback: "Brightness",
          suffix: "%",
          limit: limits.brightnessPercent
        },
        {
          key: "transparencyPercent",
          field: "config.theme.transparencyPercent",
          labelKey: "label_profile_card_theme_transparency",
          labelFallback: "Transparency",
          suffix: "%",
          limit: limits.transparencyPercent
        }
      ];
    }

    function formatThemeValue(key, value) {
      const numeric = Number.parseInt(value, 10);
      if (!Number.isFinite(numeric)) {
        return "";
      }
      if (key === "hueDeg") {
        return `${numeric}°`;
      }
      return `${numeric}%`;
    }

    function resolveEntryTheme(entry) {
      const config = entry && entry.config && typeof entry.config === "object"
        ? entry.config
        : {};
      return normalizeTheme(config.theme, getThemeDefaults());
    }

    function buildThemePreviewFilter(theme) {
      const normalized = normalizeTheme(theme, getThemeDefaults());
      const saturation = Math.max(0, normalized.saturationPercent / 100);
      const brightness = Math.max(0, normalized.brightnessPercent / 100);
      const opacity = Math.max(0, Math.min(1, normalized.transparencyPercent / 100));
      return `hue-rotate(${normalized.hueDeg}deg) saturate(${saturation}) brightness(${brightness}) opacity(${opacity})`;
    }

    function getModuleEntryById(moduleId) {
      const normalizedId = String(moduleId || "").trim();
      if (!normalizedId) {
        return {};
      }
      const byId = activeModulePrefs && typeof activeModulePrefs === "object"
        && activeModulePrefs.byId
        && typeof activeModulePrefs.byId === "object"
        ? activeModulePrefs.byId
        : {};
      const entry = byId[normalizedId];
      return entry && typeof entry === "object" ? entry : {};
    }

    function resolveThemeFromCardInputs(moduleId, card) {
      const entry = getModuleEntryById(moduleId);
      const fallbackTheme = resolveEntryTheme(entry);
      if (!(card instanceof HTMLElement)) {
        return fallbackTheme;
      }
      const nextTheme = { ...fallbackTheme };
      for (const sliderDef of getThemeSliderDefinitions()) {
        const slider = card.querySelector(
          `input[type="range"][data-module-id="${moduleId}"][data-theme-key="${sliderDef.key}"]`
        );
        if (slider instanceof HTMLInputElement) {
          nextTheme[sliderDef.key] = Number.parseInt(slider.value, 10);
        }
      }
      return normalizeTheme(nextTheme, fallbackTheme);
    }

    function applyThemePreviewToCard(card, theme) {
      if (!(card instanceof HTMLElement)) {
        return;
      }
      const filterValue = buildThemePreviewFilter(theme);
      const swatch = card.querySelector(".language-module-color-trigger-swatch");
      if (swatch instanceof HTMLElement) {
        swatch.style.filter = filterValue;
      }
      const panel = card.querySelector(".language-module-color-panel");
      if (panel instanceof HTMLElement) {
        panel.style.filter = filterValue;
      }
    }

    function renderDragHandle(definition) {
      const handle = document.createElement("button");
      handle.type = "button";
      handle.className = "language-module-drag-handle";
      handle.draggable = true;
      handle.dataset.moduleId = definition.id;
      const label = translate(
        "label_module_drag_reorder",
        null,
        "Drag to reorder"
      );
      handle.setAttribute("aria-label", `${getModuleLabel(definition)}: ${label}`);
      handle.setAttribute("title", label);

      const dots = document.createElement("span");
      dots.className = "language-module-drag-dots";
      dots.setAttribute("aria-hidden", "true");
      handle.appendChild(dots);
      return handle;
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

    function renderColorTrigger(definition, entry) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "language-module-color-trigger";
      button.dataset.action = "toggle-color-drawer";
      button.dataset.moduleId = definition.id;
      const isOpen = openColorDrawerModuleId === definition.id;
      button.setAttribute("aria-pressed", isOpen ? "true" : "false");
      button.setAttribute("aria-expanded", isOpen ? "true" : "false");
      button.setAttribute(
        "aria-label",
        `${getModuleLabel(definition)}: ${translate(
          "subsection_profile_card_theme",
          null,
          "Card color tuning"
        )}`
      );

      const swatch = document.createElement("span");
      swatch.className = "language-module-color-trigger-swatch";
      swatch.style.filter = buildThemePreviewFilter(resolveEntryTheme(entry));
      button.appendChild(swatch);
      return button;
    }

    function renderColorDrawer(definition, entry) {
      const theme = resolveEntryTheme(entry);
      const sliderDefs = getThemeSliderDefinitions();
      const drawer = document.createElement("div");
      drawer.className = "language-module-color-drawer";
      drawer.dataset.moduleId = definition.id;

      const panel = document.createElement("div");
      panel.className = "language-module-color-panel";
      panel.style.filter = buildThemePreviewFilter(theme);

      const grid = document.createElement("div");
      grid.className = "language-module-color-grid";
      for (const sliderDef of sliderDefs) {
        const cell = document.createElement("div");
        cell.className = "language-module-color-cell";

        const metaRow = document.createElement("div");
        metaRow.className = "language-module-color-meta";

        const label = document.createElement("label");
        label.className = "language-module-color-label";
        const inputId = `module-theme-${definition.id}-${sliderDef.key}`;
        label.setAttribute("for", inputId);
        label.textContent = translate(
          sliderDef.labelKey,
          null,
          sliderDef.labelFallback
        );

        const value = document.createElement("span");
        value.className = "language-module-color-value";
        value.dataset.themeValueFor = `${definition.id}:${sliderDef.key}`;
        value.textContent = formatThemeValue(sliderDef.key, theme[sliderDef.key]);

        metaRow.appendChild(label);
        metaRow.appendChild(value);
        cell.appendChild(metaRow);

        const input = document.createElement("input");
        input.type = "range";
        input.id = inputId;
        input.className = "language-module-color-range";
        input.dataset.moduleId = definition.id;
        input.dataset.field = sliderDef.field;
        input.dataset.themeKey = sliderDef.key;
        input.min = String(sliderDef.limit && sliderDef.limit.min !== undefined ? sliderDef.limit.min : 0);
        input.max = String(sliderDef.limit && sliderDef.limit.max !== undefined ? sliderDef.limit.max : 100);
        input.step = String(sliderDef.limit && sliderDef.limit.step !== undefined ? sliderDef.limit.step : 1);
        input.value = String(theme[sliderDef.key]);
        cell.appendChild(input);

        grid.appendChild(cell);
      }

      panel.appendChild(grid);
      drawer.appendChild(panel);
      return drawer;
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
      card.dataset.moduleId = definition.id;
      const themeTuningEnabled = supportsThemeTuning(definition);
      if (themeTuningEnabled) {
        card.classList.add("language-module-card-themeable");
      }
      const isDrawerOpen = themeTuningEnabled && openColorDrawerModuleId === definition.id;
      card.classList.toggle("is-color-drawer-open", isDrawerOpen);

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
      const innerWrap = document.createElement("div");
      innerWrap.className = "language-module-inner";
      if (opts.innerContent instanceof HTMLElement) {
        innerWrap.appendChild(opts.innerContent);
      }
      if (opts.innerContent instanceof HTMLElement) {
        main.appendChild(innerWrap);
      }

      const controls = document.createElement("div");
      controls.className = "language-module-controls";
      controls.appendChild(renderEnableToggle(definition, entry));

      card.appendChild(renderDragHandle(definition));
      card.appendChild(main);
      card.appendChild(controls);
      if (themeTuningEnabled) {
        card.appendChild(renderColorTrigger(definition, entry));
        card.appendChild(renderColorDrawer(definition, entry));
        applyThemePreviewToCard(card, resolveEntryTheme(entry));
      }
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
      resetModuleDragState();
      modulesList.textContent = "";
      const language = normalizeLanguage(targetLanguage || resolveTargetLanguage());
      const visibleModules = getVisibleModules(language);
      const orderedCardDefinitions = resolveOrderedCardDefinitions(visibleModules, modulePrefs);
      const visibleModuleIds = new Set(orderedCardDefinitions.map((definition) => String(definition.id || "")));
      if (openColorDrawerModuleId && !visibleModuleIds.has(openColorDrawerModuleId)) {
        openColorDrawerModuleId = "";
      }
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
      for (const definition of orderedCardDefinitions) {
        if (definition.id === "ja-script-forms") {
          modulesList.appendChild(renderJapaneseScriptModule(definition, definitionsById, prefs));
          continue;
        }
        const entry = ensureModuleEntry(prefs, definition.id);
        modulesList.appendChild(renderModuleCard(definition, entry));
      }
      syncOpenColorDrawerDomState();
    }

    function syncOpenColorDrawerDomState() {
      if (!modulesList) {
        return;
      }
      const activeModuleId = String(openColorDrawerModuleId || "").trim();
      const cards = modulesList.querySelectorAll(".language-module-card-themeable");
      cards.forEach((card) => {
        if (!(card instanceof HTMLElement)) {
          return;
        }
        const cardModuleId = String(card.dataset.moduleId || "").trim();
        card.classList.toggle("is-color-drawer-open", Boolean(activeModuleId && cardModuleId === activeModuleId));
      });
      const colorButtons = modulesList.querySelectorAll("button[data-action='toggle-color-drawer']");
      colorButtons.forEach((button) => {
        if (!(button instanceof HTMLButtonElement)) {
          return;
        }
        const buttonModuleId = String(button.dataset.moduleId || "").trim();
        const isOpen = Boolean(activeModuleId && buttonModuleId === activeModuleId);
        button.setAttribute("aria-pressed", isOpen ? "true" : "false");
        button.setAttribute("aria-expanded", isOpen ? "true" : "false");
      });
    }

    function setOpenColorDrawer(moduleId) {
      openColorDrawerModuleId = String(moduleId || "").trim();
      syncOpenColorDrawerDomState();
    }

    function clearDragDomState() {
      if (!modulesList) {
        return;
      }
      modulesList.classList.remove("is-module-dragging");
      const cards = modulesList.querySelectorAll(".language-module-card");
      cards.forEach((card) => {
        if (!(card instanceof HTMLElement)) {
          return;
        }
        card.classList.remove("is-drag-source", "is-drag-over-before", "is-drag-over-after");
      });
    }

    function resetModuleDragState() {
      activeDragModuleId = "";
      clearDragDomState();
    }

    function resolveDragCard(moduleId) {
      if (!modulesList) {
        return null;
      }
      const normalized = String(moduleId || "").trim();
      if (!normalized) {
        return null;
      }
      const node = modulesList.querySelector(
        `.language-module-card[data-module-id="${normalized}"]`
      );
      return node instanceof HTMLElement ? node : null;
    }

    function markDragTarget(card, placement) {
      if (!(card instanceof HTMLElement)) {
        return;
      }
      const normalizedPlacement = placement === "after" ? "after" : "before";
      const cards = modulesList ? modulesList.querySelectorAll(".language-module-card") : [];
      cards.forEach((node) => {
        if (!(node instanceof HTMLElement) || node === card) {
          return;
        }
        node.classList.remove("is-drag-over-before", "is-drag-over-after");
      });
      card.classList.toggle("is-drag-over-before", normalizedPlacement === "before");
      card.classList.toggle("is-drag-over-after", normalizedPlacement === "after");
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

    async function persistModuleOrder(orderIds) {
      if (!settingsManager) {
        return;
      }
      const visibleModules = getVisibleModules(activeTargetLanguage);
      const cardDefinitions = resolveModuleCardDefinitions(visibleModules);
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
      if (target instanceof HTMLInputElement && target.type === "range") {
        persistModuleChange(moduleId, field, target.value).catch(() => {});
        return;
      }
      if (target instanceof HTMLSelectElement) {
        persistModuleChange(moduleId, field, target.value).catch(() => {});
      }
    }

    function handleModulesInput(event) {
      const target = event && event.target;
      if (!(target instanceof HTMLInputElement) || target.type !== "range") {
        return;
      }
      const moduleId = String(target.dataset.moduleId || "").trim();
      const themeKey = String(target.dataset.themeKey || "").trim();
      if (!moduleId || !themeKey || !modulesList) {
        return;
      }
      const valueNode = modulesList.querySelector(
        `[data-theme-value-for="${moduleId}:${themeKey}"]`
      );
      if (valueNode instanceof HTMLElement) {
        valueNode.textContent = formatThemeValue(themeKey, target.value);
      }
      const card = modulesList.querySelector(`.language-module-card[data-module-id="${moduleId}"]`);
      if (card instanceof HTMLElement) {
        const liveTheme = resolveThemeFromCardInputs(moduleId, card);
        applyThemePreviewToCard(card, liveTheme);
      }
    }

    function handleModulesDragStart(event) {
      if (!modulesList) {
        return;
      }
      const dragEvent = typeof DragEvent !== "undefined" && event instanceof DragEvent
        ? event
        : null;
      const eventTarget = dragEvent && dragEvent.target instanceof HTMLElement
        ? dragEvent.target
        : null;
      const handle = eventTarget && typeof eventTarget.closest === "function"
        ? eventTarget.closest(".language-module-drag-handle")
        : null;
      if (!(handle instanceof HTMLElement)) {
        return;
      }
      const moduleId = String(handle.dataset.moduleId || "").trim();
      const card = resolveDragCard(moduleId);
      if (!moduleId || !(card instanceof HTMLElement)) {
        return;
      }
      activeDragModuleId = moduleId;
      modulesList.classList.add("is-module-dragging");
      card.classList.add("is-drag-source");
      if (dragEvent.dataTransfer) {
        dragEvent.dataTransfer.effectAllowed = "move";
        dragEvent.dataTransfer.dropEffect = "move";
        dragEvent.dataTransfer.setData("text/plain", moduleId);
      }
    }

    function handleModulesDragOver(event) {
      if (!modulesList || !activeDragModuleId) {
        return;
      }
      const dragEvent = typeof DragEvent !== "undefined" && event instanceof DragEvent
        ? event
        : null;
      if (!dragEvent) {
        return;
      }
      dragEvent.preventDefault();
      if (dragEvent.dataTransfer) {
        dragEvent.dataTransfer.dropEffect = "move";
      }

      const dragCard = resolveDragCard(activeDragModuleId);
      if (!(dragCard instanceof HTMLElement)) {
        return;
      }
      const eventTarget = dragEvent.target instanceof HTMLElement ? dragEvent.target : null;
      const overCard = eventTarget && typeof eventTarget.closest === "function"
        ? eventTarget.closest(".language-module-card")
        : null;
      if (!(overCard instanceof HTMLElement) || overCard === dragCard) {
        return;
      }
      const rect = overCard.getBoundingClientRect();
      const insertBefore = dragEvent.clientY < (rect.top + rect.height / 2);
      if (insertBefore) {
        modulesList.insertBefore(dragCard, overCard);
      } else {
        modulesList.insertBefore(dragCard, overCard.nextSibling);
      }
      markDragTarget(overCard, insertBefore ? "before" : "after");
    }

    function handleModulesDrop(event) {
      if (!modulesList || !activeDragModuleId) {
        return;
      }
      const dragEvent = typeof DragEvent !== "undefined" && event instanceof DragEvent
        ? event
        : null;
      if (dragEvent) {
        dragEvent.preventDefault();
      }
      const orderedIds = Array.from(
        modulesList.querySelectorAll(".language-module-card[data-module-id]")
      )
        .map((card) => String(card.getAttribute("data-module-id") || "").trim())
        .filter(Boolean);
      resetModuleDragState();
      persistModuleOrder(orderedIds).catch(() => {});
    }

    function handleModulesDragEnd() {
      if (modulesList && activeDragModuleId) {
        const orderedIds = Array.from(
          modulesList.querySelectorAll(".language-module-card[data-module-id]")
        )
          .map((card) => String(card.getAttribute("data-module-id") || "").trim())
          .filter(Boolean);
        resetModuleDragState();
        persistModuleOrder(orderedIds).catch(() => {});
        return;
      }
      resetModuleDragState();
    }

    function handleModulesClick(event) {
      const eventTarget = event && event.target;
      if (!(eventTarget instanceof Node) || !modulesList) {
        return;
      }
      const button = eventTarget instanceof HTMLElement && typeof eventTarget.closest === "function"
        ? eventTarget.closest("button[data-action]")
        : null;
      if (!(button instanceof HTMLButtonElement)) {
        return;
      }
      const action = String(button.dataset.action || "").trim();
      const moduleId = String(button.dataset.moduleId || "").trim();
      if (!action || !moduleId) {
        return;
      }
      if (action === "toggle-enable") {
        const field = String(button.dataset.field || "").trim();
        if (field !== "enabled") {
          return;
        }
        const currentlyEnabled = button.getAttribute("aria-pressed") === "true";
        persistModuleChange(moduleId, "enabled", !currentlyEnabled).catch(() => {});
        return;
      }
      if (action === "toggle-color-drawer") {
        const nextModuleId = openColorDrawerModuleId === moduleId ? "" : moduleId;
        setOpenColorDrawer(nextModuleId);
        return;
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
        lastFocusedElement = document.activeElement instanceof HTMLElement
          ? document.activeElement
          : null;
      }
      isOpen = open === true;
      if (!isOpen) {
        openColorDrawerModuleId = "";
        resetModuleDragState();
      }
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
      modulesList.addEventListener("input", handleModulesInput);
      modulesList.addEventListener("dragstart", handleModulesDragStart);
      modulesList.addEventListener("dragover", handleModulesDragOver);
      modulesList.addEventListener("drop", handleModulesDrop);
      modulesList.addEventListener("dragend", handleModulesDragEnd);
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
