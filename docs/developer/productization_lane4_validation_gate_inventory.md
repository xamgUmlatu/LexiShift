# Productization Lane 4 Validation Gate Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 command inventory review against `scripts/package.json`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, workflow docs, and Lane 3 evidence
Purpose: map change types to the smallest validation bundle that honestly proves the touched surface before product expansion resumes
Source-of-truth: inventory only; command behavior lives in `scripts/package.json`, workflow scripts, CI config, hooks, and subsystem test harnesses.
Related docs:
- `productization_closure_roadmap.md`
- `productization_lane3_feature_state_truth_inventory.md`
- `documentation_governance.md`
- `genai_workflow_architecture.md`
- `build_and_release.md`
- `feature_state_matrix.md`
- `../../scripts/README.md`

## Scope

Lane: Lane 4, verification gate consolidation.

This inventory does not invent a new validation policy. It reconciles the
existing commands into a compact by-change-type map so future agents do not
choose gates from memory or stale packet examples.

Explicitly out of scope:

1. changing quality baselines or policy thresholds,
2. making `check:changed` replace the full `check` gate,
3. treating generated `*_latest` artifacts as architecture authority,
4. requiring full packaging builds for docs-only or narrow test-only edits,
5. certifying signed release installers.

## Command Authority

Use package-script surfaces first when they exist:

| Surface | Command | Primary Output |
| --- | --- | --- |
| Repo safety | `npm --prefix scripts run check` | terminal gate; `pre-push` mirror |
| Repo safety report | `npm --prefix scripts run check:report` | `docs/test_outputs/dev_workflow/check_latest.json` |
| CI repo safety report | `npm --prefix scripts run check:report:ci` | `docs/test_outputs/dev_workflow/check_latest.json` without redundant Windows parity |
| Branch-scope safety | `npm --prefix scripts run check:changed` | branch delta gate from `origin/main` |
| Local/staged safety | `npm --prefix scripts run check:changed:local` / `check:changed:staged` | narrower current-edit gate |
| Canonical docs | `npm --prefix scripts run check:docs` | canonical doc metadata/reference gate |
| Feature-state ledger | `npm --prefix scripts run check:state` | `docs/test_outputs/dev_workflow/feature_state_audit_latest.json` |
| Build smoke | `npm --prefix scripts run build` | BetterDiscord and GUI build validation |
| Full build report | `npm --prefix scripts run build:report` | `docs/test_outputs/dev_workflow/build_latest.json` |
| CI-safe build report | `npm --prefix scripts run build:ci:report` | `docs/test_outputs/dev_workflow/build_ci_latest.json` |
| Windows parity | `npm --prefix scripts run check:windows:parity` | `docs/test_outputs/dev_workflow/windows_parity_latest.json` |
| Windows parity summary | `npm --prefix scripts run check:windows:parity:summary` | `docs/test_outputs/dev_workflow/windows_parity_summary_latest.md` |
| SRS quality | `npm --prefix scripts run quality:srs:harness` | `docs/test_outputs/srs_quality_latest.json` |
| SRS quality summary | `npm --prefix scripts run quality:srs:summary` | `docs/test_outputs/srs_quality_summary_latest.md` |

Raw `python3 scripts/...` commands remain valid when a package wrapper does not
exist or when direct CLI flags are needed. When a package wrapper and a raw
command are equivalent, prefer the package wrapper in runbooks and handoffs.

## Always-On Review Rules

Every slice should keep these rules explicit:

1. run targeted tests for changed modules,
2. run `git diff --check` before staging,
3. use `check:state` when `feature_state_matrix.md`, status claims, evidence
   paths, or default behavior claims change,
4. use `check:docs` or `check_doc_references.py` when canonical routing docs
   or referenced canonical paths change,
5. use JSON-report variants when another agent or CI step will consume the
   result,
6. say exactly which heavier gates were not run when they are intentionally
   skipped.

## Change-Type Gate Map

