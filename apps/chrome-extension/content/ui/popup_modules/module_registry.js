(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRegistry(options) {
    const opts = options && typeof options === "object" ? options : {};
    const resolveModules = typeof opts.resolveModules === "function"
      ? opts.resolveModules
      : null;

    function normalizeDescriptors(modules) {
      const list = Array.isArray(modules) ? modules : [];
      return list
      .filter((moduleDef) => moduleDef && typeof moduleDef === "object")
      .map((moduleDef) => {
        const id = String(moduleDef.id || "").trim();
        const build = typeof moduleDef.build === "function" ? moduleDef.build : null;
        return { id, build };
      })
      .filter((moduleDef) => moduleDef.id && moduleDef.build);
    }

    const modules = Array.isArray(opts.modules) ? opts.modules : [];
    const descriptors = normalizeDescriptors(modules);

    function isDomNode(value) {
      if (typeof Node === "undefined") {
        return false;
      }
      return value instanceof Node;
    }

    function buildModules(target, debugLog) {
      const log = typeof debugLog === "function" ? debugLog : (() => {});
      let activeDescriptors = descriptors;
      if (resolveModules) {
        try {
          activeDescriptors = normalizeDescriptors(resolveModules());
        } catch (error) {
          log("Popup module descriptor resolution failed.", {
            error: error && error.message ? error.message : "Unknown error"
          });
          activeDescriptors = descriptors;
        }
      }
      const rendered = [];
      for (const descriptor of activeDescriptors) {
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
