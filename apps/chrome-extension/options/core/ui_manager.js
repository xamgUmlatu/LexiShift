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
    const ids = Array.isArray(globalThis.LexiShift && globalThis.LexiShift.optionsUiManagerDomIds)
      ? globalThis.LexiShift.optionsUiManagerDomIds
      : [];

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

  collapseSrsStoryCardsAfterDelete() { this.srsStoryViewModel().collapseStoryCard(this.dom.srsStoryCurrentCard); }

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

}

(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  if (root.optionsUiManagerProfileBackgroundMethods) {
    Object.assign(UIManager.prototype, root.optionsUiManagerProfileBackgroundMethods);
  }
})();
