# Feature State Matrix

Status: active ledger
Role: Canonical current
Last updated: 2026-03-17
Source-of-truth: cross-cutting state ledger; runtime truth still lives in code, tests, and dated evidence artifacts.

Purpose:
- Keep feature state explicit for GenAI-driven development.
- Separate `implemented`, `default-on`, `verified`, and `planned` so current behavior is easy to recover.
- Give each feature a dated checkpoint plus evidence paths.

Use this file when:
- default behavior changes,
- benchmark policy or baseline assumptions change,
- a workstream moves from scaffolded to executable,
- code inspection finds a doc/code mismatch that should be tracked.

## Status Vocabulary

- `planned`: documented idea only.
- `scaffolded`: code/docs shape exists, but behavior is not yet fully executable.
- `implemented`: code path exists and is usable.
- `default-on`: implemented and enabled in normal/default behavior.
- `verified`: implementation has recent evidence (artifact, test, or direct code inspection).

## Date Fields

- `Last documented checkpoint`: most recent dated doc milestone or spec update.
- `Last verified`: most recent artifact date, test evidence, or dated code inspection.

## Rulegen Benchmark / Gate / Triage Loop

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-02-24`
- Last verified: `2026-03-12` local summary rerender + CI wiring review
- Default behavior:
  - Required for rulegen scoring, candidate filtering, POS normalization, and LP tuning changes.
  - Canonical loop remains benchmark -> quality gate -> triage.
  - Latest rulegen artifacts now have human-facing Markdown summaries for benchmark, gate, and triage surfaces.
- Evidence:
  - `AGENTS.md`
  - `docs/developer/ai_workflow.md`
  - `scripts/testing/rulegen_benchmark.py`
  - `scripts/testing/rulegen_benchmark_summary.py`
  - `scripts/testing/rulegen_quality_gate.py`
  - `scripts/testing/rulegen_quality_gate_summary.py`
  - `scripts/testing/rulegen_benchmark_triage.py`
  - `scripts/testing/rulegen_benchmark_triage_summary.py`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.md`
  - `docs/test_outputs/rulegen_benchmark_summary_latest.md`
  - `docs/test_outputs/rulegen_quality_gate_latest.json`
  - `docs/test_outputs/rulegen_quality_gate_summary_latest.md`
  - `docs/test_outputs/rulegen_benchmark_triage_summary_latest.md`
- Known gaps:
  - Current `docs/test_outputs/rulegen_quality_gate_latest.json` has FAIL findings for `en-es` quality floor and delta budget.
  - Recommended pairs (`en-ja`, `en-de`, `es-en`) are still advisory rather than hard-gated.
  - Current quality-gate output also shows saturation warnings for `en-es`.
  - Artifact history and pair inference still depend on wrapper usage rather than a mandatory repo-wide gate.

## Rulegen Auto Audit Wrapper

- Status: `implemented`, `verified`, `default-on` = `no`
- Last documented checkpoint: `2026-03-11`
- Last verified: `2026-03-11` CLI inspection
- Default behavior:
  - Optional wrapper for touched-pair rulegen audits.
  - Preserves the canonical benchmark -> quality gate -> triage sequence by calling `rulegen_pair_audit_cycle.py`.
  - Adds dated artifacts, `*_latest` alias updates, and run manifests.
- Evidence:
  - `docs/developer/ai_workflow.md`
  - `docs/developer/genai_workflow_architecture.md`
  - `scripts/testing/rulegen_auto_audit.py`
  - `scripts/testing/rulegen_pair_audit_cycle.py`
- Known gaps:
  - Pair inference is heuristic and should not replace explicit `--pairs` when the touched scope is ambiguous.
  - Wrapper coverage is currently specific to the rulegen quality loop and not yet mirrored for SRS quality work.

## SRS Quality Harness

- Status: `implemented`, `verified`, `default-on` = `yes` for SRS scheduler/admission/publication workflow
- Last documented checkpoint: `2026-03-12`
- Last verified: `2026-03-12` synthetic harness run + summary artifact
- Default behavior:
  - Use the synthetic harness for SRS scheduler, admission refresh, helper publication, set execution, and runtime-serving workflow changes.
  - Current harness covers bootstrap/publication/runtime diagnostics for `en-ja` and `en-de`, plus an `en-ja` feedback-cycle pause/resume scenario.
  - Human-facing summary is available from the JSON artifact.
