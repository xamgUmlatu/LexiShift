(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const onVisibleChange = typeof opts.onVisibleChange === "function"
      ? opts.onVisibleChange
      : (() => {});
    const busyBackdrop = elements.busyBackdrop || null;
    const busyMessage = elements.busyMessage || null;
    const closeButton = elements.closeButton || null;
    let visible = false;

    function defaultMessage() {
      return translate(
        "status_srs_story_flow_initializing",
        null,
        "Saving settings and starting Vocabulary Practice…"
      );
    }

    function setVisible(isVisible, message) {
      visible = isVisible === true;
      if (busyMessage) {
        busyMessage.textContent = message || defaultMessage();
      }
      if (busyBackdrop) {
        busyBackdrop.classList.toggle("hidden", !visible);
        busyBackdrop.setAttribute("aria-hidden", visible ? "false" : "true");
      }
      if (closeButton) {
        closeButton.disabled = visible;
      }
      onVisibleChange(visible);
    }

    function isVisible() {
      return visible;
    }

    return {
      setVisible,
      isVisible
    };
  }

  root.optionsSrsStoryFlowBusyOverlay = {
    createController
  };
})();
