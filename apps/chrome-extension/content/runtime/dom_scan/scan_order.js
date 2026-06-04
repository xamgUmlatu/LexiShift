(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createReorderNodesForScan(options) {
    const opts = options && typeof options === "object" ? options : {};
    const normalizeProfileId = typeof opts.normalizeProfileId === "function"
      ? opts.normalizeProfileId
      : (value) => String(value || "").trim() || "default";

    function hash32(value) {
      const text = String(value || "");
      let hash = 0x811c9dc5;
      for (let index = 0; index < text.length; index += 1) {
        hash ^= text.charCodeAt(index);
        hash = Math.imul(hash, 0x01000193);
      }
      return hash >>> 0;
    }

    function mix32(value) {
      let mixed = Number(value) >>> 0;
      mixed ^= mixed >>> 16;
      mixed = Math.imul(mixed, 0x7feb352d);
      mixed ^= mixed >>> 15;
      mixed = Math.imul(mixed, 0x846ca68b);
      mixed ^= mixed >>> 16;
      return mixed >>> 0;
    }

    function shouldDistributeScanOrder(settings) {
      const maxTotal = Number.parseInt(settings && settings.maxReplacementsPerPage, 10);
      const maxPerLemma = Number.parseInt(settings && settings.maxReplacementsPerLemmaPerPage, 10);
      return (Number.isFinite(maxTotal) && maxTotal > 0)
        || (Number.isFinite(maxPerLemma) && maxPerLemma > 0);
    }

    function getViewportSize() {
      const width = Number(globalThis.innerWidth || 0);
      const height = Number(globalThis.innerHeight || 0);
      return {
        width: Number.isFinite(width) && width > 0 ? width : 0,
        height: Number.isFinite(height) && height > 0 ? height : 0
      };
    }

    function getElementForNode(node) {
      if (!node || typeof node !== "object") {
        return null;
      }
      if (node.parentElement && typeof node.parentElement.getBoundingClientRect === "function") {
        return node.parentElement;
      }
      if (node.parentNode && typeof node.parentNode.getBoundingClientRect === "function") {
        return node.parentNode;
      }
      if (typeof node.getBoundingClientRect === "function") {
        return node;
      }
      return null;
    }

    function getViewportBand(node, viewport) {
      if (!viewport || viewport.width <= 0 || viewport.height <= 0) {
        return 2;
      }
      const element = getElementForNode(node);
      if (!element) {
        return 2;
      }
      let rect = null;
      try {
        rect = element.getBoundingClientRect();
      } catch (_error) {
        rect = null;
      }
      if (!rect) {
        return 2;
      }
      const visible = rect.bottom > 0
        && rect.top < viewport.height
        && rect.right > 0
        && rect.left < viewport.width;
      if (visible) {
        return 0;
      }
      const near = rect.bottom > -viewport.height
        && rect.top < viewport.height * 2
        && rect.right > -viewport.width
        && rect.left < viewport.width * 2;
      if (near) {
        return 1;
      }
      return 2;
    }

    return function reorderNodesForScan(nodes, settings) {
      if (!Array.isArray(nodes) || nodes.length < 2) {
        return nodes;
      }
      const distribute = shouldDistributeScanOrder(settings);
      const viewport = getViewportSize();
      let locationKey = "";
      try {
        if (globalThis.location) {
          locationKey = `${globalThis.location.origin || ""}${globalThis.location.pathname || ""}`;
        }
      } catch (_error) {
        locationKey = "";
      }
      const profileId = normalizeProfileId(settings && settings.srsProfileId);
      const seed = hash32(`${locationKey}|${profileId}|scan-order`);
      const ranked = nodes.map((node, index) => ({
        node,
        index,
        band: getViewportBand(node, viewport),
        score: mix32(seed ^ Math.imul((index + 1) >>> 0, 0x9e3779b1))
      }));
      ranked.sort((left, right) => {
        if (left.band !== right.band) {
          return left.band - right.band;
        }
        if (!distribute) {
          return left.index - right.index;
        }
        if (left.score !== right.score) {
          return left.score - right.score;
        }
        return left.index - right.index;
      });
      return ranked.map((entry) => entry.node);
    };
  }

  root.contentDomScanOrder = {
    createReorderNodesForScan
  };
})();
