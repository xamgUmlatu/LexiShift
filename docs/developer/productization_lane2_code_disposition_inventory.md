# Productization Lane 2 Code Disposition Inventory

Status: active inventory
Role: Planning / WIP
Last updated: 2026-05-15
Last verified: 2026-05-15 semantic-veto, semantic-LLM, semantic-shadow, and source-admission sub-registries; semantic family evidence expansion; sentence-veto support, generalization-bound, and prompt-runner splits; focused tests, project-health report, doc-reference check, state check, and diff hygiene
Purpose: identify redundant, dead, tentative, oversized, or weakly classified code paths before behavior cleanup or deletion
Source-of-truth: inventory only; runtime truth still lives in source code, tests, package scripts, generated health reports, and `feature_state_matrix.md`.
Related docs:
- `productization_closure_roadmap.md`
- `productization_lane2_semantic_testing_script_registry.md`
- `project_health_remediation_workstream.md`
- `project_integrity_stabilization_backlog.md`
- `project_integrity_stabilization_runbook.md`
- `../rulegen/semantic_rulegen_authority_map.md`
- `../../scripts/README.md`

## Slice Scope

Lane: Lane 2, redundant, dead, or tentative code.

Slice: first code/script disposition inventory.

This pass does not delete code, move modules, change runtime behavior, update
thresholds, or run paid semantic generation. It identifies the first cleanup
queues so code changes can happen in small reviewed slices.

Explicitly out of scope:

1. deleting semantic/rulegen experiment scripts,
2. changing SRS, rulegen, semantic-veto, or extension runtime behavior,
3. changing project-health thresholds or baselines,
4. treating a lack of exact filename references as proof that a script is dead,
5. refreshing generated semantic/rulegen/SRS evidence beyond the project-health
   report used for this inventory.

## Scan Method

Commands used during the inventory:

```bash
find core scripts apps -path apps/gui/dist -prune -o -path '*/__pycache__' -prune \
  -o -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.tsx' \
  -o -name '*.mjs' -o -name '*.cjs' \) -print | wc -l

find core scripts apps -path apps/gui/dist -prune -o -path '*/__pycache__' -prune \
  -o -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.tsx' \
  -o -name '*.mjs' -o -name '*.cjs' \) -print | xargs wc -l | sort -nr

npm --prefix scripts run health:project:report

find scripts/testing -maxdepth 1 -type f -name '*.py' -print | wc -l
find scripts/testing -maxdepth 1 -type f -name '*semantic*' -name '*.py' | wc -l

rg -n "<candidate script stem or path>" docs scripts core apps \
  --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'

rg -n "semantic_decision_|semantic_non_v10_|semantic_example_|semantic_phrase_|semantic_reverse_aux_|semantic_surface_|semantic_translation_|semantic_authorization_|semantic_wordnet_|semantic_wiktextract_" \
  docs scripts core apps --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'

rg -n "semantic_shadow_" \
  docs scripts core apps --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'

find scripts/testing -maxdepth 1 -type f -name 'semantic_veto_*.py' -print

rg -n "execute-live|OPENAI|Responses|responses|api_key|estimated_cost|cost|live" \
  scripts/testing/semantic_veto_*.py

find scripts/testing -maxdepth 1 -type f -name 'semantic_llm_*.py' -print

rg -n "execute-live|OPENAI|Responses|responses|api_key|estimated_cost|cost|live" \
  scripts/testing/semantic_llm_*.py

find scripts/testing -maxdepth 1 -type f -name 'semantic_shadow_*.py' -print

rg -n "semantic_shadow_" \
  docs scripts core apps --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'

find scripts/testing -maxdepth 1 -type f \( \
  -name 'semantic_source_*.py' -o \
  -name 'semantic_wordnet_*.py' -o \
  -name 'semantic_wiktextract_*.py' -o \
  -name 'semantic_example_*.py' -o \
  -name 'semantic_reverse_aux_*.py' -o \
  -name 'semantic_phrase_*.py' -o \
  -name 'semantic_surface_*.py' -o \
  -name 'semantic_translation_*.py' -o \
  -name 'semantic_authorization_*.py' \
\) -print | sort

rg -n "semantic_source_|semantic_wordnet_|semantic_wiktextract_|semantic_example_|semantic_reverse_aux_|semantic_phrase_|semantic_surface_|semantic_translation_|semantic_authorization_" \
  docs scripts core apps --glob '!docs/test_outputs/**' --glob '!apps/gui/dist/**'
```

