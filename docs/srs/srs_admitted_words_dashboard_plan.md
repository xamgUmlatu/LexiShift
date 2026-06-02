# SRS Admitted Words Dashboard Plan

Status: active implementation contract
Role: Product/UX decision, implementation contract, and verification runbook
Last updated: 2026-06-02
Last verified: 2026-05-27 helper/options dashboard tests, profile-bootstrap
initialize -> rule publication -> dashboard bridge test, local search/filter/
sort/pagination/meta-control tests, published-rule summary/detail tests, durable
discard workflow tests, encounter-watch summary tests, SRS quality harness, and
local changed-file gate; 2026-05-27 SRS quality harness now includes an
encounter-watch scenario covering fresh unseen, stale unseen, legacy age-unknown,
reviewed, and no-enabled-rule active items; 2026-06-02 Vocabulary Library and
shared word-info route documented with no runtime behavior change; 2026-06-02
learner-facing dashboard wording changed `queued` rows to `Upcoming`, page
serving copy to `Page replacement`, removed raw ids from normal advanced view,
and made row details open from the row rather than a separate view action
Purpose: document the user-facing SRS admitted-words dashboard decision, the
current dashboard lifecycle action contract, module/data boundaries, and
deferred lifecycle actions
Source-of-truth: product decision and UI contract live here; executable truth
lives in helper endpoints, options-page code, tests, and
`docs/developer/feature_state_matrix.md`.

## Decision

The admitted-words viewer is a user-facing learning dashboard, not a developer
diagnostic panel.

It should answer four learner questions without requiring debug knowledge:

- what words are currently in my SRS path for this profile and language pair?
- which of those words are active, due, upcoming, or removed?
- which words can currently appear as page replacements?
- how can I remove one specific word that I do not want in my SRS path?

Default view should show useful learner concepts:

- total admitted words for the selected profile/pair;
- active words;
- due now and due soon words;
- words currently eligible for page replacement (`active` plus due/no due date
  plus at least one enabled published rule);
- upcoming admitted words that are not currently active;
- active words that are still unseen and have no review feedback;
- removed words, including discarded or cleared items;
- per-word display text, due status, review count, exposure count, and source
  label;
- per-word published rule count and a compact source-phrase preview, when a
  current helper-published ruleset exists;
- on-demand published rule details for a selected word, capped to keep the
  normal dashboard payload small;
- local search, status filtering, sort, page-size, pagination, and clear-filter
  controls for already-loaded words;
- dashboard refresh metadata showing last refresh time, loaded/viewed counts,
  active-inventory source, and current published-ruleset availability.

Technical details belong behind an Advanced details toggle:

- item id;
- lifecycle state/reason/update timestamp;
- scheduler state and step;
- confidence, stability, and difficulty;
- normalized word-package details when needed later.

The dashboard is not the SRS review UI, not a rulegen debugger, and not the
primary admission-control surface. Preferences, proficiency, refresh admission,
and review feedback remain separate workflows.

Dedicated Vocabulary Library expansion, learner-facing definitions/glosses, and
the built-in browser popup definition module are now routed through
`docs/srs/srs_vocabulary_library_and_word_info_plan.md`. This dashboard plan
remains the contract for the current embedded admitted-words dashboard and its
existing helper read models.

## User Surface

The options page exposes the dashboard in the SRS settings area for the selected
profile and language pair.

Top-level controls:

- `Open full library`: opens the dedicated selected-pair Vocabulary Library page.
- `Refresh words`: loads a fresh pair/profile payload from the helper.
- `Advanced details`: toggles technical per-row fields.
- `Search`: filters the loaded payload by display, lemma, reading, status,
  source, or rule source phrase.
- `Status`: filters to all, active, due, upcoming, or removed words.
- `Sort`: keeps source order by default, with due-first, word, review-count,
  and exposure-count alternatives.
- `Rows`: selects page size for local pagination.
- `Clear filters`: resets search/status/sort to defaults and returns to page 1.

Summary cards:

- `Active`
- `Due now`
- `Due soon`
- `Upcoming`
- `Unseen`
- `Removed`
- `Total`

Metadata row:

- `Last refreshed`: timestamp from the latest helper refresh result, not from
  local filter or pagination renders.
- `Loaded`: total words in the currently loaded helper payload.
- `Viewing`: words after local search/status/sort filtering.
- `Page replacement`: words that can currently appear as page replacements.
- `Encounter watch`: active words that may need observation because they have
  zero exposure and zero feedback, because they crossed the diagnostic age
  threshold while still unseen, or because no enabled published rule exists.
