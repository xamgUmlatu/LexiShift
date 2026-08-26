# LexiShift TODOs

Status: Active backlog
Role: Planning / WIP
Last updated: 2026-08-26
Last verified: 2026-08-26 dictionary/beta infrastructure follow-up capture; older backlog content not globally re-audited
Purpose: consolidated product and architecture backlog retained after root README cleanup
Source-of-truth: backlog planning only; current implementation truth lives in source code, tests, and `docs/developer/feature_state_matrix.md`.

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

## Post-Current-Workstream Beta Infrastructure And Dictionary Follow-Ups

Captured on 2026-08-26 after implementing local Yomitan dictionary import,
per-language-pair ordered lookup stacks, acquisition guidance, and packaged GUI
validation. These tasks should resume after the current workstream rather than
expanding the in-flight dictionary branch further.

### Highest-priority infrastructure

#### INFRA-01: Make the Python development and hook environment reproducible

Problem:
- Repository launchers currently fall through to the first available `python3`
  when no repository virtual environment is present.
- A verified dictionary change hit a false-negative pre-push failure because
  Homebrew Python 3.14 did not have the project's `fsrs` dependency, while the
  focused suite and packaged build passed under the supported Python 3.10
  environment.

Implementation TODO:
- Declare and document the supported Python version or version range.
- Provide one repository bootstrap/sync command for a local `.venv`.
- Make `scripts/dev/run_python.js` and installed hooks use that environment.
- Fail early with an actionable interpreter/dependency message instead of
  producing a large unrelated import-error cascade.

Acceptance criteria:
- A fresh contributor setup can create the supported environment with one
  documented command.
- `npm --prefix scripts run check` and the pre-push hook select the same Python
  environment.
- A normal verified push does not require `--no-verify` because of interpreter
  drift.

#### INFRA-02: Finish packaged GUI startup diagnosis and remove blocking work

Owning plan:
- `docs/developer/packaged_gui_startup_performance_plan.md`

Problem:
- Recent packaged resource-settings launches recorded approximately 224 and
  487 seconds inside `MainWindow` construction, far outside the existing cold
  launch targets. The responsible initialization step has not yet been isolated.

Implementation TODO:
- Add fine-grained startup checkpoints around `MainWindow` construction and
  resource-panel initialization.
- Render a usable window before scanning or loading large installed-resource
  inventories.
- Move proven expensive metadata/index work off the GUI thread and cache safe
  inventory results where appropriate.
- Add a packaged startup budget check using repeatable warm/cold samples.

Acceptance criteria:
- The responsible blocking operation is identified with checkpoint evidence.
- Resource Settings meets the targets in the owning startup-performance plan,
  or a current-machine exception is explicitly documented.
- Large installed dictionaries do not make the application appear dead.

#### INFRA-03: Add one-command macOS build, install, verify, and relaunch

Problem:
- The current manual PyInstaller, quit, `ditto`, comparison, and relaunch flow
  is error-prone; macOS can retain the previous application process during a
  bundle replacement.

Implementation TODO:
- Add a supported script/package command that validates the build, terminates
  only the installed LexiShift process, waits for exit, installs the bundle,
  verifies important bundle artifacts, and optionally relaunches to a requested
  settings view.
- Keep `/Applications/LexiShift.app` replacement separate from Application
  Support so user data is preserved.

Acceptance criteria:
- One documented command produces and launches the same bundle that passed
  validation.
- The command detects a stale running process and reports each lifecycle step.
- Verification does not rely on recursive directory comparison that follows
  framework symlink loops.

### Dictionary resilience and maintainability

#### DICT-01: Add a redistributable large-dictionary performance fixture

Implementation TODO:
- Generate a synthetic Yomitan format-3 archive large enough to exercise
  multi-bank import, indexing, repeat import, lookup, and cancellation costs.
- Add bounded import/lookup performance reporting without committing commercial
  dictionary data or using local Daijirin files as CI inputs.

Acceptance criteria:
- CI or a documented local quality command can detect major importer/indexing
  regressions using only redistributable generated data.
- Correctness coverage remains separate from machine-sensitive performance
  thresholds.

#### DICT-02: Add dictionary health, recovery, and source visibility

Implementation TODO:
- Detect missing, incompatible, or corrupt installed dictionary artifacts and
  offer a clear reimport/repair path.
- Show which dictionary supplied the displayed definition, using the existing
  provider/pack metadata without exposing local filesystem paths.
- Consider exporting/importing dictionary-stack assignments while explicitly
  excluding dictionary contents.

Acceptance criteria:
- A broken configured dictionary does not silently look healthy.
- Users can recover without manually editing settings or managed data folders.
- Definition-source identification remains compact and learner-friendly.

### Integration checkpoint

#### INTEGRATION-01: Merge the dictionary work into the beta line while fresh

Implementation TODO:
- Merge or rebase the coherent dictionary commits onto the active beta line
  before several more major feature branches accumulate.
- Run the combined changed-file/repository gates and validated packaged build.
- Perform a real-extension smoke covering import, per-pair ordering, first-match
  fallback, and displayed source identity.

Acceptance criteria:
- Dictionary, popup, sentence-density, and beta-release work coexist on one
  tested integration branch.
- Any merge conflicts are resolved from current product intent rather than
  deferred until the code has drifted.

### Deliberately deferred dictionary expansion

Do not treat the following as beta blockers unless testing reveals a concrete
need:
- merging definitions from multiple dictionaries instead of first-match
  fallback;
- Yomitan image/media import;
- per-profile dictionary stacks instead of the current global-per-pair model;
- a full curated in-app dictionary catalogue or automatic commercial-data
  download flow.

## Backlog Migrated From README

### GUI app UI overhaul
- Do a full UX pass across all major GUI screens (navigation, hierarchy, spacing, and affordances).
- Normalize layout density and visual consistency across locales, themes, and window sizes.
- Simplify settings information architecture so language packs, profiles, and SRS controls are easier to find.
- Define and implement keyboard shortcuts for profile/ruleset workflows after the Manage Profiles UX architecture is finalized.
- Fix squished UI elements in settings of core app.
- Fix ghost ruleset populated in ruleset selection UI in core app when no ruleset exists.

### Guide completion
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
- Page replacement density settings now apply to the merged SRS/manual runtime
  output and use explicit standard defaults.
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
  - move installed translation packs to a manifest-backed compiled-artifact model with SQLite as the preferred canonical runtime format,
  - treat provider-native raw downloads/extraction trees as build inputs rather than runtime contracts, and delete them after successful build by default,
  - treat app-managed GUI/helper/native-host/tooling surfaces as free to rename/remove now rather than preserving legacy `freedict_*` or TEI-first naming for compatibility,
  - apply the same manifest-backed compiled-artifact model to existing frequency and embedding pack flows, not only translation packs,
  - require any new data-source onboarding to use pack-id roots + manifest + canonical compiled artifact + raw cleanup by default,
  - generalize the compiled pair-context boundary,
  - use `de-en` as the first additional translation LP once the contract is clean enough,
  - use German frequency workflow polish as the first missing data-source lane that unlocks multiple LPs,
  - planning specs:
    - `docs/developer/data_source_normalization_architecture.md`
    - `docs/developer/data_source_normalization_execution_order.md`
    - `docs/developer/language_pair_generalization_roadmap.md`
    - `docs/language_pairs/de_en_workstream_roadmap.md`
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
   - Decide whether to phase out broad manual file-path selection entirely; current expectation is probably yes unless a concrete user need survives.
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
