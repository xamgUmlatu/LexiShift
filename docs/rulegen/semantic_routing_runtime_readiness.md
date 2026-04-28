# Semantic Routing Runtime Readiness

Status: active mixed readiness
Role: Mixed
Last updated: 2026-04-24
Last verified: 2026-04-24 runtime-eval truth pass against the current `v10` fixed-shadow artifacts, held-out bound, phrase-leak probe, queue-review note, and canonical state docs
Purpose: describe the current shipped semantic-routing runtime seam and the remaining readiness boundary so rollout work stays grounded in executable behavior instead of research-only optimism
Source-of-truth: mixed as-is + readiness boundary; current runtime truth still lives in code, tests, and `docs/developer/feature_state_matrix.md`
Verification:
- `README.md`
- `docs/getting-started/index.md`
- `docs/architecture/extension_system_map.md`
- `docs/srs/srs_roadmap.md`
- `docs/rulegen/rule_generation_technical.md`
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_publication_contract.md`
- `apps/chrome-extension/shared/settings/settings_defaults.js`
- `apps/chrome-extension/shared/helper/helper_client.js`
- `apps/chrome-extension/content/runtime/rules/helper_rules_runtime.js`
- `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
- `apps/chrome-extension/content/runtime/semantic/semantic_gate_runtime.js`
- `apps/chrome-extension/content/processing/replacements.js`
- `apps/chrome-extension/content/runtime/diagnostics/apply_diagnostics_reporter.js`
- `core/tests/dev/test_extension_semantic_gate_runtime_contract.py`
- `core/tests/rulegen/test_semantic_routing_runtime_policy.py`
- `core/tests/helper/test_helper_engine.py`
- `core/tests/dev/test_helper_translation_dict_entrypoints.py`

Sequencing note:

- this doc explains the shipped runtime seam, the remaining readiness boundary, and the current research posture
- `docs/rulegen/semantic_sentence_veto_algorithm.md` owns the cohesive end-to-end algorithm explanation that connects runtime eligibility, scoring math, phrase preemption, active rescue, and current matrix findings
- `docs/rulegen/semantic_routing_implementation_roadmap.md` owns the near-term implementation order
- `docs/rulegen/semantic_routing_en_es_publish_checklist.md` owns the first controlled browser-extension `en-es` launch runbook
- `docs/rulegen/semantic_routing_generalization_evaluation_plan.md` and `docs/rulegen/semantic_shadow_testing_architecture.md` own the broader blocker-generation evaluation and research workflow

## Purpose

This document exists to answer one narrow product question:

- what must be true before LexiShift can safely use semantic routing to decide whether a browser replacement should apply in real reading?

The intended end-to-end experience is:

1. the user reads a normal English page,
2. runtime notices an opportunity to use a target lemma already active in SRS,
3. a semantic gate decides whether the local sentence clearly supports that learner target,
4. LexiShift either:
   - applies the replacement,
   - surfaces a softer non-destructive affordance,
   - or abstains entirely.

The governing product preference is:

- false abstain is usually acceptable,
- harmful replacement is not.

This asymmetry should shape both the research program and the eventual runtime policy.

## How To Read This Doc

- Treat `Current Shipped Runtime Seam` and `Current Emitted-Rule Provenance Reality` as the current runtime contract.
- Treat `Current Sentence-Level Runtime Harness` and the research-result sections as evidence and experimentation surfaces, not shipped runtime truth.
- Treat `docs/rulegen/semantic_shadow_testing_architecture.md` as the authority for detailed artifact filenames and research workflow lanes; this doc should summarize what the current evidence means, not carry the full artifact directory listing in the prose.
- Treat `What Is Still Missing For True End-To-End Automatic Semantic Routing` and `Runtime Readiness Floor` as the remaining readiness boundary.
- Use the roadmap for implementation sequencing and the checklist for launch operation; this doc should not be used as a step-by-step plan.

## What Progress Means Here

Not every semantic-routing improvement is the same kind of improvement.
When reading new results, keep these axes separate:

- upstream blocker generation:
  - did the system mine and promote the right shadow competitors at all
- runtime discrimination:
  - given the right fixed competition set, did scoring choose the correct active-vs-shadow outcome
- phrase / frame containment:
  - did the system correctly identify lexicalized-expression or frame cases that should not be treated as ordinary sense competition
- decision-policy shape:
  - how the score geometry is mapped into `replace`, `soft_affordance`, and `abstain`
- confidence tightening:
  - how conservative the held-out floor / ceiling corridor is, not just the point estimate
- research machinery:
  - whether the repo can reproduce, isolate, and explain a failure class cleanly

This matters because a turn can be real progress even when the headline score does not improve.

Common examples:

- a new held-out family can lower the visible metrics while still improving the project, because it exposes a real failure class that was previously hidden
- a cleaner failure taxonomy can be progress even before a runtime row improves
- a bounded experimental overlay can improve understanding without being ready for shipped policy

So the current campaign should not be read as one scalar optimization problem.
It is a coordinated effort to improve:

1. blocker-generation quality,
2. runtime score separation,
3. phrase containment,
4. policy conservatism,
5. and trust in the evaluation surface itself.

## Current Shipped Runtime Seam

Today the browser-extension runtime already has a narrow semantic-admission gate, but it is now capability-driven rather than toggle-driven.

Current shipped behavior:

1. initialize/refresh already publish semantic artifacts without a separate semantic-admission toggle
2. the runtime gate only activates when both:
   - `srsEnabled === true`
   - the current enabled SRS ruleset for that pair/profile has computed semantic runtime capability `active`
3. current capability states are:
   - `active`
   - `published_unready`
   - `unavailable`
   - `error`
4. only SRS-origin rules are eligible for semantic gating
5. even within SRS-origin rules, a match is only eligible when the rule already carries `metadata.semantic_admission`
6. only publications with nonzero ready coverage (`ruleset_rules_semantic_ready > 0`) can activate helper semantic scoring
7. ready matches are grouped by `pair` + `profile_id`
8. before helper scoring, the extension runtime resolves semantic inventory through:
   - helper first
   - helper-cache fallback second