Summary after the current Lane 2 splits:

| Metric | Count | Interpretation |
| --- | ---: | --- |
| Non-generated Python/JS/TS files under `core`, `scripts`, and `apps` | 1,042 | Excludes `apps/gui/dist`; broad enough for a Lane 2 inventory, not a full dead-code proof. |
| Files checked by current project-health report | 693 | The health checker scopes maintainability rules to selected source/script files. |
| Project-health advisory violations | 0 | The first structural splits retired the active violations without threshold changes. |
| Project-health near-limit warnings | 0 | Remaining warning debt was cleared by focused support-module splits. |
| `scripts/testing/*.py` files | 306 | Testing/analysis scripts are the largest code-disposition surface. |
| `scripts/testing/*semantic*.py` files | 255 | Semantic/routing/veto research scripts need a registry before any retirement pass. |
| `scripts/testing/*semantic_veto*.py` files | 131 | The semantic-veto research surface is dense enough to require family-level triage. |
| Testing scripts with no exact filename reference outside themselves | 88 | This is a triage signal only; many support modules are imported by module stem, not filename. |
| Tracked files under `apps/gui/dist` | 0 | Built GUI distribution output is excluded from Lane 2 source disposition. |

## Disposition Labels

Use these labels in follow-up Lane 2 passes:

| Label | Meaning |
| --- | --- |
| Keep | Current runtime, test, build, or documented workflow path. |
| Split | Current path with structural-health pressure; reduce size without changing behavior. |
| Registry | Dense script family needs a manifest of current/historical/experimental purpose before moves or deletion. |
| Quarantine | Useful experiment or one-off tool should stay available but stop looking like product authority. |
| Archive | Historical code artifact whose surviving value has moved to a maintained script/doc. |
| Delete candidate | No current caller, no tests, no docs, no generated-evidence role, and no needed historical value after exact import/reference checks. |
| Defer | Too risky or too unclear to classify in this slice. |

No `Delete candidate` is final in this first inventory. Deletion needs a later
exact import/reference search, generated-artifact review, and value-migration
note.

## Domain Disposition Inventory

