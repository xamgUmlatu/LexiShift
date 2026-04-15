# SRS Preference Update And Inventory Rebalance Policy

Status: partially implemented
Role: Policy + implementation boundary
Purpose: define the non-destructive policy for user-preference updates, active inventory rebalance, protected-item retention, and the options UX, while recording the current implemented v1 boundary.
Last updated: 2026-04-12
Last verified: 2026-04-12 targeted rebalance/helper/planner tests plus synthetic SRS quality harness
Verification:
- `core/lexishift_core/srs/rebalance.py`
- `core/lexishift_core/srs/store.py`
- `core/lexishift_core/srs/scheduler.py`
- `core/lexishift_core/srs/sampling.py`
- `core/lexishift_core/helper/use_cases/rebalance_set.py`
- `core/tests/srs/test_srs_rebalance.py`
- `core/tests/helper/test_helper_engine.py`
- `docs/test_outputs/srs_quality_latest.json`
- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_profile_schema.md`
- `apps/chrome-extension/options.html`
- `apps/chrome-extension/options/controllers/srs/actions/workflows.js`
- `apps/chrome-extension/options/controllers/srs/actions/formatters.js`

Related design:
- `docs/srs/srs_set_planning_technical.md`
- `docs/srs/srs_preference_signal_admission_design.md`
- `docs/srs/srs_preference_signal_admission_v1_contract.md`
- `docs/srs/srs_profile_schema.md`
- `docs/srs/srs_roadmap.md`
- `docs/developer/language_difficulty_and_proficiency_model.md`

## Goal

When a user changes preferences, LexiShift should:

1. update future admission behavior immediately,
2. avoid deleting learned history,
3. optionally rebalance the current pair-local study inventory when the user explicitly asks for it,
4. keep destructive reset separate and explicit.

This doc is the policy for that behavior.

## Implemented v1 scope

Implemented now:

- manual rebalance preview and apply helper APIs
- pair-local active inventory mutation through `srs_inventory.json`
- explicit protected/swappable partitioning for current active items
- non-destructive parking of retained history
- options buttons for preview and apply
- confirmation messaging with protected/park/activate counts

Still not implemented:

- automatic rebalance on preference edit
- general continuous `profile_growth`
- empirical-trend-driven `adaptive_refresh`
- a formal long-term lifecycle label such as `mastered`

## Current verified constraints

Current code already provides these facts:

- profile preference signals are stored separately from SRS progress
  - extension path: `srsProfiles.<profile_id>.srsSignalsByPair.<pair>`
- the admitted-word sample preview is non-mutating
  - it previews what would be admitted under current preferences
- the sampled rulegen button is downstream of the persisted pair-local SRS store
  - it now reads the explicit pair-local active inventory manifest when present, then samples from the corresponding retained item records
- SRS item records already contain useful learning evidence
  - `history`
  - `stability`
  - `difficulty`
  - `next_due`
  - `scheduler_state`
  - `exposures`
- there is no explicit stored label today for:
  - `mastered`
  - `parked`
  - `protected`
- pair-local active inventory membership now has an explicit persisted seam in `srs_inventory.json`
  - `srs_store.json` remains the retained learning-history store
- current runtime “active” selection is due-based
  - due items are derived at runtime from scheduler state
- current sampled rulegen and helper-side publication now use the explicit active-inventory manifest when it exists
  - if no manifest exists yet for a pair, the helper falls back to current store membership for compatibility

## Policy decisions

These are the intended product and architecture rules.

### 1. Preference updates are non-destructive by default

Changing:

- topic interests
- proficiency estimate
- challenge target
- later onboarding/placement outputs

must not wipe pair-local SRS data automatically.

The immediate effect of a preference change is:

- future `profile_bootstrap` preview changes,
- future initialization/admission decisions change,
- later growth/refresh logic should use the new weights.

The immediate effect is not:

- deleting current SRS items,
- deleting scheduler history,
- deleting learned words,
- resetting the pair.

### 2. Rebalance is manual and pair-local

If the user wants current inventory to reflect new preferences more aggressively, that must be a separate manual action.

That action is:

- pair-local,
- previewable before mutation,
- non-destructive to retained history,
- constrained by an explicit protection policy.

It must not run automatically on every preference edit.

### 3. Learned items are protected

Preference changes do not mean prior learning was invalid.

Any item with meaningful learning evidence should be protected from rebalance removal, even if it no longer matches the new preference profile strongly.

This includes the practical case the user described:

- words that have been learned enough that they no longer appear often because their due dates are far away.

Even without a formal `mastered` label, those items already leave evidence in scheduler state and should remain protected.

### 4. Reset remains separately destructive

“Start over” is a different user intent from “update preferences.”

The existing reset path should remain the only destructive button in this workstream.

Rebalance must not be a disguised reset.

## Final architecture

The clean final architecture separates three concerns:

1. profile signals
2. per-item learning records
3. current admitted inventory membership

### Profile signals

Profile signals remain in extension/profile context storage and feed planning:

- `interests`
- `proficiency`
- `difficulty_preferences`
- later onboarding/placement outputs

### Per-item learning records

Per-item history remains in the helper-owned SRS store:

- item identity
- pair
- scheduling state
- review history
- stability/difficulty
- exposures

This record is the long-lived learning memory.

### Active inventory membership

Current admitted set `S` should become an explicit helper-owned membership manifest rather than being inferred only from pair membership in `srs_store.json`.

Current helper file:

- `srs/profiles/<profile_id>/srs_inventory.json`

Proposed shape:

```json
{
  "version": 1,
  "pairs": {
    "en-en": {
      "active_item_ids": [
        "en-en:money",
        "en-en:man"
      ],
      "last_initialized_at": "2026-04-12T00:00:00+00:00",
      "last_rebalanced_at": "2026-04-12T00:00:00+00:00"
    }
  }
}
```

This is the preferred final architecture because:

- learning history remains in one place,
- active inventory membership is explicit,
- parked items can retain history without contaminating current rulegen/sampling,
- rebalance can mutate inventory membership without deleting item records.

This is better than adding an ad hoc deletion rule, and better than silently overloading current pair membership forever.

## Inventory semantics

For planning and UX purposes, each pair-local item falls into one of these conceptual buckets:

- retained record
  - exists in the SRS store
- active inventory member
  - included in current set `S` for that pair
- parked record
  - retained in history but not currently part of active inventory
- due-active item
  - active inventory member and currently due/eligible at runtime

Important distinction:

- active inventory membership is not the same thing as due state
- due state is scheduler-derived
- inventory membership is planner/admission-derived

That distinction is required for non-destructive rebalance.

## Protection policy

Protection is planner-calculated, not a hand-edited label.

The first implementation should use an explicit, logged heuristic.

### Protected item heuristic (v1 implemented)

An active item is protected from rebalance removal if any of the following are true:

1. `history_count >= 4`
2. `stability >= 14`
3. `scheduler_state == "review"` and `next_due >= now + 7 days`

Definitions:

- `history_count` means number of recorded review events
- `stability` uses the existing scheduler field
- `next_due` means the stored due timestamp if present

Rationale:

- the thresholds are conservative enough to keep genuinely learned items,
- they are explicit and testable,
- they rely only on fields that already exist,
- they avoid inventing a fake “mastered” label before the lifecycle schema is ready.

### Swappable item heuristic (v1 implemented)

An active item is swappable if it is not protected.

Typical swappable items are:

- newly admitted items,
- items with very short review history,
- low-stability items,
- items still effectively in early learning.

### Required diagnostics

Every rebalance preview/apply must expose:

- protected count
- swappable count
- the exact rule that protected each protected item
- the exact rule that marked each swappable item eligible

No hidden thresholds.

## Rebalance policy

### Core rule

Rebalance modifies active inventory membership, not learning history.

It should:

- keep protected items active,
- allow swappable items to leave the active inventory,
- admit better preference-matching replacements,
- preserve parked item history,
- preserve protected item history,
- never erase retained records as a side effect.

### Pair-local budget rule

Rebalance is pair-local and constrained by the pair’s effective active budget:

- default source: `max_active_items`
- if there is already an explicit pair-local active inventory size, that size may be used as the target ceiling

Protected items reserve capacity first.

Remaining slots are filled by the best-ranked candidates under the current preference profile.

### Candidate source rule

Rebalance candidates can come from:

1. currently active swappable items
2. parked retained items for the same pair
3. newly generated candidate lemmas from the neutral seed pool reranked by current profile context

Preference order:

1. keep protected active items
2. reactivate previously retained items when they now fit well
3. admit genuinely new items as needed

This keeps history reuse stronger than churn.

## Planner contract

Rebalance should have a preview-first contract.

### Helper APIs

- `srs_rebalance_plan`
- `srs_rebalance_apply`

### `srs_rebalance_plan` input

- `pair`
- `profile_id`
- current `profile_context`
- active-budget inputs if override is needed
- trigger metadata

### `srs_rebalance_plan` output

Minimum payload:

```json
{
  "pair": "en-en",
  "profile_id": "suisui",
  "plan": {
    "strategy_requested": "profile_growth",
    "strategy_effective": "profile_growth",
    "objective": "rebalance",
    "can_execute": true,
    "execution_mode": "rebalance_preview",
    "notes": []
  },
  "summary": {
    "active_count_before": 40,
    "protected_count": 18,
    "swappable_count": 22,
    "candidate_slots_available": 22,
    "proposed_keep_count": 18,
    "proposed_park_count": 12,
    "proposed_activate_count": 12,
    "active_count_after": 40
  },
  "protected_items": [],
  "swappable_items": [],
  "proposed_parks": [],
  "proposed_activations": [],
  "diagnostics": {}
}
```

### `srs_rebalance_apply` semantics

Apply should:

- update inventory membership only,
- preserve item history in the store,
- be idempotent for the same plan,
- return the realized mutations and resulting counts.

It should not:

- delete protected items,
- delete parked retained history,
- run an implicit full reset.

## Relationship to existing planner strategies

This should live under the set planner, not as a UI-only special case.

Recommended taxonomy:

- strategy: `profile_growth`
- objective: `rebalance`

Reason:

- the action is profile-conditioned,
- it is not initial bootstrap,
- it is not pure feedback refresh,
- it is still fundamentally an inventory-admission mutation.

`adaptive_refresh` should remain the feedback/trend-driven path.

Manual preference rebalance is a different intent and should not be hidden inside refresh.

## Testability requirements

This design is worth planning now because it improves testability.

Required tests for the current implementation:

1. Preference edit is non-destructive.
   - editing profile signals changes preview/plan results
   - store history remains unchanged

2. Pair isolation.
   - `en-en` rebalance does not mutate `en-es`

3. Protected item preservation.
   - any protected item remains active after apply

4. Swappable-only replacement.
   - only non-protected active items can leave inventory

5. History retention.
   - parked items retain `history`, `stability`, `difficulty`, and due state

6. Rulegen/sampling isolation.
   - sampled rulegen and active-inventory rule publication exclude parked items

7. Idempotence.
   - repeated apply with unchanged context produces no extra churn

8. Preview/apply agreement.
   - apply result matches prior preview plan except for explicitly logged races or missing resources

## UX policy

This section defines the intended options UX for this workstream.

### Use case 1: “I changed preferences and want future admissions to reflect that.”

UX:

- user edits preference inputs
- settings auto-save on change
- no confirmation
- no mutation of current inventory

Result:

- admitted-word sample preview changes immediately
- future initialization/growth/rebalance uses the new profile context

### Use case 2: “I want to see what the current preferences would admit.”

Button:

- `Generate admitted words sample (5)…`

Behavior:

- non-mutating
- no confirmation
- shows:
  - active signals
  - normalized profile context
  - sample admitted items
  - rerank explanations

### Use case 3: “This pair has no inventory yet; initialize it from current preferences.”

Button:

- `Initialize S for this pair`

Behavior:

- mutating
- should initialize the pair-local active inventory
- no confirmation when the pair has no existing inventory

Planned UX note:

- once rebalance exists, this button should primarily be the empty-pair path
- if the pair already has active inventory, the UI should steer users toward preview/rebalance instead of silently acting like a reset

### Use case 4: “I want the current pair inventory to better match my new preferences.”

Buttons:

- `Preview rebalance to current preferences`
- `Apply rebalance…`

Behavior:

- manual
- pair-local
- preview-first
- non-destructive to retained history
- protected items remain active
- swappable items may be parked
- new or retained better-fit items may be activated

Confirmation policy:

- preview is non-mutating
- apply is a separate explicit button
- apply requires confirmation

Current confirmation message:

- `Rebalance the active SRS set for {pair} using current preferences?`
- `{keep_count} protected words will stay active, {park_count} low-commitment words will leave the active set, and {activate_count} words will be activated. Review history will be preserved.`

### Use case 5: “I want feedback-driven admission refresh, not preference-driven replacement.”

Button:

- `Refresh S + publish rules`

Behavior:

- no confirmation
- planner/feedback path
- not the same as manual preference rebalance
- should remain non-destructive with respect to retained history

### Use case 6: “I want to see downstream rulegen from what is already in the pair inventory.”

Button:

- `Run sampled rulegen (5)…`

Behavior:

- diagnostic
- no confirmation
- samples from current pair-local active inventory only
- if the pair has no current inventory, the UX should say that explicitly

Important UX rule:

- this button is downstream validation
- it is not the right tool for testing preference changes before initialization/rebalance

### Use case 7: “I want to start over for this pair.”

Button:

- `Reset SRS data`

Behavior:

- destructive
- separate from rebalance
- requires explicit double confirmation

Current confirmation messages:

1. `Are you sure you want to reset all SRS progress for this language pair? This cannot be undone.`
2. `Really delete all learning history and start over for this pair?`

This button should remain the only explicit full-wipe path in this workstream.

## Button inventory

Current buttons in scope:

- preference fields
  - auto-save on change
  - no confirmation
- `Generate admitted words sample (5)…`
  - no confirmation
  - non-mutating
- `Initialize S for this pair`
  - no confirmation for empty pair
  - mutating
- `Refresh S + publish rules`
  - no confirmation
  - mutating but non-destructive to retained history
- `Run sampled rulegen (5)…`
  - no confirmation
  - diagnostic only
- `Reset SRS data`
  - destructive
  - double confirmation

Planned button:

- `Rebalance active set to current preferences`
  - preview first
  - confirmation required for apply
  - non-destructive to retained history

Rejected for v1:

- generic `Clear admitted words` button

Reason:

- too easy to confuse with reset,
- too destructive as a primary preference-update affordance,
- rebalance plus reset already covers the legitimate intents more cleanly.

If a stronger clear action is ever added later, it must:

- be advanced-only,
- explicitly say whether it parks or deletes items,
- remain distinct from both rebalance and full reset.
