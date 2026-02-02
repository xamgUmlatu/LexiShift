(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const state = {
    dataset: null,
    loading: null,
    error: null
  };

  const DEFAULT_WEIGHTS = {
    base_freq: 0.55,
    topic_bias: 0.15,
    user_pref: 0.1,
    confidence: 0.1,
    difficulty_target: 0.1
  };

  const DEFAULT_PENALTIES = {
    recency_threshold: 0.25,
    recency_multiplier: 0.3,
    mastered_multiplier: 0.2,
    oversubscribed_multiplier: 0.8
  };

  function clamp01(value, fallback = 0) {
    const num = Number(value);
    if (!Number.isFinite(num)) {
      return fallback;
    }
    if (num < 0) return 0;
    if (num > 1) return 1;
    return num;
  }

  async function loadDataset() {
    if (state.dataset) {
      return state.dataset;
    }
    if (state.loading) {
      return state.loading;
    }
    const url = root.chrome && root.chrome.runtime
      ? root.chrome.runtime.getURL("shared/srs_selector_test_dataset.json")
      : (globalThis.chrome && chrome.runtime ? chrome.runtime.getURL("shared/srs_selector_test_dataset.json") : "");
    if (!url) {
      state.error = new Error("No chrome runtime available to load dataset.");
      return null;
    }
    state.loading = fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load SRS dataset (${response.status}).`);
        }
        return response.json();
      })
      .then((data) => {
        state.dataset = data;
        state.error = null;
        return data;
      })
      .catch((err) => {
        state.error = err;
        state.dataset = null;
        return null;
      })
      .finally(() => {
        state.loading = null;
      });
    return state.loading;
  }

  function scoreItem(item, weights = DEFAULT_WEIGHTS, penalties = DEFAULT_PENALTIES) {
    const baseFreq = clamp01(item.base_freq);
    const topicBias = clamp01(item.topic_bias);
    const userPref = clamp01(item.user_pref);
    const confidence = clamp01(item.confidence);
    const difficultyTarget = clamp01(item.difficulty_target);

    const components = {
      base_freq: baseFreq * weights.base_freq,
      topic_bias: topicBias * weights.topic_bias,
      user_pref: userPref * weights.user_pref,
      confidence: confidence * weights.confidence,
      difficulty_target: difficultyTarget * weights.difficulty_target
    };
    const weightedSum = Object.values(components).reduce((sum, value) => sum + value, 0);
    let score = weightedSum;
    const applied = [];

    const recency = item.recency;
    if (recency !== undefined && recency !== null && recency < penalties.recency_threshold) {
      score *= penalties.recency_multiplier;
      applied.push("recent");
    }
    if (item.mastered) {
      score *= penalties.mastered_multiplier;
      applied.push("mastered");
    }
    if (item.oversubscribed) {
      score *= penalties.oversubscribed_multiplier;
      applied.push("oversubscribed");
    }

    return {
      item,
      score,
      weightedSum,
      components,
      penalties: applied
    };
  }

  function sampleScored(scoredItems, count) {
    const pool = scoredItems.filter((entry) => entry.score > 0);
    const selected = [];
    const working = pool.slice();
    const target = Math.max(0, count || 0);
    while (selected.length < target && working.length) {
      const total = working.reduce((sum, entry) => sum + entry.score, 0);
      if (total <= 0) {
        break;
      }
      let roll = Math.random() * total;
      let pickedIndex = -1;
      for (let i = 0; i < working.length; i += 1) {
        roll -= working[i].score;
        if (roll <= 0) {
          pickedIndex = i;
          break;
        }
      }
      if (pickedIndex < 0) {
        pickedIndex = 0;
      }
      selected.push(working[pickedIndex]);
      working.splice(pickedIndex, 1);
    }
    return selected;
  }

  async function selectActiveItems(settings = {}) {
    const dataset = await loadDataset();
    if (!dataset || !Array.isArray(dataset.items)) {
      return {
        items: [],
        lemmas: [],
        stats: {
          total: 0,
          filtered: 0,
          datasetLoaded: false,
          error: state.error ? String(state.error.message || state.error) : null
        }
      };
    }
    const pair = settings.srsPair || "en-en";
    const maxActive = Number.isFinite(Number(settings.srsMaxActive))
      ? Math.max(1, Number(settings.srsMaxActive))
      : 40;
    const items = dataset.items;
    const filtered = pair === "all"
      ? items
      : items.filter((item) => item.language_pair === pair);

    const scored = filtered.map((item) => scoreItem(item));
    scored.sort((a, b) => b.score - a.score);
    const selected = scored.slice(0, maxActive);
    return {
      items: selected,
      lemmas: selected.map((entry) => String(entry.item.lemma || "")),
      stats: {
        total: items.length,
        filtered: filtered.length,
        maxActive,
        pair,
        datasetLoaded: true,
        error: null
      }
    };
  }

  async function selectSampledItems(settings = {}, count = 5) {
    const dataset = await loadDataset();
    if (!dataset || !Array.isArray(dataset.items)) {
      return {
        items: [],
        lemmas: [],
        stats: {
          total: 0,
          filtered: 0,
          datasetLoaded: false,
          error: state.error ? String(state.error.message || state.error) : null
        }
      };
    }
    const pair = settings.srsPair || "en-en";
    const items = dataset.items;
    const filtered = pair === "all"
      ? items
      : items.filter((item) => item.language_pair === pair);
    const scored = filtered.map((item) => scoreItem(item));
    const sampled = sampleScored(scored, count);
    return {
      items: sampled,
      lemmas: sampled.map((entry) => String(entry.item.lemma || "")),
      stats: {
        total: items.length,
        filtered: filtered.length,
        sampleCount: count,
        pair,
        datasetLoaded: true,
        error: null
      }
    };
  }

  root.srsSelector = {
    loadDataset,
    scoreItem,
    selectActiveItems,
    selectSampledItems
  };
})();