| Area | Current Read | Initial Disposition | Next Action |
| --- | --- | --- | --- |
| `core/lexishift_core/` runtime modules | Core product behavior; no current project-health violations in the fresh report. Rulegen and SRS modules remain behavior-sensitive. | Keep / split only by seam | Do not make cleanup-only runtime edits without targeted tests. Rulegen scoring/filtering/POS changes still need the rulegen quality loop. |
| `core/tests/` | Largest individual files are test suites, especially helper/rulegen/semantic fixtures. They are verification assets, not cleanup leftovers. | Keep / split only when useful | Avoid test deletion. Split only when a specific test suite becomes hard to maintain or blocks targeted validation. |
| `scripts/dev/` | Current repo safety, build, style, state, docs, project-health, parity, and scaffolding entrypoints. | Keep | Treat `scripts/package.json` and `scripts/README.md` as the entrypoint routing layer. Review demos/probes separately before pruning. |
| `scripts/build/`, `scripts/data/`, `scripts/helper/` | Build, conversion, and helper entrypoints are mostly routed from package scripts, docs, GUI pack code, or feature-state evidence. Some pair-specific converter wrappers preserve user-facing commands around generic converters. | Keep / wrapper review | Do not collapse pair-specific wrappers until docs, GUI call sites, and migration notes agree on the generic command. |
| `scripts/testing/` canonical harnesses | Rulegen benchmark/gate/triage, SRS quality/journey, resource/POS audits, and summary renderers are active quality loops. | Keep | Preserve package-script entrypoints and default artifact paths. |
| `scripts/testing/` semantic/routing/veto research scripts | 255 semantic-named testing scripts, including many source, LLM, veto, routing, and shadow experiments. Several are current evidence producers; others are likely historical or one-off. | Registry / quarantine review | Build a semantic testing script registry before code moves. Classify by current harness, support library, active no-spend experiment, paid/LLM runner, historical evidence generator, or retire candidate. |
| `apps/chrome-extension/` | Current browser runtime and options UI. No current project-health warning in this pass. | Keep / split only by seam | Runtime splits require manifest-order and DOM scan/context tests before conclusion. |
| `apps/gui/src/` | Current desktop GUI source. No fresh project-health warning in this pass. | Keep | Avoid preventive churn unless GUI changes increase pressure again. |
| `apps/gui/dist/` | Local build output; `git ls-files apps/gui/dist` returns `0`. | Exclude | Keep generated distribution output out of source disposition. |
| `apps/betterdiscord-plugin/` | Source modules build the single-file `LexiShift.plugin.js`; build workflow verifies the bundle. | Keep | Do not treat the built plugin file as duplicate source unless the build/release contract changes. |

## Current Project-Health Queue

Fresh command:

```bash
npm --prefix scripts run health:project:report
```

Fresh artifact:

- `../test_outputs/project_health/project_health_latest.json`

Current advisory violations: none.

Current near-limit warnings: none.

## First Cleanup Queue

### L2-A: Current Health Snapshot Reconciliation

Goal:
- update current planning docs so they no longer claim the project-health
  advisory surface is zero-warning.

Progress:
- `L2-A.1` refreshed the current project-health report and identified `3`
  advisory violations plus `7` near-limit warnings.
- `L2-A.2` refreshed the report after the first sentence-veto support split;
  advisory violations dropped to `2`, with `7` near-limit warnings unchanged.
- `L2-A.3` refreshed the report after the generalization-bound config split;
  advisory violations dropped to `1`, with `8` near-limit warnings.
- `L2-A.4` refreshed the report after the prompt bakeoff safety/common split;
  advisory violations dropped to `0`, with `9` near-limit warnings.
- `L2-A.5` refreshed the report after the prompt bakeoff intake split; advisory
  violations remain `0`, and near-limit warnings dropped to `8`.
- `L2-A.6` refreshed the report after the warning-clearance splits; advisory
  violations remain `0`, and near-limit warnings dropped to `0`.

Validation:

```bash
npm --prefix scripts run health:project:report
python3 scripts/dev/check_doc_references.py
npm --prefix scripts run check:state
git diff --check
```

### L2-B: Semantic Testing Script Registry

Goal:
- stop treating 240 semantic-named testing scripts as one undifferentiated
  bucket.

Output:
- `productization_lane2_semantic_testing_script_registry.md`, a script-family
  registry that classifies semantic scripts as one of:
  current harness, support library, active no-spend experiment, paid/LLM runner,
  historical evidence generator, generated-output helper, or retire candidate.

Start with:

1. the former 3 project-health violation files,
2. the former semantic testing-script warning files,
3. scripts referenced from `../rulegen/semantic_rulegen_authority_map.md`,
4. scripts referenced from `../developer/feature_state_matrix.md`,
5. scripts listed in `../../scripts/README.md` and `scripts/package.json`.

Progress:

- `L2-B.1` added `productization_lane2_semantic_testing_script_registry.md` as
  the v0 family registry and classified the current project-health hotlist plus
  the semantic scripts cited by the current denominator/expansion path.

### L2-C: `semantic_routing_sentence_veto_support.py` Split Plan

