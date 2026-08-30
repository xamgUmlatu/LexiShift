# en-ja Learner Difficulty First-200 Agent Review

Generated: 2026-06-27 JST

Scope: first `200` rows of
`docs/test_outputs/srs_learner_difficulty_final_ranking_en_ja_latest.csv`,
using final overlay variant
`exgate_orth_ec06_fl044_fh058_mr022_xcr0_ts04_te06_sp05`.

## Summary

The first `200` rows are broadly usable as an early learner pool, but not clean
enough to ship without a manual polish pass. The main problem is not obscure
vocabulary flooding the band. It is specific surface/reading rows that are
awkward as standalone SRS items: alternate readings, old written forms, or
compound-only readings.

## Proposed Manual Polish Rows

| Rank | Row | Score | Issue | Suggested action |
| ---: | --- | ---: | --- | --- |
| 3 | `ワイシャツ/わいしゃつ` | `0.001` | Too high priority in exact first-page order despite being easy. This is likely source-backed, but jarring before core verbs/nouns. | Do not treat as a model blocker. Consider a manual minimum around `0.08-0.12`, or let topic/lesson selection decide whether it appears early. |
| 31 | `居る/おる` | `0.014` | Specific reading/register is much later than `居る/いる`; too early as ordinary standalone vocabulary. | Manual raise or route as reading/register variant. |
| 55 | `何処/どこ` | `0.025` | Lexical item is beginner, but written form is not ideal for first-page learner display. | Prefer kana display `どこ`; no scalar raise needed if display can be fixed. |
| 78 | `後/ご` | `0.035` | Common morpheme/reading, but awkward as standalone early SRS word. | Review admission/display; likely route as affix/compound component, not early standalone vocab. |
| 118 | `道/どう` | `0.051` | Reading is common in compounds but questionable as standalone first-200 vocabulary. | Manual raise or route as compound-reading/component row. |
| 127 | `前/ぜん` | `0.053` | Frequency/difficulty is plausible, but standalone SRS item is awkward. | Review admission/display; likely route as affix/compound component. |
| 153 | `村/そん` | `0.057` | `村/むら` is normal early vocab; `そん` is compound/administrative reading and should not sit this early as standalone. | Manual raise or route as compound-reading/component row. |
| 179 | `下/もと` | `0.062` | Reading is not first-page-normal compared with `下/した` or `下/した`. | Manual review; likely raise or route as variant reading. |
| 186 | `明日/あす` | `0.063` | Reviewed expected value is `0.22`; final model treats raw JLPT exact support as decisive. | Manual raise to the reviewed target neighborhood. |
| 187 | `来たる/きたる` | `0.063` | Normalized-only JLPT row with weak core rank; too early for ordinary beginner presentation. | Manual raise or require exact/source confidence before early admission. |
| 191 | `奇麗/きれい` | `0.063` | Word is easy, but this written form is less learner-friendly than `きれい`/`綺麗`. | Prefer kana/common display; scalar raise only if display cannot be controlled. |
| 199 | `外/そと` | `0.065` | Meaning is early, but kanji display may be acceptable; less concerning than rows above. | Watch only. |

## Interpretation

This review strengthens the case for a final post-model override layer. The
model is doing reasonably well at broad level assignment, but it cannot always
decide whether a surface/reading pair is a good standalone SRS item. The product
should separate:

- scalar presentation level;
- display form preference;
- standalone/admission suitability;
- manual overrides for known bad surface+reading pairs.

## Next Review Scope

The next efficient pass is not all rows from `201` onward. It is flagged rows
through score `0.20`, especially:

- same-surface rare readings such as `夜/よ`;
- compound-only readings such as `道/どう`, `村/そん`, `前/ぜん`;
- normalized-only JLPT rows such as `来たる/きたる`;
- kana-preferred written forms where the word is easy but the displayed form is
  bad for beginners.