| Change Type | Minimum Honest Bundle | Add When Applicable |
| --- | --- | --- |
| Docs-only, non-canonical wording | `git diff --check`; targeted reference check if links changed. | `check:docs` when canonical docs or referenced paths change. |
| Canonical docs, routing, governance | `python3 scripts/dev/check_doc_references.py`; `git diff --check`. | `npm --prefix scripts run check:state` if state/evidence/default claims changed. |
| Feature-state/status updates | `npm --prefix scripts run check:state`; targeted docs check; `git diff --check`. | Focused tests or harnesses proving the status claim. |
| Workflow/meta command docs | focused dev-workflow tests; `check:state` if matrix claims changed; `git diff --check`. | `check:changed:staged` or `check:changed:local` for current-slice integration. |
| General code refactor | targeted tests for changed modules; `git diff --check`. | `check:changed:staged` for staged-slice safety; project-health gates for structural splits. |
| Rulegen scoring, filtering, POS, or LP tuning | canonical benchmark sweep; quality gate; triage extraction; targeted tests. | Rulegen summaries for handoff; never update baselines without explicit rationale. |
| Rulegen LP onboarding without scoring change | LP profile/conformance checks; benchmark dataset/CLI tests; adapter/capability tests; `git diff --check`. | Pair audit cycle if the new or changed pair affects generated quality artifacts. |
| SRS scheduling, admission, helper publication, set execution, or runtime serving | SRS quality harness; summary when human-facing; targeted SRS/helper/runtime tests; `git diff --check`. | `check:state` when evidence/status changed; journey lanes when item-level behavior is the claim. |
| Semantic runtime or semantic pack lifecycle | focused semantic publication/runtime/helper tests; `check:state` if status/evidence changed; `git diff --check`. | Operator smoke or named-pack installer tests when install/publication files change. |
| Browser replacement runtime | focused extension contract tests for DOM scan, semantic gate, diagnostics, replacement spans, SRS gate; `git diff --check`. | Browser/manual smoke only when visual or live-page behavior is the product claim. |
| Helper/native-host routes | focused helper route, native-host install, startup logging, and extension transport/localization tests; `git diff --check`. | Windows parity audit when helper packaging, native messaging, or browser connection files change. |
| Packaging/platform parity | `check:windows:parity`; parity summary; focused build/workflow/parity tests; `git diff --check`. | `build:report` for full macOS/Windows build contract changes; `build:ci:report` for unsupported-host CI-safe behavior. |
| GitHub Pages workflow or docs-site deployment | `cd docs && bundle exec jekyll build --trace`; `git diff --check`. | Keep `docs/runbooks/github_pages_setup.md` aligned with workflow changes. |
| Chrome Web Store upload gate | `npm --prefix scripts run preflight:cws`; targeted CWS docs/runbook checks. | Manual reviewer sign-off for externally visible upload/release decisions. |
| Release/product ops | relevant build/installer/signing commands plus targeted tests and generated reports. | Lane 7 should define release certification and rollback proof before expansion resumes. |

## Canonical Rulegen Bundle

For changes touching rulegen scoring, candidate filtering, POS normalization, or
LP tuning, use the repo-local canonical loop:

```bash
python3 scripts/testing/rulegen_benchmark.py \
  --pairs en-es \
  --json-output docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --markdown-output docs/test_outputs/rulegen_benchmark_en_es_latest.md \
  --html-output docs/test_outputs/rulegen_benchmark_en_es_latest.html

python3 scripts/testing/rulegen_quality_gate.py \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --policy-json docs/test_inputs/rulegen_quality_policy.json \
  --baseline-json docs/test_outputs/baselines/rulegen_quality_baseline.json \
  --pos-probe-json docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json \
  --pos-inventory-json docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json

python3 scripts/testing/rulegen_benchmark_triage.py \
  --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json \
  --json-out docs/test_outputs/rulegen_benchmark_triage_latest.json \
  --markdown-out docs/test_outputs/rulegen_benchmark_triage_latest.md
```

Run targeted tests for changed modules after the benchmark loop. Use the
summary wrappers only for handoff readability; they do not replace the
benchmark/gate/triage commands above.

## Canonical SRS Bundle

For changes touching SRS scheduling, admission refresh, helper publication, set
execution, or runtime SRS serving, use:

```bash
python3 scripts/testing/srs_quality_harness.py \
  --json-out docs/test_outputs/srs_quality_latest.json

python3 scripts/testing/srs_quality_summary.py \
  --quality-json docs/test_outputs/srs_quality_latest.json \
  --markdown-out docs/test_outputs/srs_quality_summary_latest.md
```

Then run targeted tests for the changed SRS/helper/runtime modules. Keep the
current harness scope explicit: synthetic bootstrap/publication/runtime
diagnostics cover `en-ja` and `en-de`, the feedback-cycle scenario covers
`en-ja`, and due-aware runtime serving is verified through helper SRS metadata
plus extension gating while helper publication may remain broader than the due
subset.

