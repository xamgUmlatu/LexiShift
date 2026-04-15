(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function buildSampledRulegenSamplingLines(options) {
    const opts = options && typeof options === "object" ? options : {};
    const sampling = opts.sampling && typeof opts.sampling === "object" ? opts.sampling : {};
    const sampledLemmas = Array.isArray(opts.sampledLemmas) ? opts.sampledLemmas : [];
    const sampleCount = Number(opts.sampleCount || 0);
    const sampledCount = Number(opts.sampledCount || sampledLemmas.length || 0);
    return [
      `- strategy_requested: ${sampling.strategy_requested || "n/a"}`,
      `- strategy_effective: ${sampling.strategy_effective || "n/a"}`,
      `- sample_count_requested: ${sampleCount || sampling.sample_count_requested || "n/a"}`,
      `- sample_count_effective: ${sampledCount}`,
      `- total_items_for_pair: ${sampling.total_items_for_pair ?? "n/a"}`
    ];
  }

  function buildSampledRulegenHeader(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const sampledCount = Number(opts.sampledCount || 0);
    const rulegenTargets = Number(opts.rulegenTargets || 0);
    const rulegenRules = Number(opts.rulegenRules || 0);
    const duration = Number(opts.duration || 0);
    return translate(
      "status_srs_rulegen_sampled_summary",
      [sampledCount, rulegenTargets, rulegenRules, duration.toFixed(1)],
      `Sampled rulegen: ${sampledCount} words, ${rulegenTargets} targets, ${rulegenRules} rules (${duration.toFixed(1)}s)`
    );
  }

  function buildSampledRulegenEmptyOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.translate);
    const header = String(opts.header || "");
    const samplingLines = Array.isArray(opts.samplingLines) ? opts.samplingLines : [];
    const diagnostics = opts.diagnostics && typeof opts.diagnostics === "object" ? opts.diagnostics : {};
    const srsPair = String(opts.srsPair || "en-en");
    const storeSample = Array.isArray(diagnostics.store_sample) ? diagnostics.store_sample : [];
    const lines = [header, ...samplingLines, ""];
    lines.push(
      translate(
        "status_srs_rulegen_sampled_empty",
        null,
        "There are no rules for the current words."
      )
    );
    lines.push("");
    lines.push("Diagnostics:");
    lines.push(`- pair: ${srsPair}`);
    lines.push(`- jmdict: ${diagnostics.jmdict_path || "n/a"} (exists=${diagnostics.jmdict_exists === true})`);
    lines.push(`- freedict: ${diagnostics.freedict_de_en_path || "n/a"} (exists=${diagnostics.freedict_de_en_exists === true})`);
    lines.push(`- set_source_db: ${diagnostics.set_source_db || "n/a"} (exists=${diagnostics.set_source_db_exists === true})`);
    lines.push(`- store_items: ${diagnostics.store_items ?? 0}`);
    lines.push(`- store_items_for_pair: ${diagnostics.store_items_for_pair ?? 0}`);
    lines.push(`- store_sample: ${storeSample.join(", ")}`);
    return lines.join("\n");
  }

  function buildSampledRulegenTargetsOutput(options) {
    const opts = options && typeof options === "object" ? options : {};
    const header = String(opts.header || "");
    const samplingLines = Array.isArray(opts.samplingLines) ? opts.samplingLines : [];
    const targets = Array.isArray(opts.targets) ? opts.targets : [];
    const lines = [header, ...samplingLines, ""];
    targets.forEach((target) => {
      const lemma = target && target.source && target.source.lemma
        ? String(target.source.lemma)
        : "(unknown)";
      const ruleCount = Array.isArray(target && target.rules) ? target.rules.length : 0;
      lines.push(`- ${lemma} (${ruleCount} rules)`);
      const rules = Array.isArray(target && target.rules) ? target.rules : [];
      rules.slice(0, 5).forEach((rule) => {
        if (!rule || typeof rule !== "object") {
          return;
        }
        const rendered = [
          String(rule.kind || "rule"),
          rule.output ? `output=${String(rule.output)}` : "",
          Number.isFinite(Number(rule.weight)) ? `weight=${Number(rule.weight).toFixed(3)}` : ""
        ].filter((part) => part).join(", ");
        lines.push(`  - ${rendered}`);
      });
      if (rules.length > 5) {
        lines.push(`  - ... ${rules.length - 5} more`);
      }
    });
    return lines.join("\n");
  }

  root.optionsSrsSampledRulegenFormatter = {
    buildSampledRulegenSamplingLines,
    buildSampledRulegenHeader,
    buildSampledRulegenEmptyOutput,
    buildSampledRulegenTargetsOutput
  };
})();
