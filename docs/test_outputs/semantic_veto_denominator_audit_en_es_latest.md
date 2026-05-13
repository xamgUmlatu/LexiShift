# en-es Semantic Veto Denominator Audit

- Status: `ok`
- Decision: `semantic_veto_denominator_audit_current`
- Generated: `2026-05-13T21:10:55+00:00`
- SRS learner-target universe: `1984` target lemmas from `2000` seed rows
- Semantic-veto replacement denominator: `570` source-target families
- Covered active-only families: `455` (79.8%)
- Uncovered active-only families: `115`
- Remaining generation queue: `0` families / `0` selected requests

## What The Denominator Means

The semantic-veto source-target denominator is the set of current rulegen-produced English source / Spanish target replacement families for the installed en-es SRS target universe.

The 1,984 SRS-admissible Spanish target lemmas are the learner target universe, not the browser replacement-family denominator.

Current accounting identity: `570 = 49 pre-full-generation covered + 406 reviewed/generated + 115 excluded`.

## Source Pipeline

| Step | Current Value |
| --- | --- |
| Frequency DB | `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-es-cde.sqlite` |
| Seed top N requested | `50000` |
| Seed rows | `2000` |
| Unique SRS target lemmas | `1984` |
| Rulegen targets | `1984` |
| Rulegen rules | `570` |
| Source-target pairs | `570` |
| Translation dictionary | `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/freedict-es-en/main.sqlite` |
| Reverse dictionary | `/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/wiktionary-en-es.sqlite` |

## Review Outcome

| Bucket | Families |
| --- | ---: |
| Pre-full-generation covered product-scope control | 49 |
| Source-target review approved for active-only generation | 406 |
| Source-target review excluded | 115 |
| `exclude_no_visible_replacement` | 27 |
| `exclude_weak_source_target_mapping` | 88 |

## Coverage By Source Band

| Band | Families | Covered | Uncovered | Covered Share |
| --- | ---: | ---: | ---: | ---: |
| `zipf_5_plus_very_common` | 109 | 95 | 14 | 87.2% |
| `zipf_4_to_5_common` | 235 | 196 | 39 | 83.4% |
| `zipf_3_to_4_mid` | 152 | 125 | 27 | 82.2% |
| `zipf_below_3_rare` | 52 | 38 | 14 | 73.1% |
| `missing` | 22 | 1 | 21 | 4.5% |

## Coverage By Target Band

| Band | Families | Covered | Uncovered | Covered Share |
| --- | ---: | ---: | ---: | ---: |
| `zipf_5_plus_very_common` | 84 | 66 | 18 | 78.6% |
| `zipf_4_to_5_common` | 219 | 181 | 38 | 82.7% |
| `zipf_3_to_4_mid` | 206 | 167 | 39 | 81.1% |
| `zipf_below_3_rare` | 61 | 41 | 20 | 67.2% |

## Excluded Family Breakdown

