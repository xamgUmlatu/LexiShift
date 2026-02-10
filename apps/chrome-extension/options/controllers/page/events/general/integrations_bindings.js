(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function bind(options) {
    const opts = options && typeof options === "object" ? options : {};
    const ui = opts.ui && typeof opts.ui === "object"
      ? opts.ui
      : {
          LINKS: {
            app: "",
            plugin: ""
          }
        };
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {};
    const openDesktopAppButton = elements.openDesktopAppButton || null;
    const openBdPluginButton = elements.openBdPluginButton || null;

    if (openDesktopAppButton) {
      openDesktopAppButton.addEventListener("click", () => {
        window.open(ui.LINKS.app, "_blank", "noopener");
      });
    }

    if (openBdPluginButton) {
      openBdPluginButton.addEventListener("click", () => {
        window.open(ui.LINKS.plugin, "_blank", "noopener");
      });
    }
  }

  root.optionsEventGeneralIntegrationsBindings = {
    bind
  };
})();