## Artifact Freshness Rules

| Artifact Family | Producing Command | Freshness Rule |
| --- | --- | --- |
| `check_latest.json` | `check:report` or `check:report:ci` | Treat as latest repo-safety evidence only for the run that produced it. |
| `check_changed_latest.json` | `check:changed:report` | Branch-scope by default; use local/staged variants for narrow slices. |
| `feature_state_audit_latest.json` | `check:state` | Update when feature-state evidence/status/default claims change. |
| `doc_references_latest.json` | `check:docs:report` | Update when canonical reference evidence is needed. |
| `build_latest.json` | `build:report` | Full build report for desktop-capable hosts; historical unless rerun. |
| `build_ci_latest.json` | `build:ci:report` | CI-safe partial lane on unsupported hosts; do not cite as full desktop proof. |
| `windows_parity_latest.json` | `check:windows:parity` / strict variant | Parity evidence, not release certification. |
| `srs_quality_latest.json` | SRS quality harness | Required for SRS scheduling/admission/publication/runtime SRS changes. |
| rulegen benchmark/gate/triage latest files | canonical rulegen bundle | Required for rulegen scoring/filtering/POS/LP tuning changes. |

Generated artifacts are evidence snapshots. If policy, baselines, benchmark
labels, or grading semantics changed, record that the runs are not directly
comparable instead of flattening them into a simple pass/fail story.

## Handoff Artifact Refresh Policy

Refresh generated workflow artifacts only when the producing command is part of
the honest validation bundle for the slice:

| Handoff Need | Refresh | Do Not Refresh By Default |
| --- | --- | --- |
| Docs-only or routing checkpoint | `feature_state_audit_latest.json` only if `check:state` was run; `doc_references_latest.json` only if `check:docs:report` was explicitly run. | `check_latest.json`, `build_latest.json`, rulegen benchmark/gate/triage outputs, SRS quality outputs. |
| Workflow/meta checkpoint | the report artifact for the command actually used, such as `check_changed_latest.json` when `check:changed:report` was the gate. | Full `check:report` or `build:report` unless the workflow behavior itself changed and the report is needed as evidence. |
| SRS checkpoint | `srs_quality_latest.json` and summary when SRS scheduling/admission/publication/runtime SRS behavior changed. | SRS journey lanes unless item-level journey behavior is the claim. |
| Rulegen quality checkpoint | benchmark, quality-gate, and triage artifacts from the same run. | Baseline updates, unrelated pair artifacts, or summary-only refreshes without a matching source JSON run. |
| Packaging/platform checkpoint | Windows parity JSON/summary for parity work; build reports only for build contract changes or explicit build validation. | Signed installer/notarization artifacts unless release certification is the slice. |

Rules for summaries:

1. render Markdown summaries only from source JSON generated by the same
   validation pass or from an explicitly accepted historical artifact,
2. if a `*_latest` artifact is historical and not rerun, call it historical in
   the handoff,
3. do not regenerate heavyweight artifacts just to make timestamps look fresh,
4. never treat a summary as stronger evidence than its source JSON.

## CI And Hook Alignment

Current alignment:

1. `pre-push` mirrors `npm --prefix scripts run check`.
2. `pre-commit` handles whitespace/EOF, YAML/TOML, Ruff, BetterDiscord
   freshness for touched plugin inputs, changed project-health, and feature
   state audit when the matrix changes.
3. Ubuntu repo-safety uses `check:report:ci`, then gates via JSON so artifacts
   can upload before failure.
4. macOS and Windows hosted build jobs use `build:report`.
5. Windows hosted CI runs both full build reporting and strict Windows parity.
6. SRS quality has a dedicated hosted job.

Known limits:

1. hooks are optional until installed with `npm --prefix scripts run
   hooks:install`,
2. Ubuntu `build:ci:report` is a partial non-GUI proof lane,
3. Windows parity is required evidence but not release certification,
4. full rulegen and SRS gates are change-type gates, not mandatory for every
   docs-only edit.

## Lane 4 Next Work

Lane 4 now has the first-pass command map, handoff routing, and artifact
freshness policy needed before expansion resumes. The next stabilization work
should move to Lane 5 high-risk runtime seams unless a later validation command
change requires another Lane 4 update.