9. the runtime only calls helper `semantic_admit_batch` when:
   - the match status is `ready`
   - semantic inventory resolved successfully
   - helper semantic-admission transport is available
10. the shipped runtime still uses internal `legacy_on_unavailable` fallback for ready-rule transport/inventory failures; non-ready publications stay on standard SRS behavior instead of exposing a user-facing fallback selector
10. only `decision=replace` survives into DOM apply today
11. `abstain` and the currently reserved `soft_affordance` outcome both keep the original text in the shipped DOM path

Current operational boundaries:

- this runtime path is implemented for the browser extension, not the BetterDiscord/plugin runtime
- helper artifacts remain local; there is no cloud transport in the shipped runtime path
- active-rules runtime and apply diagnostics already record:
  - whether semantic admission is enabled
  - which fallback policy is active
  - whether semantic inventory resolved
  - whether inventory came from helper or helper-cache
  - aggregate eligible / ready / replace / abstain / soft-affordance counts plus the current `decision_policy_id`

What the shipped gate is not:

- not a broad shadow-mined semantic runtime
- not a default-on feature
- not a rendered soft-affordance UX yet
- not proof that automatic blocker discovery is rollout-ready

## What Current Strong Prototype Results Actually Mean

Current prototype readouts often use phrases like:

- `source-derived + cosine`
- `automatic sense text`

Those labels are directionally correct, but incomplete.

The current semantic-routing research prototype is not yet fully automatic end to end.
It already shows that source-backed sense representations can score very well once the ambiguity family is known.
It does not yet prove that LexiShift can discover, select, and serve the right semantic competition set automatically during browser runtime.

That distinction matters enough to be explicit.

## Lexical-Mathematical Model

The semantic-routing problem is easiest to reason about if it is split into:

- an offline competition-generation step,
- and a runtime admission step.

### Objects

For one active learner target:

- let `a` be the active target lemma or sense candidate,
- let `t` be an English trigger phrase that justifies `a`,
- let `E(a)` be the source-derived evidence text for the active target,
- let `S(a, t) = {s1, s2, ..., sk}` be the shadow set for the active target under trigger `t`,
- let `E(si)` be the source-derived evidence text for shadow `si`,
- let `c` be the runtime sentence or transformed context view,
- let `phi(x)` be the text representation function used for lexical matching or embedding,
- let `sim(x, y)` be the comparison function, usually cosine similarity over embeddings.

Examples of `phi(...)` today include:

- masked sentence views such as `The goalkeeper punched the ___ over the bar`,
- source-derived sense text such as `all_evidence_text`,
- compact lexical anchor views such as `core_anchor`,
- optional future bridge or cue views.

### Offline objective: build a small blocker set

The offline question is:

- given active target `a` and trigger `t`, which other targets deserve membership in `S(a, t)`?

In practical terms, the miner is approximating a support function:

- `support(a, t, s) -> blocker worthiness`

where blocker worthiness is based on evidence such as:

- active-side support for `a` under trigger `t`,
- reverse-pack support for shadow `s` under trigger `t`,
- forward-gloss support for `s` under trigger `t`,
- POS compatibility between `a` and `s`,
- future semantic-bridge support when direct lexical overlap is weak.

The important product constraint is that `S(a, t)` should be:

- small,
- conservative,
- and dominated by real runtime hazards rather than exhaustive lexical neighbors.

This is why current research prefers stricter policies such as `cross_checked_v1` over broader same-POS sweeps.

### Runtime objective: compare active sense against its shadows

Once a shadow set exists, runtime no longer needs to discover competitors from scratch.
It needs to decide whether the local context favors the active target strongly enough over the published blocker set.

For one context `c`, define:

- active score:
  - `A(a, c) = sim(phi(c), phi(E(a)))`
- strongest shadow score:
  - `M(a, t, c) = max_{s in S(a, t)} sim(phi(c), phi(E(s)))`
- margin:
  - `Delta(a, t, c) = A(a, c) - M(a, t, c)`

The runtime decision policy is then conceptually:

- `replace` if:
  - `A(a, c)` is high enough,
  - `Delta(a, t, c)` is large enough,
  - and phrase-preemption has not already blocked the apply
- `soft affordance` if the active score is suggestive but not trustworthy enough for auto-replace
- `abstain` otherwise

This expresses the product asymmetry directly:

- a false abstain is usually acceptable,
- a harmful replace happens when `M(a, t, c)` is actually competitive but the policy still allows replacement.

### Where the current miner fits

The current `en-es` shadow research is not directly optimizing runtime cosine yet.
It is optimizing the earlier problem:

- can we construct a trustworthy `S(a, t)` automatically from source data?

That is why the current evaluation stack measures things like:

- candidate precision,
- candidate recall,
- underblocking,
- overblocking,
- seed-source dependence.

Those are offline quality signals for the blocker-set generator, not final runtime replace metrics.

### Why embeddings alone are not the full answer

A tempting simplification is:

- embed the runtime context,
- embed all nearby target senses,
- choose the nearest neighbor,
- replace if the nearest score looks high.

Embeddings are useful, but that full shortcut is unsafe for product use on its own.
The main risks are:

- mirrored senses often remain near each other in embedding space,
- nearest-neighbor selection does not automatically provide a trustworthy abstain boundary,
- phrase or idiom failures remain mixed into the same score surface,
- broad lexical neighbors can look plausible even when they are not blocker-worthy runtime competitors.

The more stable architecture is therefore:

1. lexical/provenance mining proposes a small competition set `S(a, t)`,
2. optional semantic-bridge or embedding rescue helps recover hard misses,
3. strict promotion keeps the blocker set small,
4. runtime scoring compares the active target only against those blockers and prefers abstain over unsafe replace.

In other words:

- embeddings are promising as a recall tool and runtime comparison tool,
- but they should sit inside a competition-based admission system rather than replace the whole pipeline.

The first `en-es` target-card embedding bridge now makes that caveat more concrete.
Using source-derived target cards plus sentence-transformer nearest neighbors can recover the hard lexical miss `trabajo / job -> cargo`.
But on the current lower-bound proxy it only helps when the support-score threshold is lowered enough that overblocking rises sharply, and it does not solve `cargo / job -> trabajo` because the active side is still unsupported there.
So the current conclusion is:

- nearest-neighbor target cards are useful as a research recall probe,
- but they are not yet a publishable improvement over the lexical baseline.

## Current Sentence-Level Runtime Harness

The repo now has a research-only harness that isolates the runtime scorer from upstream shadow mining.

Current files:

- `docs/test_inputs/semantic_routing/sentence_veto_case.schema.json`
- `docs/test_inputs/semantic_routing_cases/en_es_sentence_veto_v10.json`
- `core/lexishift_core/rulegen/semantic_routing_runtime_scoring.py`
- `scripts/testing/semantic_routing_sentence_veto_harness.py`
- `scripts/testing/semantic_routing_sentence_veto_sweep.py`
- `scripts/testing/semantic_routing_sentence_veto_ladder.py`
- `scripts/testing/semantic_routing_sentence_veto_weak_active_probe.py`
- `scripts/testing/semantic_routing_sentence_veto_phrase_leak_probe.py`

Operational note:

- the default sweep now stays on the cheap lexical scorer family (`token_jaccard`, `tfidf_cosine`)
- the heavier `sentence_transformer_cosine` lane is available explicitly for model-choice comparisons
- the current evaluation slice now aligns to `en_es_sentence_veto_v10`; the shipped `en-es` helper runtime still uses the bounded `en_es_sentence_veto_v3` sentence-transformer phrase-guard lane by default, while the lexical `en_es_sentence_veto_v2` row remains the explicit conservative control
- this bounded default still relies on existing helper availability of `sentence_transformers`; if model load fails, the current fallback path still abstains rather than forcing a replace

Current dataset scope:

- pair: `en-es`
- 19 ambiguity families: `ball`, `bank`, `plant`, `cell`, `spring`, `seal`, `file`, `match`, `board`, `table`, `branch`, `park`, `drink`, `play`, `watch`, `check`, `order`, `trip`, `report`
- 95 labeled sentences total
- fixed active sense plus fixed shadow senses per family
- `v10` adds:
  - `report` on the held-out side as a noun-active / verb-shadow weak-active-support family
  - two new held-out under-replacement rows (`report:001`, `report:002`)
  - one lexicalized `report back` phrase row that broadens the mixed noun/verb phrase surface without becoming a second harmful-replace seam

What this harness is for:

- compare scorer families with the same exact active-vs-shadow competition set
- compare raw vs masked sentence views
- compare full-sentence vs local-window context views
- compare evidence views such as `sense_label`, `gloss_text`, and `all_evidence_text`
- sweep `min_active_score` and `min_margin` without changing any upstream miner behavior

What it is not for:

- proving automatic shadow mining quality
- proving end-to-end runtime readiness
- choosing a production threshold from a tiny curated dataset

Current lexical read on that fixed-shadow harness:

- after widening the threshold sweep to include lower active-score gates, the best current lexical row is:
  - `tfidf_cosine`
  - `masked_sentence`
  - `all_evidence_text`
  - `noun_family_frame_guard`
  - `sense_label_near_tie_active_rescue`
  - `min_active_score=0.05`
  - `min_margin=0.00`
- that row currently yields on `v10`:
  - `73.7%` decision accuracy
  - `100.0%` replace precision
  - `34.2%` replace recall
  - `0.0%` harmful replace
  - `65.8%` false abstain
- the family breakdown matters:
  - lexical control is already perfect on `cell`, `file`, and `seal`
  - it still fully abstains on the active rows for `ball`, `bank`, `check`, `order`, `park`, `plant`, `play`, `report`, `spring`, and `trip`
  - `board`, `branch`, `match`, `table`, and `watch` remain mid-strength breadth / held-out families (`80.0%` decision accuracy / `50.0%` active recall)
  - `report` is the newest held-out weak-active-support family:
    - both active rows still abstain
    - its lexicalized `report back` row still abstains safely, so it widens cue-data residue rather than reopening the phrase-leak seam

Current model-choice read:

- on the expanded `v10` dataset, model choice is still a decisive runtime lever, but the clean hard-replace story is still gone:
  - best zero-harm sentence-transformer budget row:
    - `masked_sentence + all_evidence_text + noun_family_frame_guard + sense_label_near_tie_active_rescue + min_active_score=0.00 + min_margin=0.10`
    - `75.8%` decision accuracy
    - `100.0%` replace precision
    - `39.5%` replace recall
    - `0.0%` harmful replace
    - `60.5%` false abstain
  - best objective sentence-transformer row:
    - `masked_sentence + all_evidence_text + noun_family_frame_guard + sense_label_near_tie_active_rescue + min_active_score=0.00 + min_margin=0.00`
    - `89.5%` decision accuracy
    - `96.7%` replace precision
    - `76.3%` replace recall
    - `1.8%` harmful replace
    - `23.7%` false abstain
    - `88.2%` winner accuracy
    - `100.0%` shadow-winner accuracy
    - current hard errors are now:
      - harmful replace: `play:005`
      - false abstains: `plant:002`, `park:001`, `drink:002`, `play:002`, `check:002`, `order:002`, `trip:002`, `report:001`, `report:002`
- interpretation:
  - the lexical control remains the conservative shipped gate posture
  - the stronger sentence-transformer lane still materially beats lexical control on the fixed-shadow harness
  - but `v10` still shows there is no clean hard-replace sentence-transformer row on the active evaluation slice
  - `report` does not reopen the phrase-leak seam; instead it widens the held-out weak-active-support residue beyond the earlier `check` / `order` / `trip` cluster
  - the next runtime question is now no longer “does the stronger lane exist”; it is how to preserve phrase-leak containment while deciding whether new cue data can move the unresolved held-out residue

Decision-ladder read on the frozen `v10` runtime row:

- `docs/test_outputs/semantic_routing_sentence_veto_ladder_latest.md`
  - keep the current hard-replace gate fixed:
    - `sentence_transformer_cosine + masked_sentence + all_evidence_text + noun_family_frame_guard + sense_label_near_tie_active_rescue + min_active_score=0.00 + min_margin=0.00`
  - then allow `soft_affordance` only over the current abstains
  - best zero-noise ladder row is:
    - `soft_min_active_score=0.60`
    - `soft_min_margin=0.00`
    - `0` soft true positives
    - `0` soft false positives
    - `76.3%` replace-or-soft recall
- interpretation:
  - the old zero-noise soft-ladder optimism does not survive `v10`
  - the current fixed zero-noise soft reference is now a monitoring control, not a live product or prompt-design frontier
  - visible `soft_affordance` product behavior should therefore remain deferred

Weak-active-support runtime probe on frozen `v10`:

- `docs/test_outputs/semantic_routing_sentence_veto_weak_active_latest.md`
  - current default row now reads:
    - `1` harmful replace
    - `9` false abstains
    - `76.3%` replace recall
    - `89.5%` decision accuracy
    - rescue coverage:
      - `ball:002`
      - `drink:001`
      - `play:001`
  - direct primary-surface swaps do recover the weak-active-support misses, but they are too noisy for promotion:
    - `masked_sentence + sense_label`
      - `4` harmful replaces
      - `10` false abstains
      - `73.7%` replace recall
    - `raw_sentence + all_evidence_text`
      - `8` harmful replaces
      - `1` false abstain
      - `97.4%` replace recall
    - `raw_window + all_evidence_text`
      - `8` harmful replaces
      - `2` false abstains
      - `94.7%` replace recall
  - the best simulated rescue overlay is now only bounded, not clean:
    - primary stays `masked_sentence + all_evidence_text`
    - backup stays `sense_label`
    - widening the rescue trigger floor from `-0.02` to `-0.05` yields:
      - `1` harmful replace
      - `6` false abstains
      - `84.2%` replace recall
      - `92.6%` decision accuracy
      - rescued rows:
        - `ball:002`
        - `plant:002`
        - `park:001`
        - `drink:001`
        - `drink:002`
        - `play:001`
      - remaining residue:
        - harmful replace: `play:005`
        - false abstains: `play:002`, `check:002`, `order:002`, `trip:002`, `report:001`, `report:002`
- interpretation:
  - `park`-like misses are still recoverable without promoting raw-context or sense-label primaries
  - `report` sharpens the limit of that path: the accepted overlay still does not recover either new `report` active row
  - `v10` therefore strengthens the current read that the next likely gain is cue-data work, not generic scorer reshaping or a broader rescue rollout

Held-out confidence update after `v10`:

- `docs/test_outputs/semantic_routing_generalization_bound_en_es_latest.md`
  - the bound surface now carries five runtime references:
    - `Sentence-transformer phrase-guard candidate`
    - `Sentence-transformer active-sense phrase-guard experiment`
    - `Sentence-transformer zero-noise soft ladder`
    - `Sentence-transformer widened-rescue candidate (simulated)`
    - `Sentence-transformer active-sense phrase-guard overlay (simulated)`
  - current corridor:
    - runtime reference replace-recall conservative floor: `63.2%`
    - runtime reference harmful-replace conservative ceiling: `5.3%`
    - runtime reference false-abstain conservative ceiling: `36.8%`
    - active-sense hard experimental replace-recall conservative floor: `63.2%`
    - active-sense hard experimental harmful-replace conservative ceiling: `0.0%`
    - active-sense hard experimental false-abstain conservative ceiling: `36.8%`
    - runtime ladder replace-or-soft conservative floor: `63.2%`
    - runtime ladder soft-noise conservative ceiling: `0.0%`
    - rescue-overlay replace-recall conservative floor: `71.1%`
    - rescue-overlay harmful-replace conservative ceiling: `5.3%`
    - rescue-overlay false-abstain conservative ceiling: `28.9%`
    - active-sense overlay experimental replace-recall conservative floor: `71.1%`
    - active-sense overlay experimental harmful-replace conservative ceiling: `0.0%`
    - active-sense overlay experimental false-abstain conservative ceiling: `28.9%`
- interpretation:
  - the plain runtime reference and plain widened-rescue overlay are still not clean, because `play:005` remains their only harmful row
  - the active-sense overlay remains the clean bounded comparator after adding `report`
  - the zero-noise soft lane no longer carries practical additional lift on the current slice
  - the next honest step is therefore not another runtime-policy push, but a pre-prompt cue-data investigation on the frozen `v10` queue

Phrase-leak probe on frozen `v10`:

- `docs/test_outputs/semantic_routing_sentence_veto_phrase_leak_latest.md`
  - testing-only comparison:
    - current mixed-POS phrase guard
    - active-sense noun phrase guard
    - current widened overlay
    - active-sense noun guard overlay
  - hard-row result:
    - current mixed-POS phrase guard:
      - `1` harmful replace
      - `9` false abstains
      - `76.3%` replace recall
      - `89.5%` decision accuracy
    - active-sense noun phrase guard:
      - `0` harmful replaces
      - `9` false abstains
      - `76.3%` replace recall
      - `90.5%` decision accuracy
    - only decision change:
      - `play:005`
        - `replace -> abstain`
        - phrase reason becomes `modal_trigger_frame`
  - bounded overlay result:
    - current widened overlay:
      - `1` harmful replace
      - `6` false abstains
      - `84.2%` replace recall
      - `92.6%` decision accuracy
    - active-sense noun guard overlay:
      - `0` harmful replaces
      - `6` false abstains
      - `84.2%` replace recall
      - `93.7%` decision accuracy
    - only decision change:
      - `play:005`
        - `replace -> abstain`
  - explicit tradeoff:
    - phrase-preemption hits broaden from `7` to `21`
    - newly phrase-preempted mixed noun/verb shadow rows include:
      - `park:003`
      - `park:004`
      - `park:005`
      - `drink:003`
      - `drink:004`
      - `drink:005`
      - `play:004`
      - `watch:005`
      - `check:003`
      - `check:005`
      - `order:005`
      - `trip:005`
      - `report:005`
