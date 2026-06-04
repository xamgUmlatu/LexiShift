(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const COPY = Object.freeze({
    first: Object.freeze({
      heading: ["heading_srs_start_new_story", "Start Vocabulary Practice"],
      hint: ["hint_srs_start_new_story", "Choose a language pair, tune your preferences, then start practicing."],
      button: ["button_srs_start_new_story", "Start setup"]
    }),
    add: Object.freeze({
      heading: ["heading_srs_add_new_story", "Add another language"],
      hint: ["hint_srs_add_new_story", "Create a separate Vocabulary Practice for a new language pair. Your existing practice stays unchanged."],
      button: ["button_srs_add_new_story", "Add language"]
    })
  });

  function createPresenter(options) {
    const opts = options && typeof options === "object" ? options : {};
    const i18n = opts.i18n && typeof opts.i18n.t === "function" ? opts.i18n : null;
    const doc = opts.document || globalThis.document || null;
    const elements = opts.elements && typeof opts.elements === "object" ? opts.elements : {
      heading: doc ? doc.getElementById("srs-story-start-heading") : null,
      hint: doc ? doc.getElementById("srs-story-start-hint") : null,
      button: doc ? doc.getElementById("srs-story-start") : null
    };

    function translate(key, fallback) {
      return i18n ? i18n.t(key, null, fallback) : fallback;
    }

    function applyCopy(node, copyEntry) {
      if (!node || !Array.isArray(copyEntry)) return;
      const [key, fallback] = copyEntry;
      node.dataset.i18n = key;
      node.textContent = translate(key, fallback);
    }

    function update(profile) {
      const existingPairs = Number(profile && profile.srsPairCount);
      const copy = Number.isFinite(existingPairs) && existingPairs > 0 ? COPY.add : COPY.first;
      applyCopy(elements.heading, copy.heading);
      applyCopy(elements.hint, copy.hint);
      applyCopy(elements.button, copy.button);
    }

    return { update };
  }

  root.optionsSrsStartCardPresenter = { createPresenter };
})();
