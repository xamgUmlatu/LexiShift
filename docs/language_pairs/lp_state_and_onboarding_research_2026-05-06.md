# Language Pair State And Onboarding Research

Status: research snapshot
Role: Mixed
Last updated: 2026-05-06
Last verified: 2026-05-06 against local code, docs, generated artifacts, and non-mutating research commands
Source-of-truth: snapshot only; executable truth remains in code, tests, and regenerated artifacts

## Scope

This report covers:

- current language-pair support across capabilities, rulegen adapters, benchmark artifacts, SRS harnesses, local resources, and semantic-publication readiness
- mechanisms available for onboarding a new rulegen LP
- mechanisms available for bringing an existing LP closer to parity
- current contradictions and evidence gaps that should be fixed before making stronger status claims

This report does not attempt to optimize any LP or refresh canonical benchmark artifacts. Temporary quality gates were written under `/tmp` so the repo artifacts were not overwritten.

The worktree was already dirty on `codex/veto-data-sources-exp` when this research started. This file is intentionally standalone.

## Executive Read

The current system has three different LP maturity layers, and they should not be collapsed:

1. Capability/SRS visibility:
- Known pairs in `core/lexishift_core/helper/lp_capabilities.py`: `en-ja`, `ja-ja`, `en-en`, `de-en`, `en-de`, `en-es`, `es-en`, `es-es`, `de-de`, `en-zh`.
- SRS-selectable pairs: all of those except `en-zh`.
- Rulegen-supported pairs: `en-ja`, `de-en`, `en-de`, `en-es`, `es-en`.

2. Rulegen evidence:
- Machine-readable rulegen LP profiles exist only for `en-es` and `en-de`.
- Benchmark case files exist for `en-es`, `en-de`, `en-ja`, and `es-en`.
- No `de-en` benchmark case file exists yet, even though the code now has a `de-en` adapter.
- `check:lp-profiles` and `check:lp-conformance` pass, but they validate only the two profiled pairs.

3. SRS/runtime evidence:
- Synthetic SRS quality harness currently covers `en-ja` and `en-de`.
- SRS journey artifacts cover `en-ja` and `en-es` only.
- Local frequency audit currently shows valid local EN/ES/JA frequency DBs, invalid local German frequency DB, and missing Chinese frequency DB.

The practical conclusion:

- `en-es` is the richest and most researched LP, but current latest rulegen artifacts are not production-green.
- `en-de` has the strongest non-`en-es` advisory path, especially in a Kaikki/Wiktionary experiment, but the canonical lane and local German frequency resource are not parity-clean.
- `en-ja` remains the SRS/reference stability baseline, but not the richest rulegen/semantic pair.
- `es-en` is implemented baseline, but lacks a current dedicated profile/lane.
- `de-en` is code-enabled but not benchmark-onboarded.
- Monolingual LPs are mostly resource-visible, not rulegen-ready.

## Verification Commands Run

Non-mutating checks:

```bash
npm --prefix scripts run check:lp-profiles
npm --prefix scripts run check:lp-conformance
python3 scripts/testing/rulegen_quality_gate.py --benchmark-json docs/test_outputs/rulegen_benchmark_en_es_latest.json --policy-json docs/test_inputs/rulegen_quality_policy.json --baseline-json docs/test_outputs/baselines/rulegen_quality_baseline.json --pos-probe-json docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json --pos-inventory-json docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json --pair-scope en-es --json-out /tmp/lexishift_rulegen_gate_en_es_research.json
python3 scripts/testing/rulegen_quality_gate.py --benchmark-json docs/test_outputs/rulegen_benchmark_en_de_latest.json --policy-json docs/test_inputs/rulegen_quality_policy.json --baseline-json docs/test_outputs/baselines/rulegen_quality_baseline.json --pos-probe-json docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json --pos-inventory-json docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json --pair-scope en-de --json-out /tmp/lexishift_rulegen_gate_en_de_research.json
python3 scripts/testing/rulegen_quality_gate.py --benchmark-json docs/test_outputs/rulegen_benchmark_en_de_kaikki_register_latest.json --policy-json docs/test_inputs/rulegen_quality_policy.json --baseline-json docs/test_outputs/baselines/rulegen_quality_baseline.json --pos-probe-json docs/test_outputs/phase6_pos_inventory/phase6_pos_probe_2026-02-23_final.json --pos-inventory-json docs/test_outputs/phase6_pos_inventory/phase6_pos_inventory_2026-02-23_final.json --pair-scope en-de --json-out /tmp/lexishift_rulegen_gate_en_de_kaikki_research.json
python3 scripts/testing/resource_integrity_audit.py --json-out /tmp/lexishift_resource_integrity_research.json
```

