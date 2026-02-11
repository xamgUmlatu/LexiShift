(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createScanCounters(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getFocusWord = typeof opts.getFocusWord === "function"
      ? opts.getFocusWord
      : ((_settings) => "");

    function buildCounter(currentSettings, options) {
      const localOptions = options && typeof options === "object" ? options : {};
      const detailLimit = Number(localOptions.detailLimit || 0);
      const focusDetailLimit = Number(localOptions.focusDetailLimit || 0);
      return {
        totalNodes: 0,
        emptyNodes: 0,
        whitespaceNodes: 0,
        replacements: 0,
        nodes: 0,
        scanned: 0,
        skippedEditable: 0,
        skippedExcluded: 0,
        skippedLexi: 0,
        skippedCached: 0,
        detailLogs: 0,
        detailLimit,
        detailTruncated: false,
        focusWord: currentSettings.debugEnabled ? getFocusWord(currentSettings) : "",
        focusSubstringNodes: 0,
        focusTokenNodes: 0,
        focusReplaced: 0,
        focusUnmatched: 0,
        focusSkippedEditable: 0,
        focusSkippedExcluded: 0,
        focusSkippedLexi: 0,
        focusSkippedCached: 0,
        focusSubstringNoToken: 0,
        focusDetailLogs: 0,
        focusDetailLimit,
        focusDetailTruncated: false
      };
    }

    function createFullScanCounter(currentSettings) {
      return buildCounter(currentSettings, { detailLimit: 40, focusDetailLimit: 30 });
    }

    function createMutationCounter(currentSettings) {
      return buildCounter(currentSettings, { detailLimit: 20, focusDetailLimit: 15 });
    }

    return {
      createFullScanCounter,
      createMutationCounter
    };
  }

  root.contentDomScanCounters = {
    createScanCounters
  };
})();
