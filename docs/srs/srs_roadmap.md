# SRS Roadmap (Set S + Practice Layer)

Status: active mixed roadmap
Role: Mixed
Last updated: 2026-05-27
Last verified: 2026-05-27 en-es admission calibration report, focused calibration test, generated JSON/Markdown artifacts, SRS encounter-watch harness update, and en-es profile-preference journey lane; roadmap claims not fully re-audited
Purpose: preserve the SRS current-state snapshot, remaining E2E gaps, and roadmap workstreams
Source-of-truth: mixed roadmap; current behavior truth lives in SRS/helper/extension code, SRS harnesses, and `docs/developer/feature_state_matrix.md`.

Related design:
- `docs/srs/README.md`
- `docs/srs/srs_hybrid_model_technical.md`
- `docs/srs/srs_admitted_words_dashboard_plan.md`
- `docs/srs/srs_browsing_based_admission_plan.md`
- `docs/architecture/srs_lp_architecture.md`

Routing note:
- use `docs/srs/README.md` to decide which SRS doc owns a claim before
  editing or archiving SRS docs
- use `docs/developer/feature_state_matrix.md` for implemented/default-on/
  verified status
- treat this roadmap as mixed current snapshot plus planned work, not as proof
  that a behavior is shipped

## Goal
Ship a non-destructive SRS layer where:
- `S` is the active study inventory
- scheduling is feedback-driven (1..4 ratings)
- planner strategies control admission/growth of `S`
- rulegen/debug uses current helper-managed `S`

## Current architecture snapshot

### Runtime and storage
- Practice gate and scheduler are implemented.
- Canonical helper profile store path:
  - `.../LexiShift/srs/profiles/<profile_id>/srs_store.json`
- Helper also owns:
  - `srs/srs_settings.json` (global policy defaults)
  - `srs/profiles/<profile_id>/srs_status.json`
  - `srs/profiles/<profile_id>/srs_rulegen_snapshot_<pair>.json`
  - `srs/profiles/<profile_id>/srs_ruleset_<pair>.json`
  - `srs/profiles/<profile_id>/srs_signal_queue.json`
- Extension runtime applies local rules and helper SRS rules concurrently.
- Extension-to-helper communication is routed through the extension service worker bridge (single native messaging boundary).
- Runtime diagnostics now include helper/store/ruleset/cache counts plus the last helper rules fetch error from the tab runtime.
- Helper profile snapshot API now reads GUI settings at `settings.json` (active profile + profile list) for cross-surface profile selection.
- Extension storage model is now profile-first (`srsSelectedProfileId` + `srsProfiles.<profile>.srsByPair/srsSignalsByPair`) with no legacy LP-first fallback.
- Profile-scoped extension UI prefs are now part of the same container (`srsProfiles.<profile>.uiPrefs`) and include staged/apply flow for options background settings.
- Current first-class admission preference controls in options are still narrow:
  - topic interests
  - proficiency estimate
  - challenge target
- other signal families can persist in `srsSignalsByPair`, but they are not yet dedicated options controls.

### Set planning scaffolding
- `srs/set_strategy.py`: strategy/objective taxonomy.
- `srs/set_policy.py`: centralized sizing policy/defaults/clamps.
- `srs/set_planner.py`: plan metadata + diagnostics.
- `srs_plan_set` helper command: no side effects.
- `srs_initialize` helper command: mutation via the requested executable
  bootstrap strategy.
- Current execution reality:
  - `frequency_bootstrap` remains the no-strategy helper default
  - options initialize and admission preview explicitly request
    `profile_bootstrap`
  - requested `profile_bootstrap` now reports and executes as profile-aware
    bootstrap over the frequency seed frontier
  - refresh now defaults to `profile_growth`, which keeps later admissions
    specialized after the initial bootstrap batch by applying profile-aware
    candidate scoring before the normal refresh gates
  - `adaptive_refresh` remains a non-default future strategy
- Bootstrap admission policy now applies explicit POS buckets with centralized coefficients (non-magic constants).
- JP stopword filtering is active from helper-owned `srs/stopwords/stopwords-ja.json` (or sibling fallback path).

### Feedback pipeline
- Extension popup ratings:
  - `1 -> again`
  - `2 -> hard`
  - `3 -> good`
  - `4 -> easy`
- Helper updates item scheduling fields on feedback.
- Extension helper sync now uses a persistent queue with retry/backoff to submit `record_feedback`.
- Signal queue persists event stream for future aggregation.

