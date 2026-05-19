# en-es Food/Cooking Signal Review And Coverage Plan

Status: active diagnostic
Role: SRS topic enrichment evidence
Last updated: 2026-05-19
Last verified: 2026-05-19 from food/cooking signal audits, current and full-source review labels, SPALEX 10k review packet, source-capacity audits, topic-overlay PoC, and focused tests
Purpose: record which food/cooking candidates are real, what the failure modes are, and how to get product-level coverage beyond the current conservative 2k baseline

Related artifacts:

- `../test_inputs/srs_food_cooking_signal_policy_en_es.json`
- `../test_inputs/srs_food_cooking_signal_review_labels_en_es_current.json`
- `../test_outputs/srs_food_cooking_existing_signal_audit_en_es_current_latest.md`
- `../test_outputs/srs_food_cooking_signal_review_packet_en_es_current_latest.md`
- `../test_outputs/srs_food_cooking_source_capacity_audit_en_es_latest.md`
- `../test_outputs/srs_food_cooking_topic_overlay_en_es_current_latest.json`
- `../test_outputs/srs_food_cooking_topic_overlay_poc_en_es_current_latest.md`
- `../test_inputs/srs_food_cooking_full_source_review_labels_en_es.json`
- `../test_outputs/srs_food_cooking_full_source_review_packet_en_es_latest.md`
- `../test_outputs/srs_food_cooking_full_source_review_precision_summary_en_es_latest.md`
- `../test_outputs/srs_food_cooking_existing_signal_audit_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_food_cooking_source_capacity_audit_en_es_spalex_10k_latest.md`
- `../test_outputs/srs_food_cooking_signal_review_packet_en_es_spalex_10k_latest.md`

## Review Result

The first food/cooking packet reviewed the full conservative current-CDE
candidate universe: `46 / 46` rows across `16 / 16` review cells.

Manual labels:

| Decision | Count | Meaning |
| --- | ---: | --- |
| `accept_strong_topic` | 19 | Direct food, drink, dish, ingredient, or cooking vocabulary. |
| `accept_light_topic` | 18 | Real food/cooking sense, but polysemous, secondary, regional, profession/venue, or animal/plant overlap. |
| `reject_secondary_or_obscure_sense` | 6 | Food/cooking sense exists but is too secondary or obscure for current overlay promotion. |
| `reject_wrong_topic` | 3 | Food appeared only incidentally or the category was misleading. |

So `37 / 46` rows are true food/cooking signals, but only `19 / 46` are strong
enough to treat as direct topic members without a light-weight caveat.

## Reject Lessons

The `9 / 46` rejected rows are useful policy evidence, not random noise.

Rejects cluster into four avoidable failure modes:

- secondary or obscure culinary senses, such as a dominant non-food word with a
  rare food/cooking meaning;
- generic verbs where food appears only as an example object;
- category overlap where the dominant lemma belongs to animals, plants, people,
  or another topic rather than food/cooking;
- broad Tier D gloss/translation patterns that capture incidental examples
  instead of primary learner-facing senses.

The natural avoidance rule is to keep Tier D and noisy overlap signals as
candidate-discovery channels only. They can enter review packets, but they
should not automatically become product topic evidence. For this current
overlay PoC, the rule is stricter: only reviewed `accept_strong_topic` and
`accept_light_topic` rows become overlay rows, while
`reject_secondary_or_obscure_sense` and `reject_wrong_topic` rows are excluded
and counted in the overlay policy.

## Precision By Evidence Type

| Evidence slice | Accepted | Strong | Light | Rejected | Takeaway |
| --- | ---: | ---: | ---: | ---: | --- |
| Tier A explicit `sense_topics` | 2 / 2 | 1 | 1 | 0 | Good, but sparse and sometimes secondary. |
| Tier B primary translations | 2 / 2 | 2 | 0 | 0 | High precision; expand the translation allowlist. |
| Tier C allowlisted categories/tags | 23 / 25 | 14 | 9 | 2 | Good mining signal after review; `legumes` and some vegetables need caution. |
| Tier D gloss/translation patterns | 10 / 17 | 2 | 8 | 7 | Useful recall probe, not safe for automatic lift without review. |

Best source-label patterns:

- `foods`: `7 / 7` accepted, `6` strong.
- `fruits`: `3 / 3` accepted, `2` strong.
- `meats`: `6 / 6` accepted, mostly light because animal/body senses compete.
- `seafood`: `3 / 3` accepted, `2` strong.
- `soups`, `spices`, and primary translations were clean in this packet.
- `food_gloss_pattern`: `9 / 14` accepted, but mostly light; keep review-gated.
- `food_translation_pattern`: `1 / 3` accepted; too broad without better primary-sense controls.

