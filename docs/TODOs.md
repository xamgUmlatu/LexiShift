# LexiShift TODOs

Status: Active backlog
Last updated: 2026-03-26

This file is the consolidated TODO source of truth. It replaces the large TODO and plan sections that previously lived in the root `README.md`.

Related decision context:
- `docs/architecture/chrome_web_store_review_working_doc.md`
- `docs/architecture/design_diagram_workplan.md`

## Architecture Diagram Rollout

Use `docs/architecture/design_diagram_workplan.md` and `docs/architecture/diagrams/README.md` as the execution tracker.

- DG-01: Data ownership + storage layout (`[AS-IS]` first).
- DG-02: Settings propagation (Options -> runtime mirrors -> content runtime).
- DG-03: Rule resolution + DOM replacement pipeline.
- DG-04: Feedback + eventual sync queue/retry path.
- DG-05: SRS initialize/refresh control flow.
- DG-06: Helper availability/degraded-mode state model.

## Detailed Product Improvements (From 2026-02-18 Discussion)

### 1) Helper dependency UX: strong warning plus graceful degraded mode

Product intent:
- SRS value requires helper connectivity (installed dictionaries + SRS updates).
- If helper is missing, the extension should make this obvious immediately.
- Handcrafted JSON rules should still work without helper.

Implementation TODO:
- Add a high-visibility warning state in extension options and SRS surfaces when helper is unavailable.
- Add blocking guidance for helper-required SRS actions (`init`, `refresh`, rulegen-triggering actions).
- Keep non-SRS manual rules runtime available and clearly labeled as the degraded mode.
- Add explicit install/recovery guidance for both install orders (desktop-first and extension-first).

Open questions:
- Final warning copy/severity level and exact placement.
- Whether to provide a one-click "Retry helper connection" action everywhere.

Acceptance criteria:
- Missing helper is visible to users without opening deep diagnostics.
- SRS helper-required actions fail fast with a clear reason and recovery path.
- Handcrafted local JSON rules continue functioning when helper is unavailable.

### 2) Sensitive sentence history hardening (default OFF, no URL retention)

Product intent:
- Sentence history can include sensitive text and must be treated as high-risk data.
- Default behavior should minimize stored sensitive data.

Implementation TODO:
- Keep sentence-history capture disabled by default.
- Remove URL persistence from sentence/history records (no URL field stored).
- Keep exposure telemetry URL retention (`srsExposureLog`) explicitly documented as "retained for now" until policy changes.
- Keep processing/storage local-only and document this in user-facing privacy text.
- Add clear opt-in language for any sentence-history capture features.
- Add or confirm user controls for clearing sentence-history data.

Open questions:
- Final retention window and minimization policy (for opted-in users).
- Final wording for privacy disclosure and reviewer notes.
- Whether sentence excerpt storage remains enabled behind opt-in after additional research.

Acceptance criteria:
- Fresh install has sentence-history capture OFF.
- Stored sentence-history records do not include URL values.
- Users can understand and control sentence-history behavior from settings.

### 3) Helper-unavailable reliability policy (fail-fast SRS actions plus eventual feedback retry)

Product intent:
- Manual rules should remain usable offline from helper.
- SRS control operations should not silently degrade.
- Feedback/sync paths should eventually converge when helper returns.

Implementation TODO:
- For helper-dependent SRS controls, return immediate structured errors when helper is unavailable.
- Queue feedback events on the extension side so they can be retried after helper recovery.
- Persist queue state across MV3 service worker idle/restart boundaries.
- Add bounded queue limits and diagnostics visibility (queue depth, last retry, last error).
- Retry queued feedback with explicit backoff policy until success or retention limit.

Open questions:
- Queue size and retention limits.
- Exact diagnostics detail shown to end users vs advanced diagnostics only.
- Final retry/backoff timing policy.

Acceptance criteria:
- Interactive SRS controls fail fast with actionable error text while helper is down.
- Feedback generated during helper downtime is retained and eventually synced after recovery.
- Service worker wake/idle cycles do not lose queued feedback.

## Backlog Migrated From README

