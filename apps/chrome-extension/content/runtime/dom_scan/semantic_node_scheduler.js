(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const DEFAULT_SEMANTIC_SCAN_NODE_BATCH_SIZE = 96;
  const MAX_SEMANTIC_SCAN_NODE_BATCH_SIZE = 128;

  function resolveSemanticScanNodeBatchSize(settings, concurrent) {
    if (!concurrent) {
      return 1;
    }
    const parsed = Number.parseInt(settings && settings.debugSemanticScanNodeBatchSize, 10);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      return DEFAULT_SEMANTIC_SCAN_NODE_BATCH_SIZE;
    }
    return Math.min(MAX_SEMANTIC_SCAN_NODE_BATCH_SIZE, Math.max(1, parsed));
  }

  async function processTextNodes(options) {
    const opts = options && typeof options === "object" ? options : {};
    const list = Array.isArray(opts.nodes) ? opts.nodes : [];
    const textNodeProcessor = opts.textNodeProcessor || {};
    const pageBudgetState = opts.pageBudgetState || null;
    const semanticBatchable = Boolean(
      opts.semanticGateRuntime
      && opts.settings
      && opts.settings.srsSemanticAdmissionEnabled === true
    );
    const budgetedSemanticPreflight = Boolean(
      semanticBatchable
      && pageBudgetState
      && typeof textNodeProcessor.preflightSemanticTextNode === "function"
    );
    const concurrent = Boolean(semanticBatchable && (!pageBudgetState || budgetedSemanticPreflight));
    const batchSize = resolveSemanticScanNodeBatchSize(opts.settings, concurrent);
    let deadlineMs = opts.deadlineMs;
    for (let index = 0; index < list.length; index += batchSize) {
      const batch = list.slice(index, index + batchSize);
      if (semanticBatchable && typeof opts.recordScanNodeBatch === "function") {
        opts.recordScanNodeBatch(
          opts.counter,
          batch.length,
          concurrent,
          pageBudgetState ? "page_budget" : "serial"
        );
      }
      if (concurrent && pageBudgetState && budgetedSemanticPreflight) {
        const preflightOptions = { semanticPreflightBudget: {
          maxTotal: pageBudgetState.maxTotal,
          maxPerLemma: pageBudgetState.maxPerLemma,
          maxPerSentence: pageBudgetState.maxPerSentence,
          usedTotal: pageBudgetState.usedTotal,
          usedByLemma: { ...(pageBudgetState.usedByLemma || {}) },
          usedBySentence: { ...(pageBudgetState.usedBySentence || {}) }
        } };
        const preflightResults = await Promise.all(
          batch.map((node) => textNodeProcessor.preflightSemanticTextNode(node, opts.counter, preflightOptions))
        );
        for (let batchIndex = 0; batchIndex < batch.length; batchIndex += 1) {
          const preflightResult = preflightResults[batchIndex];
          const semanticResultOverride = preflightResult && preflightResult.semanticResultOverride
            ? preflightResult.semanticResultOverride
            : null;
          await textNodeProcessor.processTextNode(batch[batchIndex], opts.counter, { semanticResultOverride });
        }
      } else if (concurrent) {
        await Promise.all(batch.map((node) => textNodeProcessor.processTextNode(node, opts.counter)));
      } else {
        await textNodeProcessor.processTextNode(batch[0], opts.counter);
      }
      if (typeof opts.maybeYieldDuringScan === "function") {
        deadlineMs = await opts.maybeYieldDuringScan(
          opts.counter,
          deadlineMs,
          index + batch.length < list.length,
          opts.nowMs,
          opts.yieldToPage
        );
      }
    }
    return deadlineMs;
  }

  root.contentDomScanSemanticNodeScheduler = {
    processTextNodes
  };
})();
