# Semantic Shadow Source Intake Plan

Status: active plan
Role: Planning / operational
Purpose: prepare broad data-source experimentation for semantic-shadow mining without turning runtime veto into a source-specific heuristic pile
Last updated: 2026-04-25
Last verified: 2026-04-25 no-spend source/insertion probe plus missing-row generation plan against the frozen `v10` queue
Source-of-truth: planning doc only; executable truth still lives in the current semantic-shadow modules and experiment artifacts
Related inputs:
- `docs/test_inputs/semantic_shadow_source_registry.json`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/rulegen/semantic_llm_generation_queueing_plan.md`
- `docs/rulegen/semantic_llm_prompt_bakeoff_plan.md`
- `docs/rulegen/semantic_feedback_promotion_flow.md`
- `docs/rulegen/semantic_shadow_testing_architecture.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`

## Why this exists

The current veto frontier is no longer blocked by basic plumbing.

The remaining hard problems are:

- coverage: can the miner surface the right competing senses at all,
- discrimination: can it keep real blockers while dropping harmless near-neighbors,
- and provenance: can we later boil a broad research stack down to a small runtime-safe contract.

That means the next phase should be source-heavy, but only in the offline research layer.

The intended operating model is:

- ingest broadly,
- normalize aggressively,
- ablate ruthlessly,
- publish narrowly.

## Core design rules

### 1. Broad ingest, narrow runtime

Research can use many noisy or partial sources.
Runtime should eventually consume only a distilled blocker set plus compact provenance.

Do not let the runtime policy become a direct union of every source-specific rule.

### 2. Separate coverage from discrimination

Not all sources solve the same problem.

- Coverage sources help surface missing candidates or missing seed triggers.
- Discrimination sources help separate true competing senses from synonyms, paraphrases, and phrase leakage.
- Cue sources help build better downstream runtime evidence once a blocker is already known.
- Silver sources may accelerate discovery, but they must remain explicitly tagged and non-authoritative.

### 3. Keep provenance explicit

Every new source family must stay visible in artifacts and in ablations.

If a source helps, we should be able to answer:

- which cases it fixed,
- whether it helped coverage or discrimination,
- what new noise it introduced,
- and whether the gain survives once the source is removed but the derived feature remains.

### 4. Normalize into one evidence model

New sources should not introduce bespoke downstream logic by default.

Each source should map into a common offline evidence shape with fields such as:

- `source_id`
- `source_family`
- `role`
- `relation_type`
- `pair`
- `trigger`
- `active_target`
- `candidate_target`
- `sense_locator`
- `candidate_pos`
- `is_multiword`
- `evidence_text`
- `example_count`
- `confidence`
- `path_length`
- `runtime_publishable`
- `provenance`

The exact final implementation can evolve, but the discipline should not.

### 5. Branch the churn, not the stable harness

The current veto branch should stay focused on:

- schemas
- evaluation harnesses
- diagnostics
- stable miner improvements that survive measurement

Broad source-ingestion work should move to a dedicated experiment branch once external source families begin landing.

## Source classes

Use these classes deliberately.

### A. Structured coverage sources

Goal:
- surface blocker candidates that current lexical mining misses

Examples:
- Wiktionary sense and translation inventories
- WordNet or Open Multilingual WordNet style sense graphs
- bilingual dictionary exports with explicit per-sense structure
- aligned phrase or translation tables

Primary success signal:
- fewer `seed_missing` and `candidate_missing` harmful-allow rows

### B. Discrimination sources

Goal:
- separate true competing senses from harmless near-neighbors

Examples:
- definitions and gloss text
- example sentence banks
- argument-structure or selectional-preference signals
- contextual or sentence-embedding comparisons over example usage

Primary success signal:
- fewer `promotion_miss` rows without a parallel rise in `false_abstain`

### C. Cue-generation sources

Goal:
- build better runtime-facing evidence for an already known blocker

Examples:
- source-derived anchor extraction
- source-derived example bundles
- later, reviewed or generated cue bundles

Primary success signal:
- better future runtime separation once the blocker set is fixed

### D. Silver or synthetic sources

Goal:
- cheaply propose candidates or cues that can later be filtered by stronger evidence

Examples:
- LLM-generated shadow proposals
- LLM-generated anchor/cue drafts
- heuristic paraphrase generation

Primary success signal:
- improved recall after downstream filtering

Guardrail:
- silver data must remain tagged as silver and must not silently become a gold assumption

## Repo operating model

### Source registry

The approval and planning queue lives in:

- `docs/test_inputs/semantic_shadow_source_registry.json`

That file is intentionally machine-readable so future scripts can:

- build approval queues
- render source readouts
- or validate that experiment rows only depend on approved source families

### Code placement

When new source families are implemented, prefer this split:

- source-specific normalization and loading under `core/lexishift_core/rulegen/`
- experiment orchestration under `scripts/testing/`
- documentation and approval state under `docs/rulegen/` and `docs/test_inputs/`

Do not bury new source-family assumptions inside the runtime publication layer.

First repo-facing intake lane now exists for heterogeneous semantic source batches:

- `docs/test_inputs/semantic_routing/semantic_llm_intake_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_evidence_batch.schema.json`
- `core/lexishift_core/rulegen/semantic_evidence.py`

That means later API or external-source jobs only need to emit cohesive raw batch rows.
The batch-to-canonical mapping seam is now explicit instead of ad hoc.
The normalizer now accepts `llm`, `external`, and `internal` source types while preserving explicit `source_family` values.
The current source contract now has the row shape needed by the prototype-admission result:

- active and shadow examples use existing cue/discrimination rows
- phrase-control abstain examples can use `relation_type=phrase_control_example`
- batches that include phrase containment must declare the `phrase_containment` role
- these rows remain `runtime_publishable=false` until a separate runtime publication path exists
- `scripts/testing/semantic_llm_example_frame_contract_en_es.py` checks raw intake or normalized evidence batches for the full active/shadow/phrase-control contract
- the same contract gate can require an expected queue/dataset family set via `--required-family-json`, so a cherry-picked complete subset cannot pass as a complete source batch
- `scripts/testing/semantic_llm_reviewed_example_frame_batch_en_es.py` now builds the no-spend reviewed fixture as raw intake plus normalized evidence
- `scripts/testing/semantic_reverse_aux_example_frame_batch_en_es.py` now builds a non-LLM installed-pack reverse-aux example-frame batch as raw intake plus normalized evidence
- `docs/test_outputs/semantic_llm_example_frame_contract_latest.md` is the positive frozen-queue fixture read: `8 / 8` families complete
- `docs/test_outputs/semantic_llm_example_frame_contract_required_latest.md` is the same positive frozen-queue fixture with required-family coverage enforced
- `docs/test_outputs/semantic_llm_example_frame_contract_expanded_latest.md` is the positive full-`v10` fixture read: `19 / 19` families complete
- `docs/test_outputs/semantic_llm_example_frame_contract_overlap_latest.md` preserves the old overlap target batch as a negative read: `0 / 6` families complete because all six families still lack shadow and phrase-control example rows
- `docs/test_outputs/semantic_reverse_aux_example_frame_contract_latest.md` preserves the real external-source reverse-aux read as `review`: `0 / 8` families complete because the source has active text for all six target families, shadow text for four target families, and no phrase-control examples
- `scripts/testing/semantic_llm_example_frame_generation_plan_en_es.py` turns that required-family contract gap into a no-spend, exact missing-row request plan
- `docs/test_outputs/semantic_llm_example_frame_generation_plan_latest.md` plans exactly `11` rows: `1` active example for `play`, `2` shadow examples for `plant`/`check`, and `8` phrase-control examples across the frozen queue
- the plan deliberately keeps reviewed sentence-veto case text and translation targets out of prompt input; prompts use the English trigger, active/shadow sense labels and glosses, and queue role/archetype/notes while internal row previews retain target ids for normalization
- `scripts/testing/semantic_llm_example_frame_generation_run_en_es.py` has now executed that plan live with append-only journaling and explicit spend guards
- `docs/test_outputs/semantic_llm_example_frame_generation_run_latest.md` shows the live run accepted and normalized `11 / 11` rows (`3382` input tokens / `358` output tokens)
- `scripts/testing/semantic_example_frame_batch_merge_en_es.py` merged those rows with reverse-aux into `24` composite rows: `8` active, `8` shadow, and `8` phrase-control examples
- `docs/test_outputs/semantic_llm_example_frame_generation_contract_latest.md` shows the merged batch is structurally complete: `8 / 8` required families
- `docs/test_outputs/semantic_llm_example_frame_generation_quality_gate_latest.md` rejects it as analysis-only because the best containment-aware prototype config is still only `67.5%` decision accuracy / `31.2%` replace recall / `2` harmful / `11` false abstains
- the no-spend containment ablation is now explicit: broad semantic phrase-control prototypes put phrase-overreach pressure on `12` active false-abstain rows and directly add `2` incremental false abstains beyond the active-guard baseline, while local containment-pattern use creates `0` incremental containment false abstains and `2` correct phrase containment hits
- the diagnostic lesson is now narrower and stronger: filling missing rows is not enough; generated phrase-control rows should not be semantic competitors, and the next source pass must generate balanced active/shadow exemplars while keeping phrase-control rows as containment patterns or separately gated abstain evidence
- `scripts/testing/semantic_llm_example_frame_remediation_plan_en_es.py` turns the containment-aware residuals into the next no-spend source plan
- `docs/test_outputs/semantic_llm_example_frame_remediation_plan_latest.md` plans `8` targeted requests: `7` active examples for the `11` false-abstain cases and `1` shadow example for the `2` harmful `report` cases; it preserves the no reviewed-sentence leakage policy and keeps phrase-control rows out of broad semantic scoring

First repo-facing source/insertion upper-bound lane now also exists:

- `reviewed_sentence_veto_example_frames` in `docs/test_inputs/semantic_shadow_source_registry.json`
- `scripts/testing/semantic_llm_source_insertion_probe_en_es.py`
- `docs/test_outputs/semantic_llm_source_insertion_probe_latest.md`
- `scripts/testing/semantic_llm_prototype_admission_probe_en_es.py`
- `docs/test_outputs/semantic_llm_prototype_admission_probe_latest.md`
- `docs/test_outputs/semantic_llm_prototype_admission_probe_expanded_latest.md`
- `docs/test_outputs/semantic_llm_reviewed_example_frame_batch_latest.md`
- `docs/test_outputs/semantic_llm_reviewed_example_frame_batch_expanded_latest.md`

Current read:

- symmetric reviewed active/shadow example frames erase the false-abstain slice but reopen phrase leaks under the old family-wide phrase guard
- the same reviewed example frames plus active-sense phrase guarding reach `100.0%` decision accuracy / `100.0%` replace recall / `0` harmful / `0` false abstains on the frozen queue
- the prototype-admission variant keeps the UX decision binary, scores context against active/shadow reviewed examples directly, and also reaches `100.0%` / `100.0%` / `0` / `0` on the frozen queue
- the expanded full-`v10` reviewed-oracle prototype read shows why phrase-control evidence needs a first-class lane: active-sense phrase guarding alone reaches `97.9%` accuracy / `100.0%` recall / `2` harmful / `0` false abstains, while reviewed phrase-control prototypes reach `100.0%` / `100.0%` / `0` / `0`; generated phrase-control rows must still be admitted through local containment or a separate abstain gate rather than broad semantic competition
- the prototype probe now uses the normalized reviewed evidence batch as input, not only the sentence-veto dataset directly
- this is an internal reviewed-data oracle, not runtime-publishable source evidence
- it does prove the next useful source shape: competition-symmetric active/shadow example-frame evidence plus explicit phrase-control containment or separately gated abstain evidence
- the real reverse-aux source batch is useful as gap-routing evidence, not as a promotion-ready prototype source:
  - `docs/test_outputs/semantic_reverse_aux_example_frame_batch_en_es_latest.md`
  - `docs/test_outputs/semantic_reverse_aux_prototype_admission_probe_latest.md`
  - the direct prototype read is only `67.5%` decision accuracy / `50.0%` replace recall / `5` harmful / `8` false abstains because phrase-control examples are absent and `plant`/`check` lack shadow-side auxiliary rows
  - the next generated/source batch should fill exactly those missing shadow and phrase-control rows before any runtime claim

### Experiment discipline

Every source family should be tested in four stages:

1. intake-only
2. intake plus normalization
3. intake plus one simple gating policy
4. ablation against the current best lexical baseline

The key question is not "does this source seem smart".
The key question is "which failure bucket moved, and at what precision cost".

## Immediate approval queue

The next likely source families worth considering are:

1. `wiktionary_sense_inventory_dump`
   - likely value: structured coverage and sense-link expansion
   - main risk: noisy sense alignment and normalization burden

2. `open_multilingual_wordnet`
   - likely value: coarse sense-graph coverage and cross-lemma competition hints
   - main risk: sense granularity mismatch with learner-facing dictionary senses

3. `aligned_phrase_table`
   - likely value: coverage for phrase-sensitive competitors and MWE spillover
   - main risk: high noise without strong filtering

4. `example_sentence_bank`
   - likely value: stronger discrimination and future runtime cue quality
   - main risk: uneven coverage and heavier preprocessing cost

5. `llm_shadow_proposals`
   - likely value: cheap candidate recall for hard lexical misses
   - main risk: silent hallucination or benchmark-shaped overfitting unless strictly quarantined

6. `llm_anchor_cues`
   - likely value: richer runtime evidence once blockers are known
   - main risk: good prose that is semantically weak or unstable

These should not all be added at once.
The first step is to approve a small batch with one coverage-heavy source and one discrimination-heavy source.

## Recommended next move after approval

Once a source family is approved:

1. create a dedicated experiment branch for source-heavy ingestion
2. add one adapter and one normalized evidence lane
3. expose that lane in the semantic-shadow experiment harness
4. run gold-proxy, veto-proxy, and row-compare ablations against the lexical control
5. keep only the derived evidence fields or source families that survive measurement

That sequence is intentionally conservative.
It keeps the current veto workstream understandable while still moving quickly on data discovery.
