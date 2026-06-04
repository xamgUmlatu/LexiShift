---
---

(() => {
  const configuration = {{ site.data.landing_visual_mocks | jsonify }};
  const root = document.querySelector("[data-landing-mock-root]");
  if (!root || !configuration || !Array.isArray(configuration.mocks)) {
    return;
  }

  const mocksById = new Map();
  configuration.mocks.forEach((mock) => {
    if (mock && typeof mock.id === "string") {
      mocksById.set(mock.id, mock);
    }
  });

  if (mocksById.size === 0) {
    return;
  }

  const aliases = configuration.aliases || {};
  const defaultMock = mocksById.has(configuration.defaultMock)
    ? configuration.defaultMock
    : configuration.mocks[0].id;

  const normalizeKey = (value) =>
    String(value || "")
      .trim()
      .toLowerCase()
      .replace(/_/g, "-");

  const resolveMockId = (value) => {
    const normalized = normalizeKey(value);
    if (!normalized) {
      return "";
    }
    if (mocksById.has(normalized)) {
      return normalized;
    }
    return aliases[normalized] || "";
  };

  const query = new URLSearchParams(window.location.search);
  const requestedMock = query.get("mock") || query.get("visual-mock") || query.get("lp");
  const initialMockId = resolveMockId(requestedMock) || defaultMock;

  const setText = (selector, value) => {
    const target = root.querySelector(selector);
    if (target) {
      target.textContent = String(value || "");
    }
  };

  const setSentence = (mock) => {
    const sentence = root.querySelector("[data-landing-mock-sentence]");
    if (!sentence) {
      return;
    }

    sentence.replaceChildren(
      document.createTextNode(mock.sentencePrefix || ""),
      Object.assign(document.createElement("span"), {
        textContent: mock.targetWord || "",
      }),
      document.createTextNode(mock.sentenceSuffix || ""),
    );
  };

  const setFeedback = (mock) => {
    const feedback = root.querySelector("[data-landing-mock-feedback]");
    if (!feedback) {
      return;
    }

    feedback.replaceChildren();
    const token = document.createElement("strong");
    token.textContent = mock.targetWord || "";
    feedback.append(token);

    const gloss = document.createElement("em");
    gloss.textContent = mock.gloss || mock.sourceWord || "";
    feedback.append(gloss);

    (mock.feedback || []).forEach((label) => {
      const option = document.createElement("span");
      option.textContent = label;
      feedback.append(option);
    });
  };

  const applyMock = (mock) => {
    if (!mock) {
      return "";
    }

    root.dataset.landingMockActive = mock.id;
    document.documentElement.dataset.landingVisualMock = mock.id;
    setText("[data-landing-mock-label]", `${mock.label || mock.id} reading view`);
    setText("[data-landing-mock-source]", mock.sourceWord);
    setText("[data-landing-mock-target]", mock.targetWord);
    setText("[data-landing-mock-profile]", mock.profile);
    setText("[data-landing-mock-ruleset]", mock.ruleset);
    setText("[data-landing-mock-runtime]", mock.runtime);
    setSentence(mock);
    setFeedback(mock);
    return mock.id;
  };

  const api = {
    apply: (key) => applyMock(mocksById.get(resolveMockId(key))),
    data: configuration,
    defaultMock,
    keys: Array.from(mocksById.keys()),
  };

  window.LexiShiftLandingVisualMocks = Object.freeze(api);
  applyMock(mocksById.get(initialMockId) || mocksById.get(defaultMock));
})();
