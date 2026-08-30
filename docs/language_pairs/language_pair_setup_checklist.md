# Language Pair Setup Checklist

Status: active LP onboarding runbook
Role: Runbook / operational
Last updated: 2026-06-30
Last verified: 2026-06-10 en-ja advisory rulegen acceptance, SRS/runtime journey smoke, installed-resource journey smoke, topic-source/review/overlay diagnostics, and targeted SRS/extension/helper contract tests; 2026-06-30 learner-difficulty playbook routing link only
Source-of-truth: operational onboarding checklist; current LP capability truth still lives in capability/resource code, canonical architecture docs, tests, and generated audits.

Purpose:
- Provide a formal, reusable checklist for implementing a new LP (Language Pair) end-to-end.
- Keep implementation work consistent across GUI, extension, helper, core rulegen, and SRS.

Scope:
- LP means `source-target` key (examples: `en-ja`, `en-de`, `de-en`, `ja-ja`).
- This checklist covers setup for both synonym generation and SRS-backed runtime usage.

Related:
- Language-pair docs authority map: `docs/language_pairs/README.md`.
- Core LP architecture contract: `docs/architecture/srs_lp_architecture.md`.
- For extension + helper focused rollout sequencing, see `docs/language_pairs/extension_lp_generalization_checklist.md`.
- POS normalization implementation plan: `docs/rulegen/pos_normalization_workstream.md`.
- Rulegen onboarding operating model: `docs/rulegen/lp_onboarding_operating_model.md`.
- SRS learner-difficulty ranking onboarding:
  `docs/srs/srs_learner_difficulty_lp_onboarding_playbook.md`.

Routing note: this checklist is the cross-surface operational runbook. Use
`docs/language_pairs/README.md` to choose the owning LP doc before changing
status, resource, or onboarding claims. Use
`docs/rulegen/lp_onboarding_operating_model.md` for rulegen-specific mature-pair
bring-up.

## `en-ja` Onboarding Status And Next Queue (2026-06-10)

Evidence checked for this status:

- Source stack: `core/lexishift_core/helper/source_stacks.py` declares
  `en-ja-default-v1` with `freq-ja-bccwj` for target-frequency SRS/admission
  and `jmdict-ja-en` for rulegen/semantic locator support.
- Rulegen advisory lane:
  `docs/test_outputs/rulegen_benchmark_en_ja_latest.json` reports `33` cases,
  `96.97%` top1, `100.00%` top3, `0.00%` forbidden-top1, and `3.03%`
  forbidden-any.
- Rulegen quality gate:
  `docs/test_outputs/rulegen_quality_gate_en_ja_latest.json` has no failures;
  the remaining warnings are `DELTA_SCOPE_BASELINE_MISSING` and
  `SATURATION_SINGLE_RUN_WARN`.
- SRS quality harness:
  `docs/test_outputs/srs_quality_latest.json` reports `PASS` with `pass=22`,
  `warn=0`, `fail=0` across the current synthetic SRS coverage.
- Topic-source readiness:
  `docs/test_outputs/srs_jmdict_topic_source_readiness_en_ja_latest.json`
  reports `9,258` candidate-like BCCWJ rows in the top `10k` frontier, `8,403`
  with any JMDict match, `8,363` with strong exact/alias JMDict matches,
  `1,910` with trusted JMDict topic fields after product-taxonomy mapping, and
  `866` with trusted topic fields through strong exact/alias matching.
  `12 / 16` product taxonomy families have strong candidate rows.
- Topic precision calibration:
  `docs/test_outputs/srs_jmdict_topic_review_packet_en_ja_latest.json`
  samples `144` rows across all `116` family/match/source-label cells and
  applies `144` user-approved labels: `8` strong accepts, `57` light accepts,
  `63` wrong-topic rejects, and `16` secondary/obscure rejects.
- Topic overlay/admission PoC:
  `docs/test_outputs/srs_jmdict_topic_overlay_poc_en_ja_latest.json` builds a
  user-approved, non-default `65` row overlay candidate from accepted labels
  (`8` strong, `57` light). Only the `8` strong labels are runtime-effective
  under the current `profile_injection_min_membership=1.0` policy; light labels
  remain lower-membership evidence for later scalar-topic work. Strong accepted
  labels move the profile preview for `finance_business`,
  `law_politics_civics`, `medicine_health`, and `sports_fitness`; `games` and
  `science_technology` remain thin at the top-preview window. This proves
  reviewed-label integration and some admission movement, not broad
  product-ready topic recall.
