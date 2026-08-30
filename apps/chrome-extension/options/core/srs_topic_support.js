(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const SUPPORTED_TOPICS_BY_PAIR = {
    "en-ja": new Set([
      "animals",
      "anime_manga_pop_culture",
      "arts_literature_humanities",
      "computing_internet",
      "finance_business",
      "food_cooking",
      "games",
      "hobbies_crafts",
      "law_politics_civics",
      "medicine_health",
      "music_media_entertainment",
      "plants_nature",
      "science_math",
      "science_technology",
      "shopping_money",
      "sports_fitness",
      "travel_places_transport",
      "work_office"
    ]),
    "en-es": new Set([
      "animals",
      "arts_literature_humanities",
      "computing_internet",
      "finance_business",
      "food_cooking",
      "games",
      "hobbies_crafts",
      "law_politics_civics",
      "medicine_health",
      "music_media_entertainment",
      "plants_nature",
      "science_math",
      "science_technology",
      "shopping_money",
      "sports_fitness",
      "travel_places_transport",
      "work_office"
    ]),
    "en-de": new Set([
      "arts_literature_humanities",
      "finance_business",
      "games",
      "law_politics_civics",
      "medicine_health",
      "music_media_entertainment",
      "science_technology",
      "sports_fitness",
      "travel_places_transport"
    ])
  };

  function normalizePairKey(pairKey) {
    return String(pairKey || "").trim().toLowerCase();
  }

  function supportedTopicsForPair(pairKey) {
    return SUPPORTED_TOPICS_BY_PAIR[normalizePairKey(pairKey)] || null;
  }

  function normalizeTopicList(value) {
    const source = Array.isArray(value) ? value : String(value || "").split(",");
    const seen = new Set();
    return source
      .map((entry) => String(entry || "").trim())
      .filter((entry) => {
        if (!entry || seen.has(entry)) {
          return false;
        }
        seen.add(entry);
        return true;
      });
  }

  function isTopicSupported(pairKey, topic) {
    const supportedTopics = supportedTopicsForPair(pairKey);
    if (!supportedTopics) {
      return true;
    }
    return supportedTopics.has(String(topic || "").trim());
  }

  function filterTopicsForPair(pairKey, topics) {
    const normalized = normalizeTopicList(topics);
    const supportedTopics = supportedTopicsForPair(pairKey);
    if (!supportedTopics) {
      return normalized;
    }
    return normalized.filter((topic) => supportedTopics.has(topic));
  }

  function applyTopicChipSupport(buttons, pairKey) {
    const buttonList = Array.isArray(buttons) ? buttons : [];
    const supportedTopics = supportedTopicsForPair(pairKey);
    buttonList.forEach((button) => {
      if (!button || typeof button.getAttribute !== "function") {
        return;
      }
      const topic = String(
        button.getAttribute("data-srs-topic-interest")
          || button.getAttribute("data-srs-story-topic-interest")
          || ""
      ).trim();
      const supported = Boolean(!supportedTopics || supportedTopics.has(topic));
      button.disabled = !supported;
      button.hidden = !supported;
      if (button.classList && typeof button.classList.toggle === "function") {
        button.classList.toggle("is-unsupported", false);
      }
      if (typeof button.removeAttribute === "function") {
        button.removeAttribute("aria-disabled");
        button.removeAttribute("title");
      }
    });
  }

  root.optionsSrsTopicSupport = {
    applyTopicChipSupport,
    filterTopicsForPair,
    isTopicSupported,
    supportedTopicsForPair
  };
})();