Observed check results:

- `check:lp-profiles`: PASS, 2 profiles.
- `check:lp-conformance`: PASS, 2 profiles.
- Current gate on `docs/test_outputs/rulegen_benchmark_en_es_latest.json`: FAIL.
- Current gate on `docs/test_outputs/rulegen_benchmark_en_de_latest.json`: FAIL.
- Current gate on `docs/test_outputs/rulegen_benchmark_en_de_kaikki_register_latest.json`: FAIL from saturation, despite satisfying the quality floor.
- Local frequency audit: exit 1 with 3 errors, all tied to invalid German frequency DB or missing Chinese frequency DB.

## Current LP Inventory

| LP | Capability state | Rulegen state | Benchmark / quality evidence | SRS / resource state | Current read |
| --- | --- | --- | --- | --- | --- |
| `en-ja` | SRS-selectable, `rulegen_mode=en_ja`, requires JMDict for seed and rulegen | Adapter and pair module exist; semantic locator is `jmdict_entry`; no machine-readable LP profile | Case file has 17 cases; latest all-pairs 2026-03-21 read: top1 `94.12%`, top3 `100%`; quality floor satisfied in all-pairs artifact | SRS journey core/edge/real/installed artifacts exist; local JA frequency DB is valid but unlinked in settings audit | Stable baseline/reference pair, not current richest rulegen or semantic pair |
| `en-es` | SRS-selectable, `rulegen_mode=en_es`, requires translation dictionary; semantic locators `sense_provenance`, `translation_gloss`; competition publication mode `emitted_rule_siblings` | Richest adapter; reverse-check, Kaikki/Wiktionary policy, compiled resources, semantic/shadow research scaffolding | Current latest benchmark has 73 cases, top1 `52.05%`, top3 `72.60%`, forbidden top1 `10.96%`; current gate fails floor and delta budgets; triage has 36 FAIL/REVIEW items | SRS journey core/edge/real/installed artifacts exist; local ES frequency DB is valid but unlinked; FreeDict ES->EN coverage is known inadequate for production publication alone | Richest research and runtime PoC pair, but not quality-green; semantic readiness is narrow and should not be treated as LP parity |
| `en-de` | SRS-selectable, `rulegen_mode=en_de`, requires translation dictionary; semantic locators `sense_provenance`, `translation_gloss` | Adapter and profile exist; source-frequency, reverse-check, Kaikki policy, same-sense and compiled/prepared support are present in code/profile | Current canonical latest has 58 cases, top1 `65.52%`, top3 `93.10%`, forbidden top1 `1.72%`; current gate fails top1 floor. Kaikki register experiment has top1 `93.10%`, top3 `96.55%`, but fails saturation with only 2 runs and 1 unique metric vector | Synthetic SRS quality harness covers `en-de`; local German frequency DB is invalid, so real initialize/refresh parity is blocked locally | Best non-`en-es` quality candidate, but source-lane promotion and German frequency repair are blockers |
| `es-en` | SRS-selectable, `rulegen_mode=es_en`, requires translation dictionary; semantic locator `translation_gloss` | Baseline adapter exists; reverse-check code path exists in `es_en.py`; no machine-readable LP profile | Case file has 16 cases. Latest all-pairs 2026-03-21 read: top1 `75%`, top3 `75%`, quality floor failed. No current dedicated latest/profile lane | Uses EN frequency; local EN frequency DB is valid but unlinked. No SRS journey lane | Implemented baseline, not parity. Needs a profile and dedicated advisory lane before tuning claims |
| `de-en` | SRS-selectable, `rulegen_mode=de_en`, requires translation dictionary; semantic locator `translation_gloss` | Adapter and pair module now exist | No benchmark case file, no machine-readable LP profile, no dedicated benchmark/gate/triage lane | Uses EN frequency, which is locally valid but unlinked; forward pack is `freedict-en-de`; reverse pack defaults to `freedict-de-en` | Code-enabled but not benchmark-onboarded. Next milestone is benchmark seed/profile, not basic enablement |
| `en-en` | SRS-selectable, no rulegen mode | Monolingual source data exists in catalog (`wordnet-en`, `moby-en`), but adapter missing | No benchmark case file/profile | Uses EN frequency, locally valid but unlinked | Resource-visible but pipeline-missing |
| `ja-ja` | SRS-selectable, no rulegen mode | JP WordNet sources exist in catalog, adapter missing | No benchmark case file/profile | Uses JA frequency, locally valid but unlinked | Resource-visible but pipeline-missing |
| `es-es` | SRS-selectable, no rulegen mode | Spanish monolingual source still TBD; adapter missing | No benchmark case file/profile | Uses ES frequency, locally valid but unlinked; stopwords usually missing | Not onboarded |
| `de-de` | SRS-selectable, no rulegen mode, fallback frequency is `freq-de-default.sqlite` | German monolingual sources exist in catalog (`odenet-de`, `openthesaurus-de`), adapter missing | No benchmark case file/profile | Local German frequency DB is invalid | Blocked by German frequency plus monolingual adapter |
| `en-zh` | Known but not SRS-selectable, no rulegen mode | CC-CEDICT source registered, adapter missing | No benchmark case file/profile | Local Chinese frequency DB missing | Not active |