- SRS journey smoke: deterministic, real-publication, and installed-data
  `en-ja` journey lanes complete with `fail=0`. The only journey warning is
  the known admitted-set publication broader than due-subset observation.
- Installed-resource smoke: the installed-data journey uses real BCCWJ/JMDict
  candidates, publishes rules/snapshots/semantic inventory, and preserves
  Japanese script-form word packages in an isolated temp helper root.
- Semantic/veto breadth-stress lane:
  `docs/test_outputs/semantic_routing_sentence_veto_en_ja_breadth_latest.json`
  reports `95` cases, `96.8%` decision accuracy, `100.0%` replace
  precision, `92.1%` replace recall, `0` harmful replacements, and `3` false
  abstains under the current lexical breadth candidate.
- Semantic/veto product-quality breadth gate:
  `docs/test_outputs/semantic_veto_product_quality_en_ja_latest.json` reports
  `92.1%` positive allow, `100.0%` negative abstain, utility above both
  lexical allow-all and abstain-all baselines, and status `review` only because
  representative browsing coverage remains unmeasured.

Completed for current `en-ja` onboarding stage:

- [x] Source-stack setup resources are declared for Learning Languages.
- [x] JMDict-backed rulegen adapter exists and has a dedicated advisory lane.
- [x] Current rulegen advisory result is accepted for this stage; the single
      `世界` triage item is not blocking.
- [x] SRS initialize/refresh/publication smoke passes for `en-ja`.
- [x] Installed-resource journey smoke passes for `en-ja` without mutating live
      helper state.
- [x] Options/SRS story-card and runtime contract tests pass after the
      multi-story UI work.
- [x] First expanded semantic/veto breadth-stress suite and product-quality
      policy exist and pass the mirrored `en-es` initial product thresholds.
- [x] Explicit backend semantic decision policy
      `en_ja_sentence_veto_breadth_v1` is registered for helper calls, but not
      promoted as the default `en-ja` runtime policy.
- [x] Promotion posture is decided for this stage: keep the current rulegen lane
      and sentence-veto policy advisory/non-default. Do not promote an `en-ja`
      machine delta baseline, `required_benchmark_pairs`, or default runtime
      semantic policy until product/default enablement needs that stronger
      contract.
- [x] `世界` triage posture is decided for this stage: keep `sphere` forbidden
      because it is obscure and not a candidate we want to bless for teaching,
      but accept the current advisory lane with this known nonblocking
      forbidden-any failure rather than weakening the case labels.

Real remaining `en-ja` onboarding/backlog items:

- [ ] Run a broader en-ja parameter-sensitivity sweep only if we need evidence
      beyond the accepted one-config advisory lane.
- [x] Run the `en-ja` topic-source readiness pass and store the pair-local
      taxonomy/evidence artifacts:
      `docs/test_inputs/srs_topic_preference_taxonomy_en_ja.json` and
      `docs/test_outputs/srs_jmdict_topic_source_readiness_en_ja_latest.json`.
- [x] Generate the first deterministic topic precision review packet:
      `docs/test_outputs/srs_jmdict_topic_review_packet_en_ja_latest.json`
      samples `144` rows across all `116` family/match/source-label cells.
- [x] Add the first agent-labeled calibration file:
      `docs/test_inputs/srs_jmdict_topic_review_labels_en_ja.json`.
- [x] Generate a diagnostic topic-overlay/admission PoC:
      `docs/test_outputs/srs_jmdict_topic_overlay_en_ja_latest.json` and
      `docs/test_outputs/srs_jmdict_topic_overlay_poc_en_ja_latest.json`.
- [x] Promote the approved strong-label overlay into ordinary helper admission
      overlay resolution for `en-ja` while keeping the overlay non-default and
      light labels non-effective at runtime. Focused helper preview coverage in
      `core/tests/helper/test_helper_engine.py` verifies that an `en-ja`
      medicine/health interest can activate the approved overlay and move a
      matched Japanese candidate into the admitted preview.
- [x] Gate the Options topic chips for `en-ja` to the approved strong-label
      families (`finance_business`, `games`, `law_politics_civics`,
      `medicine_health`, `science_technology`, `sports_fitness`) with focused
      extension contract coverage.
- [ ] Complete the ordinary installed Options/helper/runtime E2E for `en-ja`:
      add/select an `en-ja` Vocabulary Practice story in the Options page,
      initialize or preview through the GUI-backed helper using one supported
      topic, and confirm runtime replacement still publishes and serves the
      selected pair.