### GUI app UI overhaul
- Do a full UX pass across all major GUI screens (navigation, hierarchy, spacing, and affordances).
- Normalize layout density and visual consistency across locales, themes, and window sizes.
- Simplify settings information architecture so language packs, profiles, and SRS controls are easier to find.
- Define and implement keyboard shortcuts for profile/ruleset workflows after the Manage Profiles UX architecture is finalized.
- Fix squished UI elements in settings of core app.
- Fix ghost ruleset populated in ruleset selection UI in core app when no ruleset exists.

### Getting-started guide completion
- Complete the manual end-to-end (all sections finalized, screenshots added, and setup steps verified against current UI labels).
- Keep guide steps synchronized with extension/core app releases when labels or flow change.

### Ruleset display/highlight settings
- Move manual rules display/highlight controls into per-ruleset settings (not one shared/manual-only setting).
- Per-ruleset settings:
  - Display
  - Highlight replaced words (click to toggle original)
  - Highlight color

### CJK / no-space languages
- Detect whether input is likely a no-space language (CJK) using lightweight heuristics.
- If CJK, choose between:
  - character/n-gram tokenization with a trie that matches sequences, or
  - exact substring replacement without token boundaries.
- Keep exact substring mode as a user-selectable fallback for mixed-language text.

### Replacement pacing/sensitivity controls
- Move "Replacement Behavior" settings out of "Manual Rules" scope into global scope for the full experience.
- Applies to all replacements (ruleset and SRS).
- Settings to move:
  - Replace max 1 word per text block.
  - Allow replacing adjacent words.
  - Max replacements per page (`0` = unlimited).
  - Max per word per page (`0` = unlimited).
- Consider limiting replacements per sentence.
- Add settings to adjust sensitivity/strictness for the rules above.

### S-set visibility/review UX
- Add a list view of all the words currently in S.
- Consider a dedicated study/review view for S.
- Move `Run sampled rulegen (5)...` guidance into an Advanced diagnostics-only category in setup docs/UI (not baseline setup flow).

### Japanese script quality
- Check and improve the accuracy of generated romaji for Japanese words.

### Rule generation quality
- Execution-order reference for the current rulegen workstream:
  - `docs/developer/rulegen_workstream_execution_order.md`
- Improve rulegen quality by making generation/scoring shallower and higher precision.
- Improve SRS rulegen quality (helper-published rules) for better pedagogical precision and fewer broad/ambiguous outputs.
- `en-ja` now uses strict JMdict reading match (`surface + reading` from `word_package`); targets with no reading-matched entry currently stay in S but emit no rules.
- Evaluate a disposal/pruning policy for those unmatched S targets (for example, remove or quarantine after repeated misses).
- Add reverse-check scoring when reverse dictionaries are available:
  - score/penalize candidate rules by source->target consistency in reverse lookup.
  - implementation spec: `docs/rulegen/reverse_check_scoring_phase1.md`
  - follow-up: tune exact-hit ambiguity penalty against `reverse_check_total`; the first bounded `en-es` experiment did not beat existing miss/far penalty settings, but the signal is now implemented and harness-exposed.
- Add the next low-hanging additive `en-es` rulegen signals before or around the broad sweep:
  - next provenance / competition signals beyond the first implemented `late_sense_clean_earlier_competition_penalty`:
    - richer uses of `target_provenance`
    - richer uses of `gloss_provenance`
    - richer uses of `sense_provenance`
    - richer uses of `kaikki_policy_shadow`
  - per-family Kaikki demotion strengths rather than one coarse family block
  - gloss-decay shape exposure rather than only gloss-decay weight
  - narrow short-phrase admission for lexical verb phrases instead of global multiword admission
  - execution-order reference: `docs/developer/rulegen_workstream_execution_order.md`
- Add sense-risk penalties for ambiguous/specialized senses:
  - use lexical cues/metadata to demote risky polysemic or niche senses.
  - Kaikki/Wiktionary follow-up for `en-es`: use topics/categories/tags to demote domain-specific lexical senses after structural candidate recovery is fixed first (for example `presentar -> table`, `plaza -> bullring`).
