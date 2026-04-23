# Semantic LLM Generation Queueing Plan

Status: active plan
Role: Planning / pre-scan framing
Purpose: define what semantic-routing data should eventually be generated with LLM support, which units deserve queueing, what can be inferred automatically versus what remains hypothesis, and how to avoid redundant generation work
Last updated: 2026-04-24
Last verified: 2026-04-24 repo-doc review against the semantic-routing data/publication contracts, runtime-readiness framing, source-intake plan, first concrete family inventory, and frozen bakeoff queue
Source-of-truth: planning doc only; current implemented truth still lives in the semantic-routing contracts, inventory publication code, and offline evidence normalization seam
Related docs:
- `docs/rulegen/semantic_shadow_source_intake_plan.md`
- `docs/rulegen/semantic_llm_prompt_bakeoff_plan.md`
- `docs/rulegen/semantic_routing_data_update_lifecycle.md`
- `docs/rulegen/semantic_feedback_promotion_flow.md`
- `docs/rulegen/semantic_routing_data_contract.md`
- `docs/rulegen/semantic_routing_runtime_readiness.md`
- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`
- `docs/test_inputs/semantic_routing/semantic_report_event_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_local_override_bundle.schema.json`
- `docs/test_inputs/semantic_routing/semantic_llm_intake_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_evidence_batch.schema.json`

## Why this exists

The next obvious question is not:

- "what should the prompt be?"

The next obvious question is:

- "which semantic problems are actually worth generating data for?"

That question is not trivial.

If LexiShift asks an LLM for semantic data indiscriminately, it will:

- waste budget on families that are already safe,
- waste budget on phrase/parsing failures that are not data problems,
- generate duplicate rows for the same underlying ambiguity family,
- and make later evaluation harder because the queueing logic itself was not explicit.

This document exists to prevent that.

## Core framing

The generation queue should not be built at the level of:

- raw emitted rule rows,
- target lemmas in isolation,
- or "all polysemous words."

The correct unit is a semantic competition family.

Current practical family identity:

- `pair`
- `normalized trigger`
- `active target`

Preferred future family identity once active sense linking is stronger:

- `pair`
- `trigger_id`
- `active_sense_id`
- `competition_set_id`

In other words:

- `pelota` is not the unit
- `ball -> pelota` is closer
- `en-es / trigger=ball / active sense=pelota(ball-object)` is the real unit

That matches the current semantic-routing architecture more closely than a word list does.

## What "worried about polysemy" should mean

A family is "worried about polysemy" when it is plausible that:

- the runtime trigger can support more than one meaning,
- at least one alternative meaning could map to a different learner-relevant target,
- a wrong replacement would be meaningfully harmful,
- and current non-semantic controls do not already make the family safe enough.

This is not the same as:

- "the English word is polysemous in a dictionary"

Many dictionary-polysemous words do not deserve semantic-routing investment because:

- the trigger is phrase-specific enough,
- the rule is not currently publishable or common enough,
- or the ambiguity does not create a meaningful replacement hazard.

So the queueing question is not:

- "is this word polysemous?"

It is:

- "is this family risky enough, live enough, and data-fixable enough to justify semantic-generation effort?"

## Current intended generated data

The current LLM intake seam supports three row types:

- `shadow_candidate`
- `bridge_candidate`
- `anchor_cue`

Interpretation:

- `shadow_candidate`
  - propose another target reading that competes with the active target under the same trigger
- `bridge_candidate`
  - propose a plausible competing target that current lexical mining may miss
- `anchor_cue`
  - propose discriminative evidence text for an already-known active/shadow contrast

Those rows are offline evidence only.
They are not runtime decisions and they are not runtime sidecars.

## Budget posture

The current intended operating posture is:

- spend one bounded first LLM tranche to see how far veto quality can improve
- preserve every batch as additive source-of-truth evidence
- and keep the repo able to accept later tranches without reworking the pipeline

That means the first budgeted run should be treated as:

- a deliberate pilot slice
- not a one-time monolithic dump
- and not a shortcut to runtime artifacts

The practical implication is:

- queue a limited set of high-value families first
- record which families were attempted and by which batch
- normalize every batch into the canonical evidence layer
- and let later batches add coverage family-by-family

## Why the first tranche must be additive

If the first LLM tranche is handled as a one-off merged blob, later expansion becomes awkward.

The main failure modes would be:

- redundant generation for families that were already attempted
- loss of provenance about which prompt/model fixed which family
- difficult rollback when a later batch is worse
- and inability to compare one budget wave against another

The desired future is simpler:

1. generate for a bounded family queue
2. ingest raw batch rows
3. normalize and dedupe them
4. compile a new generation
5. compare that generation against the previous one
6. keep the new generation only if it is genuinely better

That process only works cleanly if the first tranche already follows it.

## Queueing buckets

The current working buckets are:

- `not_applicable`
- `needs_shadow_data`
- `needs_cue_data`
- `needs_algorithm_fix`
- `needs_phrase_parsing_fix`

These are operating labels.
They are not ground truth claims.

That distinction matters enough to make explicit:

- the system will usually not know the true root cause with certainty
- the system can only infer the most likely explanation from the current evidence

So in practice the desired output of a future queueing pass is not:

- `bucket=needs_shadow_data`

It is:

- `likely_bucket=needs_shadow_data`
- `bucket_confidence=...`
- `bucket_evidence=[...]`

## What can and cannot be known automatically

### What we cannot know with certainty

Without manual review, the system usually cannot prove:

- whether a family truly needs more blocker coverage or just better pruning,
- whether a family is fundamentally a phrase-boundary bug,
- whether the current active sense identity is already slightly wrong,
- or whether a family is simply not worth semantic-routing investment.

That means a fully automatic pass cannot be treated as authoritative diagnosis.

### What we can infer well enough to triage

A future automatic pass can still be useful if it emits:

- a likely bucket,
- a confidence estimate,
- evidence signals,
- and a recommended next action.

This is enough to drive:

- human sampling,
- LLM budget allocation,
- and later ablation work.

The correct posture is:

- automatic triage first
- sampled human review second
- policy refinement third

## Signals for each bucket

These are current working heuristics, not final rules.

### 1. `needs_shadow_data`

Likely when:

- the family is plausibly ambiguous,
- harmful allow risk appears to come from missing competitors,
- and the current competition set is empty or obviously too thin.

Example signal pattern:

- trigger has multiple plausible readings
- current `competition_set` is missing or has no ready `shadow_sense_ids`
- manual or lower-bound shadows substantially improve the family
- runtime scorer quality is not the main bottleneck once blockers are present

Interpretation:

- coverage problem first

### 2. `needs_cue_data`

Likely when:

- the blocker identities are mostly right,
- but runtime still abstains too often or fails to separate active from shadow because the evidence text is weak.

Example signal pattern:

- the competition set exists and looks plausible
- the same shadow identities perform much better with stronger evidence text
- the main weakness is weak active-vs-shadow separation, not missing competitors

Interpretation:

- discrimination problem first

### 3. `needs_algorithm_fix`

Likely when:

- the needed information is already in the pipeline or candidate pool,
- but current filtering, promotion, pruning, or thresholding discards or misuses it.

Example signal pattern:

- good candidates appear in the raw candidate pool but do not survive promotion
- small policy-node changes recover the family without new source data
- the family looks data-rich but decision-poor

Interpretation:

- logic problem first

### 4. `needs_phrase_parsing_fix`

Likely when:

- the family is not primarily about sense competition,
- but about broken phrase retention, MWE leakage, or malformed trigger extraction.

Example signal pattern:

- phrasal forms collapse into bare tokens
- POS alignment becomes implausible in a way that suggests bad span identity
- the wrong text span is being admitted into semantic routing

Interpretation:

- parse or surface-form problem first

### 5. `not_applicable`

Likely when:

- the family does not create enough semantic hazard to justify queueing,
- or existing controls already make it safe enough.

Example signal pattern:

- ambiguity is narrow or harmless
- phrase specificity already protects the family
- semantic routing adds little practical value even if the word is dictionary-polysemous

Interpretation:

- do not spend queue budget here yet

## Reuse rules

The queue should be optimized for reuse from the start.

Do not generate separately for every emitted rule row when the same semantic family repeats.

### Shadow proposal reuse

Generate once per family:

- `pair`
- `normalized trigger`
- `active target`

or later:

- `pair`
- `trigger_id`
- `active_sense_id`

The same result should then feed every emitted rule that points to that family.

### Cue reuse

Cue generation should usually be keyed more narrowly:

- `pair`
- `active sense`
- `shadow sense`

That is because cue text is about distinguishing one specific contrast, not about expanding the whole family.

### Sense-hint reuse

Any future sense hints or reviewed locators should be reusable across families whenever:

- the same target sense appears in multiple trigger families

### Publication reuse

Even if helper materialization stays profile-local, semantic-generation work should aim toward:

- pair-global semantic core
- profile-local overlay only where needed

That remains the best way to avoid redundant cloud or local artifact churn later.

## Family inventory and queue state

To support later add-on waves, the repo needs explicit family-level queue state.

Without that state, later LLM work would keep re-answering questions the repo has already asked.

Current first concrete artifact:

- `docs/test_inputs/semantic_routing/semantic_family_inventory_en_es_v10.json`
- `docs/test_outputs/semantic_llm_queue_review_en_es_latest.md`
- `docs/test_outputs/semantic_example_sentence_bank_pilot_en_es_latest.md`

Current posture from that first artifact:

- current first-tranche queue is cue-heavy, not shadow-heavy
- current routed primary targets are `check`, `order`, `trip`, and `report`
- current calibration families are `plant` and `drink`
- current negative controls are `play` and `watch`
- current `needs_shadow_data` tranche count is `0`
- current installed packs expose no queued-family example rows on that frozen slice:
  - `0 / 6` target families are example-ready for `example_sentence_bank`
  - `6 / 6` target families do expose reverse-side auxiliary sense text
- the new reverse-aux-text pilot now resolves that remaining cheap-control choice:
  - `reverse_aux_plus_all_evidence` is the best non-LLM queue-slice control
  - it improves the frozen prompt-slice point read without widening the current harmful count
  - so prompt spend can now proceed with one explicit non-LLM reference row rather than an unresolved source question

Minimum family inventory responsibilities:

- remember which family has already been queued
- remember whether the family received shadow generation, cue generation, or both
- remember which `batch_id` attempted the family
- remember whether the family still looks unresolved
- remember whether the current best diagnosis is data-related or non-data-related

Minimum family inventory fields:

- `family_id`
- `pair`
- `trigger`
- `normalized_trigger`
- `active_target`
- `active_sense_hint`
- `queue_status`
- `attempted_generation_kinds`
- `last_attempt_batch_id`
- `last_attempted_at`
- `resolved_status`
- `likely_bucket`
- `bucket_confidence`
- `recommended_action`

This inventory is not optional if the goal is:

- spend a bounded amount now and add more later without redundant regeneration

It is the memory layer for the generation queue.

Current planning anchor:

- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`

