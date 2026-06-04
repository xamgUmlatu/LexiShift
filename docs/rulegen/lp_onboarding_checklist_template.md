# Rulegen LP Onboarding Checklist Template

Status: Active template
Role: Runbook / operational
Purpose:
- Provide a copyable checklist for bringing a new rulegen language pair through the standard onboarding stages.
- Keep LP bring-up consistent across contributors and future agent sessions.
Last updated: 2026-04-04
Source-of-truth: reusable onboarding template; pair-specific truth should live in the copied workstream doc plus code/tests/artifacts
Verification:
- `docs/rulegen/lp_onboarding_operating_model.md`
- `docs/rulegen/rulegen_lp_support_guide.md`
- `docs/developer/ai_workflow.md`

## Copy Rules

When starting a new pair:

1. copy this file into `docs/language_pairs/<lp>_workstream_roadmap.md` if the pair needs phased planning,
2. replace `<lp>` and fill the checkboxes,
3. keep status/evidence claims aligned with `docs/developer/feature_state_matrix.md`.

If the pair is too small to justify a roadmap, use this checklist informally and record only the final state in `feature_state_matrix.md`.

Optional scaffold entrypoint:

```bash
npm --prefix scripts run scaffold:rulegen:lp -- --pair en-fr --translation-family freedict --translation-pack-id freedict-fr-en --reverse-family freedict --reverse-pack-id freedict-en-fr --with-roadmap
```

## Pair Identity

- Pair key: `<source-target>`
- Primary target language: `<target>`
- Reverse pair: `<target-source>` or `none`
- Primary source family: `FreeDict | Kaikki | JMDict | other`
- Reverse source family: `<family or none>`
- Current stage: `Source Audit | Scaffolded | Benchmarkable | Source-Shaped | Sweepable | Prepared | Promotable`

## Stage 0: Source Audit

- [ ] Confirm the primary source pack or source path.
- [ ] Confirm whether a reverse source exists and whether it is usable.
- [ ] Audit raw metadata coverage.
- [ ] Audit punctuation / qualifier / boilerplate patterns.
- [ ] Record missing-but-expected fields.
- [ ] Record whether a Kaikki-style family mapping is relevant.

Evidence:

- SQL or probe notes:
- Source artifact path(s):

## Stage 1: Scaffolded

- [ ] Pair capability exists.
- [ ] Pair adapter wiring exists.
- [ ] Pair config dataclass exists.
- [ ] Minimal probe seam exists.
- [ ] Minimal targeted tests exist.

Touched files:

- pair module:
- adapter:
- tests:

## Stage 2: Benchmarkable

- [ ] LP-specific benchmark case file exists.
- [ ] Pair-scoped benchmark/gate/triage commands exist.
- [ ] Named latest artifact paths exist.
- [ ] One obvious refresh command exists.
- [ ] Pair status is documented in `feature_state_matrix.md`.

Commands:

- benchmark:
- gate:
- triage:
- wrapper:

Artifacts:

- benchmark latest:
- gate latest:
- triage latest:

## Stage 3: Source-Shaped

- [ ] Major punctuation cleanup is implemented.
- [ ] Qualifier / annotation cleanup is implemented.
- [ ] Probe can distinguish source-missing vs ranking-misordered failures.
- [ ] Normalization tests exist.
- [ ] Source-shaping changes are evidenced by artifacts, not prose alone.

Implemented normalization profile:

- punctuation rules:
- qualifier rules:
- known remaining patterns:

## Stage 4: Sweepable

- [ ] Live mechanisms are identified in the support guide or pair notes.
- [ ] Inert knobs are documented or removed from the active matrix.
- [ ] The pair has at least one stable advisory lane.
- [ ] Sentinel failures are known, but mechanism design is not word-driven.
- [ ] The current best config is recorded with explicit caveats.

Live mechanisms:

- baseline shared:
- pair-specific:
- experimental:

Current best lane:

- source:
- key toggles:
- metric summary:

## Stage 5: Prepared

- [ ] Compiled resource object exists.
- [ ] Candidate-row IR exists.
- [ ] Prepared score/select reuse exists.
- [ ] Live vs compiled equivalence tests exist.
- [ ] The prepared path is benchmark-equivalent to the live path.

Prepared path notes:

- compiled resource class:
- prepared tables:
- known missing parity with `en-es`:

## Stage 6: Promotable

- [ ] Default source choice is justified.
- [ ] Remaining gaps are explicitly documented.
- [ ] Advisory vs promoted status is unambiguous.
- [ ] Baseline/policy implications are explicit.
- [ ] The pair is ready for stronger CI or policy treatment if desired.

Promotion notes:

- accepted default source:
- remaining caveats:
- promotion blockers:

## Pair-Local Profiles

Fill these even if the pair is still immature.

### Source Profile

- primary pack/source:
- reverse pack/source:
- canonical record contract:

### Normalization Profile

- punctuation families handled:
- qualifier/head extraction rules:
- unresolved cleanup families:

### POS Profile

- POS mapping source:
- compatibility rules:
- known POS risks:

### Metadata Family Profile

- register markers:
- region markers:
- domain markers:
- rarity / archaism markers:

### Morphology Profile

- allowed variants:
- forbidden variants:
- context-dependent deferrals:

## Anti-Patterns Check

- [ ] No benchmark-shaped exact lexical override was added to canonical behavior.
- [ ] No broad sweep was treated as meaningful while most knobs were inert.
- [ ] No source swap and scoring change were bundled into the same comparison claim.
- [ ] No pair-specific mechanism was justified only by one benchmark word.

## Final Handoff

- Current stage:
- Best evidence artifact:
- Most important remaining gap:
- Recommended next mechanism or infrastructure step:
