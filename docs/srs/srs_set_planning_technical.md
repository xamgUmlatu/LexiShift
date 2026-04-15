# SRS Set Planning Technical Notes

Related design:
- `docs/srs/srs_hybrid_model_technical.md`
- `docs/srs/srs_preference_signal_admission_design.md`
- `docs/srs/srs_preference_signal_admission_v1_contract.md`
- `docs/developer/language_difficulty_and_proficiency_model.md`
- `docs/srs/srs_onboarding_and_placement_schema.md`
- `docs/srs/srs_preference_update_and_rebalance_policy.md`

## Purpose
Define how set `S` is planned and mutated:
- bootstrap `S` initially
- grow/refresh `S` over time
- keep scheduling and admission responsibilities separated

## Scope boundary
- Planner chooses strategy and returns execution metadata.
- Scheduler handles review timing from feedback.
- Planner must not treat passive display as a scheduling event.

Difficulty/proficiency rule:
- planner inputs may include user proficiency and target vocabulary-band intent
- planner outputs may later include derived difficulty-target signals
- those should remain separate from observed item difficulty in the scheduler

## Modules

- `core/lexishift_core/srs/set_strategy.py`
  - Strategy/objective constants and normalization.
- `core/lexishift_core/srs/set_planner.py`
  - Request/response model and planning logic.
- `core/lexishift_core/srs/set_policy.py`
  - Centralized sizing policy defaults, clamps, and normalization.
- `core/lexishift_core/srs/signal_queue.py`
  - Event queue storage and summarization.
- `core/lexishift_core/helper/engine.py`
  - `plan_srs_set(...)` planner API.
  - `initialize_srs_set(...)` mutation API.
- `core/lexishift_core/srs/rebalance.py`
  - Protected-item classification and non-destructive rebalance planning.
- `core/lexishift_core/helper/use_cases/rebalance_set.py`
  - Rebalance preview/apply helper workflow.

## Strategy matrix

- `frequency_bootstrap`
  - Status: executable.
  - Behavior: initialize `S` from frequency + dictionary constraints.

- `profile_bootstrap`
  - Status: executable.
  - Behavior: planner accepts profile context and reranks the neutral seed pool before admission.
  - Current active signals:
    - proficiency fit
    - explicit topic interests when candidate topic hints or exact lexical matches are available
    - challenge preference fit
  - Current non-goal:
    - seed generation itself remains the neutral frequency/dictionary candidate builder
  - Current execution contract:
    - raw planner input is normalized into explicit `topic_weights`, `proficiency_estimate`, `challenge_target`, and `challenge_spread` fields before scoring
    - planner diagnostics surface which signals were active, which were missing, and which source fields supplied them

- `profile_growth`
  - Status: partially executable.
  - Behavior: `objective="rebalance"` is now a manual preview/apply path that preserves protected learned items, parks only swappable active items, reuses retained history when possible, and can admit new seed items when needed.
  - Current non-goal:
    - general continuous growth admission is still not executable yet.

- `adaptive_refresh`
  - Status: planner-only.
  - Behavior: intended to refresh `S` using aggregated feedback trends.
  - Current scaffold note: planner diagnostics may still request both `feedback_signals` and `exposure_signals`; exposure remains non-authoritative unless policy changes.

## Native helper API

- `srs_plan_set`
  - Input:
    - `pair`, `strategy`, `objective`, `replace_pair`, `profile_context`, `trigger`
    - sizing: `bootstrap_top_n` (preferred), `initial_active_count`, `max_active_items_hint`
    - compatibility: `set_top_n` (legacy alias for bootstrap size)
  - Output: plan metadata, signal summary, existing pair counts.
  - Side effects: none.

- `srs_initialize`
  - Input: same planning fields + sources (`jmdict_path`, `set_source_db`).
  - Output: plan metadata + mutation result (`applied`, counts).
  - Side effects: updates helper-owned `srs/profiles/<profile_id>/srs_store.json` only when plan is executable.

- `srs_rebalance_plan`
  - Input: pair/profile planning fields + sources needed for seed candidate generation.
  - Output: preview-only rebalance plan, protection diagnostics, proposed parks/activations, and candidate-pool diagnostics.
  - Side effects: none.

- `srs_rebalance_apply`
  - Input: same as `srs_rebalance_plan`.
  - Output: realized non-destructive rebalance result plus republished rulegen counts when the active inventory changed.
  - Side effects:
    - updates helper-owned `srs/profiles/<profile_id>/srs_inventory.json`
    - inserts newly activated seed items into `srs_store.json` when needed
    - preserves parked item history
    - republishes pair-local rulegen from the resulting active inventory

## Sizing policy (implemented)

All sizing normalization is centralized in `srs/set_policy.py` to avoid duplicated magic numbers.

Current constants:
- `DEFAULT_BOOTSTRAP_TOP_N = 800`
- `MIN_BOOTSTRAP_TOP_N = 200`
- `MAX_BOOTSTRAP_TOP_N = 50000`
- `DEFAULT_INITIAL_ACTIVE_COUNT = 40`
- `MIN_INITIAL_ACTIVE_COUNT = 1`
- `MAX_INITIAL_ACTIVE_COUNT = 5000`

