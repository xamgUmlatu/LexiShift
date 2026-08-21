(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const support = root.contentDomScanSemanticContextSupport || {};
  const clipContext = support.clipContext;
  const createContextCache = support.createContextCache;
  const normalizeCache = support.normalizeContextCache;
  const MAX_WORDS = 48;
  const MAX_CHARS = 1200;
  const MAX_TEXT_NODES = 80;
  const MAX_ANCESTOR_DEPTH = 8;
  const MAX_CACHE_CHARS = MAX_CHARS * 4;
  const SIDE_NODE_BUDGET = Math.floor((MAX_TEXT_NODES - 1) / 2);
  const FLOW_BREAK = "\u2029";
  const LEXISHIFT_SCAN_SKIP_ATTR = "data-lexishift-scan-skip";
  const CONTAINER_TAGS = new Set([
    "P", "LI", "TD", "TH", "BLOCKQUOTE", "FIGCAPTION", "CAPTION", "DD", "DT", "PRE",
    "H1", "H2", "H3", "H4", "H5", "H6", "ADDRESS", "SUMMARY", "BUTTON", "LEGEND"
  ]);
  const FALLBACK_CONTAINER_TAGS = new Set(["ARTICLE", "SECTION", "MAIN", "DIV"]);
  const FLOW_BREAK_TAGS = new Set([
    "BR", "HR", "P", "LI", "TR", "TD", "TH", "BLOCKQUOTE", "FIGCAPTION", "CAPTION",
    "DD", "DT", "PRE", "H1", "H2", "H3", "H4", "H5", "H6", "ADDRESS", "SUMMARY",
    "ARTICLE", "SECTION", "MAIN", "DIV", "ASIDE", "HEADER", "FOOTER", "NAV"
  ]);
  const BLOCK_DISPLAY_VALUES = new Set([
    "block", "flow-root", "flex", "grid", "list-item", "table", "table-row", "table-cell"
  ]);
  const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE"]);
  const WORD_RE = /[\p{L}\p{M}\p{N}]+(?:['’][\p{L}\p{M}\p{N}]+)*/gu;
  const containerIds = new WeakMap();
  let nextContainerId = 1;

  function countWords(text) {
    const matches = String(text || "").match(WORD_RE);
    return matches ? matches.length : 0;
  }

  function isElementNode(node) {
    return Boolean(node && Number(node.nodeType) === 1);
  }

  function isTextNode(node) {
    return Boolean(node && Number(node.nodeType) === 3);
  }

  function getElementTag(element) {
    return String(element && element.tagName ? element.tagName : "").trim().toUpperCase();
  }

  function getParentElement(node) {
    if (!node) return null;
    if (node.parentElement) return node.parentElement;
    return node.parentNode && isElementNode(node.parentNode) ? node.parentNode : null;
  }

  function getContainerId(container) {
    if (!container || (typeof container !== "object" && typeof container !== "function")) {
      return "";
    }
    if (!containerIds.has(container)) {
      containerIds.set(container, nextContainerId);
      nextContainerId += 1;
    }
    return String(containerIds.get(container));
  }

  function normalizeFilters(value) {
    const filters = value && typeof value === "object" ? value : {};
    return {
      isEditable: typeof filters.isEditable === "function" ? filters.isEditable : (() => false),
      isExcluded: typeof filters.isExcluded === "function" ? filters.isExcluded : (() => false),
      isLexiShiftNode: typeof filters.isLexiShiftNode === "function" ? filters.isLexiShiftNode : (() => false)
    };
  }

  function hasClassName(element, className) {
    if (!element || !className) return false;
    if (element.classList && typeof element.classList.contains === "function") {
      return element.classList.contains(className);
    }
    return String(element.className || "").split(/\s+/).some((value) => value === className);
  }

  function elementMatchesLexiShiftReplacement(element, stopElement) {
    let cursor = element;
    while (cursor && isElementNode(cursor)) {
      if (hasClassName(cursor, "lexishift-replacement")) return true;
      if (
        typeof cursor.getAttribute === "function"
        && String(cursor.getAttribute(LEXISHIFT_SCAN_SKIP_ATTR) || "").trim().toLowerCase() === "true"
      ) {
        return true;
      }
      if (cursor === stopElement) return false;
      cursor = getParentElement(cursor);
    }
    return false;
  }

  function isElementHidden(element) {
    if (!element || !isElementNode(element)) return false;
    if (element.hidden === true) return true;
    if (typeof element.getAttribute === "function") {
      const ariaHidden = String(element.getAttribute("aria-hidden") || "").trim().toLowerCase();
      if (ariaHidden === "true") return true;
    }
    if (!globalThis.getComputedStyle || typeof globalThis.getComputedStyle !== "function") {
      return false;
    }
    let style = null;
    try {
      style = globalThis.getComputedStyle(element);
    } catch (_error) {
      style = null;
    }
    if (!style) return false;
    const display = String(style.display || "").trim().toLowerCase();
    const visibility = String(style.visibility || "").trim().toLowerCase();
    return display === "none" || visibility === "hidden" || visibility === "collapse";
  }

  function shouldSkipElement(element, stopElement) {
    if (!element || !isElementNode(element)) return false;
    if (SKIP_TAGS.has(getElementTag(element))) return true;
    if (element.isContentEditable === true || isElementHidden(element)) return true;
    return elementMatchesLexiShiftReplacement(element, stopElement);
  }

  function isFlowBreakElement(element) {
    if (!element || !isElementNode(element)) return false;
    if (FLOW_BREAK_TAGS.has(getElementTag(element))) return true;
    if (!globalThis.getComputedStyle || typeof globalThis.getComputedStyle !== "function") {
      return false;
    }
    let style = null;
    try {
      style = globalThis.getComputedStyle(element);
    } catch (_error) {
      style = null;
    }
    return Boolean(style && BLOCK_DISPLAY_VALUES.has(String(style.display || "").trim().toLowerCase()));
  }

  function getChildNodes(node) {
    return Array.isArray(node && node.childNodes)
      ? node.childNodes
      : Array.from(node && node.childNodes || []);
  }

  function getNextDomNode(node, stopElement) {
    if (!node) return null;
    const children = getChildNodes(node);
    if (children.length) return children[0];
    let cursor = node;
    while (cursor && cursor !== stopElement) {
      const parent = cursor.parentNode || getParentElement(cursor);
      if (!parent) return null;
      const siblings = getChildNodes(parent);
      const index = siblings.indexOf(cursor);
      if (index >= 0 && index + 1 < siblings.length) return siblings[index + 1];
      cursor = parent;
    }
    return null;
  }

  function resolveFlowOwner(textNode, container) {
    let element = getParentElement(textNode);
    while (element && element !== container) {
      if (isFlowBreakElement(element)) return element;
      element = getParentElement(element);
    }
    return container;
  }

  function hasFlowBreakBetween(previousNode, currentNode, container) {
    if (!previousNode || !currentNode || previousNode === currentNode) return false;
    if (resolveFlowOwner(previousNode, container) !== resolveFlowOwner(currentNode, container)) {
      return true;
    }
    let cursor = getNextDomNode(previousNode, container);
    let visited = 0;
    while (cursor && cursor !== currentNode && visited < MAX_TEXT_NODES * 8) {
      if (isElementNode(cursor) && isFlowBreakElement(cursor) && !isElementHidden(cursor)) {
        return true;
      }
      cursor = getNextDomNode(cursor, container);
      visited += 1;
    }
    return false;
  }

  function appendContextNode(buffer, node, previousNode, container) {
    const value = String(node && node.nodeValue || "");
    if (!value) return { text: buffer, start: -1 };
    let text = buffer;
    if (previousNode && hasFlowBreakBetween(previousNode, node, container)) {
      text += FLOW_BREAK;
    }
    const start = text.length;
    text += value;
    return { text, start };
  }

  function isUsableTextNode(candidate, container, filters) {
    if (!candidate || !isTextNode(candidate)) return false;
    const value = String(candidate.nodeValue || "");
    if (!value || !value.trim()) return false;
    if (filters.isEditable(candidate) || filters.isExcluded(candidate) || filters.isLexiShiftNode(candidate)) {
      return false;
    }
    let element = getParentElement(candidate);
    while (element && isElementNode(element)) {
      if (shouldSkipElement(element, container)) return false;
      if (element === container) return true;
      element = getParentElement(element);
    }
    return false;
  }

  function resolveContainer(textNode) {
    let element = getParentElement(textNode);
    let fallback = null;
    let depth = 0;
    while (element && isElementNode(element) && depth < MAX_ANCESTOR_DEPTH) {
      const tag = getElementTag(element);
      if (CONTAINER_TAGS.has(tag)) return element;
      if (!fallback && FALLBACK_CONTAINER_TAGS.has(tag)) fallback = element;
      if (tag === "BODY" || tag === "HTML") break;
      element = getParentElement(element);
      depth += 1;
    }
    return fallback;
  }

  function createWalker(container) {
    if (
      !globalThis.document
      || typeof globalThis.document.createTreeWalker !== "function"
      || !globalThis.NodeFilter
      || !Number.isFinite(Number(globalThis.NodeFilter.SHOW_TEXT))
    ) {
      return null;
    }
    try {
      return globalThis.document.createTreeWalker(container, globalThis.NodeFilter.SHOW_TEXT);
    } catch (_error) {
      return null;
    }
  }

  function collectSideNodesWithWalker(container, textNode, direction, filters) {
    const walker = createWalker(container);
    if (!walker) return null;
    const nodes = [];
    let wordCount = 0;
    let charCount = 0;
    try {
      walker.currentNode = textNode;
    } catch (_error) {
      return null;
    }
    const nextNode = direction === "previous" ? () => walker.previousNode() : () => walker.nextNode();
    let candidate = nextNode();
    while (candidate && nodes.length < SIDE_NODE_BUDGET && wordCount < MAX_WORDS && charCount < MAX_CHARS) {
      if (isUsableTextNode(candidate, container, filters)) {
        const value = String(candidate.nodeValue || "");
        nodes.push(candidate);
        wordCount += countWords(value);
        charCount += value.length;
      }
      candidate = nextNode();
    }
    return nodes;
  }

  function collectTextNodesFallback(container, filters) {
    const nodes = [];
    let visited = 0;
    function visit(node) {
      if (!node || visited >= MAX_TEXT_NODES) return;
      visited += 1;
      if (isTextNode(node)) {
        if (isUsableTextNode(node, container, filters)) nodes.push(node);
        return;
      }
      if (!isElementNode(node) && node !== container) return;
      if (node !== container && shouldSkipElement(node, container)) return;
      const children = Array.isArray(node.childNodes) ? node.childNodes : Array.from(node.childNodes || []);
      for (const child of children) {
        visit(child);
        if (visited >= MAX_TEXT_NODES) break;
      }
    }
    visit(container);
    return nodes;
  }

  function collectContainerNodesWithWalker(container, filters) {
    const walker = createWalker(container);
    if (!walker) return null;
    const nodes = [];
    let truncated = false;
    let candidate = walker.nextNode();
    while (candidate) {
      if (isUsableTextNode(candidate, container, filters)) {
        if (nodes.length >= MAX_TEXT_NODES) {
          truncated = true;
          break;
        }
        nodes.push(candidate);
      }
      candidate = walker.nextNode();
    }
    return { nodes, truncated };
  }

  function collectContainerNodesFallback(container, filters) {
    const nodes = [];
    let truncated = false;
    let visited = 0;
    const maxVisited = MAX_TEXT_NODES * 8;
    function visit(node) {
      if (!node || truncated) return;
      visited += 1;
      if (visited > maxVisited) {
        truncated = true;
        return;
      }
      if (isTextNode(node)) {
        if (isUsableTextNode(node, container, filters)) {
          if (nodes.length >= MAX_TEXT_NODES) {
            truncated = true;
            return;
          }
          nodes.push(node);
        }
        return;
      }
      if (!isElementNode(node) && node !== container) return;
      if (node !== container && shouldSkipElement(node, container)) return;
      const children = Array.isArray(node.childNodes) ? node.childNodes : Array.from(node.childNodes || []);
      for (const child of children) {
        visit(child);
        if (truncated) break;
      }
    }
    visit(container);
    return { nodes, truncated };
  }

  function collectContainerNodes(container, filters) {
    return collectContainerNodesWithWalker(container, filters)
      || collectContainerNodesFallback(container, filters);
  }

  function buildContainerBuffer(container, filters) {
    const collected = collectContainerNodes(container, filters);
    if (!collected || collected.truncated || !Array.isArray(collected.nodes) || !collected.nodes.length) {
      return null;
    }
    const nodeStarts = new WeakMap();
    let text = "";
    let previousNode = null;
    for (const node of collected.nodes) {
      const appended = appendContextNode(text, node, previousNode, container);
      if (appended.start < 0) continue;
      if (appended.text.length > MAX_CACHE_CHARS) return null;
      nodeStarts.set(node, appended.start);
      text = appended.text;
      previousNode = node;
    }
    return text ? { text, nodeStarts } : null;
  }

  function getCachedContainerBuffer(container, filters, cache) {
    if (!cache || !container) return null;
    if (cache.records.has(container)) {
      if (cache.stats && typeof cache.stats === "object") cache.stats.recordReuses += 1;
      return cache.records.get(container);
    }
    if (cache.stats && typeof cache.stats === "object") cache.stats.containerBuilds += 1;
    const record = buildContainerBuffer(container, filters);
    cache.records.set(container, record || null);
    return record;
  }

  function collectContextNodes(container, textNode, filters) {
    const previousWithWalker = collectSideNodesWithWalker(container, textNode, "previous", filters);
    const nextWithWalker = collectSideNodesWithWalker(container, textNode, "next", filters);
    if (previousWithWalker && nextWithWalker) {
      return previousWithWalker.reverse().concat([textNode], nextWithWalker);
    }
    const allNodes = collectTextNodesFallback(container, filters);
    const currentIndex = allNodes.indexOf(textNode);
    if (currentIndex < 0) return [textNode];
    const start = Math.max(0, currentIndex - SIDE_NODE_BUDGET);
    const end = Math.min(allNodes.length, currentIndex + SIDE_NODE_BUDGET + 1);
    return allNodes.slice(start, end);
  }

  function buildContextBuffer(textNode, filters, resolvedContainer) {
    const container = resolvedContainer || resolveContainer(textNode);
    if (!container) return null;
    const contextNodes = collectContextNodes(container, textNode, filters);
    let text = "";
    let textNodeStart = -1;
    let previousNode = null;
    for (const candidate of contextNodes) {
      if (!isUsableTextNode(candidate, container, filters) && candidate !== textNode) continue;
      if (text.length >= MAX_CHARS && textNodeStart >= 0) break;
      let value = String(candidate.nodeValue || "");
      if (!value) continue;
      const separator = previousNode && hasFlowBreakBetween(previousNode, candidate, container)
        ? FLOW_BREAK
        : "";
      if (text.length + separator.length + value.length > MAX_CHARS && textNodeStart >= 0) {
        value = value.slice(0, Math.max(0, MAX_CHARS - text.length - separator.length));
      }
      text += separator;
      if (candidate === textNode) textNodeStart = text.length;
      text += value;
      previousNode = candidate;
      if (textNodeStart >= 0 && countWords(text) >= MAX_WORDS * 2) break;
    }
    if (textNodeStart < 0) return null;
    return { text, textNodeStart, container };
  }

  function buildResolverBuffer(textNode, filters, cache) {
    const container = resolveContainer(textNode);
    if (!container) return null;
    const cached = getCachedContainerBuffer(container, filters, cache);
    if (cached && cached.nodeStarts) {
      const cachedStart = cached.nodeStarts.get(textNode);
      if (Number.isFinite(Number(cachedStart))) {
        if (cache && cache.stats && typeof cache.stats === "object") cache.stats.usableReuses += 1;
        return {
          text: cached.text,
          textNodeStart: Number(cachedStart),
          container
        };
      }
    }
    if (cache && cache.stats && typeof cache.stats === "object") cache.stats.bypasses += 1;
    return buildContextBuffer(textNode, filters, container);
  }

  function createResolver(textNode, options) {
    const opts = options && typeof options === "object" ? options : {};
    const filters = normalizeFilters(opts.nodeFilters);
    const sharedCache = normalizeCache(opts.cache, opts.nodeFilters);
    const locale = String(
      opts.locale
      || (
        globalThis.document
        && globalThis.document.documentElement
        && globalThis.document.documentElement.lang
      )
      || ""
    ).trim();
    let cachedBuffer = undefined;
    return (request) => {
      if (!request || typeof request !== "object") return null;
      const localStart = Number(request.matchStart);
      const localEnd = Number(request.matchEnd);
      if (!Number.isFinite(localStart) || !Number.isFinite(localEnd) || localStart < 0 || localEnd <= localStart) {
        return null;
      }
      const nodeText = String(textNode && textNode.nodeValue || "");
      if (localEnd > nodeText.length) return null;
      if (cachedBuffer === undefined) cachedBuffer = buildResolverBuffer(textNode, filters, sharedCache);
      if (!cachedBuffer) return null;
      const contextStart = cachedBuffer.textNodeStart + localStart;
      const contextEnd = cachedBuffer.textNodeStart + localEnd;
      if (!clipContext) return null;
      const resolved = clipContext(cachedBuffer.text, contextStart, contextEnd, { locale });
      if (!resolved) return null;
      const containerId = getContainerId(cachedBuffer.container);
      const sentenceIndex = Number.isFinite(Number(resolved.sentenceIndex))
        ? Math.max(0, Number(resolved.sentenceIndex))
        : 0;
      return {
        ...resolved,
        sentenceKey: containerId ? `container:${containerId}:sentence:${sentenceIndex}` : ""
      };
    };
  }

  root.contentDomScanSemanticContext = {
    createContextCache,
    createResolver
  };
})();