- [ ] Do not claim full profile-personalized topic parity yet. The current
      overlay proves a working approved strong-label path; broader parity still
      needs either more reviewed strong labels or an explicit scalar policy for
      light labels before visible preference movement is comparable to the
      `en-es` topic MVP.
- [ ] Do not claim default-on sentence-veto parity from the breadth-stress lane
      alone. The current breadth result is healthy and close to `en-es`, but
      representative browsing or LLM-expanded locked coverage remains unmeasured.
- [ ] Keep the current zero-harmful breadth-stress posture protected in future
      sweeps; the known phrase/no-winner leaks (`ball is in your court`,
      `park that issue`) are now covered by active-only phrase scope plus the
      idiom-tail phrase signal.
- [ ] Product/default enablement still needs the same release decision path as
      other advisory LPs: setup UX, installed resources, runtime smoke, and
      explicit default-on policy. If that path starts, first refresh
      representative veto/runtime evidence and then decide whether to promote
      `en_ja_sentence_veto_breadth_v1`.

## `en-de` Onboarding Status And Real Follow-Up Queue (2026-06-09)

Evidence checked for this status:

- Source stack: `core/lexishift_core/helper/source_stacks.py` declares
  `en-de-default-v1` with required `freq-de-default`, `freedict-de-en`,
  `freedict-en-de`, and English source-frequency prior setup resources.
- Installed resource smoke: current local `freq-de-default.sqlite`,
  `freq-en-leipzig-default/main.sqlite`, `freq-en-coca.sqlite`,
  `freedict-de-en/main.sqlite`, and `freedict-en-de/main.sqlite` exist and
  pass SQLite integrity checks where applicable.
- Installed helper smoke: active profile `suisui` resolves daemon pairs
  `en-de` and `en-es`; active status has `last_error = null`.
- SRS quality harness: `docs/test_outputs/srs_quality_latest.json` reports
  `PASS` with `pass=22`, `warn=0`, `fail=0`.
- Rulegen advisory lane: `docs/test_outputs/rulegen_benchmark_en_de_latest.json`
  reports `58` cases, `86.21%` top1, `100.00%` top3, `0.00%`
  forbidden-top1, and `15.52%` forbidden-any under the top3-first Leipzig
  source-frequency preset.
- Rulegen quality gate: `docs/test_outputs/rulegen_quality_gate_en_de_latest.json`
  reports `PASS` for the scoped `en-de` advisory lane, with the expected
  `DELTA_SCOPE_BASELINE_MISSING` warning because the repo has not promoted an
  `en-de` machine delta baseline yet.
- Source-frequency default: `freq-en-leipzig-default` is implemented as an
  app-managed local Leipzig English News build and is the default English
  source-frequency prior for `en-de` rulegen; `freq-en-coca` remains fallback
  compatibility only.
- Product acceptance: the current `en-de` scoped advisory result is accepted
  for current beta/onboarding use as of 2026-06-09. This does not make `en-de`
  hard-gated parity with `en-es`, and it does not create an accepted machine
  delta baseline.

Completed for `en-de` beta:

- [x] Directional key is `en-de` for English source -> German target.
- [x] Source-stack setup resources are visible through Learning Languages.
- [x] App-managed downloads/builds cover the required `en-de` frequency and
      FreeDict resources.
- [x] Vocabulary Practice supports multiple stories; switching the active story
      does not replace or reorder cards.
- [x] Helper daemon/tray reads the active profile status instead of stale
      default-profile status.
- [x] Installed app + extension smoke passed for `en-es`/`en-de` switching and
      runtime replacements.
- [x] App-managed `freq-en-leipzig-default` local build is implemented and
      resolves as the default English source-frequency prior.
- [x] `en-de` canonical rulegen preset is retuned around the accepted
      top3-first source-frequency candidate and the scoped advisory gate
      passes.
- [x] Current scoped `en-de` advisory result is explicitly accepted for beta
      use while remaining separate from hard-gated parity and machine baseline
      promotion.

Real remaining `en-de` onboarding/backlog items:

- [ ] Decide later whether to promote an `en-de` machine delta baseline. The
      current advisory result is product-accepted for beta use, but delta checks
      intentionally warn until a baseline artifact/policy is promoted.
- [ ] TODO idea: run a limited reverse-check experiment only after the better
      source-frequency prior lands. Reverse evidence looks useful for some
      false-friend/defaultness patterns, but early broad experiments did not
      beat the best frequency-first run.