### Verified E2E slice (current)
- `srs_initialize` mutates helper-owned `S` (`srs_store.json`) and immediately publishes runtime ruleset/snapshot.
- Runtime replacements from helper-generated SRS rules are active in pages (not just debug preview).
- Local rules continue to work concurrently with SRS rules.
- Feedback UI path (`1..4`) is wired through extension sync queue to helper feedback endpoint.
- Current published ruleset still reflects the active/admitted inventory more broadly than a dedicated due-only subset, but runtime serving filters future-due helper SRS rules when helper due metadata is present.

### Remaining to reach full SRS E2E (feedback -> update -> serving)
- Complete deterministic E2E assertion flow:
  - bootstrap/initialize -> observe replacements -> submit feedback -> verify helper scheduling fields changed -> refresh/admit -> verify serving distribution changed.
- Decide whether a dedicated due-only publication artifact is still needed now that runtime gating uses helper SRS due metadata.
- Automatic refresh trigger now exists for successful helper feedback flushes:
  the helper requires thresholded feedback plus Good/Easy counts, tracks
  per-profile/pair attempt state, and then runs the normal `profile_growth`
  refresh path. Full E2E browser assertion coverage is still pending.
- Add stronger observability for feedback effects:
  - before/after snapshots of `next_due`, `stability`, `difficulty`, selected
    lemmas, and active item counts are now emitted by the SRS quality harness.
- Harden retry/idempotency semantics under helper restart/offline transitions.
- Improve rule generation quality so SRS-serving words are pedagogically precise (see rulegen quality gap below).

### Rulegen quality gap (current)
- Current JA-target rulegen can emit broad/glossy English source phrases that are semantically too general.
- This produces technically valid replacements but weaker pedagogical quality.
- Immediate quality track:
  - stronger generic-gloss demotion and denylist rules,
  - POS/sense-aware filtering before emission,
  - stricter confidence penalties for broad/ambiguous glosses.

---

## Workstream tracking

Status key:
- `[ ]` not started
- `[~]` in progress
- `[x]` done

### Workstream A — Review scheduler and practice gate
- `[x]` Core SRS item model + FSRS scheduler update function.
- `[x]` Runtime gate integration for helper-published SRS rules with due metadata (publication still remains broader than a dedicated due-only artifact).
- `[x]` Feedback ingestion from extension popup.
- `[~]` Formal lifecycle statuses (backend `active`/`discarded`/`cleared`
  markers exist; fuller review/mastery lifecycle remains planned).
- `[~]` User-facing SRS item visibility (options dashboard has search/filter/
  sort, pagination, refresh metadata, published-rule summaries/details, and
  confirmed discard plus encounter-watch visibility; restore/mastery actions
  remain planned).
- `[x]` Refresh budget hardening (`max_active` caps total active SRS items for
  the pair; `max_new_per_day` caps each refresh admission).
- `[ ]` Calendar-day quota ledger if `max_new_per_day` must remain strict
  across repeated manual refreshes in the same day.

### Workstream B — Set `S` admission and initialization
- `[x]` Frequency bootstrap pipeline for initial `S`.
- `[x]` JMDict-filtered JA bootstrap flow (`en-ja`).
- `[x]` Planner scaffold (`srs_plan_set` + extended `srs_initialize`).
- `[x]` Centralized sizing policy (`bootstrap_top_n`, `initial_active_count`, clamps, diagnostics notes).
- `[x]` Profile-aware weighting in `profile_bootstrap` (normalization,
  scoring, diagnostics, helper plan reporting, options admission preview, and
  initialize execution use profile-aware bootstrap when requested).
- `[x]` Capped reserved topic-lane selection in `profile_bootstrap` so explicit
  topic preferences can move admission while preserving a mixed general batch.
- `[~]` Encounter-starvation diagnostics/policy for rare admitted words that
  receive little or no replacement exposure and therefore cannot easily collect
  learner feedback; dashboard summary visibility and `admitted_at`-based
  stale-unseen diagnostics exist and are now covered by the SRS quality harness
  for fresh/stale/legacy/reviewed/no-rule states, refresh no-op output now
  reports stale-unseen active capacity pressure, while the exact threshold and
  release/parking policy remain undecided.
- `[x]` POS-aware admission biasing/filtering (explicit default order: noun > adjective > verb > adverb > other).
- `[x]` Helper-side stopword filtering for bootstrap candidates (strict JSON-array format).
- `[x]` Initial active subset admission in bootstrap (`initial_active_count`) now mutates persisted `S`.
- `[x]` MVP executable `profile_growth` policy for ongoing specialized
  admission after bootstrap; later refresh/growth admissions must keep applying
  profile topic/proficiency/challenge shaping instead of reverting to generic
  frequency order.