- interpretation:
  - the live `play:005` leak still appears to be caused by the current family-wide POS gate suppressing phrase control on mixed noun/verb families
  - anchoring phrase control to the active noun POS now also cleanly catches the held-out `watch:005`, `check:005`, `order:005`, `trip:005`, and `report:005` lexicalized-expression rows without disturbing the held-out active rows
  - the acceptability review now extends through a fifth held-out mixed noun/verb lexicalized-expression family:
    - the active-sense hard experiment removes the harmful-replace ceiling while keeping the same conservative recall floor as the plain hard reference
    - the active-sense overlay experiment keeps the `71.1%` replace-recall floor and `28.9%` false-abstain ceiling while dropping the harmful-replace ceiling from `5.3%` to `0.0%`
  - so the active-sense noun phrase guard is still the stronger preferred bounded experimental overlay semantics for the frozen `v10` slice
  - that means phrase leakage is currently classified tightly enough that prompt work should treat `play` as a guardrail family, not as a first-tranche cue target

Interpretation:

- the runtime harness is doing the right job: it is still separating new weak-active-support residue from the older phrase-leak seam instead of flattening them together
- on the current curated dataset, lexical weakness is still mostly conservative under-replacement
- the stronger sentence-transformer lane is still materially better than lexical control, but `play:005` means the current frontier is no longer “find more rescue”
- the live frontier is now a mixed runtime problem:
  - preserving the current hard reference while tracking the safer active-sense overlay experiment
  - plus freezing a clean pre-prompt queue now that `report` confirms the newest held-out widening is cue-data residue rather than a second phrase leak
- `v10` sharpens that read:
  - `report:001` and `report:002` widen the held-out false-abstain surface without joining the accepted overlay
  - `report:005` is safely contained by the active-sense phrase guard but does not change the live harmful row
  - the zero-noise soft ladder no longer adds practical lift
- this is therefore the right surface for:
  - a frozen first family inventory / bakeoff queue
  - an `example_sentence_bank` feasibility pilot on that queue
  - and then a reverse-aux-text control before any paid prompt smoke pass
- the new reverse-aux-text control now tightens that read:
  - on the frozen prompt queue slice, `reverse_aux_plus_all_evidence` improves the point read from:
    - `77.5%` decision accuracy / `50.0%` replace recall / `1` harmful replace / `8` false abstains
    - to `82.5%` / `62.5%` / `1` harmful replace / `6` false abstains
  - it fixes `plant:002`, `drink:002`, and `order:002`
  - it still leaves `play:005` as the live harmful row and still misses `play:002`, `check:002`, `trip:002`, `report:001`, and `report:002`
  - so it is useful as the last cheap non-LLM control, but not as a runtime-default candidate

## Boundary: Manual Vs Automatic Today

| Layer | Current status | What is manual | What is automatic |
|---|---|---|---|
| Ambiguity family framing | manual | which source family is being evaluated; which sense is active; which benchmark cases belong to the family | none |
| Shadow-family framing | mixed | final promoted shadow set is still handpicked | sibling-sense candidate mining can already be programmatic |
| Context transformation | automatic | none | masking, context windows, raw vs masked sentence views |
| Sense representation | mostly automatic | optional handwritten cue bundles | reverse sense text, gloss bundles, qualifiers, anchor construction, source-derived merged text views |
| Cue augmentation | mixed | handwritten hints and future authored cue bundles | Kaikki-derived cues and raw-example-derived cues |
| Serving policy | partial | helper/runtime capability thresholds and rollout readiness still need policy tuning; broad rollout-ready policy and soft-affordance UX are not finished | helper-side runtime policy, capability-gated activation, and benchmark-side policy experiments |

### Manual today

The current research loop still relies on people to specify:

- which ambiguity family to test,
- which sense is the active learner sense,
- which sibling senses are the first important blockers,
- which sentences count as clear allow, abstain, phrase control, or weak-context control,
- and any handwritten cue bundles.

That means current prototype success should be interpreted as:

- given a manually framed ambiguity family and a known active sense,
- source-derived evidence plus cosine scoring can work very well.

It should not be interpreted as:

- LexiShift can already discover the full sense-competition structure automatically from runtime text.

### Source-derived today

Once the active sense and candidate shadows are known, the prototype already builds many useful pieces automatically:

- masked and unmasked runtime context views,
- reverse-sense text,
- reverse gloss bundles,
- forward translation/gloss text,
- qualifier text from tags/topics/categories,
- compact anchors,
- Kaikki-text cue bundles,
- raw-example cue bundles when examples exist.

This is the part of the system that has been most encouraging.
It suggests that good runtime semantic gating may be achievable without heavy dependence on manually authored cue text.

## Current Emitted-Rule Provenance Reality

This is the most important current boundary for runtime planning.

Today, the repo has two different provenance layers:

- `candidate metadata` during rulegen/benchmarking
- `emitted rule metadata` in persisted rulesets consumed by helper/runtime

Those are not the same thing.

The verified current behavior is:

