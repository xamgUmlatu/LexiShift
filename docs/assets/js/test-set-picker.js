(() => {
  const root = globalThis;

  const LANGUAGES = [
    { id: "en", label: "English", shortLabel: "EN", sampleMode: "Native-script sample" },
    { id: "es", label: "Español", shortLabel: "ES", sampleMode: "Native-script sample" },
    { id: "ja", label: "日本語", shortLabel: "JA", sampleMode: "Romanized sample" },
    { id: "zh", label: "简体中文", shortLabel: "ZH", sampleMode: "Romanized sample" },
    { id: "de", label: "Deutsch", shortLabel: "DE", sampleMode: "Native-script sample" }
  ];

  const CONCEPTS = ["see", "time", "book", "friend", "learn"];

  const SOURCE_FORMS = {
    en: { see: "see", time: "time", book: "book", friend: "friend", learn: "learn" },
    es: { see: "ver", time: "tiempo", book: "libro", friend: "amigo", learn: "aprender" },
    ja: { see: "miru", time: "jikan", book: "hon", friend: "tomodachi", learn: "manabu" },
    zh: { see: "kan", time: "shijian", book: "shu", friend: "pengyou", learn: "xuexi" },
    de: { see: "sehen", time: "Zeit", book: "Buch", friend: "Freund", learn: "lernen" }
  };

  const TARGET_FORMS = {
    en: { see: "see", time: "time", book: "book", friend: "friend", learn: "learn" },
    es: { see: "ver", time: "tiempo", book: "libro", friend: "amigo", learn: "aprender" },
    ja: { see: "見る", time: "時間", book: "本", friend: "友達", learn: "学ぶ" },
    zh: { see: "看", time: "时间", book: "书", friend: "朋友", learn: "学习" },
    de: { see: "sehen", time: "Zeit", book: "Buch", friend: "Freund", learn: "lernen" }
  };

  const MONOLINGUAL_FORMS = {
    en: { see: "notice", time: "moment", book: "volume", friend: "companion", learn: "study" },
    es: { see: "observar", time: "momento", book: "volumen", friend: "compañero", learn: "estudiar" },
    de: { see: "betrachten", time: "Moment", book: "Band", friend: "Begleiter", learn: "studieren" }
  };

  const SAMPLE_TEXTS = {
    en: "A friend opens a book by the window. They can see the garden and take their time. Each afternoon, they learn one new idea.",
    es: "Un amigo abre un libro junto a la ventana. Puede ver el jardín y se toma su tiempo. Cada tarde, intenta aprender una idea nueva.",
    ja: "Tomodachi ga mado no soba de hon o hiraku. Niwa o miru tame ni jikan o toru. Mainichi hitotsu atarashii koto o manabu.",
    zh: "Pengyou zai chuangbian dakai yi ben shu. Ta kan huayuan, ye hua shijian. Meitian dou xuexi yi ge xin xiangfa.",
    de: "Ein Freund öffnet am Fenster ein Buch. Dort kann er den Garten sehen und nimmt sich Zeit. Jeden Nachmittag versucht er, etwas Neues zu lernen."
  };

  const JAPANESE_WORD_PACKAGES = {
    "見る": { reading: "みる", romaji: "miru", pos: "verb" },
    "時間": { reading: "じかん", romaji: "jikan", pos: "noun" },
    "本": { reading: "ほん", romaji: "hon", pos: "noun" },
    "友達": { reading: "ともだち", romaji: "tomodachi", pos: "noun" },
    "学ぶ": { reading: "まなぶ", romaji: "manabu", pos: "verb" }
  };

  function getLanguage(languageId) {
    return LANGUAGES.find((language) => language.id === languageId) || null;
  }

  function isSupportedLanguage(languageId) {
    return Boolean(getLanguage(languageId));
  }

  function resolveReplacement(sourceLanguage, targetLanguage, concept) {
    if (sourceLanguage === targetLanguage && MONOLINGUAL_FORMS[targetLanguage]) {
      return MONOLINGUAL_FORMS[targetLanguage][concept];
    }
    return TARGET_FORMS[targetLanguage][concept];
  }

  function buildJapaneseWordPackage(surface) {
    const entry = JAPANESE_WORD_PACKAGES[surface];
    if (!entry) {
      return null;
    }
    return {
      version: 1,
      language_tag: "ja",
      surface,
      reading: entry.reading,
      script_forms: {
        kanji: surface,
        kana: entry.reading,
        romaji: entry.romaji
      },
      source: {
        provider: "lexishift-public-test-set"
      },
      pos: entry.pos
    };
  }

  function buildRuleset(sourceLanguage, targetLanguage) {
    if (!isSupportedLanguage(sourceLanguage) || !isSupportedLanguage(targetLanguage)) {
      throw new Error("Unsupported language pair.");
    }
    const source = getLanguage(sourceLanguage);
    const target = getLanguage(targetLanguage);
    const pair = `${sourceLanguage}-${targetLanguage}`;
    const rules = CONCEPTS.map((concept, index) => {
      const replacement = resolveReplacement(sourceLanguage, targetLanguage, concept);
      const metadata = {
        language_pair: pair,
        concept,
        test_fixture: {
          id: `public-${pair}-v1`,
          version: 1
        }
      };
      if (targetLanguage === "ja") {
        const wordPackage = buildJapaneseWordPackage(replacement);
        if (wordPackage) {
          metadata.word_package = wordPackage;
        }
      }
      return {
        source_phrase: SOURCE_FORMS[sourceLanguage][concept],
        replacement,
        priority: CONCEPTS.length - index,
        case_policy: "as-is",
        enabled: true,
        metadata
      };
    });
    return {
      lexishift_share: {
        version: 2,
        scope: "ruleset"
      },
      data: {
        ruleset: {
          name: `LexiShift test set — ${source.label} to ${target.label}`,
          rules,
          metadata: {
            fixtureId: `public-${pair}-v1`,
            fixtureVersion: 1,
            purpose: "public_test_fixture",
            languagePair: pair,
            sourceLanguage,
            targetLanguage,
            rulesCount: rules.length,
            samplePage: "https://lexishift.app/test-sets/"
          }
        }
      }
    };
  }

  function rulesFromEnvelope(envelope) {
    return envelope.data.ruleset.rules;
  }

  function buildFilename(sourceLanguage, targetLanguage) {
    return `lexishift-test-set-${sourceLanguage}-${targetLanguage}-v1.json`;
  }

  function formatJson(value) {
    return `${JSON.stringify(value, null, 2)}\n`;
  }

  async function copyText(value) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      await navigator.clipboard.writeText(value);
      return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) {
      throw new Error("Copy is not available in this browser.");
    }
  }

  function downloadJson(filename, payload) {
    const blob = new Blob([formatJson(payload)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function initializePicker() {
    const sourceSelect = document.querySelector("[data-test-set-source]");
    const targetSelect = document.querySelector("[data-test-set-target]");
    if (!sourceSelect || !targetSelect) {
      return;
    }

    const pairSource = document.querySelector("[data-test-set-pair-source]");
    const pairTarget = document.querySelector("[data-test-set-pair-target]");
    const pairLabel = document.querySelector("[data-test-set-pair-label]");
    const modeLabel = document.querySelector("[data-test-set-mode]");
    const rulesList = document.querySelector("[data-test-set-rules]");
    const sampleText = document.querySelector("[data-test-set-sample]");
    const jsonPreview = document.querySelector("[data-test-set-json]");
    const filenameLabel = document.querySelector("[data-test-set-filename]");
    const status = document.querySelector("[data-test-set-status]");

    LANGUAGES.forEach((language) => {
      for (const select of [sourceSelect, targetSelect]) {
        const option = document.createElement("option");
        option.value = language.id;
        option.textContent = `${language.label} · ${language.shortLabel}`;
        select.appendChild(option);
      }
    });

    const params = new URLSearchParams(globalThis.location ? globalThis.location.search : "");
    sourceSelect.value = isSupportedLanguage(params.get("source")) ? params.get("source") : "en";
    targetSelect.value = isSupportedLanguage(params.get("target")) ? params.get("target") : "ja";

    let currentEnvelope = null;

    function announce(message, tone = "success") {
      status.textContent = message;
      status.dataset.tone = tone;
    }

    function render() {
      const sourceLanguage = sourceSelect.value;
      const targetLanguage = targetSelect.value;
      const source = getLanguage(sourceLanguage);
      const target = getLanguage(targetLanguage);
      currentEnvelope = buildRuleset(sourceLanguage, targetLanguage);
      const rules = rulesFromEnvelope(currentEnvelope);

      pairSource.textContent = source.shortLabel;
      pairTarget.textContent = target.shortLabel;
      pairLabel.textContent = `${source.label} → ${target.label}`;
      modeLabel.textContent = source.sampleMode;
      sampleText.textContent = SAMPLE_TEXTS[sourceLanguage];
      if (sampleText.closest("article")) {
        sampleText.closest("article").lang = sourceLanguage;
      }
      jsonPreview.value = formatJson(currentEnvelope);
      filenameLabel.textContent = buildFilename(sourceLanguage, targetLanguage);
      rulesList.replaceChildren();

      rules.forEach((rule) => {
        const item = document.createElement("li");
        const sourceWord = document.createElement("span");
        const arrow = document.createElement("span");
        const replacement = document.createElement("strong");
        sourceWord.textContent = rule.source_phrase;
        sourceWord.className = "test-set-rule__source";
        arrow.textContent = "→";
        arrow.className = "test-set-rule__arrow";
        arrow.setAttribute("aria-hidden", "true");
        replacement.textContent = rule.replacement;
        item.append(sourceWord, arrow, replacement);
        rulesList.appendChild(item);
      });

      if (globalThis.history && globalThis.location) {
        const nextUrl = new URL(globalThis.location.href);
        nextUrl.searchParams.set("source", sourceLanguage);
        nextUrl.searchParams.set("target", targetLanguage);
        globalThis.history.replaceState(null, "", nextUrl);
      }
      announce("Test set ready.", "quiet");
    }

    sourceSelect.addEventListener("change", render);
    targetSelect.addEventListener("change", render);

    document.querySelector("[data-test-set-download]").addEventListener("click", () => {
      downloadJson(buildFilename(sourceSelect.value, targetSelect.value), currentEnvelope);
      announce("Ruleset downloaded. Import it from LexiShift’s Share Center.");
    });

    document.querySelector("[data-test-set-copy-json]").addEventListener("click", async () => {
      try {
        await copyText(formatJson(currentEnvelope));
        announce("Ruleset JSON copied.");
      } catch (error) {
        announce(error.message || "Could not copy the ruleset.", "error");
      }
    });

    document.querySelector("[data-test-set-copy-sample]").addEventListener("click", async () => {
      try {
        await copyText(SAMPLE_TEXTS[sourceSelect.value]);
        announce("Sample text copied.");
      } catch (error) {
        announce(error.message || "Could not copy the sample text.", "error");
      }
    });

    render();
  }

  const api = {
    LANGUAGES,
    CONCEPTS,
    SAMPLE_TEXTS,
    buildRuleset,
    buildFilename,
    formatJson,
    rulesFromEnvelope
  };
  root.LexiShiftTestSets = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initializePicker, { once: true });
    } else {
      initializePicker();
    }
  }
})();