- `Inventory`: active-inventory source reported by the helper.
- `Ruleset`: published-ruleset state, including rule count when available.

Rows:

- show target display text and reading when distinct;
- show dashboard status using learner-facing labels;
- show due timing, current page-replacement eligibility, review count, exposure
  count, rule count, and source label;
- show a compact watch note when an active row has zero exposure plus zero
  feedback, crosses the diagnostic age threshold, has unknown admission age, or
  has no enabled published rules;
- show compact `Matches: ...` source phrases when published-rule summaries are
  available;
- open read-only rule details from the row when the row has helper-published
  rules;
- expose `Discard` only for eligible non-removed words.

Advanced row details:

- practice state and page-replacement explanation;
- scheduler state and step;
- confidence, stability, and difficulty.

Raw item ids are developer diagnostics, not part of the normal advanced learner
view.

## Lifecycle UX Policy

The SRS feedback popup remains a review-feedback surface. It should not grow
regular cooldown controls.

Current product direction:

- known words should normally move forward through SRS feedback such as `easy`;
- if a learner dislikes a specific word, the dashboard can durably discard it
  and block it from refresh admission;
- discard should be rare and explicit, not a routine temporary cooldown flow;
- deleting an SRS story clears discard/block suppression metadata by default,
  matching a fresh start for that profile/language pair;
- a later delete confirmation may offer "keep discarded words" by using the
  existing backend `preserve_lifecycle_metadata` flag.

## Current Implementation Contract

Source files:

- `apps/chrome-extension/options.html` owns the dashboard DOM surface.
- `apps/chrome-extension/options.css` owns dashboard layout, filterbar, summary,
  metadata, pagination, row, advanced-detail, rule-detail, and action styling.
- `apps/chrome-extension/options/core/ui_manager.js` registers DOM ids.
- `apps/chrome-extension/options/core/bootstrap/controller_graph_elements.js`
  passes dashboard elements into the controller graph.
- `apps/chrome-extension/options/controllers/srs/actions_controller.js` and
  `apps/chrome-extension/options/controllers/srs/actions/workflows.js` forward
  dashboard dependencies into SRS maintenance workflows.
- `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_model.js`
  owns local search/filter/sort semantics.
- `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_formatting.js`
  owns learner-facing dashboard labels, small status formatters, and pagination
  math shared by the renderer.
- `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_renderer.js`
  renders summary cards, metadata, rows, pagination, advanced fields, and
  actions.
- `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_rule_details.js`
  renders the on-demand rule detail panel.
- `apps/chrome-extension/options/controllers/srs/actions/words_dashboard_workflow.js`
  owns refresh, pagination state, local control wiring, rule-detail loading, and
  confirmed discard.
- `core/lexishift_core/helper/use_cases/srs_items.py` owns helper read models
  for list and rule-detail payloads.

Read/listing path:

- helper/native-host exposes `srs_items_list`;
- the endpoint is pair/profile scoped and read-only;
- the endpoint reads `srs_store.json` and `srs_inventory.json`;
- the endpoint also reads the current helper-published `srs_ruleset_<pair>.json`
  and attaches compact per-lemma rule summaries;
- active membership uses the existing active-inventory resolver, including
  store fallback when no pair inventory exists;
- non-active lifecycle states are visible in the dashboard but remain ineligible
  for active page replacement elsewhere;
- options.html exposes a Learning words dashboard with Refresh words, local
  search, status filter, sort controls, page-size controls, pagination, clear
  filters, refresh metadata, and an Advanced details toggle.
- search/filter/sort/pagination operate only on the already-loaded dashboard
  payload; they do not call the helper, mutate SRS state, or change serving/
  admission order.
- changing search, status, sort, page size, or clearing filters resets the
  dashboard to page 1.
- the Clear filters control is disabled until search/status/sort are adjusted;
  Escape in the search box clears the current search and returns to page 1.
- the Last refreshed value is anchored to the helper refresh result; local
  search, filter, sort, and pagination renders do not change that timestamp.
- rule summaries are display-only: rule count plus a capped source-phrase
  preview.
- rule details are also read-only and loaded on demand through
  `srs_item_rule_details` for the selected row only.

Payload contract:

- top-level payload includes `status`, `pair`, `profile_id`, store/inventory/
  ruleset paths and existence flags, `inventory_source`, `rule_summary`,
  `summary`, and `items`;