- [ ] TODO idea: add severity-aware triage notes for forbidden-any cases before
      treating the raw forbidden-any rate as a hard score. Some hits are truly
      bad teaching candidates, while others are valid-but-non-default senses.
- [ ] TODO idea: investigate English POS/defaultness enrichment only if the
      frequency replacement plus retune still leaves systematic broad-gloss
      failures.
- [ ] Generate/evaluate a real `en-de` semantic/veto reference pack before
      claiming sentence-veto parity. The current source stack intentionally
      exposes `en-de-semantic-reference-pending` as non-blocking and unwired.
- [ ] Expand `en-de` topic coverage if product UX needs more topic-selectable
      samples. Admission/profile topic plumbing is present, but the German
      frequency DB currently has no topic columns and the options UI only
      enables a limited supported-topic subset for `en-de`.
- [ ] Evaluate German monolingual sources (`OdeNet`, `OpenThesaurus`) only as
      evidence enrichment experiments. They are registered as optional/unwired
      source-stack candidates, not default algorithm inputs.
- [ ] Run a stabilization pass before PR/release handoff because this branch
      contains broad LP/resource/extension/helper changes, not a narrow patch.

Not currently a concrete `en-de` TODO:

- `en-de` false-abstain cleanup is not listed as an actionable item here because
  the current checkout has no committed `en-de` semantic-veto reference artifact.
  If such an artifact is generated later, false abstains should be tracked from
  that artifact's own benchmark/triage output.

Cross-pair follow-up:

- Keep hosted/bundled redistribution policy separate from user-local
  auto-download policy. A source can be safe for app-managed local acquisition
  without being safe for LexiShift-hosted converted artifacts.
- Manual-supply UX baseline is implemented for supported source-file frequency
  builders: provider page, expected file description, source-rights
  confirmation, Downloads-folder candidate detection, local validation/source
  conversion, manifest/provenance writing, and clear installed/error status.
  Browser or extension-level download interception remains a future convenience,
  not a setup blocker.
- After semantic/manual-supply UX settles, tighten the next-LP onboarding docs so
  future pairs follow the source-stack registry, benchmark loop, setup-resource
  catalog, and semantic-pack decision points without pair-specific archaeology.

## 0) Implementation Sequence (Use This Order Every Time)

1. Register LP capability and defaults.
   - Edit: `core/lexishift_core/helper/lp_capabilities.py`
   - Register the machine-readable source stack:
     `core/lexishift_core/helper/source_stacks.py`
   - Check fallback/resource logic: `core/lexishift_core/helper/pair_resources.py`
   - Validate requirement checks: `core/lexishift_core/helper/engine.py`
   - Create/update machine-readable rulegen LP profile: `docs/test_inputs/rulegen_lp_profiles/`
2. Register packs and conversion path.
   - Edit pack catalog: `apps/gui/src/language_packs_catalog.py`
   - Add downloader/build hooks, if needed: `apps/gui/src/language_packs.py`
   - Record source URLs/notes: `docs/language_pairs/language_pack_urls.txt`
   - Record source acquisition policy: `docs/language_pairs/data_source_licensing_and_distribution.md`
   - If the license permits user-initiated app download/build, make the pack
     auto-downloadable instead of leaving it as manual-supply.
   - Add/verify converter scripts: `scripts/data/` (for example `convert_*_to_sqlite.py`)
3. Implement rulegen support for LP.
   - Register adapter mode: `core/lexishift_core/rulegen/adapters.py`
   - Add pair pipeline: `core/lexishift_core/rulegen/pairs/<pair>.py`
   - Add shared morphology/normalization helpers if needed: `core/lexishift_core/rulegen/utils.py`
   - Add dictionary loader updates for new formats: `core/lexishift_core/resources/dict_loaders.py`
4. Ensure SRS init/refresh assumptions are LP-safe.
   - Seed/frequency behavior: `core/lexishift_core/srs/seed.py`
   - POS normalization + bucket mapping behavior: `core/lexishift_core/srs/admission_policy.py`
   - Frequency column fallback behavior: `core/lexishift_core/frequency/providers.py`
   - Rulegen publish orchestration: `core/lexishift_core/helper/rulegen.py`
   - Topic-aware admission evidence: run/source a pair-local topic coverage
     audit before claiming profile-personalized admission parity. Use
     `docs/srs/srs_topic_signal_lp_generalization_runbook.md`; SRS smoke alone
     is not enough because it may pass with no meaningful topic inventory.