| LP / pair | Candidate-level sense evidence | Emitted rule-level sense pointer |
|---|---|---|
| `en-es` | rich candidate metadata can include `dictionary_record`, `dictionary_record_views`, `gloss_provenance`, `sense_provenance`, `target_provenance`, and shadow-risk metadata | shared `metadata.semantic_admission` is emitted by default adapter/helper paths; it carries stable `trigger_id`, `sense_id`, and `competition_set_id` using `sense_provenance` first and `translation_gloss` fallback, and it now has a narrow helper-side `status=ready` PoC when real sibling senses are present either in the active emitted ruleset or in the broader initialize/refresh semantic-context pool overlaid onto that ruleset (`competition_mode=emitted_rule_siblings`), not a broad mined blocker set |
| `en-de` | same general shape as `en-es` for Kaikki/provenance-aware candidate generation | shared `metadata.semantic_admission` is emitted by default adapter/helper paths; it can now carry stable `trigger_id`, `sense_id`, and `competition_set_id` using `sense_provenance` first and `translation_gloss` fallback, but currently stays `status=unavailable` because shadow promotion is not solved yet |
| `en-ja` | no analogous rich sense-provenance layer today; candidate metadata is mostly gloss order, POS, script forms, and word-package information | shared `metadata.semantic_admission` is emitted by default adapter/helper paths and can now carry a stable `jmdict_entry`-backed active pointer derived from target forms, but it still stays `status=unavailable` because shadow promotion is not solved and the pointer is coarser than source-sense provenance |
| `de-en` | candidate metadata is mostly gloss order and POS | shared `metadata.semantic_admission` is emitted by default adapter/helper paths and can now carry a stable `translation_gloss`-backed active pointer derived from deterministic gloss order, but it still stays `status=unavailable` because shadow promotion is not solved |
| `es-en` | candidate metadata is mostly gloss order, reverse-check info, and POS | shared `metadata.semantic_admission` is emitted by default adapter/helper paths and can now carry a stable `translation_gloss`-backed active pointer derived from deterministic gloss order, but it still stays `status=unavailable` because shadow promotion is not solved |

So the current answer to:

- "for any emitted LP rule, do we already know exactly which source sense it points to?"

is:

- not fully.

What is true today is weaker:

- the repo now has a shared emitted-rule semantic-routing pointer contract,
- all current rulegen LPs can now preserve a stable active pointer into that contract,
- pointer strength differs by pair:
  - `en-es` / `en-de`: richest, source-sense provenance first
  - `de-en` / `es-en`: deterministic FreeDict gloss-slot locator
  - `en-ja`: deterministic JMDict entry locator
- `en-es` now also has a first narrow helper-side broader-context competition-set publication PoC that can emit `status=ready` from real emitted sibling senses while keeping the visible ruleset limited to active items,
- helper publication can now emit a minimal semantic inventory sidecar,
- but no LP yet emits a fully ready competition/shadow set by default.

This means active-sense provenance is not checked off yet.
It is still one of the main missing seams before semantic routing can become a real admission layer.

## What Is Still Missing For True End-To-End Automatic Semantic Routing

These are the pieces that matter before serious optimization.

### 1. Active-sense provenance seam

LexiShift needs a reliable runtime/build-time way to know:

- which source sense a candidate replacement came from,
- not just which target lemma was emitted.

This has to come from rulegen provenance and survive into the runtime-facing rule payload.

Without it:

- semantic routing is only a benchmark thought experiment,
- not a runtime admission layer.

The current verified gap is concrete:

- adapter/helper publication paths can now preserve a shared `metadata.semantic_admission` pointer,
- all current rulegen LPs can now populate stable active-pointer ids there,
- only `en-es` and `en-de` currently reach source-sense-provenance quality by default,
- `en-es` can now publish a limited batch-local emitted-sibling competition set, but that is still narrower than true mined shadow promotion and should not be read as LP-parity readiness,
- but helper publication still does not emit ready competition/shadow sets by default,
- and weaker LPs still rely on coarser entry/gloss locators rather than full source-sense provenance.

### 2. Automatic shadow-candidate mining

The system needs to enumerate sibling senses of the same source trigger from installed pack data and collapse them into stable sense clusters.

Desired output:

- a small ranked inventory of real semantic competitors,
- not a raw bag of translations or every gloss row.

This is partly understood as a mining problem already, but it is not yet integrated into the main runtime product path.

First implemented research seam:

- `scripts/testing/semantic_shadow_inventory_en_es.py` can now mine a research-only `en-es` shadow inventory from reviewed benchmark trigger phrases plus installed forward/reverse translation packs.
- detailed current artifact filenames for this seam now live in `docs/rulegen/semantic_shadow_testing_architecture.md`; the bullets below summarize what the current inventory, triage, policy, review, gold-proxy, and veto-proxy outputs mean for readiness
- the current inventory read shows broad sibling coverage, which is encouraging
- the current follow-on triage shows why publication is still blocked:
  - zero-signal promotions can be removed,
  - but the remaining top-1 preview is still dominated by `same_pos_as_active` rather than benchmark-aligned competition evidence.
- the current policy comparison now makes the algorithm tradeoff explicit:
  - `same_pos_lenient_v1`: broader still after active-trigger matching (`111` promoted triggers) and therefore even noisier as a runtime candidate
  - `benchmark_backed_v1`: cleaner (`19` promoted triggers) but narrow
  - `cross_checked_v1`: narrower still (`11` promoted triggers), and now the practical runtime-shaped starting point
  - `cross_checked_backoff_missing_active_v1`: now converges to the same `11` promoted triggers after active-side trigger matching was improved for bundled forward glosses and benchmark-only shadow rescue was disabled when the active side is completely empty
- the current gap queue isolates what the stricter policy still drops:
  - `5` rows due to missing active POS or missing active-side support
  - `3` rows due to explicit cross-POS mismatch without reviewed trigger support
- The most useful concrete fix so far is local and interpretable:
  - active-side trigger matching now uses the existing `en_es_support` gloss-fragment normalization, so bundled forward glosses like `to take, catch, hold, to get, to seize` can supply real active evidence for bare triggers such as `take` and `catch`
  - this was enough to move `coger / catch -> vista` out of the provisional review queue and into the stricter gap queue, which is the right safety direction
- the current review packet:
  - it combines the current policy snapshot, provisional keep rows, provisional drop rows, and the active-side evidence summary for each row
  - it makes the current practical recommendation explicit: treat `cross_checked_v1` as the provisional `en-es` runtime-shaped policy, keep the six surviving blocker rows, and keep the eight dropped rows out of the blocker set for now
