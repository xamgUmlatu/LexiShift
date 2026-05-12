(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createRuntime(options) {
    const opts = options && typeof options === "object" ? options : {};
    const requestContextModule = root.contentSemanticRequestContext || {};
    const summaryModule = root.contentSemanticGateSummary || {};
    const batchModule = root.contentSemanticGateBatch || {};
    const createAdmitter = typeof batchModule.createAdmitter === "function"
      ? batchModule.createAdmitter
      : null;
    if (!createAdmitter) {
      return {
        admitContextBatch: async (contexts) => (Array.isArray(contexts) ? contexts : []).map((context) => ({
          matches: Array.isArray(context && context.matches) ? context.matches : [],
          decisionMap: new Map(),
          summary: null
        })),
        admitMatches: async (context) => ({
          matches: Array.isArray(context && context.matches) ? context.matches : [],
          decisionMap: new Map(),
          summary: null
        })
      };
    }
    return createAdmitter({
      ...opts,
      createRequestMatch: requestContextModule.createRequestMatch,
      createSummary: summaryModule.createSummary,
      finalizeSummary: summaryModule.finalizeSummary,
      summarizeHelperBatch: summaryModule.summarizeHelperBatch,
      summarizeInventoryLookup: summaryModule.summarizeInventoryLookup,
      summarizeDecision: summaryModule.summarizeDecision
    });
  }

  root.contentSemanticGateRuntime = {
    createRuntime
  };
})();