Goal:
- split the largest current violation only after its import surface is
  understood.

Current observed seams:

1. dataset loading,
2. core sentence-veto report construction,
3. sweep report construction,
4. ladder simulation and ranking,
5. weak-active overlay simulation,
6. phrase-leak probe reporting,
7. focus-case payload helpers.

Boundary:
- preserve the existing module import surface at first, because many scripts and
  tests import it directly.

Progress:

- `L2-C.1` split the old `1675`-line support module into:
  - `semantic_routing_sentence_veto_support.py` (`82`-line compatibility facade),
  - `semantic_routing_sentence_veto_common.py` (`451` lines),
  - `semantic_routing_sentence_veto_sweep_support.py` (`222` lines),
  - `semantic_routing_sentence_veto_ladder_support.py` (`277` lines),
  - `semantic_routing_sentence_veto_overlay_support.py` (`768` lines).
- The existing import surface remains available from
  `semantic_routing_sentence_veto_support.py`.
- Focused validation passed:
  - `python3 -m py_compile` for the split modules,
  - focused sentence-veto pytest bundle (`8 passed`),
  - `npm --prefix scripts run health:project:report`.
- Project-health no longer lists `semantic_routing_sentence_veto_support.py` as
  an advisory violation.

### L2-D: Generalization-Bound Config Split

Goal:
- clear the smaller no-spend generalization-bound violation before touching the
  paid/LLM prompt runner.

Progress:

- `L2-D.1` moved fixed-shadow and metric-direction constants from
  `semantic_routing_generalization_bound_en_es.py` into
  `semantic_routing_generalization_bound_configs.py`.
- `semantic_routing_generalization_bound_en_es.py` dropped below the hard line
  cap after the config extraction, then below near-limit warning pressure after
  the confidence-corridor extraction.
- `L2-D.2` moved confidence-corridor assembly into
  `semantic_routing_generalization_bound_corridor.py`.
- Focused validation passed:
  - `python3 -m py_compile` for the touched modules,
  - targeted Ruff for the touched modules,
  - `core/tests/dev/test_semantic_routing_generalization_bound_en_es.py`
    (`3 passed`),
  - `npm --prefix scripts run health:project:report`.

### L2-E: Prompt/LLM Runner Safety Split Plan

Goal:
- reduce `semantic_llm_prompt_bakeoff_en_es.py` without weakening spend-safety,
  replay, journal, or artifact guarantees.

Candidate seams:

1. argument and path defaults,
2. request-row selection and bundle writing,
3. live journal/event writing,
4. response payload extraction,
5. replay client,
6. safety report and guard assertions.

Boundary:
- do not run paid live requests during cleanup validation.

Progress:
- `L2-E.1` extracted common path/default/helper utilities into
  `semantic_llm_prompt_bakeoff_common.py`.
- `L2-E.2` extracted append-only live-journal and resume-event handling into
  `semantic_llm_prompt_bakeoff_journal.py`.
- `L2-E.3` extracted no-spend safety reporting, guard assertions, API client
  construction, and replay response clients into
  `semantic_llm_prompt_bakeoff_safety.py`.
- `L2-E.4` extracted model-output intake validation into
  `semantic_llm_prompt_bakeoff_intake.py`.
- `semantic_llm_prompt_bakeoff_en_es.py` now preserves the existing CLI and
  compatibility import surface while staying below near-limit warning pressure
  (`789 / 900` lines).
- Focused validation passed:
  - `python3 -m py_compile` for the touched prompt-bakeoff modules,
  - targeted Ruff for the touched prompt-bakeoff modules,
  - prompt-runner/preflight/downstream replay tests (`29 passed`),
  - `npm --prefix scripts run health:project:report`.

### L2-F: Runtime Near-Limit Split Candidate

Goal:
- keep `apps/chrome-extension/content/runtime/dom_scan/semantic_context.js`
  below warning pressure before future DOM/semantic work lands.

