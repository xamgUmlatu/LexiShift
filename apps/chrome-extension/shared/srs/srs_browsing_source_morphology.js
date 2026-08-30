(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const DEFAULT_MAX_SOURCE_VARIANTS_PER_TERM = 12;
  const DEFAULT_SOURCE_INFLECTION_CONFIDENCE_MULTIPLIER = 0.92;
  const DEFAULT_SOURCE_DERIVATION_CONFIDENCE_MULTIPLIER = 0.82;
  const ENGLISH_LETTER_RE = /[a-z]/i;
  const VOWEL_RE = /[aeiou]/i;
  const BROAD_SINGLE_SOURCE_TERMS = new Set([
    "about", "after", "again", "also", "another", "around", "because", "before", "between",
    "both", "case", "change", "come", "could", "different", "does", "doing", "during",
    "each", "even", "every", "find", "first", "form", "from", "give", "going", "good",
    "great", "group", "hand", "have", "high", "into", "issue", "kind", "large", "last",
    "level", "light", "line", "long", "look", "made", "make", "many", "mean", "might",
    "more", "most", "move", "much", "must", "name", "need", "next", "number", "only",
    "open", "order", "other", "part", "place", "point", "power", "problem", "public",
    "right", "same", "seem", "small", "some", "state", "still", "such", "system",
    "take", "than", "that", "their", "then", "there", "these", "thing", "this", "time",
    "turn", "used", "very", "want", "well", "were", "what", "when", "where", "which",
    "while", "will", "with", "word", "work", "world", "would"
  ]);

  function normalizeSourceTerm(value) {
    return String(value || "")
      .normalize("NFKC")
      .replace(/[’‘]/g, "'")
      .replace(/[\u2010-\u2015-]+/g, " ")
      .replace(/[^0-9A-Za-z' ]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function sourceTermTokens(term) {
    return normalizeSourceTerm(term).split(" ").filter(Boolean);
  }

  function optionNumber(options, key, fallback, min, max) {
    const opts = options && typeof options === "object" ? options : {};
    const value = Number(opts[key]);
    const safe = Number.isFinite(value) ? value : fallback;
    return Math.max(min, Math.min(max, safe));
  }

  function optionBool(options, key, fallback) {
    const opts = options && typeof options === "object" ? options : {};
    if (opts[key] === true) return true;
    if (opts[key] === false) return false;
    return fallback;
  }

  function isSourceTermShapeAllowed(term) {
    const tokens = sourceTermTokens(term);
    if (!tokens.length || tokens.length > 6) {
      return false;
    }
    if (!ENGLISH_LETTER_RE.test(term)) {
      return false;
    }
    if (term.length < 4 || term.length > 64) {
      return false;
    }
    if (tokens.length === 1) {
      const [token] = tokens;
      return token.length >= 4 && !BROAD_SINGLE_SOURCE_TERMS.has(token);
    }
    return tokens.some((token) => token.length >= 4 && !BROAD_SINGLE_SOURCE_TERMS.has(token));
  }

  function isConsonantEnding(token) {
    return token.length > 0 && /[a-z]$/i.test(token) && !VOWEL_RE.test(token[token.length - 1]);
  }

  function addTokenInflections(variants, token, confidenceMultiplier, kind) {
    if (!token || token.length < 4) {
      return;
    }
    const last = token[token.length - 1];
    const previous = token[token.length - 2] || "";
    if (last === "y" && previous && !VOWEL_RE.test(previous)) {
      variants.push({ token: `${token.slice(0, -1)}ies`, confidenceMultiplier, kind });
      variants.push({ token: `${token.slice(0, -1)}ied`, confidenceMultiplier, kind });
    } else if (last === "e") {
      variants.push({ token: `${token}s`, confidenceMultiplier, kind });
      variants.push({ token: `${token}d`, confidenceMultiplier, kind });
      variants.push({ token: `${token.slice(0, -1)}ing`, confidenceMultiplier, kind });
    } else {
      variants.push({ token: `${token}s`, confidenceMultiplier, kind });
      variants.push({ token: `${token}ed`, confidenceMultiplier, kind });
      variants.push({ token: `${token}ing`, confidenceMultiplier, kind });
    }
  }

  function addDerivedBases(variants, token, options) {
    const opts = options && typeof options === "object" ? options : {};
    const multiplier = optionNumber(
      opts,
      "sourceDerivationConfidenceMultiplier",
      DEFAULT_SOURCE_DERIVATION_CONFIDENCE_MULTIPLIER,
      0,
      1
    );
    const addBase = (base) => {
      const normalized = normalizeSourceTerm(base);
      if (normalized.length >= 4) {
        variants.push({ token: normalized, confidenceMultiplier: multiplier, kind: "derivation" });
        addTokenInflections(variants, normalized, multiplier, "derivation");
      }
    };
    if (token.endsWith("ation") && token.length > 8) {
      const base = token.slice(0, -5);
      addBase(base);
      if (base.endsWith("r")) {
        addBase(`${base}e`);
      }
    }
    if (token.endsWith("ing") && token.length > 6) {
      const base = token.slice(0, -3);
      addBase(base);
      if (isConsonantEnding(base)) {
        addBase(`${base}e`);
      }
    }
    if (token.endsWith("ed") && token.length > 5) {
      const base = token.slice(0, -2);
      addBase(base);
      if (isConsonantEnding(base)) {
        addBase(`${base}e`);
      }
    }
    if (token.endsWith("ies") && token.length > 5) {
      addBase(`${token.slice(0, -3)}y`);
    } else if (token.endsWith("es") && token.length > 5) {
      addBase(token.slice(0, -2));
    } else if (token.endsWith("s") && token.length > 5) {
      addBase(token.slice(0, -1));
    }
  }

  function englishTokenVariants(token, options) {
    const opts = options && typeof options === "object" ? options : {};
    const normalized = normalizeSourceTerm(token);
    const variants = [];
    const inflectionMultiplier = optionNumber(
      opts,
      "sourceInflectionConfidenceMultiplier",
      DEFAULT_SOURCE_INFLECTION_CONFIDENCE_MULTIPLIER,
      0,
      1
    );
    addTokenInflections(variants, normalized, inflectionMultiplier, "inflection");
    addDerivedBases(variants, normalized, opts);
    const seen = new Set([normalized]);
    return variants.filter((variant) => {
      const value = normalizeSourceTerm(variant.token);
      if (!value || seen.has(value)) {
        return false;
      }
      seen.add(value);
      return true;
    });
  }

  function sourceTermVariants(term, options) {
    const opts = options && typeof options === "object" ? options : {};
    const normalized = normalizeSourceTerm(term);
    if (!normalized || !isSourceTermShapeAllowed(normalized)) {
      return [];
    }
    const maxVariants = Math.max(
      1,
      Number(opts.maxSourceVariantsPerTerm || DEFAULT_MAX_SOURCE_VARIANTS_PER_TERM)
    );
    const variants = [{
      term: normalized,
      source_variant_kind: "exact",
      source_variant_confidence_multiplier: 1
    }];
    if (optionBool(opts, "sourceMorphologyEnabled", true) === false) {
      return variants;
    }
    const tokens = sourceTermTokens(normalized);
    const tokenVariants = [];
    if (tokens.length === 1) {
      for (const variant of englishTokenVariants(tokens[0], opts)) {
        tokenVariants.push([variant.token, variant]);
      }
    } else if (optionBool(opts, "sourcePhraseMorphologyEnabled", true)) {
      const lastIndex = tokens.length - 1;
      for (const variant of englishTokenVariants(tokens[lastIndex], opts)) {
        const nextTokens = tokens.slice();
        nextTokens[lastIndex] = variant.token;
        tokenVariants.push([nextTokens.join(" "), variant]);
      }
    }
    const seen = new Set([normalized]);
    for (const [variantTerm, variant] of tokenVariants) {
      if (variants.length >= maxVariants) {
        break;
      }
      const value = normalizeSourceTerm(variantTerm);
      if (!value || seen.has(value) || !isSourceTermShapeAllowed(value)) {
        continue;
      }
      seen.add(value);
      variants.push({
        term: value,
        source_variant_kind: variant.kind,
        source_variant_confidence_multiplier: variant.confidenceMultiplier
      });
    }
    return variants;
  }

  root.srsBrowsingSourceMorphology = {
    normalizeSourceTerm,
    sourceTermTokens,
    sourceTermVariants
  };
})();
