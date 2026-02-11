(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createResolver() {
    function requireControllerFactory(moduleKey) {
      const moduleRoot = globalThis.LexiShift && typeof globalThis.LexiShift === "object"
        ? globalThis.LexiShift
        : null;
      const module = moduleRoot && moduleRoot[moduleKey] && typeof moduleRoot[moduleKey] === "object"
        ? moduleRoot[moduleKey]
        : null;
      if (!module || typeof module.createController !== "function") {
        throw new Error(`[LexiShift][Options] Missing required controller module: ${moduleKey}`);
      }
      return module.createController;
    }

    return {
      requireControllerFactory
    };
  }

  root.optionsControllerFactoryResolver = {
    createResolver
  };
})();