- `[ ]` Pair-configurable admission coefficients and denylist controls (helper source of truth).

### Workstream C — Signals and adaptive refresh
- `[x]` Signal queue format + append/read utilities.
- `[x]` Feedback event writes from helper path.
- `[x]` Browsing-based admission planning doc for opt-in, local-only word signals.
- `[~]` Event aggregation design for refresh decisions.
- `[~]` Feedback-window aggregation for admission updates (separate from due scheduling).
- `[x]` Persist automatic feedback-trigger state per profile/pair in
  `srs_auto_refresh_state.json`; broader adaptive aggregate modeling remains
  future work.
- `[~]` Persist browsing admission aggregate state (core decayed/bounded store, opt-in helper dev ingest, and hidden dev extension replacement-exposure packet builder exist; broad page capture is not wired).
- `[~]` Preview-only browsing relevance boost with neutral-vs-browsing diagnostics (backend probability diagnostics, offline helper/core text probes, refresh-path browsing preview, small-budget `Balanced` fractional lane realization, and options refresh output diagnostics exist; dedicated controls are not wired).
- `[x]` Realized-share simulation for browsing strength presets (`Off`, `Balanced`, `Strong`) under new-word budgets.
- `[~]` Runtime page replacement load model (page-level budgets, explicit standard density defaults, and SRS metadata-aware budget priority exist; durable mastered/released dropoff remains open).
- `[~]` Resource/storage/cognitive-load budget audit (source constants and
  helper artifact report exist; live browser storage bytes and helper cache TTL
  policy remain open).
- `[~]` Lifecycle audit for admission triggers, mastered/released state, and durable discard/block behavior (code-backed audit exists; refresh admission, scheduler due selection, active inventory, and rulegen publication respect non-active lifecycle states; backend `user_blocked` writer marks existing items `discarded` and removes active inventory; user-facing lifecycle controls remain open).
- `[ ]` Opt-in gated browsing relevance boost for actual admission refresh.
- `[x]` Automatic feedback-threshold trigger for the existing `profile_growth`
  refresh path, with options controls for enablement, feedback thresholds,
  same-day repeat threshold, and cooldown.
- `[ ]` Automatic `adaptive_refresh` trigger policy beyond the current
  feedback-threshold `profile_growth` trigger.
- `[~]` Explicit policy gate for any non-feedback signals (browsing helper ingest and extension replacement-exposure packet builder require opt-in; production capture policy is not wired).
- `[x]` Manual/explicit helper refresh action (`srs_refresh`) for feedback-driven admissions.

### Workstream D — Profile modeling
- `[x]` Profile schema draft and extension scaffold keys (`srsSelectedProfileId`, `srsProfiles`).
- `[x]` Profile signal normalization/validation (`profile_id`, selected profile id).
- `[x]` Options now persist/load SRS settings in profile-first storage (pair nested under selected profile).
- `[x]` Native host profile catalog API (`profiles_get`) backed by helper `settings.json`.
- `[x]` Options profile controls:
  - extension-local selected profile (global),
  - pair-specific SRS settings loaded from that profile,
  - helper profile refresh.
- `[x]` Profile-scoped options UI prefs (`uiPrefs`) with explicit Apply publish path (`backgroundAssetId`, `backgroundEnabled`, `backgroundOpacity`, `backgroundBackdropColor`).
- `[x]` Native messaging `profile_id` wiring for SRS commands (`get_ruleset/get_snapshot/srs_diagnostics/record_feedback/srs_initialize/srs_refresh/srs_reset`).
- `[x]` Helper SRS files moved to profile-scoped directory structure under `srs/profiles/<profile_id>/`.
- `[ ]` Profile editor UX (interests/proficiency/objectives/constraints).
- `[ ]` Future slow proficiency calibration from durable SRS progress
  evidence; useful later, but not required for MVP specialized admission.
- `[ ]` Pair-specific planner policy registry.