Candidate seams:

1. DOM node predicates and filters,
2. context collection and container buffering,
3. clipping and word-boundary helpers,
4. exported resolver/cache facade.

Boundary:
- this is runtime code; run DOM scan/runtime contract tests before any split.

Progress:
- `L2-F.1` extracted semantic-context sentence clipping and word-budget helpers
  into `content/runtime/dom_scan/semantic_context_support.js`.
- `content/runtime/dom_scan/semantic_context.js` now stays below near-limit
  pressure (`384 / 500` lines), and the manifest loads the support helper before
  the resolver module.
- Focused validation passed:
  - `node --check` for both semantic-context modules,
  - extension text-node context contract tests,
  - manifest-order architecture test,
  - `npm --prefix scripts run health:project:report`.

### L2-G: Semantic Script Warning-Clearance Splits

Goal:
- clear changed-file near-limit warning debt without changing scorer, source,
  or admission behavior.

Progress:
- extracted focused support helpers from:
  - `semantic_source_margin_policy_sweep_en_es.py`,
  - `semantic_non_v10_wave_builder_en_es.py`,
  - `semantic_llm_prototype_admission_probe_en_es.py`,
  - `semantic_source_failure_class_mining_en_es.py`,
  - `semantic_routing_sentence_veto_reporting.py`,
  - `semantic_wordnet_example_frame_batch_en_es.py`.
- fixed the sentence-veto support facade to re-export
  `_resolve_sentence_veto_phrase_guard_pos_tags`, preserving the private import
  surface used by prototype admission and downstream harnesses.
- focused tests for each touched script family passed.

### L2-H: Semantic Script Evidence Expansion

Goal:
- turn the semantic testing-script registry from a project-health hotlist into
  an evidence-backed disposition ledger before any quarantine/archive/delete
  action.

Progress:
- expanded the registry across the `semantic_decision_*`,
  `semantic_non_v10_*`, `semantic_example_*`, `semantic_phrase_*`,
  `semantic_reverse_aux_*`, `semantic_surface_*`, `semantic_translation_*`,
  `semantic_authorization_*`, `semantic_wordnet_*`,
  `semantic_wiktextract_*`, and `semantic_shadow_*` families.
- classified the expanded families by docs, tests, script importers, and
  generated-artifact ownership signals.
- found no safe `Delete candidate` in this pass.
- identified the next cleanup queue as sub-registry work for:
  1. `semantic_veto_*`,
  2. `semantic_llm_*`,
  3. `semantic_shadow_*`.

Current disposition:
- keep all families reviewed in `L2-H` until a family-specific sub-registry
  proves that its docs, tests, importers, generated artifacts, and historical
  evidence value have been migrated or intentionally retired.

### L2-I: Semantic-Veto Sub-Registry

Goal:
- stop treating the `131` `semantic_veto_*` scripts as one cleanup target.

Progress:
- classified `semantic_veto_*` into current SRS/denominator/registry tooling,
  active-only operator tooling, paid/live generation runners, product-quality
  research, sampling/review/repair research, and comparator/diagnostic lanes.
- explicitly separated:
  - current no-spend expansion support:
    `srs_bridge_case_mix`, `system_registry`, `denominator_zipf_expansion`,
  - current operator/checkpoint tooling:
    `active_only`,
  - paid-spend safety surfaces:
    `evidence_gap_generation`, `llm_pilot_threshold`,
  - comparator/diagnostic lanes:
    `difficulty_stratification`, `formula_shape_weight`, `full_family`,
    `heuristic_translation`, `wave7_bound_gap`, `veto_only`,
    `trusted_seed_performance`.
- found no safe delete candidate in the semantic-veto family.

Current disposition:
- keep all semantic-veto subfamilies for now.
- possible future quarantine is limited to comparator/diagnostic lanes after the
  system registry, owning docs, focused tests, and generated artifacts agree
  that the lane is superseded.