## Future user-feedback role

Future user feedback is realistic, but it should enter the system as weak evidence rather than direct truth.

The safest first interpretation is:

- raw user feedback should be captured at the per-event and per-rule level
- durable fixes will usually be promoted at the family or competition-set level
- and promotion into shared semantic truth should remain review-gated

That means the future system should preserve both:

- exact firing context for the reported rule event
- the broader semantic family that event belongs to

### What feedback can safely do

User feedback can safely support:

- local per-user safety suppression
- ranking families for manual review
- ranking families for future LLM generation
- pattern mining across repeated failures

### What feedback should not do automatically

User feedback should not directly:

- create new shared shadow candidates
- create new shared cue data
- rewrite the canonical semantic evidence layer
- or trigger global positive behavior without review

That is true even when the feedback is attached to a very specific rule event.

### Promotion posture

The current intended posture is conservative:

- even per-rule event feedback should normally require manual promotion before it changes shared semantic truth
- repeated reports may justify faster manual review or a future conservative global abstain bias
- but raw reports should not silently become global semantic data

### Pattern mining

The repo should still be able to mine user feedback for patterns such as:

- topic or domain clusters
- trigger families
- phrase-boundary failures
- repeated active-vs-shadow confusions
- policy-version regressions

Those mined patterns are valuable, but promoting them into global behavior should usually remain manual at first.