- the current lower-bound grading read:
  - it derives a reviewed-trigger-overlap gold proxy directly from `docs/test_inputs/rulegen_benchmark_cases/en_es.json`
  - it scores the current shadow-promotion policies against that proxy without inventing a second benchmark surface
  - this is not a sentence-level semantic veto benchmark, but it gives immediate candidate precision/recall, trigger-hit, underblocking, and overblocking metrics for automatic shadow promotion
  - on the current `en-es` lower-bound read, the strict policies (`cross_checked_v1` and `cross_checked_backoff_missing_active_v1`) tie as the best current lower-bound:
    - candidate precision `64.3%`
    - candidate recall `90.0%`
    - gold-trigger hit rate `90.0%`
    - overblocking rate `3.6%`
  - the same lower-bound read also clarifies the current limiting factor:
    - a new forward-index supplement now recovers benchmark-known siblings that are missing from the reverse headword rows alone
    - that lifted mined candidate-pool recall from `60.0%` to `90.0%` against the overlap proxy
    - the remaining clear miss is `trabajo / job -> cargo`, which points to a harder semantic-bridge problem rather than a simple reverse-pack coverage gap
  - the current gap audit makes that remaining miss explicit:
    - remaining gap count: `1`
    - current classification: `semantic_bridge_needed`
    - meaning: the missing shadow is not recoverable from the current reverse pack, the new forward-index supplement, or the current best rulegen source list
    - next research should therefore stay separate from the strict automatic miner and focus on a distinct semantic-bridge lane
  - the current seed-comparison read makes the current benchmark-coupling boundary explicit:
    - `benchmark_reviewed`: `64.3%` candidate precision, `90.0%` candidate recall, `90.0%` gold-trigger hit rate, `3.6%` overblocking
    - `rulegen_top3_sources`: `36.4%` candidate precision, `40.0%` candidate recall, `40.0%` gold-trigger hit rate, `5.1%` overblocking
    - `rulegen_all_sources`: `33.3%` candidate precision, `40.0%` candidate recall, `40.0%` gold-trigger hit rate, `5.8%` overblocking
    - the new source-only augmentation lane improves that meaningfully without adding new manual data:
      - `rulegen_top3_plus_forward_gloss` at the current best swept setting (`forward_seed_max_words=1`): `32.0%` candidate precision, `80.0%` candidate recall, `80.0%` gold-trigger hit rate, `9.4%` overblocking
      - `rulegen_all_plus_forward_gloss` is effectively tied at the same setting
    - the current forward-seed sweep shows the first useful numeric seed knob:
      - allowing only single-word forward-gloss-derived triggers is currently the best source-only tradeoff
      - longer phrase allowance (`2+` words) does not improve recall on the current lower-bound proxy, but it does worsen precision and overblocking
    - the current support-score sweep shows the next cleaner control surface:
      - instead of adding more named promotion policies, keep one explicit support score and sweep only the threshold plus the maximum promoted-shadow count
      - on the current source-only lane, that already improves the tradeoff materially without adding manual data:
        - `rulegen_top3_plus_forward_gloss` / `rulegen_all_plus_forward_gloss` with `min_score=5` and `max_promoted=2` now reach `47.1%` candidate precision, `80.0%` candidate recall, and `5.1%` overblocking
        - relative to the old strict `cross_checked_v1` baseline on the same seed mode, that keeps recall flat but improves precision from `32.0%` to `47.1%` and reduces overblocking from `9.4%` to `5.1%`
      - on the reviewed-trigger control, the score sweep now exposes a real safety/coverage ladder instead of a single obvious threshold:
        - `min_score=3`, `max_promoted=1`: `20.0%` precision / `90.0%` recall / `26.1%` overblocking
        - `min_score=5`, `max_promoted=1`: `100.0%` precision / `80.0%` recall / `0.0%` overblocking
      - interpretation: the support score is now a true numeric control surface for the abstain-vs-coverage tradeoff, not just a re-expression of the older strict policy
    - the current trigger-support sweep shows where the remaining seed noise actually lives:
      - keep the downstream shadow support policy fixed (`shadow min=4`, `max_promoted=2`), and filter only the source-only trigger seeds before mining
      - on `rulegen_top3_plus_forward_gloss`, a modest trigger threshold (`min_trigger_score=3`) does remove some upstream junk, but only relative to the much noisier `shadow min=4` operating point:
        - precision `8.0% -> 13.6%`
        - recall stays `80.0%`
        - overblocking `43.5% -> 23.9%`
      - on `rulegen_all_plus_forward_gloss`, the same trigger score remains too destructive:
        - precision `8.0% -> 14.3%`
        - recall `80.0% -> 20.0%`
        - inventory coverage `90.0% -> 50.0%`
      - interpretation: trigger scoring is still a coarse upstream cleanup knob, but it is no longer the best current frontier; the stronger path remains higher downstream support thresholds rather than harsher trigger pruning
    - the current frequency sweep probes a soft target-side Spanish lexical-frequency prior:
      - the experiment keeps the current best lexical source-only baseline fixed (`rulegen_top3_plus_forward_gloss`, `shadow min=5`, `max_promoted=2`) and only adds a bonus for the most frequent shadow targets within a trigger bucket
      - that bonus does not improve the current best row:
        - baseline stays `47.1%` precision / `80.0%` recall / `5.1%` overblocking
        - any positive frequency bonus is neutral at small weights and actively harmful at `bonus=1.0`
      - the follow-on similarity sweep keeps the same lexical baseline fixed and replaces the raw “most frequent shadow wins” idea with a continuous bonus for shadows that live in a similar normalized frequency band to the active target
      - that also fails to improve the current best row:
        - the best source-only setting remains `sim_weight=0.0`
        - positive similarity weights are effectively inert on the current `en-es` gold proxy
      - interpretation: the current ES frequency pack is plausible as metadata, but neither raw target frequency nor active-vs-shadow frequency similarity is yet a useful default pruning signal for semantic shadows; frequency should remain an optional research knob, not a default promotion feature
    - the current representative-pruning sweep probes a more structural condensation idea:
      - collapse same-POS candidates that share the same normalized `sense_label`, then keep only the highest-scoring representative from each cluster
      - on the current `en-es` reviewed overlap proxy, that also does not improve the best row:
        - the best source-only setting remains pruning `off`, `min_score=5`, `max_promoted=2`
        - enabling `sense_label_pos_v1` leaves precision, recall, and overblocking unchanged on the current sweep grid
      - interpretation: redundant same-sense lexical variants are real in the raw inventory, but they are not the current bottleneck on the reviewed scoring denominator; the support threshold is already filtering most of that noise before representative pruning matters
    - the current veto-proxy comparison adds the first lower-bound curated-vs-auto shadow benchmark:
      - it is intentionally not the sentence-level cosine veto benchmark
      - instead, each reviewed overlap row becomes a proxy `allow` / `abstain` decision:
        - if the shadow source emits any blockers for an ambiguous overlap row, count `abstain`
        - otherwise count `allow`
      - current result:
        - `curated_shadows`: `100.0%` overall accuracy / `100.0%` abstain recall / `0.0%` harmful allow / `0.0%` overblocking
        - `reviewed_auto_shadows`: `98.6%` overall accuracy / `80.0%` abstain recall / `20.0%` harmful allow / `0.0%` overblocking
        - `auto_shadows`: `93.9%` overall accuracy / `80.0%` abstain recall / `20.0%` harmful allow / `5.1%` overblocking
        - `no_shadows`: `93.2%` overall accuracy / `0.0%` abstain recall / `100.0%` harmful allow / `0.0%` overblocking
      - interpretation:
        - the current source-only auto shadow lane already captures most of the lower-bound veto benefit over `no_shadows`
        - the remaining harmful-allow gap is concentrated in the still-open `cargo / job` family
        - the main new cost of `auto_shadows` versus `reviewed_auto_shadows` is modest false abstain (`5.1%`), not catastrophic ambiguity miss
    - conclusion: the current miner is general enough to avoid target-specific hacks, still materially depends on reviewed-trigger seeding, and now has a more sweepable promotion surface; the next de-coupling work should improve automatic seed quality and semantic-bridge recall rather than add more branchy blocker rules

