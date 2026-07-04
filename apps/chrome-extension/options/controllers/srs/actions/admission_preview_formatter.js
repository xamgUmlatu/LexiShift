(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatTopicWeightsSummary(topicWeights) {
    if (!topicWeights || typeof topicWeights !== "object") {
      return "none";
    }
    return Object.entries(topicWeights)
      .filter((entry) => Number.isFinite(Number(entry[1])))
      .sort((left, right) => Number(right[1]) - Number(left[1]))
      .slice(0, 8)
      .map((entry) => `${entry[0]}=${Number(entry[1]).toFixed(2)}`)
      .join(", ") || "none";
  }

  function formatSignalSourcesSummary(signalSources) {
    if (!signalSources || typeof signalSources !== "object") {
      return "none";
    }
    return Object.entries(signalSources)
      .filter((entry) => entry[1] !== null && entry[1] !== undefined && entry[1] !== "")
      .sort((left, right) => String(left[0]).localeCompare(String(right[0])))
      .map((entry) => `${entry[0]}=${entry[1]}`)
      .join(", ") || "none";
  }

  function formatTopicSupportLine(entry) {
    if (!entry || typeof entry !== "object") {
      return null;
    }
    const topic = String(entry.topic || "").trim();
    if (!topic) {
      return null;
    }
    const candidateCount = Number.isFinite(Number(entry.candidate_count))
      ? Number(entry.candidate_count)
      : null;
    const supportMass = Number.isFinite(Number(entry.support_mass))
      ? Number(entry.support_mass).toFixed(3)
      : null;
    const scarcityMultiplier = Number.isFinite(Number(entry.scarcity_multiplier_preview))
      ? Number(entry.scarcity_multiplier_preview)
      : null;
    const readiness = String(entry.scarcity_readiness || "").trim() || "unknown";
    const examples = Array.isArray(entry.top_examples)
      ? entry.top_examples.map((value) => String(value || "").trim()).filter(Boolean).slice(0, 5)
      : [];
    const reasons = Array.isArray(entry.scarcity_readiness_reasons)
      ? entry.scarcity_readiness_reasons.map((value) => String(value || "").trim()).filter(Boolean)
      : [];
    const parts = [];
    if (candidateCount !== null) {
      parts.push(`candidates=${candidateCount}`);
    }
    if (supportMass !== null) {
      parts.push(`mass=${supportMass}`);
    }
    if (scarcityMultiplier !== null && scarcityMultiplier > 1.0) {
      parts.push(`multiplier=${scarcityMultiplier.toFixed(2)}`);
    }
    parts.push(`readiness=${readiness}`);
    if (reasons.length) {
      parts.push(`reasons=${reasons.join(",")}`);
    }
    if (examples.length) {
      parts.push(`examples=${examples.join(", ")}`);
    }
    return `- ${topic}: ${parts.join(" | ")}`;
  }

  function formatTopicAffinitySource(source) {
    const value = String(source || "").trim();
    if (!value) {
      return "";
    }
    if (value.startsWith("topic_hint:")) {
      return value.slice("topic_hint:".length);
    }
    if (value.startsWith("lexical:")) {
      return value.slice("lexical:".length);
    }
    return value;
  }

  function topicForAdmissionEntry(entry) {
    const signals = entry && entry.signals && typeof entry.signals === "object"
      ? entry.signals
      : {};
    const topic = formatTopicAffinitySource(signals.topic_affinity_source);
    return topic && topic !== "none" ? topic : "general";
  }

  function formatTopicLabel(topic, translate) {
    const normalized = String(topic || "general").trim() || "general";
    const fallback = normalized.replace(/_/g, " ");
    if (typeof translate === "function") {
      return translate(`topic_srs_${normalized}`, null, fallback);
    }
    return fallback;
  }

  function buildSimpleWordsHtml(admittedWords, options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const items = admittedWords
      .map((entry) => {
        const lemma = String(entry && entry.lemma ? entry.lemma : "").trim();
        if (!lemma) {
          return "";
        }
        const topic = topicForAdmissionEntry(entry);
        const topicLabel = formatTopicLabel(topic, translate);
        const topicClass = topic === "general" ? "is-general" : "is-topic";
        return [
          '<li class="srs-admission-word-item">',
          `<span class="srs-admission-word-lemma">${escapeHtml(lemma)}</span>`,
          `<span class="srs-admission-word-topic ${topicClass}">${escapeHtml(topicLabel)}</span>`,
          "</li>"
        ].join("");
      })
      .filter(Boolean);
    return items.length ? `<ul class="srs-admission-word-list">${items.join("")}</ul>` : "";
  }

  function buildTopicSummaryHtml(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const interests = Array.isArray(opts.interests) ? opts.interests : [];
    const admittedWords = Array.isArray(opts.admittedWords) ? opts.admittedWords : [];
    const activeTopicSupportEntries = Array.isArray(opts.activeTopicSupportEntries)
      ? opts.activeTopicSupportEntries
      : [];
    const profileTopicOverlay = opts.profileTopicOverlay && typeof opts.profileTopicOverlay === "object"
      ? opts.profileTopicOverlay
      : {};
    const selectedLabels = interests.map((topic) => formatTopicLabel(topic, translate));
    const sampledTopicWords = admittedWords.filter((entry) => topicForAdmissionEntry(entry) !== "general").length;
    const candidateCount = activeTopicSupportEntries.reduce((total, entry) => {
      const count = Number(entry && entry.candidate_count);
      return total + (Number.isFinite(count) ? count : 0);
    }, 0);
    const appliedSeedCount = Number(profileTopicOverlay.applied_seed_count);
    const overlayStatus = String(profileTopicOverlay.application_status || profileTopicOverlay.status || "").trim();
    const parts = [];
    if (selectedLabels.length) {
      parts.push(translate("summary_srs_admission_preview_selected_topics", [selectedLabels.join(", ")], `Selected topics: ${selectedLabels.join(", ")}.`));
      parts.push(translate("summary_srs_admission_preview_sampled_topic_words", [sampledTopicWords], `${sampledTopicWords} sampled topic ${sampledTopicWords === 1 ? "word" : "words"}.`));
      if (candidateCount > 0) {
        parts.push(translate("summary_srs_admission_preview_matched_candidates", [candidateCount], `${candidateCount} matched candidates in the preview frontier.`));
      } else if (Number.isFinite(appliedSeedCount) && appliedSeedCount === 0) {
        parts.push(translate("summary_srs_admission_preview_no_topic_candidates", null, "No matching candidates for those topics in this preview window."));
      } else if (overlayStatus) {
        parts.push(translate("summary_srs_admission_preview_overlay_status", [overlayStatus], `Overlay status: ${overlayStatus}.`));
      }
    } else {
      parts.push(translate("summary_srs_admission_preview_no_topic_priorities", null, "No topic priorities reached the helper for this sample."));
    }
    return `<p class="srs-admission-preview-topic-summary">${escapeHtml(parts.join(" "))}</p>`;
  }

  function buildAdmissionPreviewOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const srsPair = String(opts.srsPair || "en-en");
    const profileId = String(opts.profileId || "default");
    const plan = opts.plan && typeof opts.plan === "object" ? opts.plan : {};
    const preview = opts.preview && typeof opts.preview === "object" ? opts.preview : {};
    const bootstrapTopN = Number.isFinite(Number(opts.bootstrapTopN))
      ? Number(opts.bootstrapTopN)
      : (
          Number.isFinite(Number(preview.preview_bootstrap_top_n_default))
            ? Number(preview.preview_bootstrap_top_n_default)
            : (preview.selected_unique_count ?? "n/a")
        );
    const bootstrapTopNDetail = `${bootstrapTopN}${
      opts.previewFrontierCapApplied || preview.preview_frontier_cap_applied
        ? " (preview cap)"
        : ""
    }`;
    const requestProfileContextMeta = (
      opts.requestProfileContextMeta && typeof opts.requestProfileContextMeta === "object"
    )
      ? opts.requestProfileContextMeta
      : {};
    const profileBootstrap = preview.profile_bootstrap && typeof preview.profile_bootstrap === "object"
      ? preview.profile_bootstrap
      : {};
    const profileContext = profileBootstrap.profile_context && typeof profileBootstrap.profile_context === "object"
      ? profileBootstrap.profile_context
      : {};
    const activeSignals = Array.isArray(profileContext.active_signals)
      ? profileContext.active_signals
      : [];
    const missingSignals = Array.isArray(profileContext.missing_signals)
      ? profileContext.missing_signals
      : [];
    const interests = Array.isArray(profileContext.interests)
      ? profileContext.interests
      : [];
    const rawProfileKeys = Array.isArray(profileContext.raw_profile_keys)
      ? profileContext.raw_profile_keys
      : [];
    const explicitTopicWeights = profileContext.explicit_topic_weights && typeof profileContext.explicit_topic_weights === "object"
      ? profileContext.explicit_topic_weights
      : {};
    const implicitTopicWeights = profileContext.implicit_topic_weights && typeof profileContext.implicit_topic_weights === "object"
      ? profileContext.implicit_topic_weights
      : {};
    const mergedTopicWeights = profileContext.topic_weights && typeof profileContext.topic_weights === "object"
      ? profileContext.topic_weights
      : {};
    const signalSources = profileContext.signal_sources && typeof profileContext.signal_sources === "object"
      ? profileContext.signal_sources
      : {};
    const activeTopicSupport = profileBootstrap.active_topic_support
      && typeof profileBootstrap.active_topic_support === "object"
      ? profileBootstrap.active_topic_support
      : {};
    const activeTopicSupportEntries = Array.isArray(activeTopicSupport.topics)
      ? activeTopicSupport.topics
      : [];
    const profileTopicOverlay = profileBootstrap.profile_topic_overlay
      && typeof profileBootstrap.profile_topic_overlay === "object"
      ? profileBootstrap.profile_topic_overlay
      : {};
    const admittedWords = Array.isArray(preview.admitted_words) ? preview.admitted_words : [];
    const notes = Array.isArray(plan.notes) ? plan.notes : [];
    const lines = [
      translate(
        "status_srs_admission_preview_header",
        [
          preview.sample_count_effective ?? admittedWords.length,
          preview.admitted_count ?? 0,
          srsPair
        ],
        `Next-word sample: ${preview.sample_count_effective ?? admittedWords.length} shown / ${preview.admitted_count ?? 0} possible words for ${srsPair}.`
      )
    ];
    if (plan.can_execute && admittedWords.length) {
      lines.push("");
      lines.push(translate("label_srs_admission_preview_sampled_words", null, "Sampled words:"));
      admittedWords.forEach((entry) => {
        const lemma = String(entry && entry.lemma ? entry.lemma : "").trim();
        if (!lemma) {
          return;
        }
        const posBucket = String(entry && entry.pos_bucket ? entry.pos_bucket : "").trim();
        const rankDelta = Number.isFinite(Number(entry && entry.rank_delta))
          ? Number(entry.rank_delta)
          : null;
        const profileScore = Number.isFinite(Number(entry && entry.profile_score))
          ? Number(entry.profile_score).toFixed(3)
          : null;
        const signals = entry && entry.signals && typeof entry.signals === "object"
          ? entry.signals
          : {};
        const topicAffinitySource = formatTopicAffinitySource(signals.topic_affinity_source);
        const detailParts = [];
        if (posBucket) {
          detailParts.push(posBucket);
        }
        if (topicAffinitySource) {
          detailParts.push(`topic=${topicAffinitySource}`);
        }
        if (profileScore !== null) {
          detailParts.push(`score=${profileScore}`);
        }
        if (rankDelta !== null) {
          detailParts.push(`delta=${rankDelta >= 0 ? "+" : ""}${rankDelta}`);
        }
        lines.push(detailParts.length ? `- ${lemma} [${detailParts.join(", ")}]` : `- ${lemma}`);
        const explanation = String(entry && entry.explanation ? entry.explanation : "").trim();
        if (explanation) {
          lines.push(`  ${explanation}`);
        }
      });
    }
    lines.push("");
    lines.push(translate("label_srs_admission_preview_sample_details", null, "Sample details:"));
    lines.push(
      `- profile_id: ${profileId}`,
      `- strategy_requested: ${plan.strategy_requested || "n/a"}`,
      `- strategy_effective: ${plan.strategy_effective || "n/a"}`,
      `- execution_mode: ${plan.execution_mode || "n/a"}`,
      `- bootstrap_top_n: ${bootstrapTopNDetail}`,
      `- initial_active_count: ${preview.admitted_count ?? "n/a"}`,
      `- sample_count_requested: ${preview.sample_count_requested ?? "n/a"}`,
      `- sample_count_effective: ${preview.sample_count_effective ?? admittedWords.length}`,
      `- sampling_mode: ${preview.sampling_mode || "ranked"}`,
      `- sampling_pool_count: ${preview.sampling_pool_count ?? preview.admitted_count ?? "n/a"}`,
      `- selection_seed: ${preview.selection_seed ?? "none"}`,
      `- active_signals: ${activeSignals.length ? activeSignals.join(", ") : "none"}`,
      `- missing_signals: ${missingSignals.length ? missingSignals.join(", ") : "none"}`
    );
    lines.push("");
    lines.push(translate("label_srs_admission_preview_effective_profile_context", null, "Effective profile context:"));
    lines.push(`- context_source: ${requestProfileContextMeta.source || "saved_profile"}`);
    lines.push(
      `- pending_form_overrides: ${
        Array.isArray(requestProfileContextMeta.pendingOverrides)
        && requestProfileContextMeta.pendingOverrides.length
          ? requestProfileContextMeta.pendingOverrides.join(", ")
          : "none"
      }`
    );
    lines.push(`- raw_profile_keys: ${rawProfileKeys.length ? rawProfileKeys.join(", ") : "none"}`);
    lines.push(`- interests: ${interests.length ? interests.join(", ") : "none"}`);
    lines.push(`- proficiency_estimate: ${profileContext.proficiency_estimate ?? "none"}`);
    lines.push(`- challenge_target: ${profileContext.challenge_target ?? "none"}`);
    lines.push(`- challenge_spread: ${profileContext.challenge_spread ?? "none"}`);
    lines.push(`- explicit_topic_weights: ${formatTopicWeightsSummary(explicitTopicWeights)}`);
    lines.push(`- implicit_topic_weights: ${formatTopicWeightsSummary(implicitTopicWeights)}`);
    lines.push(`- topic_weights: ${formatTopicWeightsSummary(mergedTopicWeights)}`);
    lines.push(`- signal_sources: ${formatSignalSourcesSummary(signalSources)}`);
    if (profileTopicOverlay.status || profileTopicOverlay.application_status) {
      lines.push("");
      lines.push(translate("label_srs_admission_preview_topic_overlay", null, "Topic overlay:"));
      lines.push(`- status: ${profileTopicOverlay.status || "unknown"}`);
      lines.push(`- application_status: ${profileTopicOverlay.application_status || "n/a"}`);
      lines.push(`- scope: ${profileTopicOverlay.runtime_scope || "admission_preview_only"}`);
      lines.push(`- active_topics: ${
        Array.isArray(profileTopicOverlay.active_topics) && profileTopicOverlay.active_topics.length
          ? profileTopicOverlay.active_topics.join(", ")
          : "none"
      }`);
      lines.push(`- applied_seed_count: ${profileTopicOverlay.applied_seed_count ?? 0}`);
      lines.push(`- applied_row_count: ${profileTopicOverlay.applied_row_count ?? 0}`);
    }
    if (activeTopicSupportEntries.length) {
      lines.push("");
      lines.push(translate("label_srs_admission_preview_neutral_topic_support", null, "Neutral frontier topic support:"));
      activeTopicSupportEntries
        .slice(0, 8)
        .map((entry) => formatTopicSupportLine(entry))
        .filter(Boolean)
        .forEach((line) => lines.push(line));
    }
    if (!plan.can_execute) {
      lines.push("");
      lines.push(
        translate(
          "status_srs_admission_preview_plan_only",
          null,
          "Preview unavailable because the selected strategy is planner-only."
        )
      );
      if (notes.length) {
        lines.push("");
        lines.push(translate("label_srs_admission_preview_plan_notes", null, "Plan notes:"));
        notes.forEach((note) => lines.push(`- ${note}`));
      }
      return lines.join("\n");
    }
    if (!admittedWords.length) {
      lines.push("");
      lines.push(
        translate(
          "status_srs_admission_preview_empty",
          [srsPair],
          `No admission sample is available for ${srsPair}.`
        )
      );
      if (notes.length) {
        lines.push("");
        lines.push(translate("label_srs_admission_preview_plan_notes", null, "Plan notes:"));
        notes.forEach((note) => lines.push(`- ${note}`));
      }
      return lines.join("\n");
    }
    return lines.join("\n");
  }

  function buildAdmissionPreviewView(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const srsPair = String(opts.srsPair || "en-en");
    const plan = opts.plan && typeof opts.plan === "object" ? opts.plan : {};
    const preview = opts.preview && typeof opts.preview === "object" ? opts.preview : {};
    const admittedWords = Array.isArray(preview.admitted_words) ? preview.admitted_words : [];
    const advancedText = buildAdmissionPreviewOutput(options);
    const shownCount = preview.sample_count_effective ?? admittedWords.length;
    const possibleCount = preview.admitted_count ?? 0;
    const summary = translate("summary_srs_admission_preview_showing", [shownCount, possibleCount, srsPair], `Showing ${shownCount} of ${possibleCount} possible words for ${srsPair}.`);
    const bodyHtml = plan.can_execute && admittedWords.length
      ? buildSimpleWordsHtml(admittedWords, { translate })
      : `<p class="srs-admission-preview-empty">${escapeHtml(
          plan.can_execute
            ? translate("status_srs_admission_preview_empty", [srsPair], `No admission sample is available for ${srsPair}.`)
            : translate("status_srs_admission_preview_plan_only", null, "Preview unavailable for the selected strategy.")
        )}</p>`;
    const profileBootstrap = preview.profile_bootstrap && typeof preview.profile_bootstrap === "object"
      ? preview.profile_bootstrap
      : {};
    const profileContext = profileBootstrap.profile_context && typeof profileBootstrap.profile_context === "object"
      ? profileBootstrap.profile_context
      : {};
    const activeTopicSupport = profileBootstrap.active_topic_support
      && typeof profileBootstrap.active_topic_support === "object"
      ? profileBootstrap.active_topic_support
      : {};
    const profileTopicOverlay = profileBootstrap.profile_topic_overlay
      && typeof profileBootstrap.profile_topic_overlay === "object"
      ? profileBootstrap.profile_topic_overlay
      : {};
    const topicSummaryHtml = buildTopicSummaryHtml({
      translate,
      interests: Array.isArray(profileContext.interests) ? profileContext.interests : [],
      admittedWords,
      activeTopicSupportEntries: Array.isArray(activeTopicSupport.topics) ? activeTopicSupport.topics : [],
      profileTopicOverlay
    });
    const html = [
      '<div class="srs-admission-preview-view">',
      `<p class="srs-admission-preview-note">${escapeHtml(translate("note_srs_admission_preview_sample_only", null, "Sample only. No words were added."))}</p>`,
      `<p class="srs-admission-preview-summary">${escapeHtml(summary)}</p>`,
      topicSummaryHtml,
      bodyHtml,
      '<details class="srs-admission-preview-advanced">',
      `<summary>${escapeHtml(translate("label_srs_admission_preview_advanced_details", null, "Advanced details"))}</summary>`,
      `<pre>${escapeHtml(advancedText)}</pre>`,
      "</details>",
      "</div>"
    ].join("");
    return {
      html,
      text: advancedText
    };
  }

  root.optionsSrsAdmissionPreviewFormatter = {
    buildAdmissionPreviewOutput,
    buildAdmissionPreviewView
  };
})();