## Rulegen Artifact Readout

Current or relevant saved benchmark reads:

| Artifact | Generated at | Pair | Cases | Runs | Best label summary | Top1 | Top3 | Forbidden top1 | Forbidden any | Gate read |
| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| `docs/test_outputs/rulegen_benchmark_en_es_latest.json` | 2026-04-23 | `en-es` | 73 | 144 | `rev=on`, `var=on`, `kdem=off`, `kprov=off` | `52.05%` | `72.60%` | `10.96%` | `8.22%` | current temp gate FAIL |
| `docs/test_outputs/rulegen_benchmark_en_es_reverse_latest.json` | 2026-03-13 | `en-es` | 38 | 32 | reverse-focused, `rev=on`, `mr=1` | `97.37%` | `97.37%` | `2.63%` | `2.63%` | saved gate FAIL from delta budget |
| `docs/test_outputs/rulegen_benchmark_en_de_latest.json` | 2026-04-03 | `en-de` | 58 | 32 | canonical FreeDict lane, `rev=off`, `var=off` | `65.52%` | `93.10%` | `1.72%` | `24.14%` | current temp gate FAIL |
| `docs/test_outputs/rulegen_benchmark_en_de_kaikki_register_latest.json` | 2026-04-03 | `en-de` | 58 | 2 | Kaikki/register experiment, source-frequency on | `93.10%` | `96.55%` | `1.72%` | `1.72%` | temp gate FAIL from saturation only |
| `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json` | 2026-03-20 | `en-ja` | 17 | 16 | all-pairs advisory | `94.12%` | `100%` | `0%` | `0%` | quality floor OK |
| `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json` | 2026-03-20 | `en-de` | 16 | 16 | all-pairs advisory | `75%` | `100%` | `0%` | `0%` | quality floor failed |
| `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json` | 2026-03-20 | `en-es` | 38 | 16 | all-pairs advisory | `78.95%` | `78.95%` | `21.05%` | `13.16%` | quality floor failed |
| `docs/test_outputs/rulegen_benchmark_all_pairs_2026-03-21.json` | 2026-03-20 | `es-en` | 16 | 16 | all-pairs advisory | `75%` | `75%` | `0%` | `0%` | quality floor failed |