So this seam is no longer hypothetical.
What remains open is the conservative promotion policy, not whether sibling mining can run at all.

### 3. Shadow-promotion policy

Mining candidates is not enough.
LexiShift also needs a conservative promotion rule for which candidates actually become blockers in runtime.

The first production shadow set should stay:

- small,
- interpretable,
- and obviously tied to harmful confusion classes.

### 4. Phrase/idiom preemption as a separate lane

Some bad replacements are not really “wrong sense” problems.
They are phrase problems.

Examples:

- idioms,
- frozen collocations,
- multiword sports/baseball patterns,
- lexicalized expressions that should be blocked before semantic scoring even starts.

If phrase preemption is not separated from semantic veto, the runtime gate will stay muddy and harder to calibrate.

### 5. Abstain-first serving policy

The production system needs an explicit decision ladder that prefers abstain over risky allow.

The likely runtime outcomes are:

1. hard replace,
2. soft candidate / reveal / annotation,
3. abstain.

This should be an intentional product policy, not an accidental side effect of a benchmark threshold.

### 6. Runtime observability

Current runtime observability is partial, not absent.

Already present today:

- active-rules runtime reports whether semantic admission is enabled
- the options-page `SRS runtime diagnostics` action is already a three-way join:
  - helper source-of-truth payload for ruleset/snapshot/semantic-inventory/publication-manifest state
  - extension-cache payload for cached ruleset/snapshot/semantic-inventory presence and counts
  - current tab/runtime last state for live semantic gate behavior
- apply/runtime last-state diagnostics record fallback policy, inventory source/error, and aggregate eligible / ready / replace / abstain counts
- that current tab/runtime state is persisted through `chrome.storage.local` under `srsRuntimeLastState`
- per-replacement detail payloads can already carry semantic decision fields such as:
  - `decision`
  - `decision_source`
  - `reason_codes`
  - `sense_id`
  - `competition_set_id`
  - `score_margin`
  - `active_score`
  - `top_shadow_score`
  - `phrase_preempted`

Before any broader rollout, LexiShift still needs diagnostics that can answer:

- why a replacement applied,
- why it abstained,
- which shadow won,
- whether phrase preemption fired,
- which provenance row and cue view were used.

Without that deeper per-decision observability, runtime trust and debugging will still be poor even if benchmark numbers look promising.

### 7. Broader benchmark confidence

The current benchmark direction is useful, but not sufficient by itself.

Before a default runtime launch, confidence should come from:

- more source families,
- more holdout cases,
- mirrored-family hazards,
- and eventually more than one pair or direction.

## Runtime Readiness Floor

The future runtime semantic gate should be able to answer:

1. what source token/phrase candidate was considered,
2. which active sense it came from,
3. which shadows were considered,
4. which context view was scored,
5. which policy decided the outcome,
6. whether the final result was:
   - replace,
   - soft affordance,
   - abstain.

That contract should be explicit in rule metadata and runtime diagnostics before any broad default-on rollout.

Current schema references for that contract now live at:

- `docs/test_inputs/semantic_routing/semantic_admit_batch_request.schema.json`
- `docs/test_inputs/semantic_routing/semantic_admit_batch_response.schema.json`

Those schema files now describe the shipped browser-extension/helper batch seam.
They remain useful as shared references for later runtime surfaces, but they are no longer just placeholders for future implementation.

## Planning Ownership

Use the rest of the semantic-routing planning stack deliberately:

- use `docs/rulegen/semantic_routing_implementation_roadmap.md` for the near-term phase order and implementation sequencing
- use `docs/rulegen/semantic_routing_en_es_publish_checklist.md` for the first controlled `en-es` launch posture, validation commands, and per-profile enable steps
- use `docs/rulegen/semantic_routing_generalization_evaluation_plan.md` for blocker-generation evidence needed beyond the current emitted-sibling PoC
- use `docs/rulegen/semantic_shadow_testing_architecture.md` and `docs/rulegen/semantic_shadow_source_intake_plan.md` for research harness structure, experiment lanes, and source-intake expansion

This document should answer "what is shipped and what still blocks runtime readiness?", not "what exact step do we do next?"