Resolution algorithm:
1. Resolve requested bootstrap size from `bootstrap_top_n`; if missing, use `set_top_n`; if invalid, default to `800`.
2. Clamp bootstrap size to `200..50000`.
3. Resolve `max_active_items_hint` (optional), clamp to `1..5000` when present.
4. Resolve `initial_active_count`; if missing/invalid, use `max_active_items_hint` when present, otherwise default to `40`.
5. Clamp `initial_active_count` to `1..5000`, then clamp again so it never exceeds effective bootstrap size.
6. Emit policy notes in planner output whenever defaults/clamps are applied.

Current mutation behavior:
- Bootstrap builds candidate pool from `bootstrap_top_n`, then admits only `initial_active_count` unique lemmas into persisted inventory `S`.
- Items outside that admitted subset are excluded from `S` (implicit zero probability in sparse representation).
- Review scheduling still remains feedback-driven and due-based after admission.
- Active inventory membership is now persisted explicitly in `srs/profiles/<profile_id>/srs_inventory.json`.
  - `srs_store.json` retains learning history and word packages.
  - helper-side rule publication, sampled rulegen preview, runtime diagnostics, and reset now read or maintain the inventory manifest.
  - manual non-destructive rebalance now uses that manifest to mutate active membership without deleting retained history.
  - see `docs/srs/srs_preference_update_and_rebalance_policy.md`

## Event model

Queue path:
- `srs/profiles/<profile_id>/srs_signal_queue.json`

Event types supported by storage:
- `feedback`
- `exposure` (telemetry)

Policy decision for SRS scheduling:
- feedback is authoritative
- exposure is non-authoritative telemetry unless policy explicitly opts in later

## Extension/options integration

- Options action: "Initialize S for this pair".
- Options action: "Generate admitted words sample (5)".
- Options action: "Preview rebalance to current preferences".
- Options action: "Apply rebalance…".
- Options now also expose first editable admission inputs for the selected profile/pair:
  - topic interests
  - proficiency estimate
  - challenge target
- Current payload includes:
  - `strategy: "profile_bootstrap"`
  - `objective: "bootstrap"`
  - `profile_context`
  - `bootstrap_top_n`
  - `initial_active_count`
  - `max_active_items_hint`
  - `trigger: "options_initialize_button"`
- Stored signal path:
  - `srsProfiles.<profile_id>.srsSignalsByPair.<pair>`
- Current UI persistence policy:
  - blank signal inputs are treated as neutral and removed from stored pair signals
- Current executable path keeps the neutral bootstrap pool and applies profile-aware reranking on top of it.
- The new admission preview path reuses the same planner inputs but stops before any `S` mutation or rule publication.
- The new rebalance preview/apply path reuses the same normalized profile context, but runs against the current pair-local active inventory plus retained records and new seed candidates.
- That preview returns:
  - the resolved plan
  - a simulated admitted set drawn by the same weighted selector that live bootstrap uses
  - deterministic scoring diagnostics for the underlying reranked frontier
  - normalized bootstrap diagnostics and per-item explanations
- Rebalance returns:
  - protected/swappable partitions for the current active inventory
  - proposed parks and activations
  - explicit protection-rule diagnostics
  - confirmation-safe counts before mutation
- This keeps the UX aligned with the long-term architecture: user preferences steer admission first, while rulegen remains a downstream lexical layer.

## Current normalization seam

`core/lexishift_core/srs/profile_bootstrap.py` now keeps three layers separate:

- profile-context normalization
- candidate-trait extraction
- scoring policy

Current explicit policy choices:

- selector weights are versioned policy data, not ad hoc scorer-local literals
- missing profile signals remain neutral rather than being inferred
- candidate difficulty still uses the explicit bootstrap proxy `1 - admission_weight`
- topic affinity comes only from direct topic weights, candidate topic hints, or exact lexical matches
- ranking/scoring stays deterministic for tests and diagnostics, while admission selection now uses an explicit weighted-without-replacement selector
- future exact implicit lexical trends should use a bounded admission lane rather than giant lexical coefficients inside the main scorer
- future register/style preferences such as `slang` should be modeled as a separate axis, not overloaded into topic weights

That means future preference work should extend the normalized context or the scoring policy deliberately, rather than adding scorer-local field fallbacks.

## Next implementation steps

1. Refine the normalized profile context and policy registry as richer preference signals become real.
2. Expand candidate traits available to `profile_bootstrap`, especially topical hints and richer difficulty proxies.
3. Extend `profile_growth` beyond manual rebalance into controlled continuous admission/update logic for active pairs.
4. Add feedback-window aggregation for `adaptive_refresh`.
5. Define a bounded lexical-trend admission lane for opted-in exact-word implicit signals.
6. Add policy registry by pair/domain to route strategy defaults.
7. Expand UI surfaces beyond the current first-step editor and keep planner diagnostics inspectable.
   - currently editable: interests, proficiency estimate, challenge target
8. Later add explicit onboarding inputs for:
   - proficiency estimate
   - target vocabulary band
   - confidence in that estimate
