# SRS Practice Layer — Design (Current + Target)

Status: active mixed design
Role: Mixed
Last updated: 2026-05-14
Last verified: 2026-05-14 metadata-only Lane 1 normalization plus SRS-adjacent doc/code/test read; practice-layer content not fully re-audited
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
- Current helper publication/runtime gating still operate on the active/admitted inventory for `S`; they do not yet enforce a separately published due-only subset end to end.

## Explicit policy decisions
- Set `S` means "items currently studied by the user."
- Passive display/exposure is not a scheduler event.
- Feedback is the authoritative event source for scheduling.
- Due-based serving remains the intended scheduler contract; current helper publication/runtime gating still publish and consume the active inventory more broadly than the due subset.

## Architecture overview
```text
Ruleset Engine (unchanged)
        ^
Practice Gate (runtime filter by helper-published SRS rules; due-only gating not yet enforced)
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
- Current runtime gate accepts the helper-published SRS ruleset as active.
- The helper-published ruleset is currently derived from the active/admitted inventory for the pair, not a dedicated due-only artifact.
- If SRS is disabled, runtime behavior falls back to standard rules.

## 4) Planner + bootstrap/growth policies
- Decide how new words enter `S`.
- Enforce explicit sizing policy (`bootstrap_top_n`, `initial_active_count`, clamp notes).
- Keep current executable fallback (`frequency_bootstrap`) while profile strategies mature.

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
