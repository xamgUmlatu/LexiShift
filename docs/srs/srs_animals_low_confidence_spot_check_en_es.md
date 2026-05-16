# en-es Animals Low-Confidence Spot Check

Status: planning evidence
Role: Agent spot-check note
Last updated: 2026-05-17
Last verified: 2026-05-17 manual inspection of SPALEX 10k low-confidence animal candidates against installed Kaikki rows; no admission behavior changed
Purpose: record a focused low-confidence review of animal topic candidates before any overlay promotion
Source-of-truth: review note only; product promotion still requires user review and a provenance-bearing overlay.

## Inputs

- Full audit:
  `docs/test_outputs/srs_animals_plants_existing_signal_audit_en_es_spalex_10k_latest.json`
- Review packet:
  `docs/test_outputs/srs_animals_plants_signal_review_packet_en_es_spalex_10k_latest.json`
- Source rows:
  installed `wiktionary-es-en.sqlite` Kaikki/Wiktionary pack

The checked set was all `animals` candidates in `review` or `inventory`
confidence bands, plus any animal row marked `review_required`.

## Summary

- Low-confidence animal candidates checked: `54`
- Rows already in the review packet: `25`
- Clear mechanical false positives found: `1` high-visibility case, `tac`
  (`CAT scan` / `CT scan`)
- Main pattern: the low-confidence band is doing useful work. Most questionable
  rows are true animal senses that are secondary, regional, figurative,
  adjective-only, animal-adjacent, or crowded by a stronger non-animal primary
  sense.
- Recommendation: keep `review` and `inventory` animal rows out of automatic
  promotion. Use them for manual QA and policy calibration only.

## Preliminary Dispositions

These dispositions are agent spot-check notes, not user-approved labels.

| Disposition | Lemmas | Reason |
| --- | --- | --- |
| Strong animal if manually approved | `caballo`, `chivo`, `conejo`, `gallo`, `gato`, `perro`, `pájaro`, `rata`, `serpiente`, `tigre`, `buey`, `cabra`, `cerdo`, `mono`, `sapo`, `víbora`, `vicuña`, `león` | The animal reading is clear. Low score usually came from sense ordering, ambiguity penalties, proper-name competition, or category evidence rather than semantic doubt. |
| Light animal / animal-adjacent only | `aviar`, `ganadero`, `majada`, `pescado`, `piscifactoría`, `conejera`, `nasa`, `cerda`, `cotorra`, `labrador`, `martín`, `ortega`, `solitario`, `coral`, `chola`, `marta`, `pereza`, `perezoso`, `glotón` | The animal signal is real, but the lemma is adjectival, occupational, infrastructure/food-related, regional, secondary, or strongly polysemous. Do not auto-promote as strong animal interest evidence. |
| Reject or keep inventory-only | `tac`, `pesquera`, `acompañante`, `artículo`, `bonito`, `broma`, `cubrir`, `listado`, `manta`, `reo`, `jardín`, `manco`, `mozo`, `sancho`, `pico`, `celo`, `traidor` | The matched animal signal is acronymic, figurative, anatomical/behavioral, a facility/company/object, a verb action, or a secondary/obscure sense where the primary learner-facing meaning is non-animal. |

## Notable Cases

| Lemma | Current Evidence | Spot-Check Read |
| --- | --- | --- |
| `tac` | Tier D translation pattern matched `CAT scan; CT scan` and a secondary `CAT` row. | Mechanical false positive. This should be rejected if encountered in manual review. If similar acronym rows recur, add a policy-level exclusion. |
| `león` | Inventory-band category evidence because proper-name/place senses precede the common noun row. | Real animal word despite low score. This is a good example of why low score is not always wrong; proper-name ordering can suppress a valid animal sense. |
| `pico` | Inventory-band zoology topic for `crest`; primary translation is `beak`. | Animal-part evidence, not an animal topic by itself. Keep inventory-only unless a future taxonomy has animal anatomy. |
| `pescado` | Tier D pattern from `fish that has been caught; food fish`. | Real animal origin but stronger `food_cooking` candidate than animal preference evidence. Keep light/review-only. |
| `bonito`, `broma`, `manta`, `reo` | Zoology rows exist, but common non-animal meanings are prominent. | Real animal senses, but not safe for automatic strong animal admission without user review. |
| `cubrir`, `celo` | Zoology/reproduction senses. | Animal-domain behavior, not an animal-interest vocabulary item by default. |
| `traidor` | `snake` as a figurative translation. | Reject for animal topic. Figurative animal words should not count as animal-interest evidence unless the source explicitly marks an animal sense. |

## Policy Implications

1. Do not promote Tier D animal pattern matches without review.
2. Do not promote `inventory` animal rows automatically, even when the animal
   sense is real.
3. Treat primary exact animal translations as promising, but still respect
   secondary-sense and ambiguous-context penalties.
4. A future policy refinement could add exclusion rules for acronymic and
   idiomatic translations such as `CAT scan`, `CT scan`, `rabbit hole`, and
   figurative `snake`.
5. Proper-name-first rows like `león` show that source ordering can under-score
   true animal words; manual review should be allowed to rescue them.

## Current Recommendation

No broad policy rollback is needed. The low-confidence animal band is mostly
behaving correctly: it preserves recall for review while preventing automatic
promotion. The one clearly mechanical false positive in the review packet is
`tac`, and the rest should be handled by manual labels rather than by deleting
the entire signal family.
