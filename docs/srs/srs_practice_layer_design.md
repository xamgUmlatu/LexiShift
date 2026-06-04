# SRS Practice Layer — Design (Current + Target)

Status: active mixed design
Role: Mixed
Last updated: 2026-05-26
Last verified: 2026-05-26 due-aware runtime serving metadata and page-budget replacement-priority tests plus SRS quality harness refresh
Purpose: explain how SRS practice gating fits into runtime replacement behavior while keeping current due-only publication gaps explicit
Source-of-truth: mixed design reference; current runtime truth lives in helper publication code, extension SRS gate code, SRS quality/journey harnesses, and feature-state evidence.

Canonical hybrid-model details:
- `docs/srs/srs_hybrid_model_technical.md`

This document is the implementation-facing overview for how the Practice Layer fits into runtime replacement behavior.

## Goal
Provide non-destructive SRS behavior above the ruleset engine:
- rulesets stay immutable
- runtime gating decides what is active
- scheduling is feedback-driven

## Current implementation status
- Helper-owned SRS store and FSRS-based scheduler exist.
- Feedback updates (`again|hard|good|easy`) are wired end-to-end.
- Options flow can initialize set `S` and run rulegen preview.
- Set-planning/profile logic is scaffolded.
- Helper publication still emits the active/admitted inventory for `S`, but helper-published SRS rules now carry due metadata and runtime gating filters future-due rules when that metadata is present.
- Helper-published SRS metadata also carries scheduler load fields such as
  `stability`, `difficulty`, `last_seen`, `last_review`, `exposures`, and
  `review_count` when available.
- When runtime replacement-load constraints are active, the extension uses that
  SRS metadata to prefer learning/young due items over mature or future-due SRS
  items.

## Explicit policy decisions
- Set `S` means "items currently studied by the user."
- Passive display/exposure is not a scheduler event.
- Feedback is the authoritative event source for scheduling.
- Due-based serving is enforced at runtime when helper SRS due metadata is present; helper publication remains broader than the due subset.
- Page replacement budgets are separate from due gating: they control visual
  load on the current page after runtime active rules are resolved.

## Architecture overview
```text
Ruleset Engine (unchanged)
        ^
Practice Gate (runtime filter by helper-published SRS due metadata)
        ^
Scheduler (feedback-driven)
        ^
SRS Store (helper-owned source of truth)
        ^
Set Planner (bootstrap/growth/refresh strategy)
```

## Runtime responsibilities

## 1) SRS Store
- Persist per-item study state for each pair.
- Keep sparse inventory; do not persist full corpus probabilities.
- Pair-local active inventory is currently a forgiving helper-side cache:
  - if no pair entry exists, helper flows can fall back to store-derived membership
  - if stored item ids are stale, missing ids are dropped during resolution
  - runtime diagnostics reports whether the current view came from explicit inventory or `store_fallback`, plus the stale-id count

## 2) Scheduler
- Build due queue from `next_due`.
- Apply 1..4 feedback updates:
  - 1 -> `again`
  - 2 -> `hard`
  - 3 -> `good`
  - 4 -> `easy`
- Use FSRS state (`stability`, `difficulty`, `last_review`, `scheduler_state`, `scheduler_step`) to determine the next interval.
- Push mastered items to longer intervals and lapsed items to shorter intervals.

## 3) Practice Gate
- Current runtime gate filters helper-published SRS rules by `metadata.rulegen.srs.next_due` when due metadata is present.
- The helper-published ruleset is still derived from the active/admitted inventory for the pair, not a dedicated due-only artifact.
- Metadata-free cached helper rules remain active as a compatibility fallback until the ruleset is regenerated.
- If SRS is disabled, runtime behavior falls back to standard rules.

## 3.1) Page Replacement Load
- Page replacement load is enforced by the extension page budget pipeline, not
  by helper admission.
- The standard MVP page-density policy is explicit in the extension defaults:
  `maxReplacementsPerPage = 20`, `maxReplacementsPerLemmaPerPage = 2`,
  `allowAdjacentReplacements = false`, and `maxOnePerTextBlock = false`.
- `maxReplacementsPerPage` caps total replacement count on the page (`0` remains
  an explicit unlimited override).
- `maxReplacementsPerLemmaPerPage` caps repeated display of the same target
  lemma on the page (`0` remains an explicit unlimited override).
- When page budgets, one-per-block, or non-adjacent load constraints are active,
  selection inside the constrained candidate set prefers SRS items in this
  order:
  1. new, learning, or relearning items;
  2. due review items with lower stability;
  3. due review items with mature/long stability;
  4. metadata-free SRS compatibility fallback rows;
  5. future-due SRS rows if they ever reach this layer.
- This is a runtime load policy only. It does not change the SRS scheduler or
  mutate helper state.

## 4) Planner + bootstrap/growth policies
- Decide how new words enter `S`.
- Enforce explicit sizing policy (`bootstrap_top_n`, `initial_active_count`, clamp notes).
- Keep the no-strategy executable baseline (`frequency_bootstrap`) while
  allowing requested `profile_bootstrap` initialization and preview paths to
  apply profile-aware scoring over the seed frontier.

## Data ownership
- Helper is canonical for mutable SRS scheduling state.
- Extension/plugin can cache local logs, but helper state drives authoritative scheduling decisions.

## Non-destructive guarantee
- SRS does not mutate user rulesets directly.
- SRS can be disabled without data loss in ruleset files.

## Open architecture items
- Formalize state labels (`new`, `learning`, `review`, `mature`, `relearn`, `suspended`).
- Consolidate local extension logs with helper feedback ingestion contract.
- Add a policy registry for pair-specific bootstrap/growth strategy selection.
- Decide whether a dedicated due-only publication artifact is still useful now that the runtime gate can filter by helper SRS due metadata.