### Workstream E — Rulegen and S integration
- `[x]` Rulegen preview made non-mutating.
- `[x]` Helper initialize action exposed in options.
- `[x]` Ensure debug rulegen scopes to current helper-managed `S` only.
- `[x]` Add sampled rulegen debug path (helper-side probabilistic sampling from current `S`).
- `[~]` Unified diagnostics surface for plan + snapshot + ruleset.
- `[x]` Initialization diagnostics now include admission profile + weighted preview of admitted items.
- `[x]` Production publish path: `srs_initialize` now runs rulegen once and persists runtime ruleset/snapshot.
- `[x]` Production publish path: `srs_refresh` immediately runs/persists rulegen when new items are admitted.
- `[x]` Options action for explicit refresh+publish flow (non-debug).
- `[x]` Runtime diagnostics surface: helper store/ruleset + extension cache + current tab rule counts.
- `[x]` Extension runtime consumes helper rules through service-worker bridge (single native messaging boundary).
- `[x]` Read-only options dashboard can list admitted SRS words for the selected
  pair/profile through the helper/native-host route, including encounter-watch
  counters for active words with zero exposure plus zero feedback and
  age-aware stale-unseen counts when `admitted_at` is known.
- `[x]` Helper bridge test covers profile-bootstrap initialization through active
  rule publication and dashboard listing.
- `[ ]` Rule quality hardening for broad/ambiguous gloss sources.

### Workstream F — Cross-surface consistency
- `[~]` Bundle format for settings/store exists.
- `[~]` GUI/extension profile bridge:
  - extension reads helper profile catalog via native host,
  - extension keeps local selected profile (does not mutate GUI/helper active profile),
  - extension sends selected `profile_id` in runtime/helper requests.
- `[ ]` BetterDiscord plugin profile bridge wiring.
- `[ ]` Conflict handling when multiple surfaces write feedback concurrently.

### Workstream G — End-to-End validation and calibration
- `[~]` Define deterministic SRS E2E scenario set (bootstrap -> sampled rulegen -> feedback -> resample).
- `[x]` Add helper integration tests for full feedback loop affecting serving priority.
- `[x]` Add deterministic helper test: feedback updates schedule fields and can trigger `retention_low` admission pause.
- `[x]` Add assertion checks for "no schedule mutation from exposure-only events".
- `[x]` Add deterministic helper test: high-retention feedback enables admissions and publishes rulegen outputs.
- `[x]` Add multi-phase simulation test (`high retention -> low retention pause -> high retention`) asserting S growth + ruleset/snapshot evolution (`core/tests/srs/test_srs_feedback_simulation.py`).
- `[x]` Add helper bridge test for preference-aware bootstrap -> active inventory
  -> rule publication -> dashboard visibility.
- `[x]` Add deterministic journey harness lane for preference-aware en-es
  bootstrap plus feedback-driven growth/pause/resume continuity.
- `[x]` Add post-feedback `profile_growth` topic-share contract coverage: a
  fixed en-es preference loop now derives the expected preferred-topic count
  from topic strength, the capped reserved topic lane, and remaining topic
  capacity. It asserts a strong animal preference, a weaker animal preference,
  and sparse medicine/technology cases where the topic can be exhausted before
  the next refresh wave.
- `[x]` Surface refresh budget, selected lemmas, and preview-only browsing
  comparison in the options refresh output for manual SRS testing.
- `[x]` Add diagnostics snapshots for before/after feedback cycles (store,
  scheduler fields, selected lemmas, and refresh deltas).
- `[x]` Add initial per-pair calibration report for en-es admission
  distributions:
  - ranked preview batch shares are now visible across topic/proficiency profiles;
  - weighted-without-replacement seeded samples are visible and currently warn
    that full-pool weighted sampling is too diffuse for topic preferences;
  - top-k weighted diagnostics and the real reserved topic-lane policy are now
    reported so MVP policy choices can be compared against realized topic shares
    without mutating production SRS state;
  - reserved topic-lane rows now include expected topic count/status derived
    from topic strength, the lane cap, ranked-window topic candidates, and
    full-pool general fill capacity, so sparse coverage can be separated from
    policy failure.
- `[x]` Add en-es MVP topic recommendation note that classifies ordinary
  visible topics, beta/optional topics, hidden source-blocked topics, and
  register/style preferences using the release-readiness and admission
  calibration artifacts.
- `[x]` Add beta-topic deep dive for `plants_nature` and
  `travel_places_transport`, separating selector failure risk from content
  depth/precision risk and listing promotion thresholds.
- `[x]` Record strict-MVP topic-picker decision: first tester-facing picker
  excludes beta topics; `plants_nature` and `travel_places_transport` remain
  hidden until beta UX or coverage promotion work is explicit.
