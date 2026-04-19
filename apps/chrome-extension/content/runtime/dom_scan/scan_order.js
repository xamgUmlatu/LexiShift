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

    return function reorderNodesForScan(nodes, settings) {
      if (!Array.isArray(nodes) || nodes.length < 2 || !shouldDistributeScanOrder(settings)) {
        return nodes;
      }
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
        score: mix32(seed ^ Math.imul((index + 1) >>> 0, 0x9e3779b1))
      }));
      ranked.sort((left, right) => {
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