## Baseline Coverage Diagnosis

The current 46-row count is not the product ceiling. It is the 2k/current-CDE
calibration baseline: the intersection of the conservative food/cooking policy
with the current CDE frequency frontier.

The current-CDE source-capacity audit shows:

- full installed local Kaikki/Wiktionary food-signal lemmas: `2,122`;
- current frequency-frontier food-signal lemmas: `46`;
- food-signal lemmas outside the current frontier: `2,076`;
- high-confidence full-source rows: `152`;
- medium-confidence full-source rows: `1,142`.

Common food probes missing from the current frequency frontier include:
`comida`, `cocinar`, `cocina`, `agua`, `vino`, `pan`, `arroz`, `pollo`,
`carne`, `huevo`, `leche`, `queso`, `tomate`, `patata`, `azucar`, `sal`,
`sopa`, `fruta`, `verdura`, `pescado`, and `cerveza`.

That means the first recall bottleneck was not the food detector alone. The
current SRS frequency frontier was too narrow or mismatched for a satisfying
food/cooking user journey.

## SPALEX 10k Food/Cooking Frontier

The product-facing expansion question should be evaluated on the real 10k
frontier, not only the 2k/current baseline. A provisional SPALEX research pack
was rebuilt outside the repo and outside the installed app data root, then used
only for read-only audit artifacts. No raw source CSV or runtime frequency pack
was committed or installed.

The SPALEX 10k food/cooking audit reports:

- candidate lemmas measured: `10,000`;
- food/cooking candidates: `265` (`2.65%`);
- review-required candidates: `219`;
- tier counts: `A=15`, `B=31`, `C=122`, `D=97`;
- confidence bands: `high=39`, `medium=117`, `review=51`, `inventory=58`;
- strongest source-label counts: `food_gloss_pattern=78`, `foods=24`,
  `food_translation_pattern=19`, `cooking=16`, `meats=14`, `fish=11`,
  `vegetables=10`, `fruits=9`, `seafood=8`.

The SPALEX 10k source-capacity audit reports:

- full installed local Kaikki/Wiktionary food-signal lemmas: `2,122`;
- food-signal lemmas inside the SPALEX 10k frontier: `265`;
- food-signal lemmas outside the SPALEX 10k frontier: `1,857`.

The SPALEX 10k review packet is now the correct next manual-review surface:

- candidate universe: `265`;
- review rows: `96`;
- review cells covered: `62 / 62`;
- labeled rows: `0`;
- prior reviewed labels match `42 / 96` packet lemmas by lemma;
- `54 / 96` packet rows are fresh and need review before precision claims.

The practical correction is: use the current 46-row review to understand
baseline failure modes, but make product-scale food/cooking decisions from the
SPALEX 10k packet and any later promoted 10k overlay.

## Better Coverage Path

1. Promote only reviewed current rows into a diagnostic overlay.
   Use `accept_strong_topic` as membership `1.0`, `accept_light_topic` as a
   lower membership such as `0.65`, and exclude both reject decisions. This is
   enough to test the food preference path, but not enough to claim broad food
   coverage.

2. Review the SPALEX 10k packet before product claims.
   The installed Kaikki source already has much more food signal supply, and
   the rebuilt SPALEX 10k frontier includes common food lemmas that the current
   2k baseline missed. The next product-relevant step is to review the SPALEX
   10k packet, then derive precision by tier/source label before building a
   larger overlay.

3. Expand high-precision Tier B translation coverage.
   Primary-sense noun translations were clean in the current review. Add a
   reviewed food/drink/ingredient/cooking-term translation allowlist, including
   common items that the current frontier missed. This should stay data-driven
   and reviewed because words like color names, animal names, and idioms can
   create false positives.

4. Keep Tier C categories as high-recall review candidates.
   Category labels such as `foods`, `fruits`, `seafood`, `soups`, and `spices`
   were strong in this packet. Category labels that overlap plants/animals or
   non-food meanings should remain light or review-gated until sampled on the
   larger frontier.

5. Tighten Tier D before relying on it.
   Gloss patterns found real terms, but they also found incidental examples and
   obscure senses. Keep them useful for candidate discovery, not automatic
   product lift. Promote only after review labels prove a specific pattern or
   subpattern is safe.

