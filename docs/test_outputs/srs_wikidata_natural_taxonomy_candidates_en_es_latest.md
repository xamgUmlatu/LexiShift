# en-es Wikidata Natural Taxonomy Candidate Audit

- Status: `ok`
- Decision: `srs_wikidata_natural_taxonomy_candidates_ready`
- Local lemmas checked: `2481`
- Wikidata matches: `84`
- New candidates: `40`
- New strong candidates: `31`

## Topic Summary

| Topic | Matches | New | New strong | Already covered | Confidence counts |
| --- | ---: | ---: | ---: | ---: | --- |
| `animals` | 54 | 21 | 21 | 33 | strong_direct_taxonomy: 21 |
| `plants_nature` | 30 | 19 | 10 | 11 | light: 9, strong_direct_taxonomy: 10 |

## animals

| Lemma | Confidence | Roots | Match | QIDs |
| --- | --- | --- | --- | --- |
| `abeja` | `strong_direct_taxonomy` | animal, insect | label, alias | Q115131816, Q7391 |
| `atún` | `strong_direct_taxonomy` | fish | alias | Q2346039 |
| `caracol` | `strong_direct_taxonomy` | animal, mollusk | label | Q308841 |
| `cerda` | `strong_direct_taxonomy` | animal | label | Q15942027 |
| `cucaracha` | `strong_direct_taxonomy` | insect, animal | label | Q1661828 |
| `elefante` | `strong_direct_taxonomy` | animal, mammal | label | Q7378 |
| `ganado` | `strong_direct_taxonomy` | animal | label | Q103459 |
| `ganso` | `strong_direct_taxonomy` | animal, bird | label | Q16529344 |
| `gata` | `strong_direct_taxonomy` | animal | label | Q24248440 |
| `gaviota` | `strong_direct_taxonomy` | bird, animal | label | Q3112866 |
| `gorrión` | `strong_direct_taxonomy` | bird | alias | Q28753 |
| `hormiga` | `strong_direct_taxonomy` | insect, animal | label | Q7386, Q115705859 |
| `mariposa` | `strong_direct_taxonomy` | insect | alias | Q28319 |
| `mosca` | `strong_direct_taxonomy` | animal, insect | label | Q859257 |
| `ostra` | `strong_direct_taxonomy` | animal, mollusk | label | Q107411 |
| `perdiz` | `strong_direct_taxonomy` | animal, bird | label | Q732775 |
| `pollo` | `strong_direct_taxonomy` | animal, bird | label, alias | Q780, Q1642639 |
| `reina` | `strong_direct_taxonomy` | animal, insect | label | Q361578 |
| `rubio` | `strong_direct_taxonomy` | fish | alias | Q1107181 |
| `salmón` | `strong_direct_taxonomy` | animal, fish | label | Q2796766 |
| `toro` | `strong_direct_taxonomy` | animal | label | Q693690 |

## plants_nature

| Lemma | Confidence | Roots | Match | QIDs |
| --- | --- | --- | --- | --- |
| `arroz` | `strong_direct_taxonomy` | grass, plant | label | Q5090 |
| `calabaza` | `strong_direct_taxonomy` | plant | label | Q161180 |
| `caña` | `strong_direct_taxonomy` | plant | label | Q2734060 |
| `cebolla` | `strong_direct_taxonomy` | plant, vegetable | label | Q3406628 |
| `centeno` | `strong_direct_taxonomy` | plant | label | Q12099 |
| `col` | `strong_direct_taxonomy` | plant, vegetable | label | Q14328596 |
| `haya` | `strong_direct_taxonomy` | plant, tree | label | Q59779138 |
| `lima` | `light` | fruit | label | Q13195 |
| `limón` | `light` | fruit | alias, label | Q13195, Q1093742 |
| `manzana` | `light` | fruit | label | Q89 |
| `marrón` | `light` | fruit | label | Q3177204 |
| `naranja` | `light` | fruit | label | Q13191 |
| `nuez` | `light` | fruit | label | Q208021 |
| `patata` | `light` | vegetable | alias | Q16587531 |
| `pera` | `light` | fruit | label | Q13099586 |
| `perejil` | `strong_direct_taxonomy` | plant, herb | label | Q65522500 |
| `plátano` | `strong_direct_taxonomy` | plant, fruit, tree | label | Q18376030, Q503 |
| `tomate` | `strong_direct_taxonomy` | plant, vegetable, fruit | label | Q20638126 |
| `uva` | `light` | fruit | label | Q10978 |

## Limitations

- This proves source availability and local-lemma intersection, not final topic precision.
- Polysemic labels are intentionally retained as candidates unless they are obviously outside the taxonomy roots.
- Fruit/vegetable roots may overlap Food & Cooking; they are still useful natural-taxonomy candidates.
- Promote reviewed candidates into packaged LexiShift data; do not require Wikidata at runtime.
