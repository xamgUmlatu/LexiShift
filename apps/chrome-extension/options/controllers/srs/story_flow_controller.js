(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function normalizeInterestList(value) {
    const source = Array.isArray(value)
      ? value
      : String(value || "").split(",");
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

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const saveLanguageSettings = typeof opts.saveLanguageSettings === "function"
      ? opts.saveLanguageSettings
      : (() => Promise.resolve());
    const saveSrsSettings = typeof opts.saveSrsSettings === "function"
      ? opts.saveSrsSettings
      : (() => Promise.resolve());
    const saveSrsProfileId = typeof opts.saveSrsProfileId === "function"
      ? opts.saveSrsProfileId
      : (() => Promise.resolve());
    const srsActionsController = opts.srsActionsController && typeof opts.srsActionsController === "object"
      ? opts.srsActionsController
      : null;
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : {
          SUCCESS: "#3c5a2a",
          ERROR: "#b42318",
          DEFAULT: "#6c675f"
        };
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const startButton = elements.startButton || null;
    const backdrop = elements.backdrop || null;
    const modalRoot = elements.root || null;
    const closeButton = elements.closeButton || null;
    const modalSourceLanguageInput = elements.modalSourceLanguageInput || null;
    const modalTargetLanguageInput = elements.modalTargetLanguageInput || null;
    const modalProfileIdInput = elements.modalProfileIdInput || null;
    const modalProficiencyEstimateInput = elements.modalProficiencyEstimateInput || null;
    const modalProficiencyEstimateValueOutput = elements.modalProficiencyEstimateValueOutput || null;
    const modalTopicInterestsInput = elements.modalTopicInterestsInput || null;
    const modalTopicInterestChipButtons = Array.isArray(elements.modalTopicInterestChipButtons)
      ? elements.modalTopicInterestChipButtons
      : [];
    const modalMaxActiveInput = elements.modalMaxActiveInput || null;
    const modalBootstrapTopNInput = elements.modalBootstrapTopNInput || null;
    const modalInitialActiveCountInput = elements.modalInitialActiveCountInput || null;
    const sampleButton = elements.sampleButton || null;
    const initializeButton = elements.initializeButton || null;
    const previewOutput = elements.previewOutput || null;
    const mainSourceLanguageInput = elements.mainSourceLanguageInput || null;
    const mainTargetLanguageInput = elements.mainTargetLanguageInput || null;
    const mainProfileIdInput = elements.mainProfileIdInput || null;
    const mainSrsEnabledInput = elements.mainSrsEnabledInput || null;
    const mainProficiencyEstimateInput = elements.mainProficiencyEstimateInput || null;
    const mainTopicInterestsInput = elements.mainTopicInterestsInput || null;
    const mainTopicInterestChipButtons = Array.isArray(elements.mainTopicInterestChipButtons)
      ? elements.mainTopicInterestChipButtons
      : [];
    const mainMaxActiveInput = elements.mainMaxActiveInput || null;
    const mainBootstrapTopNInput = elements.mainBootstrapTopNInput || null;
    const mainInitialActiveCountInput = elements.mainInitialActiveCountInput || null;
    const mainSamplingCurtain = elements.mainSamplingCurtain || null;
    const mainDashboardCurtain = elements.mainDashboardCurtain || null;
    const mainAdmissionPreviewOutput = elements.mainAdmissionPreviewOutput || null;

    let bound = false;
    let isOpen = false;

    function setPreviewText(message, color) {
      if (!previewOutput) {
        return;
      }
      previewOutput.textContent = message || "";
      previewOutput.style.color = color || "";
    }

    const hasExplicitProficiencyValue = (input) => !(input && input.type === "range" && (input.dataset || {}).srsHasValue === "false");

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

    function updateModalProficiencyOutput() {
      if (!modalProficiencyEstimateInput || !modalProficiencyEstimateValueOutput) {
        return;
      }
      modalProficiencyEstimateValueOutput.textContent = formatProficiencyValue(
        modalProficiencyEstimateInput.value,
        hasExplicitProficiencyValue(modalProficiencyEstimateInput)
      );
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

    function setModalInterests(interests) {
      const normalized = normalizeInterestList(interests);
      if (modalTopicInterestsInput) {
        modalTopicInterestsInput.value = normalized.join(", ");
      }
      syncTopicChips(modalTopicInterestChipButtons, normalized);
    }

    function setMainInterests(interests) {
      const normalized = normalizeInterestList(interests);
      if (mainTopicInterestsInput) {
        mainTopicInterestsInput.value = normalized.join(", ");
      }
      syncTopicChips(mainTopicInterestChipButtons, normalized);
    }

    function readVisibleValues() {
      return {
        sourceLanguage: modalSourceLanguageInput ? modalSourceLanguageInput.value : "",
        targetLanguage: modalTargetLanguageInput ? modalTargetLanguageInput.value : "",
        profileId: modalProfileIdInput ? modalProfileIdInput.value : "",
        proficiencyEstimate: (
          modalProficiencyEstimateInput && hasExplicitProficiencyValue(modalProficiencyEstimateInput)
        )
          ? modalProficiencyEstimateInput.value
          : "",
        interests: normalizeInterestList(modalTopicInterestsInput ? modalTopicInterestsInput.value : ""),
        maxActive: modalMaxActiveInput ? modalMaxActiveInput.value : "",
        bootstrapTopN: modalBootstrapTopNInput ? modalBootstrapTopNInput.value : "",
        initialActiveCount: modalInitialActiveCountInput ? modalInitialActiveCountInput.value : ""
      };
    }

    function loadFromCurrentStory() {
      copySelectOptions(mainProfileIdInput, modalProfileIdInput, "default");
      setSelectValue(modalSourceLanguageInput, mainSourceLanguageInput ? mainSourceLanguageInput.value : "en", "en");
      setSelectValue(modalTargetLanguageInput, mainTargetLanguageInput ? mainTargetLanguageInput.value : "es", "es");
      setSelectValue(modalProfileIdInput, mainProfileIdInput ? mainProfileIdInput.value : "default", "default");
      if (modalProficiencyEstimateInput && mainProficiencyEstimateInput) {
        const hasValue = hasExplicitProficiencyValue(mainProficiencyEstimateInput);
        setProficiencyInput(modalProficiencyEstimateInput, mainProficiencyEstimateInput.value || "50", hasValue);
      }
      updateModalProficiencyOutput();
      if (modalMaxActiveInput && mainMaxActiveInput) {
        modalMaxActiveInput.value = mainMaxActiveInput.value || "";
      }
      if (modalBootstrapTopNInput && mainBootstrapTopNInput) {
        modalBootstrapTopNInput.value = mainBootstrapTopNInput.value || "";
      }
      if (modalInitialActiveCountInput && mainInitialActiveCountInput) {
        modalInitialActiveCountInput.value = mainInitialActiveCountInput.value || "";
      }
      setModalInterests(mainTopicInterestsInput ? mainTopicInterestsInput.value : "");
      setPreviewText("");
    }

    function setOpen(nextOpen) {
      if (!backdrop || !modalRoot) {
        return;
      }
      isOpen = nextOpen === true;
      backdrop.classList.toggle("hidden", !isOpen);
      backdrop.setAttribute("aria-hidden", isOpen ? "false" : "true");
      if (globalThis.document && globalThis.document.body) {
        globalThis.document.body.classList.toggle("modal-open", isOpen);
      }
      if (isOpen && typeof modalRoot.focus === "function") {
        modalRoot.focus();
      }
    }

    function open() {
      loadFromCurrentStory();
      setOpen(true);
    }

    function close() {
      setOpen(false);
    }

    function writeMainValues(values) {
      setSelectValue(mainSourceLanguageInput, values.sourceLanguage, values.sourceLanguage);
      setSelectValue(mainTargetLanguageInput, values.targetLanguage, values.targetLanguage);
      if (mainSrsEnabledInput) {
        mainSrsEnabledInput.checked = true;
      }
      if (mainProficiencyEstimateInput) {
        const hasValue = String(values.proficiencyEstimate || "").trim() !== "";
        setProficiencyInput(mainProficiencyEstimateInput, values.proficiencyEstimate || "50", hasValue);
      }
      if (mainMaxActiveInput) {
        mainMaxActiveInput.value = values.maxActive;
      }
      if (mainBootstrapTopNInput) {
        mainBootstrapTopNInput.value = values.bootstrapTopN;
      }
      if (mainInitialActiveCountInput) {
        mainInitialActiveCountInput.value = values.initialActiveCount;
      }
      setMainInterests(values.interests);
    }

    async function persistVisibleSettings() {
      const values = readVisibleValues();
      const nextProfileId = String(values.profileId || "default").trim() || "default";
      const currentProfileId = mainProfileIdInput
        ? String(mainProfileIdInput.value || "default").trim() || "default"
        : "default";
      if (mainProfileIdInput && nextProfileId !== currentProfileId) {
        setSelectValue(mainProfileIdInput, nextProfileId, nextProfileId);
        await saveSrsProfileId();
      }
      writeMainValues(values);
      await saveLanguageSettings();
      writeMainValues(values);
      await saveSrsSettings();
      return values;
    }

    function setActionBusy(isBusy) {
      [sampleButton, initializeButton].forEach((button) => {
        if (button) {
          button.disabled = isBusy;
        }
      });
    }

    async function previewAdmission() {
      if (!srsActionsController || typeof srsActionsController.previewAdmission !== "function") {
        return;
      }
      setActionBusy(true);
      setPreviewText(
        translate("status_srs_story_flow_previewing", null, "Saving settings and sampling possible words…"),
        colors.DEFAULT
      );
      try {
        await persistVisibleSettings();
        if (mainSamplingCurtain) {
          mainSamplingCurtain.open = true;
        }
        await srsActionsController.previewAdmission();
        if (previewOutput && mainAdmissionPreviewOutput) {
          previewOutput.textContent = mainAdmissionPreviewOutput.textContent || "";
          previewOutput.style.color = "";
        }
        setStatus(translate("status_srs_story_flow_sampled", null, "Sample updated."), colors.SUCCESS);
      } catch (err) {
        const message = err && err.message
          ? err.message
          : translate("status_srs_admission_preview_failed", null, "Word sample failed.");
        setPreviewText(message, colors.ERROR);
        throw err;
      } finally {
        setActionBusy(false);
      }
    }

    async function initializeStory() {
      if (!srsActionsController || typeof srsActionsController.initializeSet !== "function") {
        return;
      }
      setActionBusy(true);
      setPreviewText(
        translate("status_srs_story_flow_initializing", null, "Saving settings and initializing SRS story…"),
        colors.DEFAULT
      );
      try {
        await persistVisibleSettings();
        await srsActionsController.initializeSet();
        if (mainDashboardCurtain) {
          mainDashboardCurtain.open = true;
        }
        setStatus(translate("status_srs_story_flow_initialized", null, "SRS story initialized."), colors.SUCCESS);
        close();
      } catch (err) {
        const message = err && err.message
          ? err.message
          : translate("status_srs_set_init_failed", null, "Story setup failed.");
        setPreviewText(message, colors.ERROR);
        throw err;
      } finally {
        setActionBusy(false);
      }
    }

    function toggleModalTopic(button) {
      const topic = String(button.getAttribute("data-srs-story-topic-interest") || "").trim();
      if (!topic) {
        return;
      }
      const interests = normalizeInterestList(modalTopicInterestsInput ? modalTopicInterestsInput.value : "");
      const nextInterests = interests.includes(topic)
        ? interests.filter((entry) => entry !== topic)
        : [...interests, topic];
      setModalInterests(nextInterests);
    }

    function bind() {
      if (bound) {
        return;
      }
      bound = true;
      if (startButton) {
        startButton.addEventListener("click", open);
      }
      if (closeButton) {
        closeButton.addEventListener("click", close);
      }
      if (backdrop) {
        backdrop.addEventListener("click", (event) => {
          if (event.target === backdrop) {
            close();
          }
        });
      }
      if (modalTopicInterestsInput) {
        modalTopicInterestsInput.addEventListener("input", () => {
          syncTopicChips(modalTopicInterestChipButtons, modalTopicInterestsInput.value);
        });
      }
      if (modalProficiencyEstimateInput) {
        modalProficiencyEstimateInput.addEventListener("input", () => {
          setProficiencyInput(modalProficiencyEstimateInput, modalProficiencyEstimateInput.value, true);
          updateModalProficiencyOutput();
        });
      }
      updateModalProficiencyOutput();
      modalTopicInterestChipButtons.forEach((button) => {
        button.addEventListener("click", () => {
          toggleModalTopic(button);
        });
      });
      if (sampleButton) {
        sampleButton.addEventListener("click", () => {
          previewAdmission().catch((err) => {
            log("SRS story setup sampling failed.", err);
          });
        });
      }
      if (initializeButton) {
        initializeButton.addEventListener("click", () => {
          initializeStory().catch((err) => {
            log("SRS story setup initialize failed.", err);
          });
        });
      }
      if (globalThis.document && typeof globalThis.document.addEventListener === "function") {
        globalThis.document.addEventListener("keydown", (event) => {
          if (isOpen && event.key === "Escape") {
            close();
          }
        });
      }
    }

    return {
      bind,
      open,
      close,
      persistVisibleSettings,
      previewAdmission,
      initializeStory,
      readVisibleValues
    };
  }

  root.optionsSrsStoryFlow = {
    createController
  };
})();
