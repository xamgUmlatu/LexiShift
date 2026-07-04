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

  function translateMessage(key, substitutions, fallback) {
    if (globalThis.chrome && chrome.i18n && typeof chrome.i18n.getMessage === "function") {
      const message = chrome.i18n.getMessage(key, substitutions);
      if (message) {
        return message;
      }
    }
    return String(fallback || "");
  }

  function isTopicSupported(pairKey, topic) {
    const supportedTopics = supportedTopicsForPair(pairKey);
    if (!supportedTopics) {
      return true;
    }
    return supportedTopics.has(String(topic || "").trim());
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
      button.classList.toggle("is-unsupported", !supported);
      button.setAttribute("aria-disabled", supported ? "false" : "true");
      if (supported) {
        button.removeAttribute("title");
      } else {
        const pair = normalizePairKey(pairKey);
        button.setAttribute(
          "title",
          translateMessage(
            "tooltip_srs_topic_not_covered",
            [pair],
            `Not covered for ${pair} yet`
          )
        );
      }
    });
  }

  root.optionsSrsTopicSupport = {
    applyTopicChipSupport,
    isTopicSupported,
    supportedTopicsForPair
  };
})();
