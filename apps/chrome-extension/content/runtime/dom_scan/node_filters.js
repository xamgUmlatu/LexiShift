(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

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
      return Boolean(node.parentElement.closest(".lexishift-replacement"));
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
