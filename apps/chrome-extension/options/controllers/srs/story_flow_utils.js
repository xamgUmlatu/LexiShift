(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function normalizeInterestList(value) {
    const source = Array.isArray(value) ? value : String(value || "").split(",");
    const seen = new Set();
    return source
      .map((entry) => String(entry || "").trim())
      .filter((entry) => {
        if (!entry || seen.has(entry)) {
          return false;
        }
        seen.add(entry);
        return true;
      });
  }

  function setSelectValue(select, value, fallbackText) {
    if (!select) {
      return;
    }
    const nextValue = String(value || "").trim();
    if (!nextValue) {
      return;
    }
    const options = Array.from(select.options || []);
    if (!options.some((option) => option.value === nextValue)) {
      const option = globalThis.document.createElement("option");
      option.value = nextValue;
      option.textContent = fallbackText || nextValue;
      select.appendChild(option);
    }
    select.value = nextValue;
  }

  function copySelectOptions(source, target, fallbackValue) {
    if (!target) {
      return;
    }
    target.innerHTML = "";
    const options = source ? Array.from(source.options || []) : [];
    options.forEach((option) => {
      target.appendChild(option.cloneNode(true));
    });
    if (!target.options.length && fallbackValue) {
      setSelectValue(target, fallbackValue, fallbackValue);
    }
    const nextValue = source && source.value ? source.value : fallbackValue;
    setSelectValue(target, nextValue, nextValue);
  }

  const hasExplicitProficiencyValue = (input) => !(
    input && input.type === "range" && (input.dataset || {}).srsHasValue === "false"
  );

  function formatProficiencyValue(value, hasValue) {
    if (!hasValue) {
      return "Not set";
    }
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return "Not set";
    }
    return `${Math.round(Math.min(100, Math.max(0, numeric)))}%`;
  }

  function setProficiencyInput(input, value, hasValue) {
    if (!input) {
      return;
    }
    if (!input.dataset) {
      input.dataset = {};
    }
    input.value = hasValue ? String(value || "50") : "50";
    input.dataset.srsHasValue = hasValue ? "true" : "false";
  }

  function syncTopicChips(buttons, interests) {
    const selected = new Set(normalizeInterestList(interests));
    buttons.forEach((button) => {
      const topic = String(
        button.getAttribute("data-srs-story-topic-interest")
          || button.getAttribute("data-srs-topic-interest")
          || ""
      ).trim();
      const isSelected = Boolean(topic && selected.has(topic));
      if (button.classList && typeof button.classList.toggle === "function") {
        button.classList.toggle("is-selected", isSelected);
      }
      if (typeof button.setAttribute === "function") {
        button.setAttribute("aria-pressed", isSelected ? "true" : "false");
      }
    });
  }

  root.optionsSrsStoryFlowUtils = {
    copySelectOptions,
    formatProficiencyValue,
    hasExplicitProficiencyValue,
    normalizeInterestList,
    setProficiencyInput,
    setSelectValue,
    syncTopicChips
  };
})();