## Safe first product action

The safest immediate product action is a local user override.

Example:

- the user can completely remove or suppress a rule locally after a bad replacement

This is valuable because it:

- protects the user immediately
- does not require trust in global feedback quality
- and does not pollute shared semantic truth

So future feedback architecture should distinguish clearly between:

- local safety action
- and shared semantic-data promotion

The first can be automatic.
The second should usually remain review-gated.

Current planning anchors:

- `docs/test_inputs/semantic_routing/semantic_report_event_batch.schema.json`
- `docs/test_inputs/semantic_routing/semantic_local_override_bundle.schema.json`
- `docs/rulegen/semantic_feedback_promotion_flow.md`

## Recommended first-budget posture

Before any full scan, the current recommended first-budget posture is:

- choose a bounded first tranche of high-value families
- prefer families that are clearly runtime-relevant and plausibly data-fixable
- avoid spending early budget on obvious phrase/parsing failures
- avoid spending early budget on families that appear to be pure algorithm problems
- preserve raw batch provenance so future batches can be compared directly

This should make the first tranche useful in two ways:

- it may improve quality immediately
- and it will teach the repo which kinds of families are actually worth paying for

## What a future automatic pass should emit

Before attempting a full scan, the repo should converge on a family-level inventory row shape.

Minimum fields:

- `family_id`
- `pair`
- `trigger`
- `normalized_trigger`
- `active_target`
- `active_sense_hint`
- `current_pointer_status`
- `current_competition_status`
- `current_shadow_candidate_count`
- `current_promoted_shadow_count`
- `runtime_relevance`
- `likely_bucket`
- `bucket_confidence`
- `bucket_evidence`
- `recommended_action`

This inventory is the real prerequisite for later prompt work.

Current planning anchor:

- `docs/test_inputs/semantic_routing/semantic_family_inventory.schema.json`

The prompt should be written after the queueing unit is stable, not before.

The current queueing unit is now stable enough for a first bounded pre-prompt workflow:

- inventory row
- sampled manual queue review
- frozen bakeoff queue
- frozen prompt-slot manifest

What is still missing before prompt spend:

- a tiny non-LLM cue-data pilot over that frozen queue
- then prompt-slot smoke work on the same frozen slice

Once the queueing unit is stable, use `docs/rulegen/semantic_llm_prompt_bakeoff_plan.md` for the prompt-slot matrix, proxy-vs-target model policy, and cheap bakeoff workflow.

## Human review posture

The project should not aim to manually review every family.
That is not realistic.

Instead:

- automatically triage all families,
- manually sample high-impact or low-confidence families,
- cluster repeated families together,
- and use the reviewed slice to calibrate the triage policy.

The target is not:

- perfect automatic diagnosis

The target is:

- useful queue prioritization with explicit uncertainty

## Practical current takeaway

The present understanding is:

- the queueing unit should be a competition family, not a word
- "worried about polysemy" should mean product-relevant semantic hazard, not dictionary polysemy alone
- automatic classification can only produce hypotheses, not certain root-cause labels
- LLM budget should be spent only after a family-level queue exists
- reuse should happen at family level for shadows and at sense-pair level for cues

## Not yet decided

The following still need deeper discussion before a full scan/pass is justified:

- the exact family identity before full active-sense coverage exists
- the exact confidence model for bucket guesses
- the exact minimum signal set for `not_applicable`
- how much runtime evidence versus offline proxy evidence should influence queueing
- which reviewed slice should calibrate the first automatic triage pass
- what budget threshold should separate "generate now" from "leave unresolved"
