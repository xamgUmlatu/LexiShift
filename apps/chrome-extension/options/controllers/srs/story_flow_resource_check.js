(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function resourceKind(entry) {
    const rawType = entry && entry.type ? String(entry.type) : "unknown";
    if (rawType === "set_source_db" || rawType === "frequency_pack") {
      return "frequency";
    }
    if (
      rawType === "translation_dict"
      || rawType === "translation_dictionary"
      || rawType === "translation_dict_path"
      || rawType === "translation_pack_path"
    ) {
      return "translation";
    }
    if (rawType === "jmdict" || rawType === "jmdict_path") {
      return "jmdict";
    }
    return "unknown";
  }

  function formatResourceType(entry, pair, translate) {
    const kind = resourceKind(entry);
    const normalizedPair = String(pair || "").trim().toLowerCase();
    if (normalizedPair === "en-es") {
      if (kind === "frequency") return "Spanish word frequency data";
      if (kind === "translation") return "Spanish-English dictionary";
    }
    if (kind === "frequency") {
      return translate("label_srs_frequency_data", null, "Word frequency data");
    }
    if (kind === "translation") {
      return translate("label_srs_translation_dictionary", null, "Translation dictionary");
    }
    if (kind === "jmdict") {
      return translate("label_srs_jmdict_data", null, "Japanese-English dictionary");
    }
    return translate("label_srs_language_resource", null, "Language data");
  }

  function displayMissingInputs(missingInputs) {
    const seen = new Set();
    const result = [];
    missingInputs.forEach((entry) => {
      const kind = resourceKind(entry);
      const key = kind === "unknown" && entry && entry.type
        ? String(entry.type)
        : kind;
      if (seen.has(key)) {
        return;
      }
      seen.add(key);
      result.push(entry);
    });
    return result;
  }

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = typeof opts.translate === "function"
      ? opts.translate
      : root.optionsTranslateResolver.resolveTranslate(opts.t);
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
      : null;
    const getCurrentPair = typeof opts.getCurrentPair === "function"
      ? opts.getCurrentPair
      : (() => "en-es");
    const getProfileId = typeof opts.getProfileId === "function"
      ? opts.getProfileId
      : (() => "default");
    const setPreviewText = typeof opts.setPreviewText === "function"
      ? opts.setPreviewText
      : (() => {});
    const colors = opts.colors && typeof opts.colors === "object" ? opts.colors : {};
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const resourceCheckRoot = elements.resourceCheckRoot || null;
    const resourceMessage = elements.resourceMessage || null;
    const resourceList = elements.resourceList || null;
    const resourceOpenButton = elements.resourceOpenButton || null;
    let latestBlock = null;

    function setVisible(isVisible) {
      if (resourceCheckRoot && resourceCheckRoot.classList) {
        resourceCheckRoot.classList.toggle("hidden", isVisible !== true);
      }
    }

    function clear() {
      latestBlock = null;
      setVisible(false);
      if (resourceMessage) {
        resourceMessage.textContent = "";
      }
      if (resourceList) {
        resourceList.innerHTML = "";
      }
    }

    function render(detail) {
      const data = detail && typeof detail === "object" ? detail : {};
      const pair = String(data.pair || "").trim() || "this pair";
      const missingInputs = Array.isArray(data.missingInputs) ? data.missingInputs : [];
      const visibleMissingInputs = displayMissingInputs(missingInputs);
      latestBlock = { ...data, pair, missingInputs };
      if (resourceMessage) {
        resourceMessage.textContent = translate(
          "status_srs_language_data_missing",
          [pair],
          `LexiShift needs language data for ${pair} before it can sample words or start this story.`
        );
      }
      if (resourceList) {
        resourceList.innerHTML = "";
        visibleMissingInputs.forEach((entry) => {
          if (!globalThis.document || typeof globalThis.document.createElement !== "function") {
            return;
          }
          const item = globalThis.document.createElement("li");
          item.textContent = formatResourceType(entry, pair, translate);
          resourceList.appendChild(item);
        });
      }
      setVisible(true);
    }

    function handlePreflightBlocked(event, isOpen) {
      if (!isOpen) {
        return;
      }
      const detail = event && event.detail && typeof event.detail === "object" ? event.detail : {};
      const pair = String(detail.pair || "").trim();
      if (pair && pair !== getCurrentPair()) {
        return;
      }
      render(detail);
    }

    async function openSettings() {
      if (!helperManager || typeof helperManager.openResourceSettings !== "function") {
        setPreviewText(translate("status_helper_missing", null, "Helper unavailable."), colors.ERROR);
        return;
      }
      const block = latestBlock && typeof latestBlock === "object" ? latestBlock : {};
      if (resourceOpenButton) {
        resourceOpenButton.disabled = true;
      }
      if (resourceMessage) {
        resourceMessage.textContent = translate(
          "status_srs_opening_resource_settings",
          null,
          "Opening LexiShift resource settings..."
        );
      }
      try {
        const message = await helperManager.openResourceSettings(getCurrentPair(), {
          profileId: getProfileId() || block.profileId || "default",
          resourceContext: "srs_story_setup",
          missingInputs: block.missingInputs || []
        });
        if (resourceMessage) {
          resourceMessage.textContent = `${message} ${translate(
            "hint_srs_retry_after_data_install",
            null,
            "After installing the required packs, return here and retry the check."
          )}`;
        }
      } finally {
        if (resourceOpenButton) {
          resourceOpenButton.disabled = false;
        }
      }
    }

    return {
      clear,
      handlePreflightBlocked,
      latestBlock: () => latestBlock,
      openSettings
    };
  }

  root.optionsSrsStoryFlowResourceCheck = {
    createController
  };
})();
