(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const LEXISHIFT_SCAN_SKIP_SELECTOR = ".lexishift-replacement, [data-lexishift-scan-skip=\"true\"]";
  const EXCLUDED_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE"]);

  function getComputedStyleSafe(element) {
    if (!element || typeof globalThis.getComputedStyle !== "function") {
      return null;
    }
    try {
      return globalThis.getComputedStyle(element);
    } catch (_error) {
      return null;
    }
  }

  function isInsideNonRenderedSubtree(node) {
    const elementNode = node && Number(node.nodeType) === 1 ? node : null;
    const parent = elementNode || (node && node.parentElement ? node.parentElement : null);
    if (!parent) {
      return false;
    }
    const parentStyle = getComputedStyleSafe(parent);
    const parentVisibility = String(parentStyle && parentStyle.visibility || "").trim().toLowerCase();
    if (parentVisibility === "hidden" || parentVisibility === "collapse") {
      return true;
    }
    let element = parent;
    while (element) {
      if (EXCLUDED_TAGS.has(String(element.tagName || "").trim().toUpperCase())) {
        return true;
      }
      if (element.hidden === true) {
        return true;
      }
      const style = getComputedStyleSafe(element);
      const display = String(style && style.display || "").trim().toLowerCase();
      const contentVisibility = String(style && style.contentVisibility || "").trim().toLowerCase();
      if (display === "none" || contentVisibility === "hidden") {
        return true;
      }
      element = element.parentElement || null;
    }
    return false;
  }

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
      return isInsideNonRenderedSubtree(node);
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
      isLexiShiftNode,
      isInsideNonRenderedSubtree
    };
  }

  root.contentDomScanNodeFilters = {
    createNodeFilters
  };
})();