- `summary` includes `active`, `due_now`, `due_soon`, `queued`, `removed`, and
  `total`, current replacement counters `serving_now`, `serving_not_due`, and
  `serving_without_enabled_rules`, plus encounter-watch counters:
  `active_zero_exposure`, `active_zero_feedback`,
  `active_zero_exposure_zero_feedback`,
  `active_zero_exposure_zero_feedback_age_unknown`,
  `active_stale_zero_exposure_zero_feedback`,
  `active_without_enabled_rules`, `encounter_watch`, and
  `encounter_stale_age_days`;
- each item includes `item_id`, `lemma`, `display`, `reading`, `pair`, `active`,
  `status`, `status_label`, admitted timestamp/age, due/review/exposure fields,
  current replacement fields `serving`, `serving_state`, and `serving_label`,
  source fields, `pos`, `rule_summary`, `encounter_state`, and `advanced`;
- the payload status key `queued` remains the stable machine state for admitted
  rows outside active inventory, while the learner-facing label is `Upcoming`;
- item `rule_summary` includes enabled rule count and capped source-phrase
  preview;
- top-level `rule_summary` describes the current published ruleset as a whole;
- the options workflow adds `dashboard_refreshed_at` when it receives a helper
  result so local renders can preserve a stable refresh timestamp.
- page-replacement eligibility is a read-only dashboard projection of the runtime
  gate's first-order conditions: the row must be active, due now or missing a
  due date, and backed by at least one enabled helper-published rule. The
  dashboard does not itself decide replacements.

The listing endpoint should not:

- mutate SRS items;
- write lifecycle states;
- admit new words;
- change due scheduling;
- publish rulegen outputs.

Rule summary path:

- reads the full published ruleset artifact, not the capped diagnostic snapshot;
- groups enabled rules by canonical target lemma (`replacement`);
- reports `Rules: N` and a capped `Matches: ...` preview on each dashboard row;
- tolerates a missing or unreadable ruleset by showing zero rule summaries while
  preserving the SRS item list.

Rule detail path:

- helper/native-host exposes `srs_item_rule_details`;
- the endpoint is pair/profile/lemma scoped and read-only;
- it exact-matches the canonical target lemma against published rule
  `replacement`;
- it returns enabled and disabled rule counts plus capped rule rows, sorted with
  enabled and higher-priority rows first;
- it returns compact rule metadata only. Full semantic-admission inspection,
  morphology variants, and rulegen debug internals remain deferred.

Discard path:

- dashboard rows for eligible active/upcoming/due words expose a small Discard
  action;
- the action confirms before mutation;
- the action calls the existing `srs_admission_suppress` helper/native-host
  route with `reason=user_blocked`;
- the helper writes durable suppression metadata, marks an existing matching
  SRS item `discarded`, and removes it from active inventory;
- the dashboard refreshes after discard so the word appears as removed/
  discarded.

## Interaction Semantics

Local controls never change the helper or SRS store:

- search, status filter, sort, page size, and pagination operate on
  `latestWordsDashboardData`;
- changing search/status/sort/page size resets page index to 0;
- search input updates immediately;
- Escape clears search and resets to page 1;
- Clear filters is disabled until search/status/sort differ from defaults;
- Clear filters does not change page size;
- page buttons clamp to the available page range after filtering;
- rule-detail expansion reuses cached detail payloads until the next refresh;
- refresh clears expanded/loading rule-detail state and resets pagination;
- discard refreshes the dashboard after the helper mutation succeeds.

Search fields:

- `display`
- `lemma`
- `reading`
- `status_label`
- `status`
- `source_label`
- `source_type`
- published-rule source phrases

Status filter semantics:

- `all`: every row in the loaded payload;
- `active`: rows that are neither queued nor removed;
- `due`: `due_now` or `due_soon`;
- `queued`: `queued` machine state, shown to learners as `Upcoming`;
- `removed`: `discarded`, `cleared`, or `removed`.

Sort semantics:

- `source`: helper payload order;
- `due`: earliest due first, then upcoming, then removed;
- `word`: display/lemma/reading alphabetically;
- `reviews`: highest review count first;
- `seen`: highest exposure count first.

## Safety Invariants

This dashboard is intentionally small in authority.

- Listing and rule-detail routes are read-only.
- Local controls do not admit, schedule, publish, discard, clear, restore, or
  release words.
- Rule summaries and details read the helper-published ruleset; they do not run
  rulegen.