5. Wire GUI + extension pair plumbing.
   - GUI selectable pairs: `apps/gui/src/dialogs.py`
   - GUI pack->pair routing: `apps/gui/src/main.py` (`_pair_for_pack`)
   - Options action bindings: `apps/chrome-extension/options/controllers/page/events/srs_bindings.js`
   - Options helper workflows: `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
   - Runtime rendering for metadata-driven display (if needed): `apps/chrome-extension/content/processing/replacements.js`
6. Add targeted tests before merge.
   - Capability/resource tests: `core/tests/helper/test_lp_capabilities.py`, `core/tests/helper/test_helper_engine.py`, `core/tests/helper/test_helper_daemon.py`
   - Rulegen adapter tests: `core/tests/rulegen/test_rulegen_adapters.py`, `core/tests/helper/test_helper_rulegen.py`
   - Persistence/schema tests (if metadata changes): `core/tests/persistence/test_storage.py`
7. Update docs and rollout status.
   - LP requirements matrix: `docs/language_pairs/lp_resource_requirements.md`
   - Extension LP checklist status: `docs/language_pairs/extension_lp_generalization_checklist.md`
   - SRS roadmap snapshot: `docs/srs/srs_roadmap.md`
   - Changelog: `CHANGELOG.md`

## LP Definition

- [ ] LP key is defined as `source-target` (directional), for example `en-de`.
- [ ] LP direction policy is explicitly decided and documented:
  - [ ] Directional (`en-de` is distinct from `de-en`), or
  - [ ] Canonicalized (multiple directions normalized to one key).
- [ ] LP is added/verified in glossary terminology (`LP = Language Pair`).

## 1) Planning And Source Selection

- [ ] Target use-case is identified:
  - [ ] Monolingual synonym LP (for example `de-de`), or
  - [ ] Cross-lingual translation LP (for example `en-de`).
- [ ] Dictionary sources selected:
  - [ ] Primary source
  - [ ] Secondary source (optional)
- [ ] Frequency source selected for SRS bootstrap/growth.
- [ ] Required files and formats are documented (CSV/TSV/XML/SQLite/etc).
- [ ] Licensing and redistribution constraints are confirmed.
- [ ] Licensing/distribution status is reviewed in:
  - `docs/language_pairs/data_source_licensing_and_distribution.md`
- [ ] Product source-acquisition mode is explicit:
  - [ ] `auto-download` for sources whose license allows app-managed user-local
        download/build with required notices, or
  - [ ] `manual-supply` for proprietary/unresolved sources.
- [ ] Hosted/bundled redistribution of converted artifacts is considered
      separately from source auto-download.
- [ ] Source stack roles are registered:
  - [ ] target frequency
  - [ ] forward translation
  - [ ] reverse-check translation when needed
  - [ ] optional overlays/enrichment, such as POS/topic/monolingual sources

## 2) Pack Registration And Validation

- [ ] Dictionary pack(s) are registered in `apps/gui/src/language_packs_catalog.py`.
- [ ] Source-stack setup resources render in Settings -> Language Packs ->
      Learning Languages.
- [ ] Non-blocking enrichment packs are marked optional/recommended so they do
      not make pair readiness fail.
- [ ] Required extracted files are declared (`required_files`) where applicable.
- [ ] Download/extract/link validation works from Settings -> App.
- [ ] Frequency pack is registered if SRS bootstrap depends on it.
- [ ] Raw POS tag inventory is documented for the LP sources (frequency and/or dictionary).
- [ ] Source provider IDs needed by POS normalization are identified and recorded.
- [ ] Converter/build metadata includes unknown POS inventory counters and they are reviewed before LP enablement.
- [ ] POS inventory audit is run and archived:
  - `scripts/testing/pos_inventory_audit.py`
  - `docs/test_outputs/phase6_pos_inventory/`
- [ ] Optional embedding packs are mapped to the LP if ranking is required.
- [ ] Converter script exists for non-native formats and is documented in:
  - `scripts/data/`
  - `docs/language_pairs/language_pack_urls.txt`

## 3) Pair Plumbing Across Surfaces

- [ ] GUI SRS pair controls include LP in `apps/gui/src/dialogs.py`.
- [ ] Bulk synonym pack-to-pair mapping handles LP in `apps/gui/src/main.py` (`_pair_for_pack`).
- [ ] Extension language-prefs path resolves LP correctly from source/target.
- [ ] No unintended pair collapsing occurs unless explicitly intended.
- [ ] Profile-scoped pair settings persist and reload correctly.
- [ ] Helper capability + pair resource resolution matches GUI/extension pair expectations:
  - `core/lexishift_core/helper/lp_capabilities.py`
  - `core/lexishift_core/helper/pair_resources.py`

## 4) Rule Generation Implementation

- [ ] Rulegen path exists for LP (not placeholder/empty output).
- [ ] LP-specific source loader/pipeline is implemented in core rulegen modules.
- [ ] Generated rules carry `metadata.language_pair = <LP>`.
- [ ] Confidence/scoring behavior is defined (threshold, ranking, filters).
- [ ] Ambiguity/noise filters are applied (stopwords, punctuation, variant filtering as needed).
- [ ] Adapter registration and pair mode routing are wired:
  - `core/lexishift_core/rulegen/adapters.py`
  - `core/lexishift_core/helper/lp_capabilities.py` (`rulegen_mode`)
- [ ] If LP needs morphology-aware rendering, metadata contract is implemented and persisted:
  - generation: `core/lexishift_core/rulegen/generation.py`
  - variant expansion: `core/lexishift_core/rulegen/utils.py`
  - persistence: `core/lexishift_core/persistence/storage.py`

## 5) SRS Initialize And Refresh Support

- [ ] `srs_initialize` works for LP without unrelated hard dependencies.
- [ ] `srs_refresh` works for LP and can publish updated ruleset/snapshot.
- [ ] Pair-specific source defaults are configured in native-host command handling.
- [ ] Stopwords path resolution works for LP target language (if applicable).
- [ ] Pair-level planning path (`srs_plan_set`) returns executable plan where expected.
- [ ] Seed/frequency assumptions are validated for LP frequency DB schema:
  - `core/lexishift_core/srs/seed.py`
  - `core/lexishift_core/frequency/providers.py`
- [ ] POS assumptions are validated for LP raw tags and bucket outcomes:
  - `core/lexishift_core/srs/admission_policy.py`
  - `docs/rulegen/pos_normalization_workstream.md`

## 6) Runtime Integration

- [ ] Helper runtime diagnostics report LP paths/counts correctly.
- [ ] Extension runtime fetches and applies helper ruleset for LP.
- [ ] Gate/scheduler uses LP-scoped items only (no cross-pair leakage).
- [ ] Feedback/exposure events persist with correct LP key.
- [ ] Runtime display behavior matches metadata contract (if used):
  - `apps/chrome-extension/content/processing/replacements.js`
  - `docs/reference/schema.md`

## 7) Background Automation (If Used)

- [ ] Helper daemon supports LP in its supported-pairs registry.
- [ ] Scheduled jobs have LP-appropriate input sources and defaults.
- [ ] Status reporting (`last_pair`, target/rule counts) reflects LP runs.

## 8) Testing Checklist

- [ ] Unit tests:
  - [ ] pack-to-pair mapping
  - [ ] source loader/parser for LP dictionaries
  - [ ] rulegen outputs for LP
- [ ] Integration tests:
  - [ ] initialize -> ruleset/snapshot published
  - [ ] feedback -> refresh admission behavior
  - [ ] diagnostics non-zero counts for LP after publish
- [ ] Runtime tests:
  - [ ] extension consumes LP rules
  - [ ] LP-specific gate behavior validated

## 9) Documentation Checklist

- [ ] Update `docs/language_pairs/dictionary_matrix_checklist.md` LP capability rows.
- [ ] Update README support matrix and known limitations.
- [ ] Update technical notes for pair mapping and rulegen behavior.
- [ ] Record migration notes if LP direction policy changed.

## 10) Definition Of Done (LP)

- [ ] LP can be selected in UI and persisted per profile.
- [ ] LP initialize path succeeds and publishes non-empty ruleset for valid inputs.
- [ ] LP refresh path can admit items and republish runtime artifacts.
- [ ] Runtime diagnostics show non-zero pair counts after initialization.
- [ ] Test suite includes LP coverage and passes.
- [ ] Documentation reflects LP as implemented (or explicitly partial).

## LP Rollout Record (Fill Per LP)

LP key: `________`

Owner: `________`

Date: `________`

Direction policy: `Directional | Canonicalized`

Primary dictionaries: `________`

Frequency source: `________`

Status: `Not started | In progress | Implemented | Partial`

Notes:
- `________`