6. Add a curated food seed overlay only if the 10k frontier still under-covers
   basics.
   If the reviewed 10k source still misses obvious staples, add a small
   provenance-bearing curated overlay for core food/drink/dining/cooking
   vocabulary. This should be explicit data, not hidden heuristics.

7. Validate through the existing admission lab.
   After a food overlay PoC exists, run the same preference-share and
   difficulty-depth checks used for animals/plants. The desired result is not
   all-food samples forever; it is a smooth, preference-strength-dependent lift
   with enough easy, mid, and hard food terms to avoid disappearing above one
   proficiency band.

## Overlay PoC Result

`scripts/testing/srs_food_cooking_topic_overlay_poc_en_es.py` builds the first
diagnostic food/cooking overlay candidate from the reviewed current labels.

The generated artifacts are:

- `../test_outputs/srs_food_cooking_topic_overlay_en_es_current_latest.json`
- `../test_outputs/srs_food_cooking_topic_overlay_poc_en_es_current_latest.json`
- `../test_outputs/srs_food_cooking_topic_overlay_poc_en_es_current_latest.md`

Current result:

- overlay rows: `37`;
- strong rows: `19`, with membership `1.0`;
- light rows: `18`, with membership `0.65`;
- excluded rejects: `6` secondary/obscure and `3` wrong-topic rows;
- baseline food/cooking overlay hits in the profile preview: `0`;
- with-overlay food/cooking hits in the profile preview: `7`;
- runtime policy changes: none;
- helper state mutation: none.

Only strong accepted rows are injected into `profile_topics` for the runnable
preview because the current profile-bootstrap scorer consumes topic presence
rather than scalar topic membership. Light rows remain in the overlay artifact
for future scalar-aware scoring or review decisions.

## Full-Source Expansion Packet

`scripts/testing/srs_food_cooking_full_source_review_packet_en_es.py` builds
the first broader review packet from installed local Kaikki/Wiktionary
food/cooking candidates, without downloading sources or touching runtime packs.

The generated artifacts are:

- `../test_outputs/srs_food_cooking_full_source_review_packet_en_es_latest.json`
- `../test_outputs/srs_food_cooking_full_source_review_packet_en_es_latest.md`

Current guarded result:

- full local source candidates: `2,122`;
- current-frontier candidates excluded as already reviewed: `46`;
- expansion candidates sampled from: `2,076`;
- review rows: `96`;
- review cells covered: `80 / 80`;
- labeled rows: `96`;
- strong accepts: `54`;
- light accepts: `37`;
- rejects: `5`.

This packet answers the immediate coverage question more directly than more
admission tuning: the installed source has enough food/cooking supply for a
larger vocabulary surface. A first guard pass now excludes the seven reviewed
false positives from the initial broad packet (`anaranjado`, `cha`, `claudia`,
`cocobolo`, `limonero`, `loco`, and `morena`) by using reviewed
lemma/source-label rejects and context rejects for color/tree/historical exact
translation matches.

The guarded sample accepted `91 / 96` rows, which is promising enough to keep
the broad local-source path alive, but still not an automatic product overlay.
The remaining rejects show the next false-positive classes to consider before
product lift:

- botanical or fodder terms that enter through broad `legumes`
  (`maní forrajero`);
- zoological fish terms that are not food/cooking vocabulary (`artrodiro`);
- proper-name-first entries with secondary fruit/fish senses (`pavía`, `reo`);
- Tier D gloss matches that describe eaters rather than foods (`carnívoro`).

The precision summary is
`../test_outputs/srs_food_cooking_full_source_review_precision_summary_en_es_latest.md`.
It reports:

- accepted rows: `91 / 96` (`94.8%`);
- Tier C accepted `44 / 48`;
- Tier B accepted `38 / 38`;
- high-confidence rows accepted `37 / 37`;
- review-band rows accepted `31 / 33`;
- flow assessment: the current source -> review -> precision -> overlay path is
  the right direction, but residual source-label false positives still need
  either another narrow guard pass or review-gated promotion before product lift.

## Immediate Next Slice

Review the SPALEX 10k food/cooking packet. Prior labels can be reused as
evidence for the `42` matching lemmas, but the packet should remain pending
until the full 10k sample is reviewed or explicitly accepted. After that, derive
the 10k precision summary and only then decide whether to build a diagnostic
10k overlay/admission preview. Do not promote a broad food/cooking overlay
directly from unreviewed source labels.