- Evidence:
  - `AGENTS.md`
  - `docs/developer/ai_workflow.md`
  - `scripts/testing/srs_quality_harness.py`
  - `scripts/testing/srs_quality_summary.py`
  - `docs/test_outputs/srs_quality_latest.json`
  - `docs/test_outputs/srs_quality_summary_latest.md`
- Known gaps:
  - Coverage is synthetic and pair-limited; it does not yet grade pedagogical quality or real user data.
  - Current harness intentionally surfaces the due-aware publication mismatch as a warning, not a hard failure.
  - `es-en` / `en-es` SRS quality scenarios are not yet represented in the synthetic harness.

## SRS Journey E2E Harness

- Status: `implemented`, `verified`; `default-on` = `no`
- Last documented checkpoint: `2026-03-21` `en-es` parity extension for the SRS journey harness, keeping the same JSON/Markdown/HTML pedagogical review surfaces across `en-ja` and `en-es`
- Last verified: `2026-03-21` deterministic `en-ja` + `en-es` core and edge journey harness runs, stabilized `en-ja` + `en-es` real-publication lanes, Markdown summaries, and interactive HTML review artifacts
- Default behavior:
  - Deterministic `en-ja` and `en-es` core and edge journey lanes plus matching real-publication lanes are available as analysis-first SRS E2E harnesses, but they are not yet part of the required default SRS workflow loop in `AGENTS.md`.
  - The core lane captures item-level admitted `S`, due `D`, and published `P` sets across bootstrap, refresh, and fade/stick phases.
  - Journey JSON now includes bootstrap candidate audits, refresh candidate ranking audits, and richer per-item state fields such as confidence, due rank, and lexical previews for retroactive pedagogical review.
  - The edge lane captures duplicate-feedback and exposure-only behavior with the same item-level reporting contract.
  - The real-publication lane keeps deterministic clocks/resources, uses the actual seed-builder plus helper/rulegen publication path, and now holds complete due publication for the current `en-ja` and `en-es` scenarios.
  - Interactive HTML playback artifacts now provide step-by-step review with phase controls, admission rationale tables, and a sticky profile-state panel.
  - Current contract mode defaults to observation: publication broader than the due subset is surfaced as a warning rather than a hard failure.
