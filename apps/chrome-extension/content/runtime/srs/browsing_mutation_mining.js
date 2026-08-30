(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const DEFAULT_MAX_MUTATION_ROOTS = 24;

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const getCurrentSettings = typeof opts.getCurrentSettings === "function"
      ? opts.getCurrentSettings
      : (() => ({}));
    const browsingPageMiner = opts.browsingPageMiner && typeof opts.browsingPageMiner === "object"
      ? opts.browsingPageMiner
      : null;
    const mineBrowsingNode = typeof opts.mineBrowsingNode === "function"
      ? opts.mineBrowsingNode
      : ((node, reason) => mineDocument(node, reason, "Browsing mutation mining failed."));
    const shouldMine = typeof opts.shouldMine === "function" ? opts.shouldMine : (() => true);
    const log = typeof opts.log === "function" ? opts.log : (() => {});
    const nodeConstants = typeof globalThis.Node !== "undefined"
      ? globalThis.Node
      : { TEXT_NODE: 3, ELEMENT_NODE: 1 };
    let observer = null;
    let observedBody = null;
    let pendingRoots = [];
    let pendingSeen = new Set();

    function mineDocument(rootNode, reason, failureMessage) {
      if (!shouldMine()) {
        return;
      }
      if (!browsingPageMiner || typeof browsingPageMiner.mineDocument !== "function") {
        return;
      }
      browsingPageMiner.mineDocument(rootNode || globalThis.document, reason).catch((error) => {
        const settings = getCurrentSettings();
        if (settings && settings.debugEnabled) {
          log(failureMessage || "Browsing page mining failed.", error);
        }
      });
    }

    function maxRoots() {
      const settings = getCurrentSettings();
      return Math.max(
        1,
        Number(settings && settings.srsBrowsingMutationMiningMaxRoots || DEFAULT_MAX_MUTATION_ROOTS)
      );
    }

    function addRoot(roots, seen, node) {
      if (!node || seen.has(node)) {
        return;
      }
      seen.add(node);
      roots.push(node);
    }

    function describeRoot(node) {
      const tag = String(node && (node.tagName || node.nodeName) || "").toLowerCase();
      const id = node && node.id ? `#${String(node.id).trim()}` : "";
      return tag ? `${tag}${id}` : "node";
    }

    function collectMutationRoots(mutations) {
      const roots = [];
      const seen = new Set();
      for (const mutation of Array.isArray(mutations) ? mutations : []) {
        if (!mutation || typeof mutation !== "object") {
          continue;
        }
        if (mutation.type === "characterData") {
          const target = mutation.target || null;
          addRoot(roots, seen, (target && (target.parentElement || target.parentNode)) || target);
        } else if (mutation.type === "childList") {
          for (const node of Array.from(mutation.addedNodes || [])) {
            if (!node) {
              continue;
            }
            if (node.nodeType === nodeConstants.TEXT_NODE) {
              addRoot(roots, seen, (node.parentElement || node.parentNode) || node);
            } else if (
              node.nodeType === nodeConstants.ELEMENT_NODE
              || typeof node.querySelectorAll === "function"
            ) {
              addRoot(roots, seen, node);
            }
          }
        }
      }
      return roots;
    }

    function logRoots(message, roots, reason, extra) {
      if (roots.length) {
        log(message, {
          reason: String(reason || "dom mutation"),
          rootCount: roots.length,
          roots: roots.slice(0, 8).map(describeRoot),
          ...(extra || {})
        });
      }
    }

    function mineRoots(roots, reason) {
      logRoots("Browsing mutation mining roots:", roots, reason);
      for (const rootNode of roots) {
        try {
          mineBrowsingNode(rootNode, reason || "dom mutation");
        } catch (error) {
          log(
            "Browsing mutation mining failed.",
            error && error.message ? error.message : String(error || "Unknown error.")
          );
        }
      }
    }

    function deferRoots(roots, reason) {
      const limit = maxRoots();
      let addedRootCount = 0;
      for (const rootNode of roots) {
        if (pendingRoots.length >= limit) {
          break;
        }
        if (pendingSeen.has(rootNode)) {
          continue;
        }
        pendingSeen.add(rootNode);
        pendingRoots.push(rootNode);
        addedRootCount += 1;
      }
      if (addedRootCount > 0) {
        logRoots("Browsing mutation mining deferred:", pendingRoots, reason, { addedRootCount });
      }
    }

    function flushPending(reason) {
      if (!pendingRoots.length || !shouldMine()) {
        return;
      }
      const roots = pendingRoots.slice(0, maxRoots());
      pendingRoots = [];
      pendingSeen = new Set();
      mineRoots(roots, reason || "deferred dom mutation");
    }

    function mineMutationRoots(mutations, reason) {
      const roots = collectMutationRoots(mutations).slice(0, maxRoots());
      if (!roots.length) {
        return;
      }
      if (!shouldMine()) {
        deferRoots(roots, reason);
        return;
      }
      mineRoots(roots, reason || "dom mutation");
    }

    function observeChanges() {
      if (observer || !globalThis.document || !document.body || typeof MutationObserver !== "function") {
        return;
      }
      observedBody = document.body;
      observer = new MutationObserver((mutations) => {
        mineMutationRoots(mutations, "dom mutation");
      });
      observer.observe(observedBody, { childList: true, subtree: true, characterData: true });
    }

    function ensureObserver() {
      if (!globalThis.document || !document.body) {
        return;
      }
      if (!observedBody || observedBody !== document.body) {
        disconnect();
        observeChanges();
      }
    }

    function disconnect() {
      if (observer) {
        observer.disconnect();
        observer = null;
      }
      observedBody = null;
      pendingRoots = [];
      pendingSeen = new Set();
    }

    return {
      collectMutationRoots,
      disconnect,
      ensureObserver,
      flushPending,
      mineDocument,
      mineMutationRoots,
      observeChanges
    };
  }

  root.contentBrowsingMutationMiningRuntime = {
    createController
  };
})();