Important artifact drift:

- `docs/test_outputs/rulegen_quality_gate_latest.json` is older than `docs/test_outputs/rulegen_benchmark_en_es_latest.json` and records a different metric state (`top1_accuracy=0.9062` in the gate details versus current benchmark top1 `0.5205`).
- `docs/test_outputs/rulegen_quality_gate_en_de_latest.json` is also older than the current benchmark artifact mtime, but its failure result still matches the current temp gate direction.
- Treat the generated benchmark JSON plus a freshly run gate as the current evidence pair. Do not trust a `*_latest` gate file just because the `benchmark_json` path inside it points at a newer overwritten artifact.

## Triage Snapshot

Current triage examples:

- `en-es`: 36 FAIL/REVIEW items in `docs/test_outputs/rulegen_benchmark_triage_latest.json`. Examples include `madre -> bed` as forbidden top1, plus `planta`, `derecho`, `cuadro`, `cargo`, `masa`, `caso`, `parte`, `vista`, `movimiento`, `area`, and `estilo`.
- `en-de`: 21 FAIL/REVIEW items in `docs/test_outputs/rulegen_benchmark_triage_en_de_latest.json`. Examples include `Haus`, `Schule`, `Weg`, `Zeit`, `Sprache`, `Fenster`, `Tag`, `Stunde`, `Kopf`, `Gesicht`, `Ohr`, and `Fuss`.
- `en-es` reverse-focused lane: 1 triage item, `cuadro`, in `docs/test_outputs/rulegen_benchmark_triage_en_es_reverse_latest.json`.

The triage state confirms that `en-es` and `en-de` remaining work is not just missing wrapper commands. They still have concrete lexical/source/ranking failures.

## SRS And Runtime Readout

Current SRS harness state:

- `docs/test_outputs/srs_quality_latest.json` reports `WARN`, pass `15`, warn `1`, fail `0`.
- Synthetic pairs in that harness are `en-ja` and `en-de`.
- The lone warning is due-aware publication mismatch: published ruleset covers admitted items beyond the due subset.
- SRS journey artifacts exist for `en-ja` and `en-es`, each with core, edge, real-publication, and installed-resource lanes.
- `en-de` does not yet have the same SRS journey family; it appears only in the synthetic SRS quality harness.
- `es-en` and `de-en` do not have comparable journey evidence.

Local frequency resource audit:

- Valid but unlinked in settings:
  - `freq-ja-bccwj.sqlite`, rows `185136`
  - `freq-en-coca.sqlite`, rows `6100`
  - `freq-es-cde.sqlite`, rows `2000`
- Invalid:
  - `freq-de-default.sqlite`; this blocks local real `en-de` and `de-de` SRS use.
- Missing:
  - `freq-zh-default.sqlite`; this matches `en-zh` not being active/selectable.

Settings had no frequency pack links, so local runtime may still resolve via fallback filenames, but the audit flags that the settings layer is not explicitly linked.

## Semantic Publication Readout

Semantic-publication capability is not LP parity.

Current capability registry says:

- `en-es`: locators `sense_provenance`, `translation_gloss`; competition mode `emitted_rule_siblings`; policy `en_es_emitted_rule_siblings_v1`.
- `en-de`: locators `sense_provenance`, `translation_gloss`; no competition publication.
- `de-en` and `es-en`: locator `translation_gloss`; no competition publication.
- `en-ja`: locator `jmdict_entry`; no competition publication.

Feature-state docs say all current rulegen LPs can emit stable active-pointer ids, but only `en-es` has a narrow ready-status publication PoC. Even there, the PoC is limited to emitted siblings reachable from helper initialize/refresh context and does not equal broad shadow mining, phrase-preemption publication, sentence-veto readiness, or cross-LP runtime parity.

