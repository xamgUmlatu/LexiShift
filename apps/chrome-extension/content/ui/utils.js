(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function describeElement(element) {
    if (!element || !element.tagName) {
      return "<unknown>";
    }
    const parts = [];
    let current = element;
    let depth = 0;
    while (current && depth < 3) {
      let label = current.tagName.toLowerCase();
      if (current.id) {
        label += `#${current.id}`;
      }
      const className = current.className && typeof current.className === "string" ? current.className.trim() : "";
      if (className) {
        const classes = className.split(/\s+/).slice(0, 2).join(".");
        if (classes) {
          label += `.${classes}`;
        }
      }
      parts.unshift(label);
      current = current.parentElement;
      depth += 1;
    }
    return parts.join(" > ");
  }

  function shorten(text, maxLength) {
    const value = String(text || "");
    if (!maxLength || value.length <= maxLength) {
      return value;
    }
    return `${value.slice(0, maxLength - 3)}...`;
  }

  function describeCodepoints(text, index, length) {
    const value = String(text || "");
    if (!value) {
      return { snippet: "", codes: [] };
    }
    const safeIndex = Math.max(0, Number.isFinite(index) ? index : 0);
    const safeLength = Math.max(1, Number.isFinite(length) ? length : 1);
    const start = Math.max(0, safeIndex - 6);
    const end = Math.min(value.length, safeIndex + safeLength + 6);
    const snippet = value.slice(start, end);
    const codes = Array.from(snippet).map((ch) => {
      const hex = ch.codePointAt(0).toString(16).toUpperCase();
      return `${ch} U+${hex}`;
    });
    return { snippet, codes };
  }

  function countOccurrences(haystack, needle) {
    if (!needle) {
      return 0;
    }
    let count = 0;
    let index = 0;
    while (true) {
      const found = haystack.indexOf(needle, index);
      if (found === -1) {
        break;
      }
      count += 1;
      index = found + needle.length;
    }
    return count;
  }

  function collectTextNodes(rootNode) {
    const nodes = [];
    if (!rootNode) {
      return nodes;
    }
    const walker = document.createTreeWalker(rootNode, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      nodes.push(node);
      node = walker.nextNode();
    }
    return nodes;
  }

  root.utils = { describeElement, shorten, describeCodepoints, countOccurrences, collectTextNodes };
})();