- Add a formal Kaikki/Wiktionary gloss-format investigation and robust normalization/splitting pass for `en-es`:
  - classify real raw gloss structures before adding more pair-specific heuristics,
  - preserve sense order and metadata while recovering broad early lexical candidates such as `to happen, to occur` and `part; section; portion; share`.
- Add runtime apply-time polysemy safeguards (pair-aware):
  - abstain from replacement for high-risk ambiguous matches when confidence/sense margin is weak,
  - optional local-context heuristics around the matched source token,
  - structured runtime diagnostics for skipped replacements and reason codes.
- Add multi-source agreement bonus:
  - increase confidence when a candidate mapping is supported by multiple independent resources.
- Add true lexical-frequency signals for emitted source candidates:
  - move `en-es` beyond gloss-order-as-frequency,
  - evaluate source-side English lexical frequency,
  - later evaluate source-target frequency-gap features carefully rather than assuming "common beats specific."
- Add trait-conditioned rulegen profiles driven by runtime-computable features rather than human tags:
  - emit per-case trait vectors in benchmark artifacts,
  - define a small bank of named profiles,
  - analyze which profiles win by feature region,
  - later route runtime rulegen through an interpretable profile selector,
  - planning spec: `docs/rulegen/trait_conditioned_rulegen_profiles.md`.
- Generalize the benchmark/resource contract beyond the current `en-es` reference lane:
  - clean up generic resource naming so non-FreeDict providers do not leak through generic fields,
  - define a normalized translation-pack contract for benchmark/helper/adapter code,
  - generalize the compiled pair-context boundary,
  - use `de-en` as the first additional translation LP once the contract is clean enough,
  - use German frequency workflow polish as the first missing data-source lane that unlocks multiple LPs,
  - planning spec: `docs/developer/language_pair_generalization_roadmap.md`.
- Improve benchmark portability before the large broad sweep:
  - optionally add single-file archive/import ergonomics on top of the existing portable bundle export/replay flow if directory transfer becomes annoying.

### Pair-specific morphology expansion
- Current paired morphology expansion is intentionally narrow (`en-es` noun plural source -> target surface mapping).
- Add explicit morphology resolvers per LP (`en-de`, `es-en`, and future pairs) and extend beyond plural nouns.

### Embeddings scoring integration
- Hook embeddings into rule-generation scoring (downloads and one-time conversion are wired; scoring integration is pending).
- Keep embeddings as a secondary signal only:
  - require a real active `embedding_provider`,
  - validate pair-specific impact before exposing as a meaningful sweep dimension for `en-es`.

## Planned Milestones (Migrated From README)

1. Persist all GUI knowledge inside profiles/rulesets:
   - Store per-profile dictionary selection (mono vs cross-lingual) and language choices.
   - Store synonym settings (thresholds, embeddings) per profile or ruleset where appropriate (currently global).
2. Sync profiles/rulesets into clients:
   - Export active profile + ruleset list + language pack selection to Chrome/BD.
   - Add profile/ruleset switcher in extension/plugin settings.
   - Allow enabling/disabling multiple manual rulesets under a selected profile (not only one active manual ruleset).
   - Persist per-ruleset display settings:
     - Display
     - Highlight replaced words (click to toggle original)
     - Highlight color
3. Finish language pack UX polish:
   - Pack-specific validators for edge layouts.
   - Clear handling for external/manual paths vs. app-managed files.
   - Re-enable Wiktionary when we are ready to handle large downloads.
4. Add language selection controls tied to profiles/rulesets:
   - Monolingual vs cross-lingual toggle per profile or per ruleset.
   - Persist target/source language choices for bulk generation.
5. Scale large pack handling:
   - Background indexing for large packs (progress + cancel).
   - Optional cached indexes for fast reloads.
6. Add per-rule exception patterns or context gates if needed.
7. Add streaming/liveness adapter for live text replacement.
8. Localize the BetterDiscord plugin for multiple languages.
9. Consider larger Sigma symbol spaces for Share Code to shorten codes.