- `[x]` Wire strict-MVP topic visibility into peripheral code:
  `srs_topic_preference_taxonomy_en_es.json` now carries
  `mvp_picker_visibility`, the options-page chips are contract-tested against
  `strict_mvp_visible`, and the local admission lab labels all taxonomy families
  with their tester-facing or diagnostic-only visibility state.
- `[~]` Add E2E checks for post-feedback refresh trigger behavior (manual and
  automatic): helper policy/state tests exist; browser/native E2E remains open.

### Workstream H — LP parity and de-hardcoding (`en-de`/`en-es` vs `en-ja`)
Current parity snapshot (as of 2026-02-14):
- `en-de` helper rulegen path is implemented and can run when `freq-de-default.sqlite` and `freedict-de-en` are present.
- `en-es` and `es-en` helper rulegen paths are implemented and can run when `freq-es-cde.sqlite` and the corresponding FreeDict resources are present.
- `en-es` rulegen supports paired plural morphology metadata (`target_surface`) while preserving canonical replacement lemma identity.
- LP capability registry now drives helper requirement checks, daemon supported-rulegen pair selection, and SRS pair UI exposure.
- Full parity is not complete because some cross-surface runtime consistency checks are still pending.

Tracking checklist:
- `[~]` Remove `en-ja`-specific hardcoding from desktop local SRS grow/init code paths in `apps/gui/src/main.py` (frequency/dictionary requirements and source selection).
- `[x]` Generalize helper daemon supported pairs beyond `{"en-ja"}` in `apps/gui/src/helper_daemon.py`.
- `[x]` Replace JMDict-only bootstrap gate with pair-specific dictionary gates (for example FreeDict gate for `en-de`) in `core/lexishift_core/srs/seed.py`.
- `[x]` Replace hardcoded seed metadata source `"bccwj"` with pair/frequency-pack-derived metadata in `core/lexishift_core/srs/seed.py`.
- `[x]` Make POS bucket mapping pair-aware (German tags such as `SUB/VER/ADJ/ADV`) instead of substring heuristics only, in `core/lexishift_core/srs/admission_policy.py`.
- `[x]` Fix pack-to-pair mapping so FreeDict packs map by direction (`freedict-de-en -> en-de`, `freedict-en-de -> de-en`) in `apps/gui/src/main.py`.
- `[x]` Add parity-focused tests:
  - helper diagnostics for `en-de` required inputs,
  - initialize/refresh publish checks for `en-de`,
  - POS/admission behavior checks for German tags.
- `[x]` Define/ship `stopwords-de.json` policy default (helper auto-seeds placeholder under `srs/stopwords/`) and expose stopword path/existence via diagnostics.

Definition of done for `en-de` parity:
- `[~]` `en-de` initialize succeeds from GUI and helper CLI without `en-ja`-only assumptions.
- `[~]` `en-de` refresh admits/publishes ruleset and snapshot with non-empty outputs on valid inputs.
- `[x]` Admission metadata, POS buckets, and source labels are LP-correct (no JA-specific constants).
- `[~]` Runtime/diagnostics report the selected LP consistently across extension + helper + GUI surfaces.

---

## Near-term sequence

### Phase 1 (stabilize model contract)
1. Keep feedback as the only scheduling event.
2. Lock sizing contract (`bootstrap_top_n`, `initial_active_count`, `max_active_items_hint`) and document all clamps/defaults.
3. Document lifecycle statuses and migration path.
4. Keep frequency bootstrap as executable baseline.

### Phase 2 (admission quality)
1. Keep profile-aware bootstrap/growth admission calibrated against topic
   coverage and learner-proficiency behavior.
2. Make `initial_active_count` executable in active/frontier serving policy.
3. Add planner diagnostics for why each item entered `S`.
4. Add policy knobs for per-pair new-item pace.
5. Make POS/stopword admission policy pair-configurable without code edits.

### Phase 3 (adaptive refresh)
1. Aggregate feedback trends in bounded windows.
2. Add refresh trigger thresholds and rate-limit/pacing policy.
3. Execute `adaptive_refresh` with audit-friendly logs.

### Phase 4 (E2E + profile integration)
1. Lock an E2E test matrix for extension + helper feedback sync paths.
2. Implement profile-signal normalization and pair-level admission bias persistence.
3. Validate that profile adjustments affect admission (`weight 1`) but not due scheduler math (`weight 2`).
4. Add operator-facing diagnostics for admission drift and refresh decisions.

---

## Terminology
- Historical "seed" should be read as "initial set bootstrap."
- `source_type: initial_set` means "item admitted during bootstrap of S."
- Scheduling remains feedback-driven after admission regardless of initial source type.
