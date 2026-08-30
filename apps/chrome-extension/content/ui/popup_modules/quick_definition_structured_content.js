(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const DEPTH_LIMIT = 32;
  const NODE_LIMIT = 1500;
  const TAGS = new Set([
    "a", "br", "div", "li", "ol", "rp", "rt", "ruby", "span",
    "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul"
  ]);
  const ROLES = new Set([
    "headword", "headword-reading", "headword-written", "headword-writing",
    "explanation", "major-section", "section", "sense-group", "sense",
    "sense-number", "subsense", "subsense-number", "definition",
    "part-of-speech-group", "part-of-speech", "example", "note", "reference",
    "source", "source-title", "source-note", "accent", "reading-list", "reading",
    "related-terms", "related-term", "reading-note"
  ]);
  const STYLES = new Set(["bold", "italic", "super", "sub", "underline"]);

  function normalizeText(value) {
    return String(value || "").trim();
  }

  function normalizeNotes(values) {
    const notes = [];
    for (const value of Array.isArray(values) ? values : []) {
      const raw = value && typeof value === "object" ? value : {};
      if (normalizeText(raw.kind) !== "orthography_variants") continue;
      const sourceText = normalizeText(raw.source_text);
      const items = [];
      for (const itemValue of Array.isArray(raw.items) ? raw.items : []) {
        const item = itemValue && typeof itemValue === "object" ? itemValue : {};
        const writtenForm = normalizeText(item.written_form);
        const text = normalizeText(item.text);
        if (writtenForm && text) items.push({ writtenForm, text });
      }
      if (sourceText && items.length >= 2) {
        notes.push({ kind: "orthography_variants", sourceText, items });
      }
    }
    return notes;
  }

  function normalizeContent(values) {
    const state = { count: 0 };
    const nodes = [];
    for (const value of Array.isArray(values) ? values : []) {
      const node = normalizeNode(value, state, 0);
      if (node) nodes.push(node);
      if (state.count >= NODE_LIMIT) break;
    }
    return nodes;
  }

  function normalizeNode(value, state, depth) {
    if (!value || typeof value !== "object" || Array.isArray(value)
      || depth > DEPTH_LIMIT || state.count >= NODE_LIMIT) {
      return null;
    }
    const type = normalizeText(value.type).toLowerCase();
    if (type === "text" || type === "image-fallback") {
      const text = String(value.text || "");
      if (!text) return null;
      state.count += 1;
      return { type, text };
    }
    if (type === "break") {
      state.count += 1;
      return { type: "break" };
    }
    if (type !== "element") return null;
    const tag = normalizeText(value.tag).toLowerCase();
    if (!TAGS.has(tag)) return null;
    const children = [];
    for (const childValue of Array.isArray(value.children) ? value.children : []) {
      const child = normalizeNode(childValue, state, depth + 1);
      if (child) children.push(child);
      if (state.count >= NODE_LIMIT) break;
    }
    if (!children.length && tag !== "br") return null;
    const roleValue = normalizeText(value.role).toLowerCase();
    const role = ROLES.has(roleValue) ? roleValue : "";
    const styles = [];
    for (const styleValue of Array.isArray(value.styles) ? value.styles : []) {
      const style = normalizeText(styleValue).toLowerCase();
      if (STYLES.has(style) && !styles.includes(style)) styles.push(style);
    }
    state.count += 1;
    return {
      type: "element",
      tag,
      children,
      role,
      styles,
      query: normalizeText(value.query).slice(0, 200)
    };
  }

  function appendContent(parent, nodes, truncated) {
    const content = document.createElement("div");
    content.className = "lexishift-definition-structured";
    for (const node of nodes || []) {
      const rendered = buildNode(node);
      if (rendered) content.appendChild(rendered);
    }
    if (truncated) {
      const marker = document.createElement("div");
      marker.className = "lexishift-definition-structured-truncated";
      marker.textContent = "…";
      content.appendChild(marker);
    }
    parent.appendChild(content);
  }

  function buildNode(node) {
    if (!node || typeof node !== "object") return null;
    if (node.type === "text" || node.type === "image-fallback") {
      const text = document.createElement("span");
      text.className = node.type === "image-fallback"
        ? "lexishift-yomitan-image-fallback"
        : "lexishift-yomitan-text";
      text.textContent = node.text;
      return text;
    }
    if (node.type === "break") return document.createElement("br");
    if (node.type !== "element" || !TAGS.has(node.tag)) return null;
    const element = document.createElement(node.tag === "a" ? "span" : node.tag);
    const classes = ["lexishift-yomitan-element"];
    if (node.role) {
      classes.push(`lexishift-yomitan-role-${node.role}`);
      if (typeof element.setAttribute === "function") {
        element.setAttribute("data-yomitan-role", node.role);
      }
    }
    for (const style of node.styles || []) classes.push(`lexishift-yomitan-style-${style}`);
    if (node.tag === "a") {
      classes.push("lexishift-yomitan-reference-link");
      if (node.query && typeof element.setAttribute === "function") {
        element.setAttribute("title", node.query);
      }
    }
    element.className = classes.join(" ");
    for (const child of node.children || []) {
      const renderedChild = buildNode(child);
      if (renderedChild) element.appendChild(renderedChild);
    }
    return element;
  }

  root.uiQuickDefinitionStructuredContent = {
    appendContent,
    normalizeContent,
    normalizeNotes
  };
})();
