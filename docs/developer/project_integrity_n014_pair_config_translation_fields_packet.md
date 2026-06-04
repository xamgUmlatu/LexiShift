# N-014 Pair Config Translation Fields Packet

Status: active packet
Role: Packet / WIP
Last updated: 2026-04-19
Last verified: 2026-04-19 seam read across translation pair configs, adapters, probe tooling, and pair-local tests
Purpose: bound the remaining pair-local provider-shaped translation path cleanup so internal rulegen config objects use the same generic translation naming as the helper, adapter, and developer-tool seams above them
Source-of-truth: packet only; executable truth still lives in code, tests, and the validation run for this slice
Related docs:
- `project_integrity_secondary_pass_plan.md`
- `project_integrity_secondary_pass_notes.md`
- `data_source_normalization_execution_order.md`
- `project_integrity_n015_translation_gloss_locator_packet.md`

## Slice

- Track: `N-014`
- Slice: `N-014`
- Title: pair-local translation config field convergence
- Pass type: bounded internal naming cleanup

## Exact Seam

Primary code surface:

- `core/lexishift_core/rulegen/pairs/en_de.py`
- `core/lexishift_core/rulegen/pairs/en_de_live_source.py`
- `core/lexishift_core/rulegen/pairs/en_es.py`
- `core/lexishift_core/rulegen/pairs/en_es_live_source.py`
- `core/lexishift_core/rulegen/pairs/de_en.py`
- `core/lexishift_core/rulegen/pairs/es_en.py`
- `core/lexishift_core/rulegen/adapters.py`
- `scripts/testing/rulegen_probe_words.py`

Primary tests/evidence surface:

- `core/tests/rulegen/test_rulegen_adapters.py`
- `core/tests/rulegen/test_rulegen_reverse_check_metadata.py`
- `core/tests/rulegen/test_rulegen_en_es_compiled_resources.py`
- `core/tests/rulegen/test_rulegen_en_es_kaikki_policy.py`
- `core/tests/rulegen/test_rulegen_en_es_kaikki_provenance.py`
- `core/tests/rulegen/test_rulegen_pos_metadata.py`
- `core/tests/dev/test_rulegen_benchmark.py`

Primary contract/docs surface:

- `docs/developer/project_integrity_secondary_pass_notes.md`
- `docs/developer/data_source_normalization_execution_order.md`

## Explicitly Out Of Scope

This slice does not directly review:

- provider-specific loader/build surfaces that are still legitimately FreeDict-local, such as `load_freedict_gloss_records_ordered(...)`
- frequency-build support seams that still use `freedict_de_en_path`
- legacy helper payload aliases that intentionally preserve backward coverage outside the pair-local rulegen config seam
- source/provider ids like `freedict_de_en` or `wiktionary_es_en`, which remain real provider identity rather than generic transport naming
- scoring, filtering, reverse-check behavior, POS normalization, semantic publication, or benchmark policy

## Risk Score

- likelihood: `medium`
- blast radius: `medium`
- observability: `medium`
- priority: `high`

Reasoning:

- the helper and adapter seams above these configs are already generic, so the remaining provider-shaped field names are increasingly misleading
- the runtime behavior should stay unchanged, but the config objects are instantiated in many tests and pair-local call sites, so incomplete cleanup would leave the seam inconsistent
- this is still bounded because it is field naming and call-site coherence, not rulegen behavior

## Contract Sketch

The intended contract for this slice is:

1. pair-local translation rulegen configs use `translation_dict_path` and `reverse_translation_dict_path`
2. pair-local configs keep provider identity separate through fields like `source_dict_id`, `reverse_source_dict_id`, and `dictionary_pos_source_profile`
3. adapters and developer tooling instantiate those configs with generic path names
4. pair-local live-source helpers consume the same generic config fields
5. reverse-direction LPs (`de-en`, `es-en`) follow the same naming rule as forward-direction LPs (`en-de`, `en-es`)

## Claim-To-Evidence Map

| Claim | Owning code/tests | Evidence surface | Current status |
|---|---|---|---|
| Helper/adapter seams already present translation paths using generic naming. | rulegen adapter builders and helper request surfaces | `adapters.py`, prior E1 packets/tests | `verified before edit` |
| Pair-local translation config objects still expose provider-shaped path fields. | translation pair config dataclasses | pair modules plus pair-local tests | `contradicted before edit` |
| Probe/dev tooling still has to speak those provider-shaped config field names when constructing pair-local configs. | `rulegen_probe_words.py`, benchmark-focused tests | script plus targeted tests | `contradicted before edit` |
| Provider identity still belongs in explicit provider/source-id fields after the path rename. | `source_dict_id`, `reverse_source_dict_id`, `dictionary_pos_source_profile` | pair modules/tests | `verified before edit` |

## Invariants

1. translation pair configs still point at the same resolved files after the rename
2. provider identity fields remain unchanged
3. reverse-check and compiled-resource paths continue to read from the same files
4. no rulegen scoring, ranking, or filtering behavior changes in this slice
5. pair-local config naming now matches the generic adapter/probe contract above it

## Scenario Matrix

| Scenario | What to verify |
|---|---|
| `en-de` config built from adapter request | generic translation path fields are populated and reverse path survives |
| `en-es` config built with compiled resources and reverse-check inputs | compiled path still resolves and tests remain green |
| `de-en` direct config instantiation in tests | forward translation path rename is sufficient and behavior stays unchanged |
| `es-en` reverse-check config instantiation in tests | forward and reverse generic path names both work |
| probe/benchmark dev entrypoints | internal config construction no longer uses `freedict_*_path` names |

## Validation Floor

- `python3 scripts/dev/check_doc_references.py`
- targeted tests:
  - `python3 -m pytest core/tests/rulegen/test_rulegen_adapters.py core/tests/rulegen/test_rulegen_reverse_check_metadata.py core/tests/rulegen/test_rulegen_pos_metadata.py core/tests/rulegen/test_rulegen_en_es_kaikki_policy.py core/tests/rulegen/test_rulegen_en_es_kaikki_provenance.py core/tests/rulegen/test_rulegen_en_es_compiled_resources.py core/tests/dev/test_rulegen_benchmark.py -q`
- `git diff --check -- <touched files>`
- `npm --prefix scripts run check:changed:staged`

## Planned Action For This Slice

1. rename pair-local translation config path fields to `translation_dict_path` / `reverse_translation_dict_path` across the four translation LP config objects
2. update pair-local live-source helpers, adapter builders, and probe tooling to use the generic names
3. update the affected pair-local tests
4. mark `N-014` resolved and update the normalization execution board now that this internal seam is no longer provider-shaped

## Outcome

Result:

- the translation LP config objects now use generic `translation_dict_path` / `reverse_translation_dict_path` fields across `en-de`, `en-es`, `de-en`, and `es-en`
- pair-local live-source helpers, adapter builders, and `rulegen_probe_words.py` now use the same generic path naming
- the pair-local tests were updated to match the renamed config seam
- the broader benchmark test bundle also surfaced one stale expectation from the earlier generic translation-pack inference cleanup, and that expectation was updated so anonymous manual paths now correctly assert the generic `translation_*` pack identity
- `N-014` is now resolved in the secondary-pass notes, and the normalization execution order no longer treats pair-local adapter config naming as a remaining provider-shaped holdout
