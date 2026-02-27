(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRenderer(options = {}) {
    const modulesList = options.modulesList || null;
    const translate = typeof options.translate === "function"
      ? options.translate
      : ((key, _subs, fallback) => String(fallback || key || ""));
    const normalizeLanguage = typeof options.normalizeLanguage === "function"
      ? options.normalizeLanguage
      : (value) => String(value || "").trim().toLowerCase();
    const resolveTargetLanguage = typeof options.resolveTargetLanguage === "function"
      ? options.resolveTargetLanguage
      : (() => "en");
    const getVisibleModules = typeof options.getVisibleModules === "function"
      ? options.getVisibleModules
      : (() => []);
    const cloneModulePrefs = typeof options.cloneModulePrefs === "function"
      ? options.cloneModulePrefs
      : (modulePrefs) => (modulePrefs && typeof modulePrefs === "object" ? { ...modulePrefs } : { byId: {} });
    const ensureModuleEntry = typeof options.ensureModuleEntry === "function"
      ? options.ensureModuleEntry
      : (() => ({ enabled: true }));
    const resolveOrderedCardDefinitions = typeof options.resolveOrderedCardDefinitions === "function"
      ? options.resolveOrderedCardDefinitions
      : (() => []);
    const getModuleLabel = typeof options.getModuleLabel === "function"
      ? options.getModuleLabel
      : (definition) => String(definition && definition.id || "");
    const getModuleDescription = typeof options.getModuleDescription === "function"
      ? options.getModuleDescription
      : (() => "");
    const getToggleStateLabel = typeof options.getToggleStateLabel === "function"
      ? options.getToggleStateLabel
      : (enabled) => (enabled ? "On" : "Off");
    const supportsThemeTuning = typeof options.supportsThemeTuning === "function"
      ? options.supportsThemeTuning
      : (() => false);
    const getThemeSliderDefinitions = typeof options.getThemeSliderDefinitions === "function"
      ? options.getThemeSliderDefinitions
      : (() => []);
    const formatThemeValue = typeof options.formatThemeValue === "function"
      ? options.formatThemeValue
      : (_key, value) => String(value || "");
    const resolveEntryTheme = typeof options.resolveEntryTheme === "function"
      ? options.resolveEntryTheme
      : (() => ({}));
    const buildThemePreviewFilter = typeof options.buildThemePreviewFilter === "function"
      ? options.buildThemePreviewFilter
      : (() => "");
    const applyThemePreviewToCard = typeof options.applyThemePreviewToCard === "function"
      ? options.applyThemePreviewToCard
      : (() => {});
    const getOpenColorDrawerModuleId = typeof options.getOpenColorDrawerModuleId === "function"
      ? options.getOpenColorDrawerModuleId
      : (() => "");
    const setOpenColorDrawerModuleId = typeof options.setOpenColorDrawerModuleId === "function"
      ? options.setOpenColorDrawerModuleId
      : (() => {});
    const resetModuleDragState = typeof options.resetModuleDragState === "function"
      ? options.resetModuleDragState
      : (() => {});

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
      const isOpen = getOpenColorDrawerModuleId() === definition.id;
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

    function renderModuleCard(definition, entry, options = {}) {
      const card = document.createElement("div");
      card.className = "language-module-card";
      card.dataset.moduleId = definition.id;
      const themeTuningEnabled = supportsThemeTuning(definition);
      if (themeTuningEnabled) {
        card.classList.add("language-module-card-themeable");
      }
      const isDrawerOpen = themeTuningEnabled && getOpenColorDrawerModuleId() === definition.id;
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
      if (options.innerContent instanceof HTMLElement) {
        innerWrap.appendChild(options.innerContent);
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

    function syncOpenColorDrawerDomState() {
      if (!modulesList) {
        return;
      }
      const activeModuleId = String(getOpenColorDrawerModuleId() || "").trim();
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
      if (getOpenColorDrawerModuleId() && !visibleModuleIds.has(getOpenColorDrawerModuleId())) {
        setOpenColorDrawerModuleId("");
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

    return {
      renderModuleControls,
      syncOpenColorDrawerDomState
    };
  }

  root.optionsTargetLanguageModalRenderer = {
    createRenderer
  };
})();
