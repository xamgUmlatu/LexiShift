class UIManager {
  constructor(i18n) {
    this.dom = {};
    this.i18n = i18n && typeof i18n.t === "function" ? i18n : null;
    this.COLORS = {
      SUCCESS: "#3c5a2a",
      ERROR: "#b42318",
      DEFAULT: "#6c675f"
    };
    this.LINKS = {
      app: "https://lexishift.app/download",
      plugin: "https://lexishift.app/betterdiscord"
    };
    this.init();
  }

  init() {
    const ids = [
      "options-main-content",
      "enabled", "highlight-enabled", "highlight-color", "highlight-color-text",
      "max-one-per-block", "allow-adjacent", "max-replacements-per-page",
      "max-replacements-per-lemma-page", "debug-enabled", "debug-focus-word",
      "srs-enabled", "source-language", "target-language", "srs-max-active",
      "target-language-gear", "target-language-prefs-modal-backdrop",
      "target-language-prefs-modal", "target-language-prefs-modal-ok", "target-language-modules-list",
      "srs-profile-id", "srs-profile-refresh", "srs-profile-status",
      "profile-bg-backdrop-color",
      "profile-bg-opacity", "profile-bg-opacity-value",
      "profile-bg-file", "profile-bg-remove",
      "profile-bg-status", "profile-bg-preview-wrap", "profile-bg-preview",
      "profile-bg-focal-marker", "profile-bg-position-reset",
      "profile-card-theme-hue", "profile-card-theme-hue-value",
      "profile-card-theme-saturation", "profile-card-theme-saturation-value",
      "profile-card-theme-brightness", "profile-card-theme-brightness-value",
      "profile-card-theme-transparency", "profile-card-theme-transparency-value",
      "profile-card-theme-reset",
      "srs-bootstrap-top-n", "srs-initial-active-count",
      "srs-topic-interests", "srs-proficiency-estimate", "srs-challenge-target",
      "srs-proficiency-estimate-value", "srs-proficiency-estimate-saved", "srs-proficiency-estimate-restore",
      "srs-save-preferences", "srs-preferences-save-status",
      "srs-sound-enabled", "srs-highlight-color", "srs-highlight-color-text",
      "srs-semantic-admission-status", "srs-semantic-admission-status-detail",
      "srs-auto-refresh-min-feedback",
      "srs-auto-refresh-min-good-easy", "srs-auto-refresh-repeat-min-good-easy",
      "srs-auto-refresh-cooldown",
      "srs-exposure-logging-enabled",
      "srs-admission-preview", "srs-admission-preview-output",
      "srs-initialize-set", "srs-rebalance-preview", "srs-rebalance-apply",
      "srs-story-sampling-curtain",
      "srs-refresh-set", "srs-runtime-diagnostics",
      "srs-rulegen-sampled-preview",
      "srs-story-pair-list",
      "srs-story-current-card", "srs-story-current-pair", "srs-story-current-meta",
      "srs-rulegen-output", "srs-delete-story", "helper-status",
      "srs-story-start", "srs-story-flow-backdrop", "srs-story-flow",
      "srs-story-flow-close", "srs-story-flow-source-language",
      "srs-story-flow-target-language", "srs-story-flow-profile-id",
      "srs-story-flow-proficiency-estimate", "srs-story-flow-topic-interests",
      "srs-story-flow-proficiency-estimate-value",
      "srs-story-flow-max-active", "srs-story-flow-initial-active-count", "srs-story-flow-sample",
      "srs-story-flow-initialize", "srs-story-flow-preview-output",
      "srs-story-flow-busy-backdrop", "srs-story-flow-busy-message",
      "srs-story-flow-resource-check", "srs-story-flow-resource-message", "srs-story-flow-resource-list", "srs-story-flow-open-resource-settings", "srs-story-flow-retry-resources",
      "helper-last-sync", "debug-helper-test",
      "debug-semantic-pack-inventory-path", "debug-semantic-pack-id",
      "debug-semantic-pack-default-data-root", "debug-semantic-pack-data-root",
      "debug-semantic-pack-install", "debug-semantic-pack-install-output",
      "debug-helper-test-output", "debug-open-data-dir",
      "debug-open-data-dir-output", "ui-language", "rules", "save",
      "status", "rules-file", "import-file", "export-file", "file-status",
      "custom-ruleset-enabled",
      "profile-rulesets-list", "profile-rulesets-status", "profile-rulesets-refresh",
      "share-center-open-export", "share-center-open-import",
      "share-center-export-backdrop", "share-center-export-modal", "share-center-export-close",
      "share-center-import-backdrop", "share-center-import-modal", "share-center-import-close",
      "share-center-export-mode-full", "share-center-export-mode-custom", "share-center-tree-panel",
      "share-center-parent-profile", "share-center-parent-rulesets", "share-center-parent-srs",
      "share-center-parent-appearance", "share-center-parent-module-histories",
      "share-center-srs-pair-items", "share-center-srs-pair-status",
      "share-center-target-profile-settings",
      "share-center-target-appearance-theme",
      "share-center-ruleset-items", "share-center-ruleset-status",
      "share-center-module-items", "share-center-module-status",
      "share-center-summary-target", "share-center-summary-groups",
      "share-center-summary-output",
      "share-center-generate", "share-center-export-status",
      "share-center-import-file", "share-center-import-file-name", "share-center-import", "share-center-import-status",
      "share-center-status",
      "rules-updated", "rules-count", "share-code", "share-code-scope", "share-code-cjk",
      "generate-code", "import-code", "copy-code", "open-desktop-app",
      "open-bd-plugin"
    ];

    ids.forEach((id) => {
      const prop = id.replace(/-([a-z])/g, (g) => g[1].toUpperCase());
      this.dom[prop] = document.getElementById(id);
    });
    this.dom.rulesSourceInputs = Array.from(document.querySelectorAll("input[name='rules-source']"));
    this.dom.shareCenterTargetInputs = Array.from(document.querySelectorAll("input[name='share-center-target']"));
    this.dom.srsTopicInterestChipButtons = Array.from(
      document.querySelectorAll("[data-srs-topic-interest]")
    );
    this.dom.srsStoryTopicInterestChipButtons = Array.from(
      document.querySelectorAll("[data-srs-story-topic-interest]")
    );
    this.srsStoryPairSwitchHandler = null;
    if (this.dom.srsStoryPairList) {
      this.dom.srsStoryPairList.addEventListener("click", (event) => {
        const button = event.target && typeof event.target.closest === "function"
          ? event.target.closest("[data-srs-story-switch-pair]")
          : null;
        if (!button || typeof this.srsStoryPairSwitchHandler !== "function") {
          return;
        }
        const pairKey = String(button.getAttribute("data-srs-story-switch-pair") || "").trim();
        if (pairKey) {
          Promise.resolve(this.srsStoryPairSwitchHandler(pairKey)).catch((error) => {
            console.error("[LexiShift][Options] SRS story pair switch failed.", error);
          });
        }
      });
    }
    this.updateSrsStorySummary();
  }

  escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  getSelectedOptionLabel(select, fallback) {
    if (!select) return fallback;
    const option = select.options && select.selectedIndex >= 0
      ? select.options[select.selectedIndex]
      : null;
    const label = option ? String(option.textContent || option.label || option.value || "").trim() : "";
    return label || String(select.value || fallback || "").trim();
  }

  getLanguageOptionLabel(languageCode) {
    const code = String(languageCode || "").trim();
    if (!code) {
      return "";
    }
    const selects = [this.dom.sourceLanguage, this.dom.targetLanguage].filter(Boolean);
    for (const select of selects) {
      const options = Array.from(select.options || []);
      const match = options.find((option) => option.value === code);
      if (match) {
        return String(match.textContent || match.label || match.value || "").trim() || code;
      }
    }
    return code.toUpperCase();
  }

  formatSrsPairLabel(pairKey) {
    const [sourceLanguage = "", targetLanguage = ""] = String(pairKey || "").split("-");
    const sourceLabel = this.getLanguageOptionLabel(sourceLanguage);
    const targetLabel = this.getLanguageOptionLabel(targetLanguage);
    const source = sourceLabel || sourceLanguage || "Source";
    const target = targetLabel || targetLanguage || "Target";
    return this.translateMessage("label_language_pair", [source, target], `${source} -> ${target}`);
  }

  translateMessage(key, substitutions, fallback) {
    const safeFallback = String(fallback || "");
    if (!key) {
      return safeFallback;
    }
    if (this.i18n) {
      const message = this.i18n.t(key, substitutions, "");
      if (message) {
        return message;
      }
    }
    if (globalThis.chrome && chrome.i18n && typeof chrome.i18n.getMessage === "function") {
      const message = chrome.i18n.getMessage(key, substitutions);
      if (message) {
        return message;
      }
    }
    return safeFallback;
  }

  formatSrsActiveWordsLabel(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return this.translateMessage("section_srs", null, "Vocabulary Practice");
    }
    const count = String(Math.max(0, Math.round(numeric)));
    return this.translateMessage("label_srs_active_words", [count], `${count} active words`);
  }

  resolveCurrentSrsPairKey() {
    const source = this.dom.sourceLanguage ? String(this.dom.sourceLanguage.value || "").trim() : "en";
    const target = this.dom.targetLanguage ? String(this.dom.targetLanguage.value || "").trim() : "es";
    return `${source || "en"}-${target || "es"}`;
  }

  srsStoryViewModel() {
    return globalThis.LexiShift && globalThis.LexiShift.optionsSrsStoryViewModel
      ? globalThis.LexiShift.optionsSrsStoryViewModel
      : {
          currentStoryCard(profile) {
            const exists = Boolean(profile && (profile.srsStoryExists === true || profile.srsEnabled === true));
            return { exists, shouldShow: exists };
          },
          switchableStoryCards() {
            return [];
          }
        };
  }

  setSrsStoryPairSwitchHandler(handler) {
    this.srsStoryPairSwitchHandler = typeof handler === "function" ? handler : null;
  }

  updateSrsTopicChipSupport(pairKey) {
    const support = globalThis.LexiShift && globalThis.LexiShift.optionsSrsTopicSupport;
    if (!support || typeof support.applyTopicChipSupport !== "function") {
      return;
    }
    support.applyTopicChipSupport(this.dom.srsTopicInterestChipButtons, pairKey);
    support.applyTopicChipSupport(this.dom.srsStoryTopicInterestChipButtons, pairKey);
  }

  updateSrsStorySummary() {
    const pairOutput = this.dom.srsStoryCurrentPair;
    const sourceLabel = this.getSelectedOptionLabel(this.dom.sourceLanguage, "Source");
    const targetLabel = this.getSelectedOptionLabel(this.dom.targetLanguage, "Target");
    if (pairOutput) {
      pairOutput.textContent = this.translateMessage(
        "label_language_pair",
        [sourceLabel, targetLabel],
        `${sourceLabel} -> ${targetLabel}`
      );
    }
    if (this.dom.srsStoryCurrentMeta) {
      const maxActive = this.dom.srsMaxActive ? this.dom.srsMaxActive.value : "";
      this.dom.srsStoryCurrentMeta.textContent = this.formatSrsActiveWordsLabel(maxActive);
    }
    this.updateSrsTopicChipSupport(this.resolveCurrentSrsPairKey());
  }

  updateSrsStoryVisibility(profile) {
    const card = this.dom.srsStoryCurrentCard;
    if (!card) return;
    const storyCard = this.srsStoryViewModel().currentStoryCard(profile);
    card.hidden = storyCard.shouldShow !== true;
    if (storyCard.shouldShow !== true && "open" in card) card.open = false;
  }

  updateSrsStoryPairList(entriesArg) {
    const root = this.dom.srsStoryPairList;
    if (!root) {
      return;
    }
    const entries = Array.isArray(entriesArg) ? entriesArg : [];
    const currentPairKey = this.resolveCurrentSrsPairKey();
    const normalizePairKey = this.srsStoryViewModel().normalizePairKey || ((value) => String(value || "").trim());
    const normalizedCurrentPair = normalizePairKey(currentPairKey);
    const currentEntry = entries.find((entry) => (
      normalizePairKey(entry && entry.pairKey) === normalizedCurrentPair
    )) || entries.find((entry) => entry && entry.isActive === true);
    this.updateSrsCurrentStoryOrder(currentEntry);
    const visibleEntries = this.srsStoryViewModel().switchableStoryCards({
      entries,
      currentPairKey
    });
    root.hidden = visibleEntries.length === 0;
    if (!visibleEntries.length) {
      root.innerHTML = "";
      return;
    }
    root.innerHTML = visibleEntries.map((entry) => {
      const pairKey = String(entry.pairKey || "").trim();
      const rawOrder = Number(entry.creationIndex);
      const orderStyle = Number.isFinite(rawOrder)
        ? ` style="order: ${this.escapeHtml(String(rawOrder))};"`
        : "";
      const badgeKey = String(entry.badgeKey || "").trim();
      const badgeFallback = String(entry.badgeFallback || "").trim();
      const badgeText = badgeKey || badgeFallback
        ? this.translateMessage(badgeKey, null, badgeFallback)
        : "";
      const badgeClass = String(entry.badgeClass || "");
      const badgeI18n = badgeKey ? ` data-i18n="${this.escapeHtml(badgeKey)}"` : "";
      const badgeMarkup = badgeText
        ? `<span class="srs-story-badge${this.escapeHtml(badgeClass)}"${badgeI18n}>${this.escapeHtml(badgeText)}</span>`
        : "";
      const maxActive = this.formatSrsActiveWordsLabel(entry.srsMaxActive);
      const switchButton = entry.canSwitch === true
        ? `<button type="button" class="srs-story-pair-switch" data-srs-story-switch-pair="${this.escapeHtml(pairKey)}" data-i18n="button_srs_story_switch">${this.escapeHtml(this.translateMessage("button_srs_story_switch", null, "Switch"))}</button>`
        : "";
      return [
        `<article class="srs-story-pair-card" role="listitem" data-srs-story-pair="${this.escapeHtml(pairKey)}"${orderStyle}>`,
        '<div class="srs-story-pair-copy">',
        `<span class="srs-story-pair-title">${this.escapeHtml(this.formatSrsPairLabel(pairKey))}</span>`,
        `<span class="srs-story-pair-meta">${this.escapeHtml(maxActive)}</span>`,
        "</div>",
        '<div class="srs-story-pair-actions">',
        badgeMarkup,
        switchButton,
        "</div>",
        "</article>"
      ].join("");
    }).join("");
  }

  updateSrsCurrentStoryOrder(entry) {
    const card = this.dom.srsStoryCurrentCard;
    if (!card || !card.style) {
      return;
    }
    const rawOrder = Number(entry && entry.creationIndex);
    if (Number.isFinite(rawOrder)) {
      card.style.order = String(rawOrder);
    } else if (typeof card.style.removeProperty === "function") {
      card.style.removeProperty("order");
    } else {
      delete card.style.order;
    }
  }

  formatSrsProficiencyLabel(value, hasValue) {
    if (!hasValue) return "Not set";
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "Not set";
    return `${Math.round(Math.min(100, Math.max(0, numeric)))}%`;
  }

  updateSrsProficiencyDisplays(value, hasValue) {
    const label = this.formatSrsProficiencyLabel(value, hasValue);
    const savedValue = hasValue ? String(Math.round(Math.min(100, Math.max(0, Number(value))))) : "";
    if (this.dom.srsProficiencyEstimateValue) {
      this.dom.srsProficiencyEstimateValue.textContent = label;
    }
    if (this.dom.srsProficiencyEstimateSaved) {
      this.dom.srsProficiencyEstimateSaved.textContent = label;
      this.dom.srsProficiencyEstimateSaved.dataset.srsSavedHasValue = hasValue ? "true" : "false";
      this.dom.srsProficiencyEstimateSaved.dataset.srsSavedValue = savedValue;
    }
    if (this.dom.srsProficiencyEstimateRestore) {
      this.dom.srsProficiencyEstimateRestore.disabled = !hasValue;
    }
    if (this.dom.srsStoryFlowProficiencyEstimateValue) {
      this.dom.srsStoryFlowProficiencyEstimateValue.textContent = label;
    }
  }

  normalizeSrsTopicInterestList(value) {
    const source = Array.isArray(value)
      ? value
      : String(value || "").split(",");
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

  syncSrsTopicInterestChips(interestsArg) {
    const buttons = Array.isArray(this.dom.srsTopicInterestChipButtons)
      ? this.dom.srsTopicInterestChipButtons
      : [];
    if (!buttons.length) {
      return;
    }
    const interests = this.normalizeSrsTopicInterestList(
      interestsArg !== undefined
        ? interestsArg
        : (this.dom.srsTopicInterests ? this.dom.srsTopicInterests.value : "")
    );
    const selectedInterests = new Set(interests);
    buttons.forEach((button) => {
      const topic = String(button.getAttribute("data-srs-topic-interest") || "").trim();
      const selected = Boolean(topic && selectedInterests.has(topic));
      if (button.classList && typeof button.classList.toggle === "function") {
        button.classList.toggle("is-selected", selected);
      }
      if (typeof button.setAttribute === "function") {
        button.setAttribute("aria-pressed", selected ? "true" : "false");
      }
    });
  }

  setStatus(message, color) {
    const el = this.dom.status;
    if (!el) return;
    el.textContent = message;
    el.style.color = color || this.COLORS.DEFAULT;
    if (message) {
      setTimeout(() => {
        if (el.textContent === message) {
          el.textContent = "";
        }
      }, 2000);
    }
  }

  formatTimestamp(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleString();
  }

  updateRulesMeta(rules, updatedAt) {
    if (this.dom.rulesCount) {
      this.dom.rulesCount.textContent = Array.isArray(rules) ? String(rules.length) : "0";
    }
    if (this.dom.rulesUpdated) {
      this.dom.rulesUpdated.textContent = this.formatTimestamp(updatedAt);
    }
  }

  updateRulesSourceUI(source) {
    this.dom.rulesSourceInputs.forEach((input) => {
      input.checked = input.value === source;
    });
    const isFile = source === "file";
    if (this.dom.rules) this.dom.rules.disabled = isFile;
    if (this.dom.save) this.dom.save.disabled = isFile;
  }

  setHelperStatus(status, lastSync) {
    if (this.dom.helperStatus) this.dom.helperStatus.textContent = status || "—";
    if (this.dom.helperLastSync) this.dom.helperLastSync.textContent = this.formatTimestamp(lastSync);
  }

  updateSrsInputs(profile, signals) {
    this.updateSrsStoryVisibility(profile);
    if (this.srsStartCardPresenter) this.srsStartCardPresenter.update(profile);
    const signalState = signals && typeof signals === "object" ? signals : {};
    const interests = Array.isArray(signalState.interests) ? signalState.interests : [];
    const hasProficiencyEstimate = Boolean(signalState.proficiency
      && Number.isFinite(Number(signalState.proficiency.estimated_value))
    );
    const proficiencyEstimate = hasProficiencyEstimate
      ? Math.round(Math.min(1, Math.max(0, Number(signalState.proficiency.estimated_value))) * 100)
      : 50;
    const challengeTarget = signalState.difficultyPreferences
      && Number.isFinite(Number(signalState.difficultyPreferences.target_challenge_center))
      ? Math.round(Math.min(1, Math.max(0, Number(signalState.difficultyPreferences.target_challenge_center))) * 100)
      : "";
    if (this.dom.srsMaxActive) {
      this.dom.srsMaxActive.value = String(profile.srsMaxActive);
    }
    if (this.dom.srsBootstrapTopN) {
      this.dom.srsBootstrapTopN.value = "";
    }
    if (this.dom.srsInitialActiveCount) {
      this.dom.srsInitialActiveCount.value = String(profile.srsInitialActiveCount);
    }
    if (this.dom.srsTopicInterests) {
      this.dom.srsTopicInterests.value = interests.join(", ");
    }
    this.syncSrsTopicInterestChips(interests);
    this.updateSrsTopicChipSupport(this.resolveCurrentSrsPairKey());
    if (this.dom.srsProficiencyEstimate) {
      this.dom.srsProficiencyEstimate.value = String(proficiencyEstimate);
      this.dom.srsProficiencyEstimate.dataset.srsHasValue = hasProficiencyEstimate ? "true" : "false";
    }
    this.updateSrsProficiencyDisplays(proficiencyEstimate, hasProficiencyEstimate);
    if (this.dom.srsChallengeTarget) {
      this.dom.srsChallengeTarget.value = challengeTarget === "" ? "" : String(challengeTarget);
    }
    if (this.dom.srsSoundEnabled) {
      this.dom.srsSoundEnabled.checked = profile.srsSoundEnabled;
    }
    if (this.dom.srsHighlightColor) {
      this.dom.srsHighlightColor.value = profile.srsHighlightColor;
    }
    if (this.dom.srsHighlightColorText) {
      this.dom.srsHighlightColorText.value = profile.srsHighlightColor;
    }
    if (this.dom.srsFeedbackSrsEnabled) {
      this.dom.srsFeedbackSrsEnabled.checked = profile.srsFeedbackSrsEnabled;
    }
    if (this.dom.srsExposureLoggingEnabled) {
      this.dom.srsExposureLoggingEnabled.checked = profile.srsExposureLoggingEnabled;
    }
    if (this.dom.srsAutoRefreshEnabled) {
      this.dom.srsAutoRefreshEnabled.checked = profile.srsAutoRefreshEnabled !== false;
    }
    if (this.dom.srsAutoRefreshMinFeedback) {
      this.dom.srsAutoRefreshMinFeedback.value = String(profile.srsAutoRefreshMinFeedbackEvents);
    }
    if (this.dom.srsAutoRefreshMinGoodEasy) {
      this.dom.srsAutoRefreshMinGoodEasy.value = String(profile.srsAutoRefreshMinGoodEasy);
    }
    if (this.dom.srsAutoRefreshRepeatMinGoodEasy) {
      this.dom.srsAutoRefreshRepeatMinGoodEasy.value = String(profile.srsAutoRefreshRepeatMinGoodEasy);
    }
    if (this.dom.srsAutoRefreshCooldown) {
      this.dom.srsAutoRefreshCooldown.value = String(profile.srsAutoRefreshCooldownMinutes);
    }
    this.updateSrsStorySummary();
  }

  updateProfileBackgroundInputs(prefs) {
    const source = prefs && typeof prefs === "object" ? prefs : {};
    const hasAsset = Boolean(String(source.backgroundAssetId || "").trim());
    const themePrefs = globalThis.LexiShift
      && globalThis.LexiShift.profileUiThemePrefs
      && typeof globalThis.LexiShift.profileUiThemePrefs === "object"
      ? globalThis.LexiShift.profileUiThemePrefs
      : {};
    const resolveCardThemeLimits = typeof themePrefs.resolveCardThemeLimits === "function"
      ? themePrefs.resolveCardThemeLimits
      : () => ({
          hueDeg: { min: -180, max: 180, step: 1, defaultValue: 0 },
          saturationPercent: { min: 70, max: 140, step: 1, defaultValue: 100 },
          brightnessPercent: { min: 80, max: 125, step: 1, defaultValue: 100 },
          transparencyPercent: { min: 40, max: 100, step: 1, defaultValue: 100 }
        });
    const normalizeCardThemePrefs = typeof themePrefs.normalizeCardThemePrefs === "function"
      ? themePrefs.normalizeCardThemePrefs
      : () => ({
          cardThemeHueDeg: 0,
          cardThemeSaturationPercent: 100,
          cardThemeBrightnessPercent: 100,
          cardThemeTransparencyPercent: 100
        });
    const cardThemeLimits = resolveCardThemeLimits();
    const normalizedCardTheme = normalizeCardThemePrefs(source, {
      fallback: source
    });
    if (this.dom.profileBgBackdropColor) {
      this.dom.profileBgBackdropColor.value = String(source.backgroundBackdropColor || "#fbf7f0");
      this.dom.profileBgBackdropColor.disabled = false;
    }
    if (this.dom.profileBgOpacity) {
      const opacity = Number.isFinite(Number(source.backgroundOpacity))
        ? Number(source.backgroundOpacity)
        : 0.18;
      const percent = Math.round(Math.min(1, Math.max(0, opacity)) * 100);
      this.dom.profileBgOpacity.value = String(percent);
      this.dom.profileBgOpacity.disabled = false;
    }
    if (this.dom.profileBgOpacityValue) {
      const opacityValue = this.dom.profileBgOpacity
        ? Number(this.dom.profileBgOpacity.value || 18)
        : 18;
      this.dom.profileBgOpacityValue.textContent = `${Math.round(opacityValue)}%`;
    }
    if (this.dom.profileBgRemove) {
      this.dom.profileBgRemove.disabled = !hasAsset;
    }
    if (this.dom.profileBgPositionReset) {
      this.dom.profileBgPositionReset.disabled = false;
    }
    if (this.dom.profileCardThemeHue) {
      const hue = Number.isFinite(Number(normalizedCardTheme.cardThemeHueDeg))
        ? Number(normalizedCardTheme.cardThemeHueDeg)
        : Number(cardThemeLimits.hueDeg.defaultValue);
      this.dom.profileCardThemeHue.min = String(cardThemeLimits.hueDeg.min);
      this.dom.profileCardThemeHue.max = String(cardThemeLimits.hueDeg.max);
      this.dom.profileCardThemeHue.step = String(cardThemeLimits.hueDeg.step || 1);
      this.dom.profileCardThemeHue.value = String(Math.round(hue));
      this.dom.profileCardThemeHue.disabled = false;
    }
    if (this.dom.profileCardThemeHueValue) {
      const hueValue = this.dom.profileCardThemeHue
        ? Number(this.dom.profileCardThemeHue.value || 0)
        : Number(cardThemeLimits.hueDeg.defaultValue);
      this.dom.profileCardThemeHueValue.textContent = `${Math.round(hueValue)}°`;
    }
    if (this.dom.profileCardThemeSaturation) {
      const saturation = Number.isFinite(Number(normalizedCardTheme.cardThemeSaturationPercent))
        ? Number(normalizedCardTheme.cardThemeSaturationPercent)
        : Number(cardThemeLimits.saturationPercent.defaultValue);
      this.dom.profileCardThemeSaturation.min = String(cardThemeLimits.saturationPercent.min);
      this.dom.profileCardThemeSaturation.max = String(cardThemeLimits.saturationPercent.max);
      this.dom.profileCardThemeSaturation.step = String(cardThemeLimits.saturationPercent.step || 1);
      this.dom.profileCardThemeSaturation.value = String(Math.round(saturation));
      this.dom.profileCardThemeSaturation.disabled = false;
    }
    if (this.dom.profileCardThemeSaturationValue) {
      const saturationValue = this.dom.profileCardThemeSaturation
        ? Number(this.dom.profileCardThemeSaturation.value || 100)
        : Number(cardThemeLimits.saturationPercent.defaultValue);
      this.dom.profileCardThemeSaturationValue.textContent = `${Math.round(saturationValue)}%`;
    }
    if (this.dom.profileCardThemeBrightness) {
      const brightness = Number.isFinite(Number(normalizedCardTheme.cardThemeBrightnessPercent))
        ? Number(normalizedCardTheme.cardThemeBrightnessPercent)
        : Number(cardThemeLimits.brightnessPercent.defaultValue);
      this.dom.profileCardThemeBrightness.min = String(cardThemeLimits.brightnessPercent.min);
      this.dom.profileCardThemeBrightness.max = String(cardThemeLimits.brightnessPercent.max);
      this.dom.profileCardThemeBrightness.step = String(cardThemeLimits.brightnessPercent.step || 1);
      this.dom.profileCardThemeBrightness.value = String(Math.round(brightness));
      this.dom.profileCardThemeBrightness.disabled = false;
    }
    if (this.dom.profileCardThemeBrightnessValue) {
      const brightnessValue = this.dom.profileCardThemeBrightness
        ? Number(this.dom.profileCardThemeBrightness.value || 100)
        : Number(cardThemeLimits.brightnessPercent.defaultValue);
      this.dom.profileCardThemeBrightnessValue.textContent = `${Math.round(brightnessValue)}%`;
    }
    if (this.dom.profileCardThemeTransparency) {
      const transparency = Number.isFinite(Number(normalizedCardTheme.cardThemeTransparencyPercent))
        ? Number(normalizedCardTheme.cardThemeTransparencyPercent)
        : Number(cardThemeLimits.transparencyPercent.defaultValue);
      this.dom.profileCardThemeTransparency.min = String(cardThemeLimits.transparencyPercent.min);
      this.dom.profileCardThemeTransparency.max = String(cardThemeLimits.transparencyPercent.max);
      this.dom.profileCardThemeTransparency.step = String(cardThemeLimits.transparencyPercent.step || 1);
      this.dom.profileCardThemeTransparency.value = String(Math.round(transparency));
      this.dom.profileCardThemeTransparency.disabled = false;
    }
    if (this.dom.profileCardThemeTransparencyValue) {
      const transparencyValue = this.dom.profileCardThemeTransparency
        ? Number(this.dom.profileCardThemeTransparency.value || 100)
        : Number(cardThemeLimits.transparencyPercent.defaultValue);
      this.dom.profileCardThemeTransparencyValue.textContent = `${Math.round(transparencyValue)}%`;
    }
    if (this.dom.profileCardThemeReset) {
      this.dom.profileCardThemeReset.disabled = false;
    }
  }
}
