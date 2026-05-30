(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const { copySelectOptions, DEFAULT_STORY_FLOW_PROFICIENCY, formatProficiencyValue, hasExplicitProficiencyValue, matchesStoryContext, normalizeInterestList, readStoryContext, readStoryFlowValues, setProficiencyInput, setSelectValue, syncTopicChips } = root.optionsSrsStoryFlowUtils;

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
    const helperManager = opts.helperManager && typeof opts.helperManager === "object"
      ? opts.helperManager
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
    const resourceOpenButton = elements.resourceOpenButton || null;
    const resourceRetryButton = elements.resourceRetryButton || null;
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
    let openedStoryContext = null;
    const readVisibleValues = () => readStoryFlowValues(elements);

    function setPreviewText(message, color) {
      if (!previewOutput) {
        return;
      }
      previewOutput.textContent = message || "";
      previewOutput.style.color = color || "";
    }

    function currentPair() {
      const source = modalSourceLanguageInput ? String(modalSourceLanguageInput.value || "").trim() : "en";
      const target = modalTargetLanguageInput ? String(modalTargetLanguageInput.value || "").trim() : "es";
      return `${source || "en"}-${target || "es"}`;
    }

    const resourceCheck = root.optionsSrsStoryFlowResourceCheck.createController({
      translate,
      helperManager,
      elements: {
        resourceCheckRoot: elements.resourceCheckRoot,
        resourceMessage: elements.resourceMessage,
        resourceList: elements.resourceList,
        resourceOpenButton: elements.resourceOpenButton
      },
      getCurrentPair: currentPair,
      getProfileId: () => readVisibleValues().profileId,
      setPreviewText,
      colors
    });

    function clearResourceCheck() {
      resourceCheck.clear();
    }

    function handleResourcePreflightBlocked(event) {
      resourceCheck.handlePreflightBlocked(event, isOpen);
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

    function loadFromCurrentStory() {
      openedStoryContext = readStoryContext(elements);
      copySelectOptions(mainProfileIdInput, modalProfileIdInput, "default");
      setSelectValue(modalSourceLanguageInput, mainSourceLanguageInput ? mainSourceLanguageInput.value : "en", "en");
      setSelectValue(modalTargetLanguageInput, mainTargetLanguageInput ? mainTargetLanguageInput.value : "es", "es");
      setSelectValue(modalProfileIdInput, mainProfileIdInput ? mainProfileIdInput.value : "default", "default");
      if (modalProficiencyEstimateInput && mainProficiencyEstimateInput) {
        const hasValue = hasExplicitProficiencyValue(mainProficiencyEstimateInput);
        setProficiencyInput(
          modalProficiencyEstimateInput,
          hasValue ? mainProficiencyEstimateInput.value : DEFAULT_STORY_FLOW_PROFICIENCY,
          true
        );
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
      setModalInterests("");
      setPreviewText("");
      clearResourceCheck();
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

    function writeMainValues(values, optionsArg) {
      const options = optionsArg && typeof optionsArg === "object" ? optionsArg : {};
      const shouldActivateStory = options.activateStory === true;
      const sourceContext = openedStoryContext || readStoryContext(elements);
      setSelectValue(mainSourceLanguageInput, values.sourceLanguage, values.sourceLanguage);
      setSelectValue(mainTargetLanguageInput, values.targetLanguage, values.targetLanguage);
      if (mainSrsEnabledInput) {
        if (shouldActivateStory) {
          mainSrsEnabledInput.checked = true;
        } else {
          mainSrsEnabledInput.checked = sourceContext.srsEnabled && matchesStoryContext(values, sourceContext);
        }
      }
      if (mainProficiencyEstimateInput) {
        const hasValue = String(values.proficiencyEstimate || "").trim() !== "";
        setProficiencyInput(
          mainProficiencyEstimateInput,
          values.proficiencyEstimate || DEFAULT_STORY_FLOW_PROFICIENCY,
          hasValue
        );
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

    async function persistVisibleSettings(optionsArg) {
      const options = optionsArg && typeof optionsArg === "object" ? optionsArg : {};
      const values = readVisibleValues();
      const nextProfileId = String(values.profileId || "default").trim() || "default";
      const currentProfileId = mainProfileIdInput
        ? String(mainProfileIdInput.value || "default").trim() || "default"
        : "default";
      if (mainProfileIdInput && nextProfileId !== currentProfileId) {
        setSelectValue(mainProfileIdInput, nextProfileId, nextProfileId);
        await saveSrsProfileId();
      }
      writeMainValues(values, options);
      await saveLanguageSettings();
      writeMainValues(values, options);
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
        clearResourceCheck();
        await persistVisibleSettings({ activateStory: false });
        if (mainSamplingCurtain) {
          mainSamplingCurtain.open = true;
        }
        await srsActionsController.previewAdmission();
        if (resourceCheck.latestBlock()) {
          setPreviewText(
            translate("status_srs_language_data_check_required", null, "Install the required language data, then retry."),
            colors.ERROR
          );
          return;
        }
        if (previewOutput && mainAdmissionPreviewOutput) {
          const previewHtml = String(mainAdmissionPreviewOutput.innerHTML || "");
          if (previewHtml) {
            previewOutput.innerHTML = previewHtml;
          } else {
            previewOutput.textContent = mainAdmissionPreviewOutput.textContent || "";
          }
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
        clearResourceCheck();
        await persistVisibleSettings({ activateStory: true });
        await srsActionsController.initializeSet();
        if (resourceCheck.latestBlock()) {
          setPreviewText(
            translate("status_srs_language_data_check_required", null, "Install the required language data, then retry."),
            colors.ERROR
          );
          return;
        }
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

    async function openResourceSettings() {
      await resourceCheck.openSettings();
    }

    async function retryResourceCheck() {
      await previewAdmission();
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
      [modalSourceLanguageInput, modalTargetLanguageInput, modalProfileIdInput].forEach((input) => {
        if (input && typeof input.addEventListener === "function") {
          input.addEventListener("change", clearResourceCheck);
        }
      });
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
      if (resourceOpenButton) {
        resourceOpenButton.addEventListener("click", () => {
          openResourceSettings().catch((err) => {
            log("SRS story setup open resource settings failed.", err);
          });
        });
      }
      if (resourceRetryButton) {
        resourceRetryButton.addEventListener("click", () => {
          retryResourceCheck().catch((err) => {
            log("SRS story setup retry data check failed.", err);
          });
        });
      }
      if (globalThis.document && typeof globalThis.document.addEventListener === "function") {
        globalThis.document.addEventListener(
          "lexishift:srs-preflight-blocked",
          handleResourcePreflightBlocked
        );
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
      readVisibleValues,
      handleResourcePreflightBlocked,
      openResourceSettings,
      retryResourceCheck
    };
  }

  root.optionsSrsStoryFlow = {
    createController
  };
})();