| Decision | Source Band | Target Band | Families | Samples |
| --- | --- | --- | ---: | --- |
| `exclude_no_visible_replacement` | `missing` | `zipf_3_to_4_mid` | 8 | `gobackwards` -> `retroceder`, `gobeyond` -> `atravesar`, `mosaicwork` -> `mosaico`, `offerofparriage` -> `pretensión` |
| `exclude_no_visible_replacement` | `missing` | `zipf_4_to_5_common` | 7 | `beburntdown` -> `quemar`, `campingsite` -> `campamento`, `femalejournalist` -> `periodista`, `germanlanguage` -> `alemán` |
| `exclude_no_visible_replacement` | `missing` | `zipf_5_plus_very_common` | 3 | `manifacture` -> `producción`, `onethousand` -> `mil`, `thatmuch` -> `tanto` |
| `exclude_no_visible_replacement` | `missing` | `zipf_below_3_rare` | 1 | `taketheplaceof` -> `relevar` |
| `exclude_no_visible_replacement` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 1 | `ideal` -> `ideal` |
| `exclude_no_visible_replacement` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 2 | `crisis` -> `crisis`, `favor` -> `favor` |
| `exclude_no_visible_replacement` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 2 | `capital` -> `capital`, `director` -> `director` |
| `exclude_no_visible_replacement` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 2 | `burndown` -> `quemar`, `otherthan` -> `excepto` |
| `exclude_no_visible_replacement` | `zipf_below_3_rare` | `zipf_5_plus_very_common` | 1 | `turnon` -> `poner` |
| `exclude_weak_source_target_mapping` | `missing` | `zipf_3_to_4_mid` | 1 | `conversance` -> `notoriedad` |
| `exclude_weak_source_target_mapping` | `missing` | `zipf_4_to_5_common` | 1 | `middaymeal` -> `cena` |
| `exclude_weak_source_target_mapping` | `zipf_3_to_4_mid` | `zipf_3_to_4_mid` | 8 | `abandonment` -> `cesión`, `acquaintance` -> `notoriedad`, `builder` -> `labrador`, `familiarity` -> `notoriedad` |
| `exclude_weak_source_target_mapping` | `zipf_3_to_4_mid` | `zipf_4_to_5_common` | 8 | `abstraction` -> `robo`, `bark` -> `barco`, `chunk` -> `bola`, `delegate` -> `diputado` |
| `exclude_weak_source_target_mapping` | `zipf_3_to_4_mid` | `zipf_5_plus_very_common` | 4 | `barn` -> `puesto`, `centennial` -> `siglo`, `compartment` -> `departamento`, `dismal` -> `común` |
| `exclude_weak_source_target_mapping` | `zipf_3_to_4_mid` | `zipf_below_3_rare` | 7 | `dove` -> `pichón`, `govern` -> `capitanear`, `lovable` -> `afable`, `obstruct` -> `cercar` |
| `exclude_weak_source_target_mapping` | `zipf_4_to_5_common` | `zipf_3_to_4_mid` | 17 | `beg` -> `demandar`, `bid` -> `demandar`, `blank` -> `formulario`, `burst` -> `grieta` |
| `exclude_weak_source_target_mapping` | `zipf_4_to_5_common` | `zipf_4_to_5_common` | 11 | `calm` -> `silencio`, `damage` -> `defecto`, `friendly` -> `gracioso`, `fur` -> `piel` |
| `exclude_weak_source_target_mapping` | `zipf_4_to_5_common` | `zipf_5_plus_very_common` | 3 | `depression` -> `crisis`, `emergency` -> `crisis`, `shed` -> `puesto` |
| `exclude_weak_source_target_mapping` | `zipf_4_to_5_common` | `zipf_below_3_rare` | 5 | `divide` -> `segregar`, `fur` -> `incrustación`, `grow` -> `acontecer`, `nearby` -> `contiguo` |
| `exclude_weak_source_target_mapping` | `zipf_5_plus_very_common` | `zipf_3_to_4_mid` | 3 | `ask` -> `demandar`, `offer` -> `pretensión`, `show` -> `designar` |
| `exclude_weak_source_target_mapping` | `zipf_5_plus_very_common` | `zipf_4_to_5_common` | 5 | `action` -> `batalla`, `chief` -> `amo`, `hit` -> `llamar`, `kind` -> `gracioso` |
| `exclude_weak_source_target_mapping` | `zipf_5_plus_very_common` | `zipf_5_plus_very_common` | 2 | `start` -> `poner`, `want` -> `necesidad` |
| `exclude_weak_source_target_mapping` | `zipf_5_plus_very_common` | `zipf_below_3_rare` | 2 | `become` -> `acontecer`, `front` -> `frontón` |
| `exclude_weak_source_target_mapping` | `zipf_below_3_rare` | `zipf_3_to_4_mid` | 2 | `replenishment` -> `suplemento`, `sty` -> `cuadra` |
| `exclude_weak_source_target_mapping` | `zipf_below_3_rare` | `zipf_4_to_5_common` | 3 | `affable` -> `gracioso`, `alternation` -> `alternativa`, `clod` -> `bola` |
| `exclude_weak_source_target_mapping` | `zipf_below_3_rare` | `zipf_5_plus_very_common` | 1 | `trite` -> `común` |
| `exclude_weak_source_target_mapping` | `zipf_below_3_rare` | `zipf_below_3_rare` | 5 | `battlefront` -> `frontón`, `begrudge` -> `deplorar`, `beret` -> `birrete`, `frontage` -> `frontón` |

## Expansion Levers

| Lever | Effect | Risk |
| --- | --- | --- |
| `expand_or_replace_spanish_frequency_pack` | Can increase the SRS target universe beyond the current 1,984 unique target lemmas. | Only helps semantic veto if rulegen can produce visible source-target rules for the added targets. |
| `improve_rulegen_dictionary_or_filter_coverage` | Can increase the 570 replacement-family denominator from the existing 1,984 targets. | Can also add weak or awkward source-target mappings that need review before LLM spend. |
| `change_source_target_review_policy` | Can admit some of the 115 currently excluded families. | Would intentionally accept identical/no-visible or weak mappings that were excluded for product reasons. |
| `generate_shadow_or_phrase_data` | Can improve veto quality for already covered families with harmful-replacement classes. | Does not expand the denominator by itself. |

## Cleanup Recommendations

- Keep tranche-011 as the current product checkpoint and tranche-003 as the latest hands-on browser smoke.
- Do not run more active-only paid generation while selected_request_count is 0.
- Treat the next denominator-expansion task as rulegen/SRS resource work, not LLM prompt work.
- Keep the 1,984 learner-target universe and 570 replacement-family universe labeled separately in product docs.

## Checks

| Check | Result |
| --- | --- |
| `bridge_and_plan_denominator_match` | `True` |
| `coverage_plus_review_exclusions_matches_denominator` | `True` |
| `covered_plus_uncovered_matches_denominator` | `True` |
| `current_generation_queue_exhausted` | `True` |
| `no_evidence_outside_denominator` | `True` |
| `product_scope_plus_approved_plus_excluded_matches_denominator` | `True` |
| `uncovered_rows_are_review_exclusions` | `True` |

## Limitations

- This audit reads existing no-spend artifacts; it does not rerun full rulegen.
- The 570 denominator is current-resource truth, not a claim about all en-es vocabulary.
- The 115 exclusions were manually reviewed for active-only generation value, not for every possible future product policy.
- Coverage means active-only evidence coverage, not broad semantic-veto accuracy.