- Missing or unreadable published rulesets should degrade to zero summaries or a
  rule-detail warning without blocking SRS item visibility.
- Discard is the only current dashboard mutation, and it must stay explicit,
  confirmed, pair/profile scoped, and routed through `srs_admission_suppress`.
- Discard means durable learner block until the story is deleted/reset, not a
  cooldown.
- Removed words remain visible so learners can understand state after discard.
- Automatic refresh may park mature review words out of active inventory when
  the active-size target is full, but the dashboard does not directly clear,
  restore, release, or mark words mastered.
- Restore, mastered/released lifecycle UX, and undo policies remain planned, not
  implicit.

## Verification

Focused implementation tests:

```bash
python3 -m pytest \
  core/tests/dev/test_extension_srs_maintenance_workflow_contract.py \
  core/tests/dev/test_extension_helper_status_profile_contract.py \
  core/tests/dev/test_helper_browsing_admission_entrypoints.py \
  core/tests/helper/test_helper_srs_items.py \
  core/tests/helper/test_helper_admission_suppression.py
```

Required SRS quality harness for SRS dashboard/helper lifecycle changes:

```bash
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json

python3 scripts/testing/srs_quality_summary.py \
  --quality-json docs/test_outputs/srs_quality_latest.json \
  --markdown-out docs/test_outputs/srs_quality_summary_latest.md
```

Repository gates used for the latest dashboard control slice:

```bash
npm --prefix scripts run check:state
python3 scripts/dev/check_doc_references.py
git diff --check
npm --prefix scripts run check:changed:local
```

Current covered behaviors:

- helper list payload shape, summaries, active/upcoming/due/removed status, and
  published-rule summaries plus current replacement eligibility;
- `admitted_at` persistence for newly admitted items, legacy age-unknown
  handling, and encounter-watch summary counters/options rendering for active
  words with zero exposure plus zero feedback; the SRS quality harness now
  verifies the same fresh/stale/legacy/reviewed/no-rule diagnostic states;
- profile-bootstrap initialization can publish active rule outputs and then
  surface the admitted words through the dashboard read model;
- helper rule-detail payload shape and capped rule rows;
- native-host/helper-manager route plumbing;
- options dashboard refresh, search, status filter, sort, page-size,
  pagination, refresh metadata, Escape search clearing, and clear-filter
  disabled state;
- on-demand rule-detail loading and cached expansion;
- confirmed discard through the suppression route;
- SRS quality harness for supported synthetic pairs, including the
  encounter-watch diagnostic scenario.

## Deferred Work

Next product slices, after dashboard pagination and discard are stable:

1. Virtualized rendering if admitted sets become too large for page-sized local
   rendering.
2. Rich learner-facing word inspection and definitions should follow
   `docs/srs/srs_vocabulary_library_and_word_info_plan.md`; deeper rulegen debug
   metadata remains a separate advanced/dev-facing concern.
3. Optional word-context discard affordance: likely a right-click word popup
   with a discrete three-dots control. This is deferred until the dashboard
   discard path and SRS testing path are stable.
4. A confirmed restore/undo policy if discarded items should ever return.
5. Full mastered/released lifecycle semantics and restore UX, separate from the
   backend active-inventory parking used by refresh capacity.

## Release Boundary

The dashboard is acceptable for MVP when:

- the read-only endpoint and options UI are covered by focused tests;
- dashboard search/filter/sort are covered by focused workflow tests and remain
  local to the loaded payload;
- dashboard pagination/page-size controls are covered by focused workflow tests
  and remain local to the loaded payload;
- refresh metadata, clear-filter disabled state, and search Escape handling are
  covered by focused workflow tests;
- encounter-watch counters include age-aware stale-unseen visibility and are
  visible enough for tester review without implying automatic stale-clear or
  release behavior;
- the dashboard shows which loaded words can currently replace text, while
  automatic refresh remains responsible for active-inventory parking and new
  admission;
- published-rule summaries are covered by focused helper/options tests and
  remain read-only;
- on-demand rule details are covered by focused helper/options tests and remain
  read-only/capped;
- dashboard discard is covered by focused workflow tests and uses the existing
  suppression route;
- SRS quality harness still passes after the helper route lands and continues
  to surface encounter-watch counts in its JSON/Markdown artifacts;
- the feature-state matrix records dashboard discard separately from
  restore/mastery/release controls;
- docs do not claim restore/mastery UX is shipped.