- Evidence:
  - `docs/srs/srs_journey_harness_workstream.md`
  - `scripts/testing/srs_journey_harness.py`
  - `scripts/testing/srs_journey_summary.py`
  - `scripts/testing/srs_journey_html.py`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_edge_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_ja_real_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_edge_latest.html`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.json`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.md`
  - `docs/test_outputs/srs_journey/srs_journey_en_es_real_latest.html`
- Known gaps:
  - `en-de` extension is still pending.
  - The real-publication lane still uses synthetic resources; broader pair coverage is still pending.
  - The due-aware publication contract remains unresolved; the harness currently records the mismatch instead of enforcing it.

## Development Workflow Safeties

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-03-17` canonical-doc metadata enforcement + changed-scope doc-reference expansion + health warning-delta gating
- Last verified: `2026-03-21` local `check:state`, `check:report`, `check:summary`, `check:style:report`, `check:style:summary`, and `health:project:report`
- Default behavior:
  - `npm --prefix scripts run check` is the stable non-mutating repo safety command.
  - `npm --prefix scripts run check` now includes the strict Windows parity audit, so parity regressions fail the default local safety gate and pre-push hook.
  - `npm --prefix scripts run check` now includes strict repo-wide Ruff lint/format checks because the repo-wide style baseline is clean.
  - `npm --prefix scripts run check:changed` is the preferred branch-scope workflow command.
  - `npm --prefix scripts run check:changed` now records both total changed files and substantive changed files, and uses the substantive set when inferring heavier quality loops such as rulegen audit; Python uses AST comparison, JSON uses parsed equality, and Markdown/text uses whitespace-normalized comparison.
  - `npm --prefix scripts run check:docs` now validates top metadata (`Status`, `Role`, `Last updated`) plus referenced repo paths for canonical routing/policy docs.
  - `npm --prefix scripts run check:changed` now reruns the canonical doc integrity audit when canonical docs change or when referenced source files under `apps/`, `core/`, `scripts/`, `.github/`, or canonical root files change materially.
  - `npm --prefix scripts run health:project:changed` now blocks new/regressed warning debt alongside new/regressed violation debt.
  - `npm --prefix scripts run build` is the local build smoke for maintained build surfaces.
  - `npm --prefix scripts run build:report` is the full build contract and now verifies expected BetterDiscord / GUI artifacts in the report payload.
  - Hosted macOS `build:report` keeps the full GUI bundle validation path; hosted Windows `build:report` now uses the full GUI build plus artifact verification, while the strict Windows parity audit remains the dedicated Windows-specific validation gate.
  - Hosted CI now runs both the full macOS `build:report` path and the explicit Ubuntu `build:ci:report` partial path.
  - Python-backed npm workflow commands now resolve their interpreter through `scripts/dev/run_python.js` so `check` / `build` / audit entrypoints remain usable on Windows hosts.
  - `npm --prefix scripts run build:ci` / `build:ci:report` keep the same build workflow on unsupported hosts while recording explicit GUI-validation skips.
  - `npm --prefix scripts run check:style` is the standalone repo-wide style loop.
  - `npm --prefix scripts run check:style:report` and `check:style:summary` publish the current repo-wide Ruff style state as JSON and Markdown artifacts.
  - `npm --prefix scripts run check:state` audits the feature-state ledger for required fields, dated checkpoints, evidence paths, and transition-aware updates relative to `HEAD`.
  - `npm --prefix scripts run check:report`, `check:changed:report`, and `build:report` emit machine-readable JSON artifacts for automation.
  - Failed `check` / `build` commands now record stdout/stderr tail lines and missing-artifact details in the JSON reports so hosted CI failures remain inspectable from artifacts and summaries.
  - `npm --prefix scripts run check:summary` renders a Markdown summary from the latest workflow reports and now surfaces first-failure detail tails when present.
  - Hosted CI now lets report-producing steps continue long enough to upload summaries/artifacts, then fails the job via explicit JSON-based gate steps.
  - Hosted Ubuntu repo-safety now uses `npm --prefix scripts run check:report:ci`, which skips the redundant Windows parity audit; dedicated Windows parity/build jobs remain responsible for that surface.
  - Hosted repo-safety still renders the latest rulegen benchmark/gate/triage summaries, but the known-red rulegen artifact no longer blocks the generic repo-safety job.
  - `npm --prefix scripts run hooks:install` installs both `pre-commit` and `pre-push`; the pre-push hook mirrors `npm --prefix scripts run check`.
  - `pre-commit` now runs repo-wide Ruff lint and Ruff format before commit, while `pre-push` keeps the full repo-safety gate.
- Evidence:
  - `scripts/dev/feature_state_audit.py`
  - `scripts/dev/dev_workflow_check.py`
  - `scripts/dev/dev_workflow_changed_check.py`
  - `scripts/dev/dev_workflow_build.py`
  - `scripts/dev/dev_workflow_style_check.py`
  - `scripts/dev/dev_workflow_style_summary.py`
  - `scripts/dev/check_doc_references.py`
  - `scripts/dev/check_project_health.js`
  - `scripts/dev/project_health_rules.js`
  - `scripts/dev/ci_report_gate.py`
  - `scripts/dev/run_python.js`
  - `apps/betterdiscord-plugin/build_plugin.js`
  - `.pre-commit-config.yaml`
  - `.github/workflows/ci.yml`
  - `requirements-build.txt`
  - `scripts/package.json`
  - `docs/test_outputs/dev_workflow/feature_state_audit_latest.json`
  - `docs/test_outputs/dev_workflow/doc_references_latest.json`
  - `docs/test_outputs/dev_workflow/check_latest.json`
  - `docs/test_outputs/dev_workflow/check_changed_latest.json`
  - `docs/test_outputs/dev_workflow/build_latest.json`
  - `docs/test_outputs/dev_workflow/build_ci_latest.json`
  - `docs/test_outputs/dev_workflow/summary_latest.md`
  - `docs/test_outputs/dev_workflow/style_latest.json`
  - `docs/test_outputs/dev_workflow/style_summary_latest.md`
  - `docs/test_outputs/project_health/project_health_latest.json`
  - `docs/developer/documentation_governance.md`
  - `docs/developer/project_health_gate_structure.md`
  - `docs/developer/local_setup.md`
  - `docs/developer/build_and_release.md`
