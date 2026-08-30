(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const entries = Object.freeze([
    Object.freeze({
      packId: "lookup-dictionary-directory-ja",
      mode: "dictionary-directory",
      name: "Yomitan popup dictionaries",
      source: "community-maintained directory",
      recommendedName: "大辞林 第四版（画像無し）",
      recommendedFormat: "Yomitan format-3 dictionary ZIP",
      recommendedSectionId: "daijirin-fourth-edition",
      recommendedHeading: "Daijirin Fourth Edition",
      pageMatches: [
        Object.freeze({
          hostname: "github.com",
          pathname: "/MarvNC/yomitan-dictionaries",
          hash: "#daijirin-fourth-edition"
        })
      ]
    })
  ]);

  function headingElementForCandidate(candidate) {
    if (!candidate) {
      return null;
    }
    const headingSelector = "h1, h2, h3, h4, h5, h6";
    if (typeof candidate.matches === "function" && candidate.matches(headingSelector)) {
      return candidate;
    }
    if (typeof candidate.closest === "function") {
      const closestHeading = candidate.closest(headingSelector);
      if (closestHeading) {
        return closestHeading;
      }
    }
    const parent = candidate.parentElement;
    if (parent && typeof parent.querySelector === "function") {
      return parent.querySelector(headingSelector) || candidate;
    }
    return candidate;
  }

  function findRecommendedEntryElement(entry) {
    if (!entry || !entry.recommendedSectionId || typeof document === "undefined") {
      return null;
    }
    const sectionId = String(entry.recommendedSectionId).trim();
    const idCandidates = [sectionId, `user-content-${sectionId}`];
    for (const id of idCandidates) {
      const candidate = document.getElementById(id);
      if (candidate) {
        return headingElementForCandidate(candidate);
      }
    }
    if (typeof document.querySelector === "function") {
      const anchor = document.querySelector(`a[href="#${sectionId}"]`);
      if (anchor) {
        return headingElementForCandidate(anchor);
      }
    }
    if (typeof document.querySelectorAll !== "function") {
      return null;
    }
    const expectedHeading = String(entry.recommendedHeading || "")
      .trim()
      .toLowerCase();
    if (!expectedHeading) {
      return null;
    }
    return Array.from(document.querySelectorAll("h1, h2, h3, h4, h5, h6"))
      .find((heading) => String(heading.textContent || "").trim().toLowerCase()
        === expectedHeading) || null;
  }

  function focusRecommendedEntry(entry) {
    const target = findRecommendedEntryElement(entry);
    if (!target) {
      return false;
    }
    if (typeof target.scrollIntoView === "function") {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    if (!target.style) {
      return true;
    }
    const previous = {
      backgroundColor: target.style.backgroundColor,
      borderRadius: target.style.borderRadius,
      boxShadow: target.style.boxShadow,
      outline: target.style.outline,
      outlineOffset: target.style.outlineOffset,
      transition: target.style.transition
    };
    target.style.backgroundColor = "rgba(255, 220, 128, 0.28)";
    target.style.borderRadius = "6px";
    target.style.boxShadow = "0 0 0 6px rgba(255, 220, 128, 0.18)";
    target.style.outline = "2px solid rgba(168, 105, 20, 0.82)";
    target.style.outlineOffset = "4px";
    target.style.transition = "background-color 160ms ease, box-shadow 160ms ease";
    if (typeof globalThis.setTimeout === "function") {
      globalThis.setTimeout(() => {
        Object.assign(target.style, previous);
      }, 4000);
    }
    return true;
  }

  root.manualSourceDictionaryGuidance = Object.freeze({
    entries,
    findRecommendedEntryElement,
    focusRecommendedEntry
  });
})();
