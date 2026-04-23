# Semantic LLM Queue Review (`en-es` v10)

- Status: `ok`
- Generated: `2026-04-23T19:17:26Z`
- Runtime dataset: `en_es_sentence_veto_v10`
- Family inventory: `docs/test_inputs/semantic_routing/semantic_family_inventory_en_es_v10.json`
- Frozen bakeoff queue: `docs/test_inputs/semantic_routing/semantic_prompt_bakeoff_queue_en_es.json`
- Frozen slot manifest: `docs/test_inputs/semantic_routing/semantic_prompt_slot_manifest.json`

## Runtime Read First

- Strong hard runtime row (`sentence_transformer_cosine + masked_sentence + all_evidence_text + noun_family_frame_guard + sense_label_near_tie_active_rescue + a=0.00 + m=0.00`):
  - decision accuracy `89.5%`
  - replace recall `76.3%`
  - harmful replace `1.8%`
  - false abstain `23.7%`
- Accepted active-sense overlay experiment:
  - decision accuracy `93.7%`
  - replace recall `84.2%`
  - harmful replace `0` current cases / `0.0%` corridor ceiling
  - false abstain `15.8%`
- Corrected zero-noise soft ladder:
  - config `soft:a=0.60:m=0.00`
  - soft true positives `0`
  - soft false positives `0`
  - replace-or-soft recall `76.3%`
  - interpretation: the old soft-lane optimism does not survive `v10`; the zero-noise row now adds no new surfaced wins.

## Corridor Read

- Runtime reference corridor: recall floor `63.2%`, harmful ceiling `5.3%`, false-abstain ceiling `36.8%`
- Zero-noise ladder corridor: replace-or-soft floor `63.2%`, soft-noise ceiling `0.0%`
- Accepted active-sense overlay corridor: recall floor `71.1%`, harmful ceiling `0.0%`, false-abstain ceiling `28.9%`

## Inventory Counts

- Likely buckets:
  - `needs_cue_data`: `7` families
  - `needs_phrase_parsing_fix`: `1` family
  - `needs_shadow_data`: `0` families
  - `needs_algorithm_fix`: `0` families
  - `not_applicable`: `11` families
- Queue status:
  - `queued`: `4`
  - `review_pending`: `1`
  - `deferred`: `3`
  - `resolved`: `11`

## Sampled Review Notes

| Family | Queue read | Why |
| --- | --- | --- |
| `play` | `needs_phrase_parsing_fix` / `review_pending` | `play:005` is still the only harmful replace on the plain strong row; active-sense noun phrase guarding removes it without losing the current rescue wins, so prompt spend should treat `play` as a negative control rather than a target. |
| `report` | `needs_cue_data` / `queued` | `report:001` and `report:002` both stay abstained on the hard row and on the accepted overlay, while `report:005` stays safely abstained; this is the clearest new cue-data family. |
| `check` | `needs_cue_data` / `queued` | `check:002` remains unresolved after the accepted overlay, but the phrase probe keeps `check:005` safely abstained. |
| `trip` | `needs_cue_data` / `queued` | `trip:002` remains unresolved after the accepted overlay and no longer benefits from a live zero-noise soft lane on `v10`. |
| `plant` | `needs_cue_data` / `deferred` | `plant:002` is still a real cue miss on the hard row, but the accepted overlay already rescues it, so it is a calibration family rather than first-tranche spend. |
| `watch` | `not_applicable` / `resolved` | `watch` stays clean on the strong row and under the active-sense phrase guard, so it is useful as a phrase-sensitive negative control. |

## Frozen First Prompt Slice

Primary target slice:
- `cue_cross_pos_frame_v1`: `check`, `order`, `trip`, `report`
- `cue_contrastive_general_v1`: `plant`, `drink`

Guardrail families:
- `play`
- `watch`

Reserve-only for now:
- `cue_minimal_rescue_v1` with `plant`, `drink`, `park`
- `shadow_expand_core_v1`

Reason:
- `v10` widened the weak-active residue through `report`, but did not produce a second phrase-leak family.
- the zero-noise soft ladder no longer adds real lift on the current dataset, so the first bakeoff should not over-index on rescue-style prompt wording.
- the current runtime residue is still cue-heavy, not shadow-thin.

## `example_sentence_bank` Note

- `example_sentence_bank` is already approved in `docs/test_inputs/semantic_shadow_source_registry.json` for `discrimination` and `cue_generation`.
- the new feasibility artifact `docs/test_outputs/semantic_example_sentence_bank_pilot_en_es_latest.md` now makes the current local state explicit:
  - queued-family example coverage is `0 / 6` on the installed packs
  - reverse-side auxiliary sense text is available for `6 / 6` target families
- so there is still no live example-backed cue source on this machine for the frozen `v10` queue.
- the next non-prompt choice is now narrower:
  - either ingest a real example source before prompt spend
  - or run one reverse-aux-text control before prompt smoke testing