## Onboarding Mechanisms That Exist

The repo has a real onboarding system, but it is currently stronger for `en-es` / `en-de` than for the rest of the supported pairs.

Key machinery:

- Capability registry: `core/lexishift_core/helper/lp_capabilities.py`
  - declares pair, `rulegen_mode`, default frequency DB, SRS selectability, dictionary requirements, and semantic-publication locator capability.
- Pair resource resolution: `core/lexishift_core/helper/pair_resources.py`
  - resolves frequency, JMDict, forward translation pack, reverse translation pack, and stopwords using pair capability and default pack ids.
- Rulegen adapter dispatch: `core/lexishift_core/rulegen/adapters.py`
  - maps capability `rulegen_mode` into pair-specific result adapters.
- Pair modules: `core/lexishift_core/rulegen/pairs/`
  - currently includes `en_ja.py`, `de_en.py`, `en_de.py`, `en_es.py`, and `es_en.py`.
- LP profile surface: `docs/test_inputs/rulegen_lp_profiles/`
  - currently only `en_es.json` and `en_de.json`.
- LP profile checks:
  - `npm --prefix scripts run check:lp-profiles`
  - `npm --prefix scripts run check:lp-conformance`
- Scaffold command:
  - `npm --prefix scripts run scaffold:rulegen:lp -- --pair <lp> --translation-family <family> --translation-pack-id <pack_id>`
  - optional flags: `--reverse-family`, `--reverse-pack-id`, `--with-roadmap`, `--with-code-stubs`, `--with-integration-handoff`, `--with-benchmark-preset-starter`.
- Benchmark/gate/triage harness:
  - canonical rulegen commands from `AGENTS.md`
  - `python3 scripts/testing/rulegen_pair_audit_cycle.py --pairs <pair>`
  - pair-specific wrapper exists for `en-de`: `npm --prefix scripts run quality:rulegen:en-de`
  - reverse-specific `en-es` wrapper: `npm --prefix scripts run quality:rulegen:reverse:en-es`
- SRS quality harness:
  - `python3 scripts/testing/srs_quality_harness.py --json-out docs/test_outputs/srs_quality_latest.json`
  - summary renderer: `python3 scripts/testing/srs_quality_summary.py ...`
- Resource inventory and recovery docs:
  - `docs/language_pairs/lp_resource_requirements.md`
  - `docs/language_pairs/lp_data_inventory_matrix.md`
  - `docs/language_pairs/resource_recovery_playbook.md`
  - `docs/language_pairs/data_source_licensing_and_distribution.md`
- Data pack catalog:
  - `apps/gui/src/language_packs_catalog.py`
  - includes translation, synonym, embedding, and frequency pack definitions.

## Golden Path For A New LP

Use this as the practical runbook for a new translation LP.

1. Source audit
- Pick directional pair key, e.g. `fr-en` or `en-fr`.
- Confirm forward source pack, reverse source pack decision, frequency DB, stopwords, and licensing/distribution posture.
- Probe source record shape before writing pair logic: headword orientation, gloss ordering, POS fields, qualifiers, punctuation, forms, and metadata families.
- Record in `docs/language_pairs/lp_resource_requirements.md` and, if needed, a pair roadmap under `docs/language_pairs/`.

2. Scaffold the rulegen onboarding package

```bash
npm --prefix scripts run scaffold:rulegen:lp -- \
  --pair <source-target> \
  --translation-family <family> \
  --translation-pack-id <forward-pack-id> \
  --reverse-family <family> \
  --reverse-pack-id <reverse-pack-id> \
  --with-roadmap \
  --with-integration-handoff \
  --with-benchmark-preset-starter
```

Use `--with-code-stubs` only when you want starter pair/test files. The scaffold creates the profile and case-file seed, but it does not complete central registration.

3. Register central capability and resources
- Add `PairCapability` in `lp_capabilities.py`.
- Add default frequency DB and dictionary requirements.
- Add or verify fallback pack ids and filenames in capability/resource resolution.
- Add GUI/data-pack catalog entries if the pack is not already known.

