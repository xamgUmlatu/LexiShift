(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function resolveReloadPage(handler) {
    if (typeof handler === "function") return handler;
    return () => {
      const locationRef = globalThis.location || (globalThis.window && globalThis.window.location);
      if (locationRef && typeof locationRef.reload === "function") locationRef.reload();
    };
  }

  function createInitializer(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    const colors = opts.colors && typeof opts.colors === "object"
      ? opts.colors
      : { SUCCESS: "#3c5a2a", ERROR: "#b42318", DEFAULT: "#6c675f" };
    const initializeSet = typeof opts.initializeSet === "function" ? opts.initializeSet : null;
    const setActionBusy = typeof opts.setActionBusy === "function" ? opts.setActionBusy : (() => {});
    const setPreviewText = typeof opts.setPreviewText === "function" ? opts.setPreviewText : (() => {});
    const clearResourceCheck = typeof opts.clearResourceCheck === "function" ? opts.clearResourceCheck : (() => {});
    const persistVisibleSettings = typeof opts.persistVisibleSettings === "function"
      ? opts.persistVisibleSettings
      : (() => Promise.resolve());
    const hasResourceBlock = typeof opts.hasResourceBlock === "function" ? opts.hasResourceBlock : (() => false);
    const showDashboard = typeof opts.showDashboard === "function" ? opts.showDashboard : (() => {});
    const setStatus = typeof opts.setStatus === "function" ? opts.setStatus : (() => {});
    const close = typeof opts.close === "function" ? opts.close : (() => {});
    const reloadPage = resolveReloadPage(opts.reloadPage);
    const busyOverlay = opts.busyOverlay && typeof opts.busyOverlay === "object"
      ? opts.busyOverlay
      : { setVisible: () => {} };

    return async function initializeStory() {
      if (!initializeSet) return;
      const initializingMessage = translate("status_srs_story_flow_initializing", null, "Saving settings and starting Vocabulary Practice…");
      let shouldReload = false;
      setActionBusy(true);
      busyOverlay.setVisible(true, initializingMessage);
      setPreviewText(initializingMessage, colors.DEFAULT);
      try {
        clearResourceCheck();
        await persistVisibleSettings({ activateStory: true });
        await initializeSet();
        if (hasResourceBlock()) {
          setPreviewText(
            translate("status_srs_language_data_check_required", null, "Install the required language data, then retry."),
            colors.ERROR
          );
          return;
        }
        showDashboard();
        setStatus(translate("status_srs_story_flow_initialized", null, "Vocabulary Practice started."), colors.SUCCESS);
        close();
        shouldReload = true;
      } catch (err) {
        const message = err && err.message
          ? err.message
          : translate("status_srs_set_init_failed", null, "Practice setup failed.");
        setPreviewText(message, colors.ERROR);
        throw err;
      } finally {
        busyOverlay.setVisible(false);
        setActionBusy(false);
      }
      if (shouldReload) reloadPage();
    };
  }

  root.optionsSrsStoryFlowInitializer = {
    createInitializer
  };
})();
