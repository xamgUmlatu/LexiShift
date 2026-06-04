# Semantic Veto Breadth Expansion Gate

Status: active planning gate
Role: Planning / WIP
Last updated: 2026-04-30
Last verified: 2026-05-14 metadata-only Lane 1 semantic authority note; breadth gate was not executed
Source-of-truth: planning gate only; execution truth will live in the required tracked artifacts and registry summaries after the gate is run.

This gate names the next breadth test for the current
`wave6_auth_frame_raw_sentence_surface_pos_rescue` candidate. It is a test
definition, not executed breadth evidence and not a runtime-policy change.

## Gate

Gate id: `wave7_source_class_breadth_v1`

Question: does the current source-admission plus raw-sentence plus rescue-policy
shape survive fresh source-detectable semantic classes beyond the current
authorization-frame repair?

The gate exists to prevent further threshold tuning on the current 16-family
wave before broader evidence is locked.

## Starting Evidence

- `docs/test_outputs/semantic_non_v10_inventory_candidates_wave6_available_latest.md`
  still finds `100` ranked candidates after excluding `43` already studied
  triggers, so inventory availability is not the bottleneck.
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave6_anypos_supported_latest.md`
  shows that reverse/FreeDict-supported construction alone admits only `6 / 16`
  selected families, so source support is the bottleneck for a promotion-like
  lane.
- `docs/test_outputs/semantic_non_v10_wave_admission_sweep_wave6_anypos_unsupported_latest.md`
  shows the forward-only upper bound can select `16 / 16` families from a wider
  `64`-candidate pool.
- `docs/test_outputs/semantic_wiktextract_translation_support_wave6_anypos_latest.md`
  converts that upper-bound selected set to `38 / 38` supported senses and
  `16 / 16` fully supported families.
- `docs/test_outputs/semantic_surface_pos_rescue_policy_validation_non_v10_wave6_auth_frame_raw_sentence_latest.md`
  confirms the current recommended rescue policy offline at `0` harmful
  replacements and `0` false abstains across the current `54` cases.

## Required Exclusions

The next inventory run must exclude all families already used to shape the
current candidate:

- v10 sentence-veto inventory
- seed non-v10 queue
- selected wave2 families
- wave5 source-portfolio families
- current wave6 triggers:
  `leave`, `black`, `serve`, `low`, `part`, `feel`, `still`, `bear`,
  `finish`, `throw`, `upset`, `piece`, `fair`, `show`, `advance`, `rank`

Do not add browser held-out sentence text or Spanish target lemmas to source
detectors.

## Selection Rule

Build a fresh candidate pool and select a bounded supported wave:

- pool target: at least `64` ranked WordNet candidates after exclusions
- selected-family target: `16` supported families
- held-out floor: at least `48` cases, with at least two active/shadow rows and
  one phrase/no-winner row per selected family
- class breadth floor: at least `3` non-authorization semantic-class buckets
- per-class cap: no more than `6` selected families may rely on the same
  semantic-class detector

Initial class buckets to try are allowed only when their detector fires from
source gloss, translation-sense, or source example text:

| Bucket | Source-detectable signal | Examples from current inventories |
| --- | --- | --- |
| `color_appearance_state` | color, shade, brightness, appearance, condition, rank/quality wording | `blue`, `black`, `fair`, `rough`, `cool`, `rank` |
| `role_event_service` | performance, show, service, office, role, act/event wording | `serve`, `show`, `act`, `issue`, `control` |
| `market_finance_role` | market, price, finance, investor, rank/status wording | `bear`, `rank`, `score`, `firm` |
| `physical_action_object_state` | throw, finish, fit, piece, force, split, separate, movement wording | `finish`, `throw`, `piece`, `fit`, `split`, `separate` |

The authorization/permission class is already represented by wave6 and should
not count toward the class breadth floor.

## Acceptance Evidence

To claim this gate passed, produce all of the following as tracked artifacts:

1. Fresh inventory report with the required exclusions recorded.
2. Selected dataset and queue for `wave7_source_class_breadth_v1`.
3. Source-support or Wiktextract-support audit showing every selected sense is
   source-supported.
4. Source-admission cycle for the selected evidence batch.
5. Active/shadow held-out validation.
6. Phrase/no-winner held-out validation.
7. Rescue policy validation over freshly scored active/shadow plus
   phrase/no-winner rows.
8. Failure-class mining report reading the admission, held-out, source, and
   rescue-validation artifacts.
9. Registry summary after the new artifacts are classified.

Promotion-quality evidence requires `0` harmful replacements and `0` false
abstains on the locked gate suites. A failing wave is still useful only if its
failure classes are recorded before any new tuning or adapter work.

## Stop Rules

- If the selected wave cannot reach `16` fully supported families, stop at source
  support and record the support gap; do not tune the current wave6 policy.
- If a new class detector needs browser sentence text, reject it for this gate.
- If phrase/no-winner harm appears, classify it before adjusting rescue gates.
- If active/shadow false abstains appear, classify whether the miss is source
  support, semantic-class detector, scorer/context, or rescue-gate related.
- Runtime implementation remains out of scope until this breadth gate has been
  executed and reviewed.