- Known gaps:
  - GUI packaging makes `build` materially slower than `check`.
  - Hosted build coverage is now macOS full, Windows full-build plus artifact verification with a separate strict parity gate, and Ubuntu CI-safe partial; Ubuntu remains the explicit non-GUI proof lane rather than full desktop packaging.
  - Canonical-doc metadata enforcement is currently limited to the canonical routing/policy layer, not every maintained doc in the repo.
  - Pre-commit and pre-push coverage are optional until contributors run `npm --prefix scripts run hooks:install`.
  - Branch-scope changed reports intentionally surface the whole branch delta, so long-running branches can report unrelated debt unless contributors use `check:changed:local` or `check:changed:staged`.

## GitHub Pages Docs Deployment

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-03-13`
- Last verified: `2026-03-13` local `bundle exec jekyll build --trace` + hosted `pages` / `pages-build-deployment` success on `302bba5`
- Default behavior:
  - Repo-owned Pages workflow now lives in `.github/workflows/pages.yml`.
  - Pull requests touching `docs/**` run a build-only Pages validation job.
  - Pushes to `main` touching `docs/**` build and deploy the site through GitHub Actions.
  - Local parity command is `cd docs && bundle exec jekyll build --trace`.
- Evidence:
  - `.github/workflows/pages.yml`
  - `docs/runbooks/github_pages_setup.md`
  - `docs/Gemfile`
  - `docs/Gemfile.lock`
  - `docs/_config.yml`
  - `docs/developer/local_setup.md`
  - `docs/test_outputs/dev_workflow/github_pages_workflow_verification_latest.md`
- Known gaps:
  - Current workflow validates Jekyll build/deploy only; it does not yet run link checking or browser-level UI smoke tests for docs JavaScript.

## Windows GUI Parity Audit

- Status: `implemented`, `verified`, `default-on`
- Last documented checkpoint: `2026-03-12`
- Last verified: `2026-03-12` parity audit rerun + repo-safety integration + changed-scope/CI workflow wiring review
- Default behavior:
  - `npm --prefix scripts run check` now runs the strict Windows parity audit as part of repo safety and pre-push.
  - `npm --prefix scripts run check:windows:parity` writes a machine-readable parity audit of Windows GUI/helper/build parity.
  - `npm --prefix scripts run check:windows:parity:summary` renders the current parity state into Markdown for human handoff.
  - Hosted CI now has a Windows full-build lane plus parity audit artifacts.
  - `npm --prefix scripts run check:changed` now runs the Windows parity audit automatically when parity-related files change.
  - Windows CI now uses the strict parity audit command so parity regressions fail the hosted workflow.
- Evidence:
  - `docs/developer/windows_gui_parity_workstream.md`
  - `scripts/dev/windows_parity_audit.py`
  - `scripts/dev/windows_parity_summary.py`
  - `apps/gui/src/frozen_layout.py`
  - `apps/gui/src/helper_installer.py`
  - `apps/gui/src/helper_ui.py`
  - `apps/gui/src/helper_tray.py`
  - `docs/architecture/native_messaging_design.md`
  - `docs/test_outputs/dev_workflow/windows_parity_latest.json`
  - `docs/test_outputs/dev_workflow/windows_parity_summary_latest.md`
  - `.github/workflows/ci.yml`
- Known gaps:
  - The parity audit is now a required workflow gate, but it is still not a complete release certification on its own.
  - Current browser coverage is limited to the supported GUI helper environments (`chrome`, `chromium`, `brave`).

## Feature-State Evidence Audit

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-03-12`
- Last verified: `2026-03-12` local audit run + repo safety/base-ref integration
- Default behavior:
  - `scripts/dev/feature_state_audit.py` validates that feature entries include status, dated checkpoints, default behavior bullets, evidence bullets, and known gaps.
  - Evidence paths in `docs/developer/feature_state_matrix.md` must resolve on disk.
  - Repo safety now runs this audit directly against `HEAD`, pre-commit runs it when the feature ledger changes, and changed-scope workflow checks run it against the branch base when the ledger is touched.
- Evidence:
  - `scripts/dev/feature_state_audit.py`
  - `core/tests/dev/test_feature_state_audit.py`
  - `scripts/dev/dev_workflow_check.py`
  - `.pre-commit-config.yaml`
  - `docs/test_outputs/dev_workflow/feature_state_audit_latest.json`
- Known gaps:
  - The audit enforces structure and evidence existence, not semantic correctness of every status claim.
  - It does not yet require every status transition to update its verification date in the same commit.

## Generic Gloss Demotion

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-02-27`
- Last verified: `2026-02-28` benchmark artifact review; `2026-03-11` code inspection
- Default behavior:
  - Active for current rulegen pairs through pair-specific demotion lists.
  - Tuned via `semantic_demotion_scale`.
- Evidence:
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/rulegen/rulegen_congruity_implementation_plan.md`
  - `core/lexishift_core/rulegen/semantic_demotion.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/es_en.py`
  - `core/lexishift_core/rulegen/pairs/en_de.py`
  - `core/lexishift_core/rulegen/pairs/ja_en.py`
- Known gaps:
  - Heuristic demotion is conservative and does not replace sense-level disambiguation.
  - Current `en-es:madre` failure shows generic demotion alone is not sufficient.

## Reverse-Check Scoring

- Status: `implemented`, `verified`, `default-on` = `no`
- Last documented checkpoint: `2026-03-13` named reverse-check run matrix + reverse-lane artifact refresh
- Last verified: `2026-03-13` widened `en-es` slice to 38 cases, added aggressive expansion review, refreshed canonical + named reverse artifacts, and refreshed the run matrix
- Default behavior:
  - Configurable and pair-aware for `en-es` and `es-en`.
  - Not yet promoted to default production tuning.
  - Reverse-check-specific evaluation now has a named `en-es` lane via `npm --prefix scripts run quality:rulegen:reverse:en-es`.
  - Parameter-set comparison is now tracked in `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`.
- Evidence:
  - `docs/rulegen/reverse_check_scoring_phase1.md`
  - `docs/rulegen/reverse_check_rollout_matrix.md`
  - `docs/rulegen/reverse_check_en_es_case_review_2026-03-13.md`
  - `docs/rulegen/reverse_check_en_es_aggressive_expansion_2026-03-13.md`
  - `docs/rulegen/reverse_check_en_es_failure_traits_2026-03-13.md`
  - `core/lexishift_core/rulegen/ranking.py`
  - `core/lexishift_core/rulegen/pairs/en_es.py`
  - `core/lexishift_core/rulegen/pairs/es_en.py`
  - `core/lexishift_core/rulegen/tuning.py`
  - `scripts/testing/rulegen_benchmark.py`
  - `docs/test_outputs/rulegen_benchmark_en_es_latest.md`
  - `docs/test_outputs/rulegen_benchmark_triage_latest.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_far_hit_experiment_2026-03-13.md`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_far_hit_experiment_2026-03-13.md`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json`
  - `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.md`
  - `docs/test_outputs/rulegen_quality_gate_en_es_reverse_latest.json`
  - `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_latest.md`
  - `docs/test_outputs/rulegen_reverse_en_es_run_matrix_latest.md`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_off_latest.json`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_on_latest.json`
  - `docs/test_outputs/rulegen_probe_en_es_reverse_far_hit_experiment_2026-03-13.json`
- Known gaps:
  - Only `en-es` and `es-en` are wired; `en-de` and `en-ja` have no reverse-check implementation.
  - The canonical latest benchmark loop still defaults to `rev=off`; reverse-check-specific evaluation currently requires explicit benchmark overrides.
  - No committed `es-en` benchmark/gate/triage artifact yet proves rollout maturity.
  - `en-es` hard-case coverage is better, but the widened 38-case canonical artifact now shows eleven triage items; the default `rev=off` lane is intentionally much redder after the aggressive expansion.
  - The current named `en-es` reverse lane reduces remaining triage to one item (`cuadro`) and lowers `forbidden_any_rate` to `2.63%`.
  - The best objective run in the reverse lane currently uses `max_rules_per_target=1`; a near-best `mr=none` run retains `top3=100.00%` with the same remaining failure set.
  - `cuadro` still exposes a non-separable failure class for reverse evidence alone.
  - Current rollout is scoring-only, not strict candidate blocking.

## POS Normalization

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-02-23`
- Last verified: `2026-02-23` phase-6 artifacts; `2026-03-11` code inspection
- Default behavior:
  - Seed extraction and word-package metadata carry raw and canonical POS.
  - Rulegen pair modules can consume normalized POS metadata.
- Evidence:
  - `docs/rulegen/pos_normalization_workstream.md`
  - `core/lexishift_core/pos/normalization.py`
  - `core/lexishift_core/srs/seed.py`
  - `core/lexishift_core/rulegen/pairs/pos_utils.py`
  - `docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json`
  - `docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json`
- Known gaps:
  - Unknown POS inventory remains for `freq-de-default.sqlite` and `freq-ja-bccwj.sqlite`.
  - POS metadata is stronger than current downstream decision usage for both rulegen ranking and SRS growth.

## SRS Set Planner Strategies

- Status:
  - `frequency_bootstrap`: `implemented`, `default-on`, `verified`
  - `profile_bootstrap`: `scaffolded`
  - `profile_growth`: `scaffolded`
  - `adaptive_refresh`: `scaffolded`
- Last documented checkpoint: `2026-02-23`
- Last verified: `2026-03-11` code inspection
- Default behavior:
  - Executable behavior remains frequency bootstrap.
  - Profile-aware strategies still fall back to planning-only or frequency-bootstrap execution.
- Evidence:
  - `docs/srs/srs_set_planning_technical.md`
  - `core/lexishift_core/srs/set_planner.py`
  - `core/lexishift_core/helper/use_cases/initialize_set.py`
- Known gaps:
  - Planner diagnostics are ahead of executable strategy diversity.
  - Pair policy defaults are currently near-identical across active pairs.

## Due-Aware SRS Serving

- Status: `planned`; end-to-end implementation not verified
- Last documented checkpoint: `2026-02-23`
- Last verified: `2026-03-11` code inspection
- Default behavior:
  - Docs define due-set-driven serving.
  - Current helper publication and extension gate behavior appear to operate on admitted `S` items rather than a separately published due subset.
- Evidence:
  - `docs/srs/srs_hybrid_model_technical.md`
  - `core/lexishift_core/srs/scheduler.py`
  - `core/lexishift_core/helper/rulegen.py`
  - `apps/chrome-extension/shared/srs/srs_gate.js`
- Known gaps:
  - No explicit due-state artifact or due-aware helper ruleset publish path is currently tracked here.
  - This item should remain `planned` until helper publication and runtime gating are verified against due-state behavior.

## Extension-Side Confidence Gating For Helper Rules

- Status: `planned` / `unverified`
- Last documented checkpoint: `2026-02-27` rulegen docs review
- Last verified: `2026-03-11` code inspection
- Default behavior:
  - Docs describe confidence-based runtime filtering.
  - Extension runtime path inspected on `2026-03-11` did not confirm a live helper-rule confidence filter.
- Evidence:
  - `docs/rulegen/rule_generation_technical.md`
  - `docs/reference/glossary.md`
  - `apps/chrome-extension/content/runtime/rules/active_rules_runtime.js`
  - `apps/chrome-extension/shared/srs/srs_gate.js`
- Known gaps:
  - Treat this as unresolved until a code path is identified and tested.
  - Do not mark confidence gating as shipped based on docs alone.

## GenAI Workflow Architecture

- Status: `implemented`, `default-on`, `verified`
- Last documented checkpoint: `2026-03-11`
- Last verified: `2026-03-12`
- Default behavior:
  - Use the rulegen quality loop already defined in `AGENTS.md` and `docs/developer/ai_workflow.md`.
  - Use `docs/developer/genai_workflow_architecture.md` for agent roles, instance splitting, and harness policy.
  - Use `scripts/testing/rulegen_auto_audit.py` for dated plus latest rulegen audit runs when a change-aware wrapper is helpful.
- Evidence:
  - `docs/developer/genai_workflow_architecture.md`
  - `scripts/testing/rulegen_auto_audit.py`
  - `scripts/testing/rulegen_pair_audit_cycle.py`
- Known gaps:
  - Feature-state discipline is stronger now, but status transitions are not yet enforced against commit-scoped artifact diffs.
  - Hosted CI still uses an explicit CI-safe build mode rather than full macOS GUI validation.

## Current State Mismatches To Preserve Explicitly

These are not accidental wording issues. Keep them explicit until code and docs converge.

1. Reverse-check is implemented but not yet default-on.
2. SRS docs define due-aware serving, but current end-to-end publish/gate behavior is not yet verified as due-aware.
3. Docs mention runtime confidence filtering, but extension-side helper-rule confidence gating is not yet verified in code.
4. Planner docs describe multiple strategies, but executable behavior is still dominated by frequency bootstrap.
