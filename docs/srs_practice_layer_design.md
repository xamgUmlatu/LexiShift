# SRS Practice Layer — Design Draft

## Goal
Introduce a non‑destructive SRS “Practice Layer” that sits above the existing ruleset engine. It does not mutate rulesets. Instead, it controls which replacements are active *at runtime* based on SRS scheduling.

## Principles
- **Non‑destructive**: rulesets are not modified by SRS; SRS only gates which replacements are applied.
- **Modular**: candidate sources, filters, and scheduler are independent plug‑ins.
- **Portable**: SRS state and settings are exportable/importable across app, extension, and plugin.
- **Pair‑aware**: items are tagged with language pairs and only used in matching contexts.

## Architecture Overview
```
Ruleset Engine (unchanged)
        ↑
Practice Layer (SRS gate)
        ↑
Scheduler + Candidate Store + Feedback
```

## Core Components

### 1) SRS Item Store
Minimal schema (extend later):
- `item_id` (stable id)
- `lemma` (canonical word form)
- `language_pair` (e.g., en‑en, de‑en)
- `source_type` (frequency list, user‑stream, curated)
- `confidence` (0–1, derived from dictionary/embedding confidence)
- `stability`, `difficulty`, `last_seen`, `next_due`
- `history[]` (timestamp + rating)

Storage format:
- JSON (local, exportable)
- Designed to sync with extension/plugin

### 2) Scheduler
Responsibilities:
- Compute due items
- Produce `active_items` for the current session
- Update scheduling from feedback (Again/Hard/Good/Easy)

MVP scheduling:
- Due‑based queue + simple interval growth
- Capacity cap (e.g., max N active at a time)

### 3) Practice Gate (Runtime Filter)
- Sits between ruleset and replacement engine.
- Applies only rules whose replacement target is in `active_items`.
- Inverse mode optional: highlight due words without replacing.

### 4) Feedback Capture
- Minimal UI action from extension/plugin/app
- Ratings: Again / Hard / Good / Easy
- Stored in item history

### 5) Candidate Growth Pipeline (future)
Sources that add items to S:
- High‑frequency lexicon base
- User stream (words encountered in reading/writing)
- Curated packs

Filters (pluggable):
- Consensus filter
- Embedding threshold
- POS gating (if data exists)
- Confidence weighting

## Non‑Destructive Guarantee
- **Rulesets remain unchanged**.
- SRS state is stored separately and can be disabled at any time.
- If SRS is off, the system behaves exactly like the current ruleset engine.

## MVP Plan (No Code Yet)
1) Define SRS item schema and storage file format.
2) Implement a scheduler interface (pure logic).
3) Add a Practice Gate in the replacement pipeline (runtime only).
4) Capture basic feedback and persist history.
5) Export/import SRS settings + history.

## Backlog
- Language detection for user text streams.
- Confidence‑weighted scheduling.
- Pair‑specific thresholds.
- Preview UI for upcoming items.
- Cross‑platform sync.

