# SRS Practice Layer — Design (Current + Target)

Canonical hybrid-model details:
- `docs/srs/srs_hybrid_model_technical.md`

This document is the implementation-facing overview for how the Practice Layer fits into runtime replacement behavior.

## Goal
Provide non-destructive SRS behavior above the ruleset engine:
- rulesets stay immutable
- runtime gating decides what is active
- scheduling is feedback-driven

## Current implementation status
- Helper-owned SRS store and scheduler exist.
- Feedback updates (`again|hard|good|easy`) are wired end-to-end.
- Options flow can initialize set `S` and run rulegen preview.
- Set-planning/profile logic is scaffolded.

## Explicit policy decisions
- Set `S` means "items currently studied by the user."
- Passive display/exposure is not a scheduler event.
- Feedback is the authoritative event source for scheduling.
- Due-based serving is primary; weighted ranking is secondary (admission/tie-breaks).

## Architecture overview
```text
Ruleset Engine (unchanged)
        ^
Practice Gate (runtime filter by active/due S items)
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

## 2) Scheduler
- Build due queue from `next_due`.
- Apply 1..4 feedback updates:
  - 1 -> `again`
  - 2 -> `hard`
  - 3 -> `good`
  - 4 -> `easy`
- Push mastered items to longer intervals and lapsed items to shorter intervals.

## 3) Practice Gate
- Only allow replacements for currently active/due items from `S`.
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
