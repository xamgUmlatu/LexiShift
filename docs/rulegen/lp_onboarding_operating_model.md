# Rulegen LP Onboarding Operating Model

Status: Active reference
Role: Canonical current
Purpose:
- Define the golden-path process for bringing up new rulegen language pairs with low cognitive load and high verification discipline.
- Separate what should be pair-specific from what should become shared platform machinery.
- Make future LP bring-up closer to profile wiring than bespoke mechanism invention.
Last updated: 2026-04-04
Last verified: 2026-04-04 against current rulegen support/state/workflow docs and the active `en-es` / `en-de` implementation state
Source-of-truth: onboarding/process contract; implementation truth still lives in source code, `docs/rulegen/rulegen_lp_support_guide.md`, and `docs/developer/feature_state_matrix.md`
Verification:
- `docs/rulegen/rulegen_lp_support_guide.md`
- `docs/rulegen/rule_generation_technical.md`
- `docs/rulegen/rulegen_congruity_implementation_plan.md`
- `docs/developer/feature_state_matrix.md`
- `docs/developer/ai_workflow.md`
- `docs/developer/genai_workflow_architecture.md`

## Why This Doc Exists

`en-es` has become the de facto source of truth for "how a mature pair works," but that is not yet the same thing as a systematic onboarding model.

The onboarding goal is not:

- "copy `en-es` until the new pair works"

The onboarding goal is:

- identify the small number of pair-local profiles that must differ,
- keep ranking/selection machinery generic whenever possible,
- make each maturity step observable through benchmark/probe artifacts,
- and make future LP bring-up feel like following a paved road rather than rediscovering architecture.

## Design Principles

Treat LP onboarding like internal platform work.

That means:

1. reduce contributor cognitive load,
2. make the happy path obvious,
3. make deviations explicit,
4. turn repeated pair work into reusable platform machinery,
5. require evidence before promoting a pair to a stronger status.

Operationally, this means:

- scaffold before tuning,
- benchmark before sweeping,
- compile/precompute before scaling sweep size,
- and prefer profiles over pair-local heuristics.

Current machine-readable profile surface:

- `docs/test_inputs/rulegen_lp_profiles/`
- validated by `npm --prefix scripts run check:lp-profiles`
- repo-alignment audit: `npm --prefix scripts run check:lp-conformance`
  - verifies benchmark/case/preset conventions plus central pair export, adapter registration, and capability-mode registration
- scaffold entrypoint: `npm --prefix scripts run scaffold:rulegen:lp -- --pair <lp> --translation-family <family> --translation-pack-id <pack_id>`
- text/code scaffold templates: `scripts/dev/templates/rulegen_lp/`
- optional generated integration handoff: `docs/language_pairs/<pair>_integration_handoff.md`
- optional generated benchmark preset starter: `docs/language_pairs/<pair>_benchmark_preset_starter.md`

## Core Vocabulary

Use these terms precisely.

### LP Profile

A pair-local static contract that describes how one LP plugs into the shared rulegen system.

Examples:

- source loader / source pack contract
- reverse-source contract
- POS normalization profile
- normalization / punctuation-cleanup profile
- metadata-family mapping profile
- morphology profile
- benchmark case file

The intended long-term shape is:

- one machine-readable LP profile per pair,
- one small number of shared mechanisms,
- and one standard quality loop that reads the profile rather than relying on undocumented pair folklore.

### Signal

A numeric or boolean input to ranking.

Examples:

- `dict_priority`
- `frequency_weight`
- `pos_match`
- reverse-check hit/miss deltas
- source-frequency prior
- provenance/risk-family demotion strengths

Signals should be generic data inputs, not pair-specific hacks.

### Mechanism

A reusable ranking, selection, or emission behavior that consumes signals and metadata.

Examples:

- definition-group interleaving
- reverse-check scoring
- Kaikki live demotion
- provenance competition
- same-sense representative selection
- compiled/prepared benchmark sweep path

Mechanisms should ideally be shared; LPs should mostly decide whether and how they are fed.

### Artifact

The observable evidence used to justify a status claim.

Examples:

- benchmark JSON/Markdown/HTML
- quality gate JSON/Markdown
- triage JSON/Markdown
- probe output
- targeted tests
- compiled/live equivalence tests

### Stage Gate

A maturity checkpoint with explicit entry/exit criteria.

Examples:

- scaffolded
- benchmarkable
- sweepable
- advisory-ready
- promotable

## What Should Be Pair-Specific

These are the things a new LP should be expected to customize.

1. Source endpoints and resource binding
- which dictionary/source family is primary
- which reverse source exists
- which pack ids / manifests are canonical

2. Source record shape
- how raw source rows map into the canonical record contract
- which metadata fields actually exist

3. Normalization profile
- punctuation splitting
- qualifier trimming
- article stripping
- head extraction rules
- token cleanup

4. POS profile
- POS mapping and compatibility classes
- pair-local POS normalization quirks

5. Metadata family profile
- how tags/topics/categories map into canonical families such as register, region, domain, rarity, archaism

6. Morphology profile
- which variant expansions are allowed
- which ones are unsafe without context

7. Benchmark case set
- LP-specific expected outputs, forbidden outputs, and tiering

## What Should Become Generic

These are the things we should actively push out of pair modules over time.

1. Ranking signal containers
2. Reverse-check engine
3. Definition-group selection and interleaving
4. Same-sense representative selection
5. Provenance competition
6. Late-sense clean-earlier competition
7. Kaikki live-policy application
8. Compiled/prepared sweep infrastructure
9. Benchmark / gate / triage / probe reporting

The pair module should mostly provide:

- normalized candidates,
- canonical metadata,
- LP profiles,
- and a small number of enablement/config choices.

## Golden Path Stages

### Stage 0: Source Audit

Output:

- confirmed source endpoints
- actual metadata coverage notes
- known missing fields
- normalization-pattern inventory

Minimum deliverables:

- source path or pack id
- reverse-source decision
- quick SQL/probe audit for punctuation/qualifier patterns

### Stage 1: Scaffolded

Output:

- pair capability exists
- adapter wiring exists
- baseline pair config exists
- probe seam exists

Minimum deliverables:

- pair module
- adapter request/config threading
- minimal targeted tests

### Stage 2: Benchmarkable

Output:

- LP-specific case file exists
- pair-scoped benchmark/gate/triage loop exists
- latest artifacts can be refreshed by one obvious command

Minimum deliverables:

- benchmark preset
- wrapper command or canonical commands
- latest artifact paths
- initial roadmap doc if the pair is expected to mature over time

### Stage 3: Source-Shaped

Output:

- major punctuation/qualifier cleanup is in place
- probe output clearly distinguishes source-missing vs ranking-misordered failures

Minimum deliverables:

- normalization profile
- targeted normalization tests
- artifact evidence showing the cleanup moved real metrics or cleaned the candidate surface

### Stage 4: Sweepable

Output:

- the pair has enough real live mechanisms that sweeps are meaningful
- inert knobs are known and either removed, gated, or documented

Minimum deliverables:

- support-guide row updates
- pair-specific notes on which mechanisms are live
- saturation / sensitivity awareness in benchmark interpretation

### Stage 5: Prepared

Output:

- compiled resources exist
- prepared score/select reuse exists
- live and compiled paths are benchmark-equivalent

Minimum deliverables:

- compiled resource object
- row-level IR
- prepared sweep tables
- equivalence tests

### Stage 6: Promotable

Output:

- the pair has a stable advisory lane
- quality evidence is repeatable
- default-source and default-mechanism choices are justified

Minimum deliverables:

- accepted baseline policy if needed
- consistent latest artifacts
- documented remaining gaps

## Required Onboarding Package For A New LP

Treat this as the minimum deliverable set.

1. Pair module
- `core/lexishift_core/rulegen/pairs/<lp>.py`

2. LP profile notes
- source family
- reverse family
- POS profile
- normalization profile
- metadata-family profile

3. Benchmark case file
- under `docs/test_inputs/rulegen_benchmark_cases/`

4. Named quality loop
- canonical commands or wrapper commands
- named latest artifacts

5. Probe support
- enough metadata exposed to tell whether a failure is source, ranking, cap, or benchmark-contract related

6. State + roadmap docs
- update `docs/developer/feature_state_matrix.md` when status/evidence changes
- add a pair roadmap only if the pair has a real multi-phase maturation path

## Anti-Patterns

Avoid these during onboarding.

1. Pair-specific benchmark appeasement
- do not "fix" the benchmark by embedding test-shaped lexical overrides into canonical behavior

2. Sweeping inert knobs
- do not treat a large matrix as useful if the pair does not actually consume most of it

3. Combining too many causes
- do not change source, normalization, ranking, and benchmark contract in one comparison pass

4. Word-driven mechanism design
- sentinel failures are diagnostics, not the design unit
- mechanisms should be justified as reusable classes of behavior

5. Repeating pair-local machinery
- if a second pair needs the same idea, begin extracting it into a shared mechanism/profile seam

## What A Mature Onboarding System Should Feel Like

For future LPs such as `en-ja`, `ja-en`, `de-en`, and `es-en`, the ideal bring-up should mostly be:

1. bind the source packs,
2. declare the record-shape/profile mapping,
3. declare normalization and family profiles,
4. seed the benchmark case file,
5. run the standard quality loop,
6. enable additional shared mechanisms as the pair becomes ready.

The process should not require rethinking:

- how benchmark artifacts are named,
- how probe works,
- how reverse-check works,
- how provenance competition works,
- or how large sweeps are executed.

## Immediate Hardening Priorities

These are the next repo-level improvements that move onboarding toward that ideal.

1. Introduce a formal LP profile template
- one place for source family, reverse family, POS profile, normalization profile, family profile, morphology policy, and benchmark preset
- starter scaffolding now exists for the profile + benchmark case stub, optional roadmap copy, template-driven pair/test stubs, an explicit integration-handoff doc for central wiring follow-ups, and a generated benchmark preset starter; the remaining value is to keep converging the profile toward a fuller shared contract instead of letting it drift into prose again

2. Introduce a repeatable LP onboarding checklist template
- one checklist per new pair, with stage-gate acceptance criteria

3. Continue extracting pair-local ranking ideas into generic mechanism seams
- especially provenance competition and late-sense competition

4. Keep compiled/prepared sweep support converging across pairs
- so large sweeps are an infrastructure concern, not a pair-by-pair reinvention

5. Keep docs routing crisp
- onboarding doc for process
- support guide for current mechanism inventory
- feature matrix for verified state
- pair roadmap only when a pair genuinely needs phased planning

## Relationship To Existing Docs

Use the docs this way:

- `rule_generation_technical.md`
  - generalized pipeline architecture
- `rulegen_congruity_implementation_plan.md`
  - historical hardening and scoring decisions
- `rulegen_lp_support_guide.md`
  - current mechanism inventory and pair parity map
- `feature_state_matrix.md`
  - current verified status and known mismatches
- this doc
  - the operating model for how new LP support should be onboarded and matured
- `lp_onboarding_checklist_template.md`
  - reusable pair bring-up checklist to copy into a pair-specific roadmap when phased planning is warranted