4. Implement minimal rulegen adapter
- Add `core/lexishift_core/rulegen/pairs/<pair>.py`.
- Register imports and dispatch in `adapters.py`.
- Start with baseline candidate extraction, normalization, ordering, POS passthrough, variants, and caps.
- Do not port `en-es` advanced scoring until the new pair has observable failures that justify it.

5. Add benchmark seed and wrapper
- Add `docs/test_inputs/rulegen_benchmark_cases/<pair>.json`.
- Add a preset in `docs/test_inputs/rulegen_benchmark_presets.json`.
- Add package wrapper if this pair is meant to have a named advisory lane.
- Run benchmark, gate, and triage into pair-specific latest artifacts.

6. Add targeted tests
- Capability/resource tests.
- Adapter dispatch tests.
- Pair-specific normalization/loader tests.
- Rulegen output smoke tests.
- If SRS is in scope, initialize/refresh/publish/diagnostics tests.

7. Promote only with evidence
- Stage names should mean something:
  - scaffolded: capability, pair module, adapter, profile/cases seeded.
  - benchmarkable: pair-specific benchmark/gate/triage refresh works.
  - source-shaped: source normalization and probe evidence are meaningful.
  - sweepable: live mechanisms exist and sweep knobs are not mostly inert.
  - prepared: compiled/prepared path exists and matches live behavior.
  - promotable: repeatable advisory lane, justified defaults, documented gaps.

## Bringing Existing LPs To Parity

Parity should be split by target level:

- SRS-selectable parity: capability, frequency, pair-scoped initialize/refresh, publish, diagnostics.
- Rulegen baseline parity: adapter, pair module, case file, benchmark, gate, triage, targeted tests.
- Advisory-lane parity: named preset, wrapper commands, latest artifacts, summary commands, triage-to-case promotion workflow.
- Prepared/sweep parity: compiled resources, prepared score/select reuse, live-vs-compiled equivalence, non-inert sweep matrix.
- Semantic-publication parity: stable active pointers, semantic inventory sidecar, ready competition sets, runtime eligibility, sentence-veto quality evidence.

Current pair-specific parity work:

1. `de-en`
- Add machine-readable LP profile.
- Add `docs/test_inputs/rulegen_benchmark_cases/de_en.json`.
- Add `de_en_canonical_matrix` preset and wrapper commands.
- Run benchmark/gate/triage once as an advisory lane.
- Update docs that still say `de-en` adapter is pending.
- Do not start reverse-check tuning before the first forward benchmark exists.

2. `en-de`
- Repair or rebuild local `freq-de-default.sqlite`; this blocks real SRS parity.
- Decide whether the Kaikki/Wiktionary register lane is a source-lane candidate or only an experiment.
- Expand or stabilize the sweep to avoid saturation-only evidence.
- Reconcile docs that still describe the pair as smaller/less wired than current code.
- Only then consider promoting the current stronger lane.

3. `es-en`
- Add machine-readable LP profile.
- Add dedicated latest benchmark/gate/triage lane.
- Run current quality loop and extract concrete failures.
- Decide whether reverse-check and Kaikki-derived `wiktionary-es-en` should remain `en-es` reverse-support only or become part of an `es-en` forward source decision.

4. `en-ja`
- Add a machine-readable LP profile if profile coverage is meant to include all supported rulegen pairs.
- Preserve it as SRS/reference baseline.
- Do not force reverse-check/provenance mechanisms onto it just for superficial parity.

5. Monolingual pairs: `en-en`, `ja-ja`, `de-de`, `es-es`
- Treat these as a separate rulegen family, not just another translation pair.
- First monolingual proof target should probably be `en-en` after translation-pair contract cleanup, because WordNet/Moby and EN frequency exist.
- `de-de` should wait until German frequency is valid.
- `ja-ja` has JP WordNet resources but needs a separate source/adapter design.
- `es-es` lacks an explicit monolingual source decision.

6. `en-zh`
- Not SRS-selectable and no frequency DB.
- Keep as planned until Chinese frequency and CEDICT adapter are real.

## Doc Drift And Contradictions Found

These should be fixed before using the docs for another agent handoff:

1. `de-en` adapter status drift
- `docs/language_pairs/lp_data_inventory_matrix.md` still says the dedicated `de-en` adapter remains pending.
- Current code has `core/lexishift_core/rulegen/pairs/de_en.py`, adapter registration, and capability `rulegen_mode="de_en"`.

2. `en-de` maturity drift
- `docs/language_pairs/en_de_workstream_roadmap.md` still foregrounds the older 16-case / 75% read.
- Current `docs/test_inputs/rulegen_benchmark_cases/en_de.json` has 58 cases.
- Current canonical latest benchmark is top1 `65.52%`, while the Kaikki register experiment is top1 `93.10%` but saturation-failing.

3. Support-guide mechanism drift
- `docs/rulegen/rulegen_lp_support_guide.md` says `en-de` reverse-check is "No" in the mechanism inventory.
- Current feature-state docs, profile, and code indicate `en-de` reverse-check wiring exists, but is not promoted/default-on.

4. Gate artifact drift
- Some `rulegen_quality_gate*_latest.json` files are stale relative to overwritten benchmark latest artifacts.
- Any status claim should either regenerate benchmark and gate together or explicitly cite saved dated artifacts.

5. Conformance coverage gap
- `check:lp-conformance` passes for two profiles but does not assert that every supported rulegen pair has a profile.
- If profile coverage becomes the onboarding contract, the check should grow a "supported rulegen pairs must be profiled or explicitly exempt" mode.

6. Local resource drift
- Local German frequency DB exists but is invalid.
- This makes `en-de` look more code-ready than it is for local real SRS use.

## Recommended Next Work Queue

Recommended order:

1. Documentation reconciliation pass
- Update `de-en` and `en-de` docs to match current code/artifacts.
- Add an explicit note that current quality-gate latest artifacts may be stale if benchmark latest was overwritten.

2. Profile coverage pass
- Add profiles for `en-ja`, `es-en`, and `de-en`, or document why only `en-es` and `en-de` are profiled.
- Extend `check:lp-conformance` if profile completeness should be enforced.

3. `de-en` benchmark seed
- This is the cleanest proof that the generalized translation-pack contract can onboard a second direction without a new architecture slice.
- Keep the first dataset small and failure-family-driven.

4. German frequency repair
- Rebuild `freq-de-default.sqlite` with `scripts/build/de_frequency_pipeline.py`.
- Re-run resource audit.
- Then decide whether to build an `en-de` SRS journey lane.

5. `en-de` source-lane decision
- Compare canonical FreeDict and Kaikki/Wiktionary lanes with a non-saturated matrix.
- Promote only if default source, quality gate, and SRS resource story align.

6. `es-en` advisory lane
- Add profile, named preset/wrapper, current benchmark/gate/triage, then decide if source/reverse work is justified.

7. Monolingual LP planning
- Do not mix monolingual adapter design with translation-pair cleanup.
- Start with `en-en` only after the pair/resource contract is clean enough.

## Bottom Line

The onboarding architecture exists and is pointed in the right direction: capability registry, normalized pack refs, scaffold, profile checks, benchmark/gate/triage, SRS harnesses, and resource inventory docs.

The gap is coverage and truth alignment:

- only two pairs are fully profiled,
- several supported pairs lack current dedicated quality lanes,
- local German frequency is broken,
- gate artifacts can drift from benchmark artifacts,
- and semantic-publication readiness is currently `en-es`-specific and narrow.

The best immediate LP parity move is not a broad all-pairs tuning push. It is to reconcile docs, complete profile coverage for existing supported pairs, seed `de-en` benchmark evidence, and repair German frequency so `en-de` can be judged as a real SRS LP rather than only a rulegen benchmark lane.
