(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const LEXISHIFT_SCAN_SKIP_SELECTOR = ".lexishift-replacement, [data-lexishift-scan-skip=\"true\"]";

  function createNodeFilters() {
    function isEditable(node) {
      if (!node || !node.parentElement) {
        return false;
      }
      const parent = node.parentElement;
      if (parent.isContentEditable) {
        return true;
      }
      const tag = parent.tagName;
      return tag === "INPUT" || tag === "TEXTAREA";
    }

    function isExcluded(node) {
      if (!node || !node.parentElement) {
        return true;
      }
      const tag = node.parentElement.tagName;
      return tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT";
    }

    function isLexiShiftNode(node) {
      if (!node || !node.parentElement) {
        return false;
      }
      return Boolean(node.parentElement.closest(LEXISHIFT_SCAN_SKIP_SELECTOR));
    }

    return {
      isEditable,
      isExcluded,
      isLexiShiftNode
    };
  }

  root.contentDomScanNodeFilters = {
    createNodeFilters
  };
})();