- never move paid/live runner helpers unless replay mode, cost ceilings,
  `--execute-live`, raw response bundles, and append-only journals remain
  covered.

### L2-J: Semantic-LLM Sub-Registry

Goal:
- classify the `31` `semantic_llm_*` scripts without weakening live-spend
  safety or no-spend replay validation.

Progress:
- classified the family into:
  - `prompt_runner_safety`,
  - `prototype_admission`,
  - `example_frame_generation`,
  - `reviewed_source_insertion`.
- separated paid/live surfaces from no-spend research/support surfaces.
- found no safe delete candidate in the semantic-LLM family.

Current disposition:
- keep `prompt_runner_safety` and `example_frame_generation` with explicit
  paid-spend safety handling.
- keep `prototype_admission` and `reviewed_source_insertion` as active no-spend
  research/support, not runtime policy.
- do not collapse preflight, cost-estimate, replay, response-normalization, or
  journal helpers unless focused no-spend tests keep live spend opt-in.

### L2-K: Semantic-Shadow Sub-Registry

Goal:
- classify the `23` `semantic_shadow_*` scripts without mistaking research
  harnesses for runtime product authority.

Progress:
- classified the family into:
  - `inventory_policy_review`,
  - `gold_veto_seed_proxy`,
  - `sweep_candidate_sources`,
  - `experiment_matrix_compare`.
- found no safe delete candidate in the semantic-shadow family.
- recorded a test gap: most shadow scripts are documented and
  artifact-producing, but only the experiment-compare support helper has direct
  focused script-level coverage in this scan.

Current disposition:
- keep all semantic-shadow subfamilies as research/generated-evidence lanes.
- add targeted tests before any behavioral refactor or file move in this family.
- do not use this registry to promote shadow research outputs into runtime
  product claims.

### L2-L: Source-Admission And Named Adapter Sub-Registry

Goal:
- classify the remaining lower-density semantic source/admission scripts before
  any quarantine/archive/delete decision.

Progress:
- classified `33` scripts across `semantic_source_*`, `semantic_wordnet_*`,
  `semantic_wiktextract_*`, `semantic_example_*`, `semantic_reverse_aux_*`,
  `semantic_phrase_*`, `semantic_surface_*`, `semantic_translation_*`, and
  `semantic_authorization_*`.
- grouped the family into:
  - `source_admission_policy`,
  - `source_failure_gap`,
  - `source_class_probes`,
  - `example_frame_core`,
  - `wordnet_adapter_evidence`,
  - `wiktextract_adapter_evidence`,
  - `reverse_aux_fixture`,
  - `phrase_control_support`.
- found no safe delete candidate in this source/admission pass.

Current disposition:
- keep source/admission and named adapter scripts.
- treat example-frame, WordNet, reverse-aux, and phrase-control helpers as
  shared APIs because multiple scripts import them by module stem.
- future archive/quarantine work should start from generated-artifact ownership,
  not filename age.

## Stop Conditions

Stop and ask for direction if a follow-up pass finds:

1. a script appears unused but owns the only reproducer for an accepted artifact,
2. a cleanup would change rulegen scoring, POS normalization, SRS behavior, or
   semantic runtime policy,
3. a project-health split would require threshold or baseline changes,
4. a paid/LLM path cannot be validated without live requests,
5. a runtime split lacks targeted tests or load-order coverage.

## Immediate Recommendation

`L2-B` through `L2-L` are complete for the current project-health hotlist, first
evidence-expansion pass, semantic-veto sub-registry, semantic-LLM sub-registry,
semantic-shadow sub-registry, and source/admission sub-registry. There are no
current project-health advisory violations or near-limit warnings.

The first semantic-script classification layer is now complete. Continue Lane 2
only if a specific quarantine/archive decision is desired, starting with
generated-artifact ownership for the chosen family. Do not delete
artifact-producing research scripts without exact reference, importer, test, and
generated-evidence review.
