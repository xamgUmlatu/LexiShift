(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRegistry(options) {
    const opts = options && typeof options === "object" ? options : {};
    const modules = Array.isArray(opts.modules) ? opts.modules : [];
    const descriptors = modules
      .filter((moduleDef) => moduleDef && typeof moduleDef === "object")
      .map((moduleDef) => {
        const id = String(moduleDef.id || "").trim();
        const build = typeof moduleDef.build === "function" ? moduleDef.build : null;
        return { id, build };
      })
      .filter((moduleDef) => moduleDef.id && moduleDef.build);

    function isDomNode(value) {
      if (typeof Node === "undefined") {
        return false;
      }
      return value instanceof Node;
    }

    function buildModules(target, debugLog) {
      const log = typeof debugLog === "function" ? debugLog : (() => {});
      const rendered = [];
      for (const descriptor of descriptors) {
        try {
          const node = descriptor.build(target, log);
          if (!isDomNode(node)) {
            continue;
          }
          rendered.push({ id: descriptor.id, node });
        } catch (error) {
          log("Popup module build failed.", {
            moduleId: descriptor.id,
            error: error && error.message ? error.message : "Unknown error"
          });
        }
      }
      return rendered;
    }

    return {
      buildModules
    };
  }

  root.uiPopupModuleRegistry = {
    createRegistry
  };
})();
