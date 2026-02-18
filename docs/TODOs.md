# LexiShift TODOs

Status: Active backlog  
Last updated: 2026-02-19

This file is the consolidated TODO source of truth. It replaces the large TODO and plan sections that previously lived in the root `README.md`.

Related decision context:
- `docs/architecture/chrome_web_store_review_working_doc.md`

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
- Improve rulegen quality by making generation/scoring shallower and higher precision.
- Improve SRS rulegen quality (helper-published rules) for better pedagogical precision and fewer broad/ambiguous outputs.
- `en-ja` now uses strict JMdict reading match (`surface + reading` from `word_package`); targets with no reading-matched entry currently stay in S but emit no rules.
- Evaluate a disposal/pruning policy for those unmatched S targets (for example, remove or quarantine after repeated misses).

### Pair-specific morphology expansion
- Current paired morphology expansion is intentionally narrow (`en-es` noun plural source -> target surface mapping).
- Add explicit morphology resolvers per LP (`en-de`, `es-en`, and future pairs) and extend beyond plural nouns.

### Embeddings scoring integration
- Hook embeddings into rule-generation scoring (downloads and one-time conversion are wired; scoring integration is pending).

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
