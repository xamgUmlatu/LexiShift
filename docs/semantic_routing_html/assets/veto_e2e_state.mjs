const phaseLabel = {
  offline: "Offline publication",
  runtime: "Runtime admission",
  decision: "Decision gate",
  output: "Output and feedback",
};

const f = (name, description, example) => ({ name, description, example });

export const NODE_SEQUENCE = [
  "O0",
  "O1",
  "O2",
  "O3",
  "O4",
  "O5",
  "O6",
  "O7",
  "R0",
  "R1",
  "R2",
  "R3",
  "R4",
  "R5",
  "R6",
  "R7",
  "R8",
  "R9",
  "R10",
  "R11",
  "P0",
  "P1",
  "P2",
  "P3",
  "P4",
];

export const NODE_DATA = {
  O0: {
    title: "Rulegen emits active candidate rule",
    phase: "offline",
    summary:
      "Rule generation produces an active replacement candidate. At this point the object is still mainly a lexical rule, not yet a semantic-admission package.",
    introduced: [
      f("pair", "Language pair for the candidate rule.", '"en-es"'),
      f("rule_id", "Stable emitted rule identifier.", '"en-es:ball->pelota:00123"'),
      f("source_lemma", "Source-side English lemma or expression.", '"ball"'),
      f("target_lemma", "Target-side replacement lemma.", '"pelota"'),
      f("pos", "Rulegen POS tag on the candidate.", '"noun"'),
      f("rulegen_sources", "Top source phrases or gloss fragments that justified emission.", '["ball", "sports ball", "game ball"]'),
    ],
    exampleState: {
      pair: "en-es",
      rule_id: "en-es:ball->pelota:00123",
      source_lemma: "ball",
      target_lemma: "pelota",
      pos: "noun",
      metadata: {
        rulegen: {
          source_rank: 1,
          top_sources: ["ball", "sports ball", "game ball"],
        },
      },
    },
  },
  O1: {
    title: "Attach semantic_admission pointer",
    phase: "offline",
    summary:
      "The lexical rule gains a compact pointer into the semantic sidecar. This is the contract that runtime follows later.",
    introduced: [
      f("semantic_admission.status", "Readiness state for semantic routing.", '"ready" | "unavailable" | "not_applicable"'),
      f("sense_id", "Stable active-sense identifier.", '"sense:en-es:pelota:noun:object-used-in-games"'),
      f("trigger_id", "Stable trigger-set identifier used to seed competition.", '"trigger:en-es:ball:pelota"'),
      f("competition_set_id", "Stable blocker-set identifier.", '"competition:en-es:pelota:ball:v1"'),
      f("phrase_set_id", "Optional phrase-preemption set identifier.", '"phrase:en-es:ball:v1"'),
    ],
    exampleState: {
      metadata: {
        semantic_admission: {
          status: "ready",
          sense_id: "sense:en-es:pelota:noun:object-used-in-games",
          trigger_id: "trigger:en-es:ball:pelota",
          competition_set_id: "competition:en-es:pelota:ball:v1",
          phrase_set_id: "phrase:en-es:ball:v1",
        },
      },
    },
  },
  O2: {
    title: "Generate trigger seeds",
    phase: "offline",
    summary:
      "The system proposes English trigger texts that could represent the active target. Different seed modes compete here: reviewed triggers, rulegen top sources, and forward-gloss fragments.",
    introduced: [
      f("trigger_seed_rows", "Candidate trigger rows before filtering.", '[{"trigger":"ball","seed_mode":"rulegen_top3"},{"trigger":"game ball","seed_mode":"forward_gloss"}]'),
      f("seed_mode", "Where a seed came from.", '"benchmark_reviewed" | "rulegen_top3" | "forward_gloss"'),
      f("raw_seed_text", "Original unnormalized text fragment.", '"to take, catch, hold"'),
      f("normalized_trigger", "Normalized trigger used downstream.", '"catch"'),
    ],
    exampleState: {
      trigger_seed_rows: [
        {
          trigger: "ball",
          seed_mode: "rulegen_top3",
          raw_seed_text: "ball",
        },
        {
          trigger: "sports ball",
          seed_mode: "forward_gloss",
          raw_seed_text: "sports ball",
        },
      ],
    },
  },
  O3: {
    title: "Trigger support filter",
    phase: "offline",
    summary:
      "Weak trigger seeds are removed before shadow mining. This is the first explicit upstream evidence gate and a good place to inspect post-filter trigger rows.",
    introduced: [
      f("trigger_support_score", "Numeric support score assigned to each trigger seed.", "0..N"),
      f("trigger_support_features", "Feature flags behind the trigger score.", '{"from_top3":true,"active_side_support":true,"single_token":true}'),
      f("kept_trigger_rows", "Only trigger seeds that survived filtering.", '[{"trigger":"ball","score":4,"keep":true}]'),
      f("min_trigger_score", "Sweepable threshold for keeping a trigger.", "3"),
    ],
    exampleState: {
      kept_trigger_rows: [
        {
          trigger: "ball",
          trigger_support_score: 4,
          trigger_support_features: {
            from_top3: true,
            active_side_support: true,
            single_token: true,
          },
          keep: true,
        },
      ],
      dropped_trigger_rows: [
        {
          trigger: "sports ball",
          trigger_support_score: 1,
          keep: false,
        },
      ],
      min_trigger_score: 3,
    },
  },
  O4: {
    title: "Mine shadow candidates",
    phase: "offline",
    summary:
      "For each surviving trigger, the miner gathers possible competitor lemmas from reverse lookup, forward-index support, and later a semantic-bridge lane.",
    introduced: [
      f("shadow_candidate_rows", "Unfiltered competing target rows for each (a,t).", '[{"shadow_target":"baile","source":"reverse_lookup"},{"shadow_target":"bola mala","source":"forward_index"}]'),
      f("shadow_target", "Competing target lemma.", '"baile"'),
      f("shadow_sense_id", "Stable candidate sense identifier.", '"sense:en-es:baile:noun:formal-dance"'),
      f("shadow_pos", "Candidate POS used for later penalties.", '"noun"'),
      f("candidate_support_sources", "Why this candidate was surfaced.", '["reverse_lookup","forward_index"]'),
    ],
    exampleState: {
      active_target: "pelota",
      trigger: "ball",
      shadow_candidate_rows: [
        {
          shadow_target: "baile",
          shadow_sense_id: "sense:en-es:baile:noun:formal-dance",
          shadow_pos: "noun",
          candidate_support_sources: ["reverse_lookup"],
        },
        {
          shadow_target: "bola mala",
          shadow_sense_id: "sense:en-es:bola-mala:noun:bad-pitch",
          shadow_pos: "noun",
          candidate_support_sources: ["forward_index"],
        },
      ],
    },
  },
  O5: {
    title: "Shadow support score",
    phase: "offline",
    summary:
      "Each candidate shadow gets a support score from interpretable lexical features. This is now the main numeric control surface instead of many branchy named policies.",
    introduced: [
      f("shadow_support_score", "Total blocker-support score for a shadow candidate.", "0..N"),
      f("shadow_support_features", "Positive evidence contributing to score.", '{"reviewed_trigger_support":false,"same_pos_as_active":true,"active_side_support":true}'),
      f("cross_pos_mismatch_penalty", "Penalty applied when active and shadow POS conflict.", "0 or -2"),
      f("min_shadow_score", "Sweepable shadow-promotion threshold.", "4"),
    ],
    exampleState: {
      scored_shadow_rows: [
        {
          shadow_target: "baile",
          shadow_support_score: 1,
          shadow_support_features: {
            same_pos_as_active: true,
          },
          cross_pos_mismatch_penalty: 0,
        },
        {
          shadow_target: "bola mala",
          shadow_support_score: 2,
          shadow_support_features: {
            same_pos_as_active: true,
            active_side_support: true,
          },
          cross_pos_mismatch_penalty: 0,
        },
      ],
      min_shadow_score: 4,
    },
  },
  O6: {
    title: "Promote blocker set S(a,t)",
    phase: "offline",
    summary:
      "Only a small, high-signal competition set survives. This is the offline object the runtime veto will actually compare against.",
    introduced: [
      f("blocker_set", "Promoted shadow set S(a,t) for one active target and trigger.", '["bola mala"]'),
      f("max_promoted_shadows", "Cap on published competitors per (a,t).", "1 or 2"),
      f("selection_policy_version", "Version string for the promotion policy.", '"support_score_v1"'),
    ],
    exampleState: {
      active_target: "pelota",
      trigger: "ball",
      blocker_set: ["bola mala"],
      selection_policy_version: "support_score_v1",
      max_promoted_shadows: 1,
    },
  },
  O7: {
    title: "Publish semantic inventory sidecar",
    phase: "offline",
    summary:
      "The compact rule pointer now has something real to point at: a sidecar inventory containing triggers, senses, competition sets, and phrase sets.",
    introduced: [
      f("semantic_inventory.triggers", "Published trigger records keyed by trigger_id.", '{"trigger:en-es:ball:pelota":{"kept":["ball"]}}'),
      f("semantic_inventory.senses", "Published sense records keyed by sense_id.", '{"sense:...pelota...":{"lemma":"pelota"}}'),
      f("semantic_inventory.competition_sets", "Published blocker sets keyed by competition_set_id.", '{"competition:...":{"blockers":["bola mala"]}}'),
      f("semantic_inventory.phrase_sets", "Published phrase preemption records.", '{"phrase:...":{"patterns":["ball over"]}}'),
    ],
    exampleState: {
      semantic_inventory: {
        triggers: {
          "trigger:en-es:ball:pelota": {
            kept_trigger_rows: ["ball"],
          },
        },
        senses: {
          "sense:en-es:pelota:noun:object-used-in-games": {
            lemma: "pelota",
            pos: "noun",
          },
        },
        competition_sets: {
          "competition:en-es:pelota:ball:v1": {
            blockers: ["sense:en-es:bola-mala:noun:bad-pitch"],
          },
        },
      },
    },
  },
  R0: {
    title: "Browser text node contains source sentence c",
    phase: "runtime",
    summary:
      "Runtime starts with real webpage text, not benchmark abstractions. The sentence plus source span become the runtime context object c.",
    introduced: [
      f("sentence_text", "Source sentence from the browser DOM.", '"The goalkeeper punched the ball over the bar."'),
      f("source_span", "Offsets or token span of the candidate text.", '{"start":29,"end":33,"text":"ball"}'),
      f("dom_context", "Browser-local context metadata.", '{"node_id":"text-481","url":"https://example.com/article"}'),
    ],
    exampleState: {
      sentence_text: "The goalkeeper punched the ball over the bar.",
      source_span: { start: 29, end: 33, text: "ball" },
      dom_context: { node_id: "text-481", url: "https://example.com/article" },
    },
  },
  R1: {
    title: "Opportunity detector finds active SRS candidate",
    phase: "runtime",
    summary:
      "The browser runtime links the sentence span to an SRS-active rule candidate, turning raw text into an admission opportunity.",
    introduced: [
      f("candidate_rule_id", "Rule selected for possible replacement.", '"en-es:ball->pelota:00123"'),
      f("candidate_target", "Target lemma under consideration.", '"pelota"'),
      f("srs_state", "Why this candidate is active right now.", '{"deck":"sports","due_today":true}'),
    ],
    exampleState: {
      candidate_rule_id: "en-es:ball->pelota:00123",
      candidate_target: "pelota",
      srs_state: { deck: "sports", due_today: true },
    },
  },
  R2: {
    title: "Load rule pointer and semantic inventory",
    phase: "runtime",
    summary:
      "Runtime resolves the active sense and published competition set using the rule pointer plus the sidecar inventory.",
    introduced: [
      f("resolved_sense_id", "Active sense selected from semantic_admission.", '"sense:en-es:pelota:noun:object-used-in-games"'),
      f("resolved_trigger_id", "Trigger bundle loaded for this candidate.", '"trigger:en-es:ball:pelota"'),
      f("resolved_competition_set", "Blocker set hydrated for runtime scoring.", '["sense:en-es:bola-mala:noun:bad-pitch"]'),
    ],
    exampleState: {
      resolved_sense_id: "sense:en-es:pelota:noun:object-used-in-games",
      resolved_trigger_id: "trigger:en-es:ball:pelota",
      resolved_competition_set: ["sense:en-es:bola-mala:noun:bad-pitch"],
    },
  },
  R3: {
    title: "Build runtime context view phi(c)",
    phase: "runtime",
    summary:
      "The raw sentence is transformed into the context representation used for scoring. Multiple views may exist, but one active view is selected for this run.",
    introduced: [
      f("context_view_name", "Selected runtime context view.", '"masked_sentence"'),
      f("context_views", "Materialized context strings derived from c.", '{"raw_sentence":"...","masked_sentence":"The goalkeeper punched the ___ over the bar."}'),
      f("phi_c", "Vector-ready context text actually sent to the scorer.", '"The goalkeeper punched the ___ over the bar."'),
    ],
    exampleState: {
      context_view_name: "masked_sentence",
      context_views: {
        raw_sentence: "The goalkeeper punched the ball over the bar.",
        masked_sentence: "The goalkeeper punched the ___ over the bar.",
        masked_window: "goalkeeper punched the ___ over the bar",
      },
      phi_c: "The goalkeeper punched the ___ over the bar.",
    },
  },
  R4: {
    title: "Load evidence views E(a) and E(s)",
    phase: "runtime",
    summary:
      "The active target and each blocker shadow are converted into comparable evidence strings or cards. This is where source-derived sense views become runtime inputs.",
    introduced: [
      f("sense_view_name", "Selected sense-card representation.", '"all_evidence_text"'),
      f("active_evidence", "Evidence view for the active target.", '"object, generally spherical, used for playing games | ..."'),
      f("shadow_evidence_rows", "Evidence views for each published blocker.", '[{"shadow":"bola mala","text":"baseball: a pitch outside the strike zone | ..."}]'),
    ],
    exampleState: {
      sense_view_name: "all_evidence_text",
      active_evidence:
        "object, generally spherical, used for playing games | (a round or ellipsoidal object) | tags: feminine",
      shadow_evidence_rows: [
        {
          shadow: "bola mala",
          text: "baseball: a pitch that falls outside the strike zone | tags: feminine",
        },
      ],
    },
  },
  R5: {
    title: "Phrase or idiom preemption",
    phase: "decision",
    summary:
      "Before semantic scoring, a phrase layer may force abstention if the candidate sits inside an idiom or phrase family known to be unsafe.",
    introduced: [
      f("phrase_preemption_hit", "Whether a phrase rule blocked semantic admission.", "true | false"),
      f("matched_phrase_pattern", "Phrase pattern that caused preemption.", '"catch sight of"'),
      f("phrase_reason_code", "Diagnostic reason for phrase abstention.", '"phrase_preemption"'),
    ],
    exampleState: {
      phrase_preemption_hit: false,
      matched_phrase_pattern: null,
      phrase_reason_code: null,
    },
  },
  R6: {
    title: "Compute active score A",
    phase: "runtime",
    summary:
      "The runtime scorer embeds the chosen context view and the active sense evidence, then computes the active score A.",
    introduced: [
      f("model_id", "Embedding model used for similarity.", '"sentence-transformers/all-mpnet-base-v2"'),
      f("active_score", "A(a,c) = sim(phi(c), phi(E(a))).", "0.91"),
      f("active_vector_pair", "Conceptual pairing used to compute A.", '{"context":"masked_sentence","sense":"all_evidence_text"}'),
    ],
    exampleState: {
      model_id: "sentence-transformers/all-mpnet-base-v2",
      active_score: 0.91,
      active_vector_pair: {
        context: "masked_sentence",
        sense: "all_evidence_text",
      },
    },
  },
  R7: {
    title: "Compute strongest shadow score M",
    phase: "runtime",
    summary:
      "Each blocker shadow is scored against the same context. Runtime keeps the strongest competing shadow score M and remembers which shadow won.",
    introduced: [
      f("shadow_scores", "Per-shadow similarity scores.", '[{"shadow":"bola mala","score":0.22}]'),
      f("max_shadow_score", "M(a,t,c), strongest competitor score.", "0.22"),
      f("winning_shadow", "Blocker shadow that achieved M.", '"bola mala"'),
    ],
    exampleState: {
      shadow_scores: [{ shadow: "bola mala", score: 0.22 }],
      max_shadow_score: 0.22,
      winning_shadow: "bola mala",
    },
  },
  R8: {
    title: "Compute margin Delta",
    phase: "runtime",
    summary:
      "The active-vs-shadow margin becomes the main safety number. Even a good active score can be unsafe if the best shadow stays too close.",
    introduced: [
      f("margin", "Delta(a,t,c) = A - M.", "0.69"),
      f("margin_components", "Raw scores used to compute Delta.", '{"active":0.91,"shadow":0.22}'),
    ],
    exampleState: {
      margin_components: { active: 0.91, shadow: 0.22 },
      margin: 0.69,
    },
  },
  R9: {
    title: "Active-score threshold gate",
    phase: "decision",
    summary:
      "First decision gate: the active score must be strong enough on its own before the system even considers replacing.",
    introduced: [
      f("min_active_score", "Configured minimum acceptable active score.", "0.65"),
      f("active_gate_pass", "Whether A cleared the minimum score.", "true"),
    ],
    exampleState: {
      min_active_score: 0.65,
      active_score: 0.91,
      active_gate_pass: true,
    },
  },
  R10: {
    title: "Margin threshold gate",
    phase: "decision",
    summary:
      "Second decision gate: the active target must beat the strongest shadow by enough margin to justify automation.",
    introduced: [
      f("min_margin", "Configured minimum margin threshold.", "0.18"),
      f("margin_gate_pass", "Whether Delta cleared the margin threshold.", "true"),
    ],
    exampleState: {
      min_margin: 0.18,
      margin: 0.69,
      margin_gate_pass: true,
    },
  },
  R11: {
    title: "Family risk or residual shadow gate",
    phase: "decision",
    summary:
      "Final safety override. Even if score thresholds pass, some high-risk families or near-tied shadows can still force abstention.",
    introduced: [
      f("high_risk_family", "Whether the current ambiguity family is flagged conservative.", "false"),
      f("shadow_still_competitive", "Whether the top shadow remains too close for comfort.", "false"),
      f("decision_reason_code", "Final runtime reason emitted.", '"replace_strong_active_margin"'),
    ],
    exampleState: {
      high_risk_family: false,
      shadow_still_competitive: false,
      decision_reason_code: "replace_strong_active_margin",
    },
  },
  P0: {
    title: "Hard replace",
    phase: "output",
    summary:
      "The DOM is modified because the active target cleared all gates safely enough.",
    introduced: [
      f("output_action", "Concrete output action.", '"hard_replace"'),
      f("replacement_text", "Rendered replacement inserted into the DOM.", '"pelota"'),
    ],
    exampleState: {
      output_action: "hard_replace",
      replacement_text: "pelota",
      rendered_sentence: "The goalkeeper punched the pelota over the bar.",
    },
  },
  P1: {
    title: "Soft affordance",
    phase: "output",
    summary:
      "The system declines to auto-replace but still surfaces a softer cue such as annotation, hover, or reveal-only.",
    introduced: [
      f("output_action", "Soft output action instead of hard replace.", '"soft_affordance"'),
      f("soft_mode", "Type of non-destructive UI affordance.", '"hover_reveal"'),
    ],
    exampleState: {
      output_action: "soft_affordance",
      soft_mode: "hover_reveal",
    },
  },
  P2: {
    title: "Abstain",
    phase: "output",
    summary:
      "The product leaves the source text untouched. This is the intended fallback whenever confidence or margin is insufficient.",
    introduced: [
      f("output_action", "No replacement output.", '"abstain"'),
      f("abstain_reason_code", "Why runtime declined replacement.", '"phrase_preemption" | "active_score_low" | "margin_low" | "high_risk_family"'),
    ],
    exampleState: {
      output_action: "abstain",
      abstain_reason_code: "high_risk_family",
    },
  },
  P3: {
    title: "Runtime diagnostics",
    phase: "output",
    summary:
      "Regardless of output action, runtime emits diagnostics so the admission decision is inspectable and benchmarkable.",
    introduced: [
      f("diagnostic_record", "Structured runtime decision record.", '{"rule_id":"...","sense_id":"...","scores":{"A":0.91,"M":0.22,"Delta":0.69}}'),
      f("reason_code", "Primary explanation for the output.", '"replace_strong_active_margin"'),
      f("source_ids", "Pointers back to rule, trigger, sense, and competition set.", '{"rule_id":"...","competition_set_id":"..."}'),
    ],
    exampleState: {
      diagnostic_record: {
        rule_id: "en-es:ball->pelota:00123",
        sense_id: "sense:en-es:pelota:noun:object-used-in-games",
        competition_set_id: "competition:en-es:pelota:ball:v1",
        scores: { A: 0.91, M: 0.22, Delta: 0.69 },
        reason_code: "replace_strong_active_margin",
      },
    },
  },
  P4: {
    title: "Research feedback loop",
    phase: "output",
    summary:
      "Diagnostics and benchmark artifacts feed back into offline tuning. This is where policy sweeps, gold proxies, review packets, and veto experiments live.",
    introduced: [
      f("review_packet", "Human review surface for blocker decisions.", '"semantic_shadow_review_packet_en_es_latest.md"'),
      f("seed_compare_artifact", "Benchmark-vs-rulegen seed comparison artifact.", '"semantic_shadow_seed_compare_en_es_latest.md"'),
      f("support_sweep_artifact", "Support-score sweep artifact.", '"semantic_shadow_support_score_sweep_en_es_latest.md"'),
      f("veto_benchmark_artifact", "Future lower-bound curated-vs-auto veto comparison.", '"semantic_shadow_source_veto_compare_*.md"'),
    ],
    exampleState: {
      research_artifacts: [
        "semantic_shadow_review_packet_en_es_latest.md",
        "semantic_shadow_seed_compare_en_es_latest.md",
        "semantic_shadow_support_score_sweep_en_es_latest.md",
      ],
    },
  },
};

export function getNode(nodeKey) {
  return NODE_DATA[nodeKey] ?? null;
}

export function getPhaseLabel(phase) {
  return phaseLabel[phase] ?? phase;
}

export function getAvailableFields(nodeKey) {
  const index = NODE_SEQUENCE.indexOf(nodeKey);
  if (index === -1) {
    return [];
  }

  const fields = [];
  const seen = new Set();

  for (const key of NODE_SEQUENCE.slice(0, index + 1)) {
    const node = NODE_DATA[key];
    for (const item of node.introduced) {
      if (seen.has(item.name)) {
        continue;
      }
      seen.add(item.name);
      fields.push({
        ...item,
        introducedAt: key,
      });
    }
  }

  return fields;
}

export function extractStableNodeKey(rawId = "") {
  const match = rawId.match(/(?:^|[-_])([ORP]\d{1,2})(?=[-_]|$)/);
  return match ? match[1] : null;
}
