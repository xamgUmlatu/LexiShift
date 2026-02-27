(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createInteractions(options = {}) {
    const modulesList = options.modulesList || null;
    const persistModuleChange = typeof options.persistModuleChange === "function"
      ? options.persistModuleChange
      : (() => Promise.resolve());
    const persistModuleOrder = typeof options.persistModuleOrder === "function"
      ? options.persistModuleOrder
      : (() => Promise.resolve());
    const formatThemeValue = typeof options.formatThemeValue === "function"
      ? options.formatThemeValue
      : (_key, value) => String(value || "");
    const resolveThemeFromCardInputs = typeof options.resolveThemeFromCardInputs === "function"
      ? options.resolveThemeFromCardInputs
      : (() => ({}));
    const applyThemePreviewToCard = typeof options.applyThemePreviewToCard === "function"
      ? options.applyThemePreviewToCard
      : (() => {});
    const getOpenColorDrawerModuleId = typeof options.getOpenColorDrawerModuleId === "function"
      ? options.getOpenColorDrawerModuleId
      : (() => "");
    const setOpenColorDrawer = typeof options.setOpenColorDrawer === "function"
      ? options.setOpenColorDrawer
      : (() => {});

    let activeDragModuleId = "";

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
        const nextModuleId = getOpenColorDrawerModuleId() === moduleId ? "" : moduleId;
        setOpenColorDrawer(nextModuleId);
      }
    }

    return {
      handleModulesChange,
      handleModulesInput,
      handleModulesDragStart,
      handleModulesDragOver,
      handleModulesDrop,
      handleModulesDragEnd,
      handleModulesClick,
      resetModuleDragState
    };
  }

  root.optionsTargetLanguageModalInteractions = {
    createInteractions
  };
})();
