# en-es Semantic Veto Full-Family Human Review Packet

- Status: `ok`
- Decision: `full_family_human_review_packet_ready`
- Generated: `2026-05-07T01:24:14Z`
- Review families: `58` / `58`
- Review cases: `206`
- Trusted rows: `0`

## Review Rule

Every semantic decision in this packet is a proposal only. A family or case becomes trusted only after the user explicitly approves it.

## Summary

| Key | Value |
| --- | --- |
| `dataset_family_count` | `58` |
| `review_family_count` | `58` |
| `review_case_count` | `206` |
| `pilot_family_count_requested` | `58` |
| `source_band_counts` | `{"missing": 3, "zipf_3_to_4_mid": 14, "zipf_4_to_5_common": 15, "zipf_5_plus_very_common": 16, "zipf_below_3_rare": 10}` |
| `case_type_counts` | `{"phrase_no_winner": 58, "positive_active": 73, "shadow_negative": 75}` |
| `human_review_status_counts` | `{"pending_user_review": 58}` |
| `active_sense_status_counts` | `{"pending_user_review": 58}` |
| `proposed_row_quality_status_counts` | `{"no_winner_template_control": 58, "pending_user_review": 148}` |
| `weakness_counts` | `{"active_context_template_circular": 32, "active_target_sense_not_audited": 58, "evidence_context_overlap_risk": 119, "no_winner_token_boundary_artifact": 13, "shadow_competitor_target_not_reviewed": 75, "shadow_negative_synthetic_definition_context": 40, "source_form_artifact_risk": 3}` |
| `weakness_severity_counts` | `{"blocking": 75, "diagnostic_only": 191, "review_required": 74}` |
| `packet_weaknesses` | `[]` |
| `trusted_family_count` | `0` |
| `trusted_case_count` | `0` |

## Requested User Decisions

- For each family: decide whether the active English sense really matches the Spanish target.
- For each case: approve, reject, rewrite, or mark diagnostic-only.
- For phrase/no-winner rows: choose the subtype or replace the template with a realistic negative context.

## Weakness Taxonomy

Named weakness classes that keep semantic-veto test rows from being treated as trusted evaluation data until reviewed or repaired.

| ID | Scope | Severity | Detection | Meaning | Avoid By | Review Action |
| --- | --- | --- | --- | --- | --- | --- |
| `active_target_sense_not_audited` | `family` | `review_required` | `automatic_default` | The English active sense has not been confirmed to match the Spanish target lemma. | Require explicit user approval of active_sense_status before trusted scoring. | Mark active_sense_status as aligned, uncertain, mismatched, or diagnostic_exception. |
| `source_target_mapping_questionable` | `family` | `blocking` | `manual_or_llm_assisted` | The source-target pair appears semantically wrong or too loose for gold evaluation. | Exclude from trusted evaluation or correct the active evidence/source-target family. | Reject the family or mark it source_mapping_questionable with notes. |
| `source_form_artifact_risk` | `family` | `review_required` | `automatic_heuristic` | The English source form is missing a normal frequency band or looks like an artifact token. | Confirm that the source form is a real browser-facing trigger before using it as product evidence. | Approve as real, rewrite the source form, or mark diagnostic_only. |
| `active_context_template_circular` | `case` | `diagnostic_only` | `automatic_heuristic` | The positive context is a generated template that tells the scorer the intended sense. | Use independent browser-like or corpus contexts that do not mention the target or definition directly. | Rewrite before trusted scoring or keep as a template control. |
| `evidence_context_overlap_risk` | `case` | `diagnostic_only` | `automatic_heuristic` | The context likely repeats words from the evidence source, inflating lexical overlap scorers. | Keep evidence and evaluation contexts independent. | Replace with independent context before using TF-IDF or lexical-score claims. |
| `shadow_negative_synthetic_definition_context` | `case` | `diagnostic_only` | `automatic_heuristic` | The shadow-negative row is a generated definition sentence rather than a natural negative context. | Use real alternate-sense examples or human-authored browser-like negatives. | Rewrite before trusted scoring or keep as a diagnostic control. |
| `shadow_competitor_target_not_reviewed` | `case` | `blocking` | `automatic_heuristic` | The shadow target is a placeholder such as '<source> alternate sense N' rather than a reviewed Spanish competitor replacement. | Require a real alternate Spanish target and bilingual source-target review before trusted shadow-negative scoring. | Provide a reviewed competitor target, reject the row, or mark it diagnostic_only. |
| `shadow_negative_may_still_match_target` | `case` | `review_required` | `manual_or_llm_assisted` | The supposed shadow-negative context may still be a valid use of the Spanish target. | Require bilingual semantic review of shadow rows. | Approve as abstain, change gold_decision to replace, or reject the row. |
| `duplicate_case_sentence` | `case` | `blocking` | `automatic_exact` | Two rows in the same family use the same sentence and should not count as independent tests. | Deduplicate or author distinct contexts. | Drop one row or rewrite it. |
| `phrase_no_winner_template_control_only` | `case` | `diagnostic_only` | `automatic_heuristic` | The no-winner row is a repeated metalinguistic/listed-term template. | Add realistic no-winner subtypes such as named entity, phrase collision, malformed fragment, or natural nonreplacement context. | Keep as control only or replace with a realistic no-winner row. |
| `no_winner_token_boundary_artifact` | `case` | `review_required` | `automatic_heuristic` | The no-winner row contains the source only inside a larger token, file name, identifier, or punctuation shape, so it may not exercise the runtime replacement trigger. | Use a standalone visible source token or phrase in a browser-like no-winner context when testing trigger-level abstention. | Rewrite with a standalone source phrase, confirm the runtime trigger behavior intentionally, or mark diagnostic_only. |
| `review_markdown_missing_case_fields` | `packet` | `format_blocking` | `manual_or_snapshot` | The Markdown view does not expose per-case fields needed for efficient user review. | Render per-case review fields or a structured table with explicit action columns. | Fix packet rendering before large human review. |
| `pilot_not_hard_case_representative` | `packet` | `review_required` | `automatic_summary` | The pilot packet does not include enough high-polysemy, cross-POS, phrase/no-winner, and shadow-negative cases to test the review workflow. | Balance review packets across source band, polysemy, POS shape, and case type. | Regenerate or supplement the pilot before drawing workflow conclusions. |

## Packet Weaknesses

- `none`

### full_family_review:001: break -> quebrar

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `high_10_plus` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `quebrar`
- POS: `noun`
- Label: break -> quebrar
- Gloss: some abrupt occurrence that interrupts an ongoing activity

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | some abrupt occurrence that interrupts an ongoing activity | the telephone is an annoying interruption; there was a break in the action when a player was hurt |
| 2 | `v` | terminate or end | She interrupted her pregnancy; break a lucky streak |
| 3 | `n` | an unexpected piece of good luck | he finally got his big break |
| 4 | `v` | become separated into pieces or fragments | The figurine broke; The freshly baked loaf fell apart |
| 5 | `n` | (geology) a crack in the earth's crust resulting from the displacement of one side with respect to the other | they built it right over a geological fault; he studied the faulting of the earth's crust |
| 6 | `v` | render inoperable or ineffective | You broke the alarm clock when you took it apart! |
| 7 | `n` | a personal or social separation (as between opposing factions) | they hoped to avoid a break in relations |
| 8 | `v` | ruin completely | He busted my radio! |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:break:quebrar:001` | `positive_active` | `replace` | `pending_user_review` |  | the telephone is an annoying break | pending user review |
| `en-es:full-family-representative:break:quebrar:002` | `positive_active` | `replace` | `pending_user_review` |  | there was a break in the action when a player was hurt | pending user review |
| `en-es:full-family-representative:break:quebrar:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | break a lucky streak | pending user review |
| `en-es:full-family-representative:break:quebrar:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | he finally got his big break | pending user review |
| `en-es:full-family-representative:break:quebrar:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "break_notes.txt". | pending user review |

### full_family_review:002: bar -> cercar

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_below_3_rare`
- Polysemy/POS: `high_10_plus` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `cercar`
- POS: `noun`
- Label: bar -> cercar
- Gloss: a room or establishment where alcoholic drinks are served over a counter

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a room or establishment where alcoholic drinks are served over a counter | he drowned his sorrows in whiskey at the bar |
| 2 | `v` | prevent from entering; keep out | He was barred from membership in the club |
| 3 | `n` | a counter where you can obtain food or drink | he bought a hot dog and a coke at the bar |
| 4 | `v` | render unsuitable for passage | block the way; barricade the streets |
| 5 | `n` | a rigid piece of metal or wood; usually used as a fastening or obstruction or weapon | there were bars in the windows to prevent escape |
| 6 | `v` | expel, as if by official decree | he was banished from his own country |
| 7 | `n` | musical notation for a repeating pattern of musical beats | the orchestra omitted the last twelve bars of the song |
| 8 | `v` | secure with, or as if with, bars | He barred the door |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:bar:cercar:001` | `positive_active` | `replace` | `pending_user_review` |  | he drowned his sorrows in whiskey at the bar | pending user review |
| `en-es:full-family-representative:bar:cercar:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, bar referred to prevent from entering; keep out, not the target replacement. | pending user review |
| `en-es:full-family-representative:bar:cercar:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | he bought a hot dog and a coke at the bar | pending user review |
| `en-es:full-family-representative:bar:cercar:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "bar_notes.txt". | pending user review |

### full_family_review:003: offset -> distancia

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `high_10_plus` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `distancia`
- POS: `noun`
- Label: offset -> distancia
- Gloss: the time at which something is supposed to begin

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | the time at which something is supposed to begin | they got an early start; she knew from the get-go that he was the man for her |
| 2 | `v` | compensate for or counterbalance | offset deposits and withdrawals |
| 3 | `n` | a compensating equivalent |  |
| 4 | `v` | make up for | His skills offset his opponent's superior strength |
| 5 | `n` | a horizontal branch from the base of plant that produces new plants from buds at its tips |  |
| 6 | `v` | cause (printed matter) to transfer or smear onto another surface |  |
| 7 | `n` | a natural consequence of development |  |
| 8 | `v` | create an offset in | offset a wall |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:offset:distancia:001` | `positive_active` | `replace` | `pending_user_review` |  | they got an early offset | pending user review |
| `en-es:full-family-representative:offset:distancia:002` | `positive_active` | `replace` | `pending_user_review` |  | she knew from the offset that he was the man for her | pending user review |
| `en-es:full-family-representative:offset:distancia:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | offset deposits and withdrawals | pending user review |
| `en-es:full-family-representative:offset:distancia:004` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, offset referred to a compensating equivalent, not the target replacement. | pending user review |
| `en-es:full-family-representative:offset:distancia:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "offset" as a saved search query. | pending user review |

### full_family_review:004: bridle -> reprimir

- Source band: `zipf_below_3_rare`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `medium_4_to_9` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `reprimir`
- POS: `noun`
- Label: bridle -> reprimir
- Gloss: headgear for a horse; includes a headstall and bit and reins to give the rider or driver control

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | headgear for a horse; includes a headstall and bit and reins to give the rider or driver control |  |
| 2 | `v` | anger or take offense | She bridled at his suggestion to elope |
| 3 | `n` | the act of restraining power or action or limiting excess | his common sense is a bridle to his quick temper |
| 4 | `v` | put a bridle on | bridle horses |
| 5 | `v` | respond to the reins, as of horses |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:bridle:reprimir:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used bridle to describe headgear for a horse; includes a headstall and bit and reins to give the rider or driver control. | pending user review |
| `en-es:full-family-representative:bridle:reprimir:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, bridle referred to anger or take offense, not the target replacement. | pending user review |
| `en-es:full-family-representative:bridle:reprimir:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | his common sense is a bridle to his quick temper | pending user review |
| `en-es:full-family-representative:bridle:reprimir:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "bridle" as a saved search query. | pending user review |

### full_family_review:005: december -> diciembre

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `diciembre`
- POS: `noun`
- Label: december -> diciembre
- Gloss: the last (12th) month of the year

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | the last (12th) month of the year |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:december:diciembre:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used december to describe the last (12th) month of the year. | pending user review |
| `en-es:full-family-representative:december:diciembre:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "december" in the exported report. | pending user review |

### full_family_review:006: emotion -> emoción

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `emoción`
- POS: `noun`
- Label: emotion -> emoción
- Gloss: any strong feeling

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | any strong feeling |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:emotion:emocion:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used emotion to describe any strong feeling. | pending user review |
| `en-es:full-family-representative:emotion:emocion:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "emotion" in the exported report. | pending user review |

### full_family_review:007: dentist -> dentista

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `dentista`
- POS: `noun`
- Label: dentist -> dentista
- Gloss: a person qualified to practice dentistry

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a person qualified to practice dentistry |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:dentist:dentista:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used dentist to describe a person qualified to practice dentistry. | pending user review |
| `en-es:full-family-representative:dentist:dentista:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "dentist" opened an empty archive page. | pending user review |

### full_family_review:008: bouillon -> caldo

- Source band: `zipf_below_3_rare`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `caldo`
- POS: `noun`
- Label: bouillon -> caldo
- Gloss: a clear seasoned broth

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a clear seasoned broth |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:bouillon:caldo:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used bouillon to describe a clear seasoned broth. | pending user review |
| `en-es:full-family-representative:bouillon:caldo:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "bouillon_notes.txt". | pending user review |

### full_family_review:009: control -> gobernar

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `high_10_plus` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `gobernar`
- POS: `noun`
- Label: control -> gobernar
- Gloss: power to direct or determine

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | power to direct or determine | under control |
| 2 | `v` | exercise authoritative control or power over | control the budget; Command the military forces |
| 3 | `n` | a relation of constraint of one entity (thing or person or group) by another | measures for the control of disease; they instituted controls over drinking on campus |
| 4 | `v` | lessen the intensity of; temper; hold in restraint; hold or keep within limits | moderate your alcohol intake; hold your tongue |
| 5 | `n` | (physiology) regulation or maintenance of a function or action or reflex etc | the timing and control of his movements were unimpaired; he had lost control of his sphincters |
| 6 | `v` | handle and cause to function | do not operate machinery after imbibing alcohol; control the lever |
| 7 | `n` | a standard against which other conditions can be compared in a scientific experiment | the control condition was inappropriate for the conclusions he wished to draw |
| 8 | `v` | maintain influence over (others or oneself) skillfully, usually to one's advantage | She manipulates her boss; She is a very controlling mother and doesn't let her children grow up |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:control:gobernar:001` | `positive_active` | `replace` | `pending_user_review` |  | under control | pending user review |
| `en-es:full-family-representative:control:gobernar:002` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | control the budget | pending user review |
| `en-es:full-family-representative:control:gobernar:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | measures for the control of disease | pending user review |
| `en-es:full-family-representative:control:gobernar:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "control" in the exported report. | pending user review |

### full_family_review:010: demand -> deducción

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `high_10_plus` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `deducción`
- POS: `noun`
- Label: demand -> deducción
- Gloss: an urgent or peremptory request

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | an urgent or peremptory request | his demands for attention were unceasing |
| 2 | `v` | request urgently and forcefully | The victim's family is demanding compensation; The boss demanded that he be fired immediately |
| 3 | `n` | the ability and desire to purchase goods and services | the automobile reduced the demand for buggywhips; the demand exceeded the supply |
| 4 | `v` | require as useful, just, or proper | It takes nerve to do what she did; success usually requires hard work |
| 5 | `n` | required activity | the requirements of his work affected his health; there were many demands on his time |
| 6 | `v` | claim as due or just | The bank demanded payment of the loan; The banks demand the check |
| 7 | `n` | the act of demanding | the kidnapper's exorbitant demands for money |
| 8 | `v` | lay legal claim to |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:demand:deduccion:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used demand to describe an urgent or peremptory request. | pending user review |
| `en-es:full-family-representative:demand:deduccion:002` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | They demand to move | pending user review |
| `en-es:full-family-representative:demand:deduccion:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | the automobile reduced the demand for buggywhips | pending user review |
| `en-es:full-family-representative:demand:deduccion:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "demand" in the exported report. | pending user review |

### full_family_review:011: stall -> cuadra

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `high_10_plus` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `cuadra`
- POS: `noun`
- Label: stall -> cuadra
- Gloss: a compartment in a stable where a single animal is confined and fed

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a compartment in a stable where a single animal is confined and fed |  |
| 2 | `v` | postpone doing what one should be doing | He did not want to write the letter and procrastinated for days; They stall a long time |
| 3 | `n` | small area set off by walls for special use |  |
| 4 | `v` | come to a stop | The car stalled in the driveway |
| 5 | `n` | a booth where articles are displayed for sale |  |
| 6 | `v` | deliberately delay an event or action | she doesn't want to write the report, so she is stalling |
| 7 | `n` | a malfunction in the flight of an aircraft in which there is a sudden loss of lift that results in a downward plunge | the plane went into a stall and I couldn't control it |
| 8 | `v` | put into, or keep in, a stall | Stall the horse |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:stall:cuadra:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used stall to describe a compartment in a stable where a single animal is confined and fed. | pending user review |
| `en-es:full-family-representative:stall:cuadra:002` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | They stall a long time | pending user review |
| `en-es:full-family-representative:stall:cuadra:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, stall referred to small area set off by walls for special use, not the target replacement. | pending user review |
| `en-es:full-family-representative:stall:cuadra:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "stall" as a saved search query. | pending user review |

### full_family_review:012: rumanian -> rumano

- Source band: `zipf_below_3_rare`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `rumano`
- POS: `adjective`
- Label: rumanian -> rumano
- Gloss: of or relating to or characteristic of the country of Romania or its people or languages

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `a` | of or relating to or characteristic of the country of Romania or its people or languages | Romanian folk music |
| 2 | `n` | an eastern Romance language spoken in Romania |  |
| 3 | `n` | a native or inhabitant of Romania |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:rumanian:rumano:001` | `positive_active` | `replace` | `pending_user_review` |  | rumanian folk music | pending user review |
| `en-es:full-family-representative:rumanian:rumano:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, rumanian referred to an eastern Romance language spoken in Romania, not the target replacement. | pending user review |
| `en-es:full-family-representative:rumanian:rumano:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, rumanian referred to a native or inhabitant of Romania, not the target replacement. | pending user review |
| `en-es:full-family-representative:rumanian:rumano:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "rumanian" opened an empty archive page. | pending user review |

### full_family_review:013: june -> junio

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `junio`
- POS: `noun`
- Label: june -> junio
- Gloss: the month following May and preceding July

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | the month following May and preceding July |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:june:junio:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used june to describe the month following May and preceding July. | pending user review |
| `en-es:full-family-representative:june:junio:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "june_notes.txt". | pending user review |

### full_family_review:014: pub -> taberna

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `taberna`
- POS: `noun`
- Label: pub -> taberna
- Gloss: tavern consisting of a building with a bar and public rooms; often provides light meals

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | tavern consisting of a building with a bar and public rooms; often provides light meals |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:pub:taberna:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used pub to describe tavern consisting of a building with a bar and public rooms; often provides light meals. | pending user review |
| `en-es:full-family-representative:pub:taberna:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "pub_notes.txt". | pending user review |

### full_family_review:015: salesman -> vendedor

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `vendedor`
- POS: `noun`
- Label: salesman -> vendedor
- Gloss: a man salesperson

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a man salesperson |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:salesman:vendedor:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used salesman to describe a man salesperson. | pending user review |
| `en-es:full-family-representative:salesman:vendedor:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "salesman" as a saved search query. | pending user review |

### full_family_review:016: handiwork -> artesanía

- Source band: `zipf_below_3_rare`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `artesanía`
- POS: `noun`
- Label: handiwork -> artesanía
- Gloss: a work produced by hand labor

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a work produced by hand labor |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:handiwork:artesania:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used handiwork to describe a work produced by hand labor. | pending user review |
| `en-es:full-family-representative:handiwork:artesania:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "handiwork_notes.txt". | pending user review |

### full_family_review:017: continue -> durar

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `high_10_plus` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `durar`
- POS: `verb`
- Label: continue -> durar
- Gloss: continue a certain state, condition, or activity

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `v` | continue a certain state, condition, or activity | Keep on working!; We continued to work into the night |
| 2 | `v` | continue talking | ‘I know it's hard,’ he continued, ‘but there is no choice’; carry on — pretend we are not in the room |
| 3 | `v` | keep or maintain in unaltered condition; cause to remain or last | preserve the peace in the family; continue the family tradition |
| 4 | `v` | move ahead; travel onward in time or space | We proceeded towards Washington; She continued in the direction of the hills |
| 5 | `v` | allow to remain in a place or position or maintain a property or feature | We cannot continue several servants any longer; She retains a lawyer |
| 6 | `v` | do something repeatedly and showing no intention to stop | We continued our research into the cause of the illness; The landlord persists in asking us to move |
| 7 | `v` | continue after an interruption | The demonstration continued after a break for lunch |
| 8 | `v` | continue in a place, position, or situation | After graduation, she stayed on in Cambridge as a student adviser; Stay with me, please |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:continue:durar:001` | `positive_active` | `replace` | `pending_user_review` |  | continue on working! | pending user review |
| `en-es:full-family-representative:continue:durar:002` | `positive_active` | `replace` | `pending_user_review` |  | continue smiling | pending user review |
| `en-es:full-family-representative:continue:durar:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | continue — pretend we are not in the room | pending user review |
| `en-es:full-family-representative:continue:durar:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | continue the peace in the family | pending user review |
| `en-es:full-family-representative:continue:durar:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "continue" opened an empty archive page. | pending user review |

### full_family_review:018: begin -> comenzar

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `high_10_plus` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `comenzar`
- POS: `verb`
- Label: begin -> comenzar
- Gloss: take the first step or steps in carrying out an action

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `v` | take the first step or steps in carrying out an action | We began working at dawn; Who will start? |
| 2 | `v` | have a beginning, in a temporal, spatial, or evaluative sense | The DMZ begins right over the hill; The second movement begins after the Allegro |
| 3 | `v` | set in motion, cause to start | The U.S. started a war in the Middle East; The Iraqis began hostilities |
| 4 | `v` | begin to speak or say | ‘Now listen, friends’, he began; They won't begin the story |
| 5 | `v` | be the first item or point, constitute the beginning or start, come first in a series | The number ‘one’ begins the sequence; A terrible murder begins the novel |
| 6 | `v` | have a beginning, of a temporal event | WW II began in 1939 when Hitler marched into Poland; The company's Asia tour begins next month |
| 7 | `v` | have a beginning characterized in some specified way | The novel begins with a murder; My property begins with the three maple trees |
| 8 | `v` | begin an event that is implied and limited by the nature or inherent function of the direct object | begin a cigar; She started the soup while it was still hot |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:begin:comenzar:001` | `positive_active` | `replace` | `pending_user_review` |  | Who will begin? | pending user review |
| `en-es:full-family-representative:begin:comenzar:002` | `positive_active` | `replace` | `pending_user_review` |  | begin working as soon as the sun rises! | pending user review |
| `en-es:full-family-representative:begin:comenzar:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | Prices for these homes begin at $250,000 | pending user review |
| `en-es:full-family-representative:begin:comenzar:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | begin a new chapter in your life | pending user review |
| `en-es:full-family-representative:begin:comenzar:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "begin" opened an empty archive page. | pending user review |

### full_family_review:019: chic -> elegante

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `low_1_to_3` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `elegante`
- POS: `adjective`
- Label: chic -> elegante
- Gloss: elegant and stylish

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `a` | elegant and stylish | chic elegance; a smart new dress |
| 2 | `n` | elegance by virtue of being fashionable |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:chic:elegante:001` | `positive_active` | `replace` | `pending_user_review` |  | chic elegance | pending user review |
| `en-es:full-family-representative:chic:elegante:002` | `positive_active` | `replace` | `pending_user_review` |  | a chic new dress | pending user review |
| `en-es:full-family-representative:chic:elegante:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, chic referred to elegance by virtue of being fashionable, not the target replacement. | pending user review |
| `en-es:full-family-representative:chic:elegante:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "chic" as a saved search query. | pending user review |

### full_family_review:020: billow -> oleaje

- Source band: `zipf_below_3_rare`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `medium_4_to_9` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `oleaje`
- POS: `noun`
- Label: billow -> oleaje
- Gloss: a large sea wave

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a large sea wave |  |
| 2 | `v` | rise up as if in waves | smoke billowed up into the sky |
| 3 | `v` | move with great difficulty | The soldiers billowed across the muddy riverbed |
| 4 | `v` | rise and move, as in waves or billows | The army surged forward |
| 5 | `v` | become inflated | The sails ballooned |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:billow:oleaje:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used billow to describe a large sea wave. | pending user review |
| `en-es:full-family-representative:billow:oleaje:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, billow referred to rise up as if in waves, not the target replacement. | pending user review |
| `en-es:full-family-representative:billow:oleaje:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, billow referred to move with great difficulty, not the target replacement. | pending user review |
| `en-es:full-family-representative:billow:oleaje:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "billow" opened an empty archive page. | pending user review |

### full_family_review:021: among -> entre

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `entre`
- POS: ``
- Label: among -> entre
- Gloss: the intended dictionary sense of among

**Candidate WordNet Senses**

_No candidate WordNet senses found._

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:among:entre:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used among to describe the intended dictionary sense of among. | pending user review |
| `en-es:full-family-representative:among:entre:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "among" opened an empty archive page. | pending user review |

### full_family_review:022: recover -> sanar

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `sanar`
- POS: ``
- Label: recover -> sanar
- Gloss: get or find back; recover the use of

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `v-1` | get or find back; recover the use of | She regained control of herself; She found her voice and replied quickly |
| 2 | `v-2` | cover anew | recover a chair |
| 3 | `v-1` | get over an illness or shock | The patient is recuperating |
| 4 | `v-1` | regain a former condition after a financial loss | We expect the stocks to recover to $2.90; The company managed to recuperate |
| 5 | `v-1` | regain or make up for | recuperate one's losses |
| 6 | `v-1` | reuse (materials from waste products) |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:recover:sanar:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used recover to describe get or find back; recover the use of. | pending user review |
| `en-es:full-family-representative:recover:sanar:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "recover_notes.txt". | pending user review |

### full_family_review:023: adjoining -> contiguo

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_below_3_rare`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `contiguo`
- POS: ``
- Label: adjoining -> contiguo
- Gloss: the intended dictionary sense of adjoining

**Candidate WordNet Senses**

_No candidate WordNet senses found._

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:adjoining:contiguo:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used adjoining to describe the intended dictionary sense of adjoining. | pending user review |
| `en-es:full-family-representative:adjoining:contiguo:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "adjoining" as a saved search query. | pending user review |

### full_family_review:024: argentinean -> argentino

- Source band: `zipf_below_3_rare`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `argentino`
- POS: ``
- Label: argentinean -> argentino
- Gloss: the intended dictionary sense of argentinean

**Candidate WordNet Senses**

_No candidate WordNet senses found._

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:argentinean:argentino:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used argentinean to describe the intended dictionary sense of argentinean. | pending user review |
| `en-es:full-family-representative:argentinean:argentino:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "argentinean" as a saved search query. | pending user review |

### full_family_review:025: heart -> corazón

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `high_10_plus` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `corazón`
- POS: `noun`
- Label: heart -> corazón
- Gloss: the locus of feelings and intuitions

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | the locus of feelings and intuitions | in your heart you know it is true; her story would melt your bosom |
| 2 | `n` | the hollow muscular organ located behind the sternum and between the lungs; its rhythmic contractions move the blood through the body | he stood still, his heart thumping wildly |
| 3 | `n` | the courage to carry on | he kept fighting on pure spunk; you haven't got the heart for baseball |
| 4 | `n` | an area that is approximately central within some larger region | it is in the center of town; they ran forward into the heart of the struggle |
| 5 | `n` | the choicest or most essential or most vital part of some idea or experience | the gist of the prosecutor's argument; the heart and soul of the Republican Party |
| 6 | `n` | an inclination or tendency of a certain kind | he had a change of heart |
| 7 | `n` | a plane figure with rounded sides curving inward at the top and intersecting at the bottom; conventionally used on playing cards and valentines | he drew a heart and called it a valentine |
| 8 | `n` | a firm rather dry variety meat (usually beef or veal) | a five-pound beef heart will serve six |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:heart:corazon:001` | `positive_active` | `replace` | `pending_user_review` |  | in your heart you know it is true | pending user review |
| `en-es:full-family-representative:heart:corazon:002` | `positive_active` | `replace` | `pending_user_review` |  | her story would melt your heart | pending user review |
| `en-es:full-family-representative:heart:corazon:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | he stood still, his heart thumping wildly | pending user review |
| `en-es:full-family-representative:heart:corazon:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | he kept fighting on pure heart | pending user review |
| `en-es:full-family-representative:heart:corazon:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "heart_notes.txt". | pending user review |

### full_family_review:026: grow -> acontecer

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_below_3_rare`
- Polysemy/POS: `high_10_plus` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `acontecer`
- POS: `verb`
- Label: grow -> acontecer
- Gloss: pass into a condition gradually, take on a specific property or attribute; become

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `v` | pass into a condition gradually, take on a specific property or attribute; become | The weather turned nasty; She grew angry |
| 2 | `v` | become larger, greater, or bigger; expand or gain | The problem grew too large for me; Her business grew fast |
| 3 | `v` | increase in size by natural process | Corn doesn't grow here; In these forests, mushrooms grow under the trees |
| 4 | `v` | cause to grow or develop | He grows vegetables in his backyard; They grow rye in the field |
| 5 | `v` | develop and reach maturity; undergo maturation | He matured fast; The child grew fast |
| 6 | `v` | come into existence; take on form or shape | A new religious movement originated in that country; a love that sprang up from friendship |
| 7 | `v` | cultivate by growing, often involving improvements by means of agricultural techniques | The Bordeaux region produces great red wines; They produce good ham in Parma |
| 8 | `v` | come to have or undergo a change of (physical features and attributes) | He grew a beard; The patient developed abdominal pains |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:grow:acontecer:001` | `positive_active` | `replace` | `pending_user_review` |  | John will grow angry | pending user review |
| `en-es:full-family-representative:grow:acontecer:002` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | The business is going to grow | pending user review |
| `en-es:full-family-representative:grow:acontecer:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | Corn doesn't grow here | pending user review |
| `en-es:full-family-representative:grow:acontecer:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "grow" as a saved search query. | pending user review |

### full_family_review:027: cite -> mencionar

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `medium_4_to_9` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `mencionar`
- POS: `noun`
- Label: cite -> mencionar
- Gloss: a short note recognizing a source of information or of a quoted passage

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a short note recognizing a source of information or of a quoted passage | the student's essay failed to list several important citations; the acknowledgments are usually printed at the front of a book |
| 2 | `v` | make reference to | he was named in connection with the invention |
| 3 | `v` | commend | he was cited for his outstanding achievements; Sam and Sue cite the movie |
| 4 | `v` | refer to | he referenced his colleagues' work |
| 5 | `v` | repeat a passage from | He quoted the Bible to her; The parents cite a French poem to the children |
| 6 | `v` | refer to for illustration or proof | He said he could quote several instances of this behavior |
| 7 | `v` | advance evidence for |  |
| 8 | `v` | call in an official matter, such as to attend court |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:cite:mencionar:001` | `positive_active` | `replace` | `pending_user_review` |  | the article includes cite of similar clinical cases | pending user review |
| `en-es:full-family-representative:cite:mencionar:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, cite referred to make reference to, not the target replacement. | pending user review |
| `en-es:full-family-representative:cite:mencionar:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | Sam and Sue cite the movie | pending user review |
| `en-es:full-family-representative:cite:mencionar:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "cite" opened an empty archive page. | pending user review |

### full_family_review:028: snore -> roncar

- Source band: `zipf_below_3_rare`
- Target band: `zipf_below_3_rare`
- Polysemy/POS: `low_1_to_3` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `roncar`
- POS: `noun`
- Label: snore -> roncar
- Gloss: the rattling noise produced when snoring

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | the rattling noise produced when snoring |  |
| 2 | `v` | breathe noisily during one's sleep | she complained that her husband snores |
| 3 | `n` | the act of snoring or producing a snoring sound |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:snore:roncar:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used snore to describe the rattling noise produced when snoring. | pending user review |
| `en-es:full-family-representative:snore:roncar:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, snore referred to breathe noisily during one's sleep, not the target replacement. | pending user review |
| `en-es:full-family-representative:snore:roncar:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, snore referred to the act of snoring or producing a snoring sound, not the target replacement. | pending user review |
| `en-es:full-family-representative:snore:roncar:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "snore" opened an empty archive page. | pending user review |

### full_family_review:029: upon -> sobre

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `sobre`
- POS: ``
- Label: upon -> sobre
- Gloss: the intended dictionary sense of upon

**Candidate WordNet Senses**

_No candidate WordNet senses found._

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:upon:sobre:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used upon to describe the intended dictionary sense of upon. | pending user review |
| `en-es:full-family-representative:upon:sobre:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "upon" opened an empty archive page. | pending user review |

### full_family_review:030: adjoining -> vecino

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `vecino`
- POS: ``
- Label: adjoining -> vecino
- Gloss: the intended dictionary sense of adjoining

**Candidate WordNet Senses**

_No candidate WordNet senses found._

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:adjoining:vecino:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used adjoining to describe the intended dictionary sense of adjoining. | pending user review |
| `en-es:full-family-representative:adjoining:vecino:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "adjoining" as a saved search query. | pending user review |

### full_family_review:031: turnon -> poner

- Source band: `zipf_below_3_rare`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `poner`
- POS: ``
- Label: turnon -> poner
- Gloss: the intended dictionary sense of turnon

**Candidate WordNet Senses**

_No candidate WordNet senses found._

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:turnon:poner:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used turnon to describe the intended dictionary sense of turnon. | pending user review |
| `en-es:full-family-representative:turnon:poner:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "turnon" opened an empty archive page. | pending user review |

### full_family_review:032: current -> contemporáneo

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `medium_4_to_9` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `contemporáneo`
- POS: `adjective`
- Label: current -> contemporáneo
- Gloss: occurring in or belonging to the present time

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `a` | occurring in or belonging to the present time | current events; the current topic |
| 2 | `n` | a flow of electricity through a conductor | the current was measured in amperes |
| 3 | `n` | a steady flow of a fluid (usually from natural causes) | the raft floated downstream on the current; he felt a stream of air |
| 4 | `n` | dominant course (suggestive of running water) of successive events or ideas | two streams of development run through American history; stream of consciousness |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:current:contemporaneo:001` | `positive_active` | `replace` | `pending_user_review` |  | current events | pending user review |
| `en-es:full-family-representative:current:contemporaneo:002` | `positive_active` | `replace` | `pending_user_review` |  | the current topic | pending user review |
| `en-es:full-family-representative:current:contemporaneo:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | the current was measured in amperes | pending user review |
| `en-es:full-family-representative:current:contemporaneo:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | the raft floated downstream on the current | pending user review |
| `en-es:full-family-representative:current:contemporaneo:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "current" in the exported report. | pending user review |

### full_family_review:033: shed -> puesto

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `medium_4_to_9` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `puesto`
- POS: `adjective`
- Label: shed -> puesto
- Gloss: shed at an early stage of development

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `a` | shed at an early stage of development | most amphibians have caducous gills; the caducous calyx of a poppy |
| 2 | `n` | an outbuilding with a single story; used for shelter or storage |  |
| 3 | `v` | to remove | he shed his image as a pushy boss; shed your clothes |
| 4 | `v` | pour out in drops or small quantities or as if in drops or small quantities | shed tears; spill blood |
| 5 | `v` | cause or allow (a solid substance) to flow or run out or over | spill the beans all over the table |
| 6 | `v` | cast off hair, skin, horn, or feathers | our dog sheds every Spring |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:shed:puesto:001` | `positive_active` | `replace` | `pending_user_review` |  | most amphibians have shed gills | pending user review |
| `en-es:full-family-representative:shed:puesto:002` | `positive_active` | `replace` | `pending_user_review` |  | the shed calyx of a poppy | pending user review |
| `en-es:full-family-representative:shed:puesto:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, shed referred to an outbuilding with a single story; used for shelter or storage, not the target replacement. | pending user review |
| `en-es:full-family-representative:shed:puesto:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | he shed his image as a pushy boss | pending user review |
| `en-es:full-family-representative:shed:puesto:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "shed" in the exported report. | pending user review |

### full_family_review:034: parrot -> loro

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `loro`
- POS: `noun`
- Label: parrot -> loro
- Gloss: usually brightly colored zygodactyl tropical birds with short hooked beaks and the ability to mimic sounds

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | usually brightly colored zygodactyl tropical birds with short hooked beaks and the ability to mimic sounds |  |
| 2 | `v` | repeat mindlessly | The students parroted the teacher's words |
| 3 | `n` | a copycat who does not understand the words or acts being imitated |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:parrot:loro:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used parrot to describe usually brightly colored zygodactyl tropical birds with short hooked beaks and the ability to mimic sounds. | pending user review |
| `en-es:full-family-representative:parrot:loro:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, parrot referred to repeat mindlessly, not the target replacement. | pending user review |
| `en-es:full-family-representative:parrot:loro:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, parrot referred to a copycat who does not understand the words or acts being imitated, not the target replacement. | pending user review |
| `en-es:full-family-representative:parrot:loro:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "parrot_notes.txt". | pending user review |

### full_family_review:035: aberration -> equivocación

- Source band: `zipf_below_3_rare`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `equivocación`
- POS: `noun`
- Label: aberration -> equivocación
- Gloss: a state or condition markedly different from the norm

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a state or condition markedly different from the norm |  |
| 2 | `n` | a disorder in one's mental state |  |
| 3 | `n` | an optical phenomenon resulting from the failure of a lens or mirror to produce a good image |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:aberration:equivocacion:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used aberration to describe a state or condition markedly different from the norm. | pending user review |
| `en-es:full-family-representative:aberration:equivocacion:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, aberration referred to a disorder in one's mental state, not the target replacement. | pending user review |
| `en-es:full-family-representative:aberration:equivocacion:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, aberration referred to an optical phenomenon resulting from the failure of a lens or mirror to produce a good image, not the target replacement. | pending user review |
| `en-es:full-family-representative:aberration:equivocacion:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "aberration" as a saved search query. | pending user review |

### full_family_review:036: american -> americano

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `medium_4_to_9` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `americano`
- POS: `adjective`
- Label: american -> americano
- Gloss: of or relating to the United States of America or its people or language or culture

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `a` | of or relating to the United States of America or its people or language or culture | American citizens; American English |
| 2 | `n` | a native or inhabitant of the United States |  |
| 3 | `a` | of or relating to or characteristic of the continents and islands of the Americas | the American hemisphere; American flora and fauna |
| 4 | `n` | the English language as used in the United States |  |
| 5 | `n` | a native or inhabitant of a North American or Central American or South American country |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:american:americano:001` | `positive_active` | `replace` | `pending_user_review` |  | American citizens | pending user review |
| `en-es:full-family-representative:american:americano:002` | `positive_active` | `replace` | `pending_user_review` |  | American English | pending user review |
| `en-es:full-family-representative:american:americano:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, american referred to a native or inhabitant of the United States, not the target replacement. | pending user review |
| `en-es:full-family-representative:american:americano:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | the American hemisphere | pending user review |
| `en-es:full-family-representative:american:americano:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "american" opened an empty archive page. | pending user review |

### full_family_review:037: german -> alemán

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `low_1_to_3` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `alemán`
- POS: `adjective`
- Label: german -> alemán
- Gloss: of or pertaining to or characteristic of Germany or its people or language

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `a` | of or pertaining to or characteristic of Germany or its people or language | German philosophers; German universities |
| 2 | `n` | a person of German nationality |  |
| 3 | `n` | the standard German language; developed historically from West Germanic |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:german:aleman:001` | `positive_active` | `replace` | `pending_user_review` |  | German philosophers | pending user review |
| `en-es:full-family-representative:german:aleman:002` | `positive_active` | `replace` | `pending_user_review` |  | German universities | pending user review |
| `en-es:full-family-representative:german:aleman:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, german referred to a person of German nationality, not the target replacement. | pending user review |
| `en-es:full-family-representative:german:aleman:004` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, german referred to the standard German language; developed historically from West Germanic, not the target replacement. | pending user review |
| `en-es:full-family-representative:german:aleman:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "german_notes.txt". | pending user review |

### full_family_review:038: rebate -> descuento

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `medium_4_to_9` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `descuento`
- POS: `noun`
- Label: rebate -> descuento
- Gloss: a refund of some fraction of the amount paid

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a refund of some fraction of the amount paid |  |
| 2 | `v` | give a reduction in the price during a sale | The store is rebating refrigerators this week |
| 3 | `n` | a rectangular groove made to hold two pieces together |  |
| 4 | `v` | cut a rebate in (timber or stone) |  |
| 5 | `v` | join with a rebate | rebate the pieces of timber and stone |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:rebate:descuento:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used rebate to describe a refund of some fraction of the amount paid. | pending user review |
| `en-es:full-family-representative:rebate:descuento:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, rebate referred to give a reduction in the price during a sale, not the target replacement. | pending user review |
| `en-es:full-family-representative:rebate:descuento:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, rebate referred to a rectangular groove made to hold two pieces together, not the target replacement. | pending user review |
| `en-es:full-family-representative:rebate:descuento:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "rebate" as a saved search query. | pending user review |

### full_family_review:039: adder -> víbora

- Source band: `zipf_below_3_rare`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `víbora`
- POS: `noun`
- Label: adder -> víbora
- Gloss: a person who adds numbers

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a person who adds numbers |  |
| 2 | `n` | a machine that adds numbers |  |
| 3 | `n` | small terrestrial viper common in northern Eurasia |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:adder:vibora:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used adder to describe a person who adds numbers. | pending user review |
| `en-es:full-family-representative:adder:vibora:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, adder referred to a machine that adds numbers, not the target replacement. | pending user review |
| `en-es:full-family-representative:adder:vibora:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, adder referred to small terrestrial viper common in northern Eurasia, not the target replacement. | pending user review |
| `en-es:full-family-representative:adder:vibora:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "adder" in the exported report. | pending user review |

### full_family_review:040: tomorrow -> mañana

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `low_1_to_3` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `mañana`
- POS: `noun`
- Label: tomorrow -> mañana
- Gloss: the day after today

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | the day after today | what are our tasks for tomorrow? |
| 2 | `r` | the next day, the day after, following the present day |  |
| 3 | `n` | the near future | tomorrow's world; everyone hopes for a better tomorrow |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:tomorrow:manana:001` | `positive_active` | `replace` | `pending_user_review` |  | what are our tasks for tomorrow? | pending user review |
| `en-es:full-family-representative:tomorrow:manana:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, tomorrow referred to the next day, the day after, following the present day, not the target replacement. | pending user review |
| `en-es:full-family-representative:tomorrow:manana:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | tomorrow's world | pending user review |
| `en-es:full-family-representative:tomorrow:manana:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "tomorrow" opened an empty archive page. | pending user review |

### full_family_review:041: pair -> par

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `medium_4_to_9` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `par`
- POS: `noun`
- Label: pair -> par
- Gloss: a set of two similar things considered as a unit

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a set of two similar things considered as a unit |  |
| 2 | `v` | form a pair or pairs | The two old friends paired off |
| 3 | `n` | two items of the same kind |  |
| 4 | `v` | bring two objects, ideas, or people together | This fact is coupled to the other one; Matchmaker, can you match my daughter with a nice young man? |
| 5 | `n` | two people considered as a unit |  |
| 6 | `v` | occur in pairs |  |
| 7 | `n` | a poker hand with 2 cards of the same value |  |
| 8 | `v` | arrange in pairs | Pair these numbers |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:pair:par:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used pair to describe a set of two similar things considered as a unit. | pending user review |
| `en-es:full-family-representative:pair:par:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, pair referred to form a pair or pairs, not the target replacement. | pending user review |
| `en-es:full-family-representative:pair:par:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, pair referred to two items of the same kind, not the target replacement. | pending user review |
| `en-es:full-family-representative:pair:par:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "pair" in the exported report. | pending user review |

### full_family_review:042: endure -> durar

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `medium_4_to_9` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `durar`
- POS: `verb`
- Label: endure -> durar
- Gloss: put up with something or somebody unpleasant

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `v` | put up with something or somebody unpleasant | I cannot bear his constant criticism; The new secretary had to endure a lot of unprofessional remarks |
| 2 | `v` | face and withstand with courage | She braved the elements |
| 3 | `v` | continue to live and avoid dying | We went without water and food for 3 days; These superstitions survive in the backwaters of America |
| 4 | `v` | undergo or be subjected to | He suffered the penalty; Many saints suffered martyrdom |
| 5 | `v` | last and be usable | This dress wore well for almost ten years |
| 6 | `v` | persist for a specified period of time | The bad weather lasted for three days |
| 7 | `v` | continue to exist | These stories die hard; The legend of Elvis endures |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:endure:durar:001` | `positive_active` | `replace` | `pending_user_review` |  | I cannot endure his constant criticism | pending user review |
| `en-es:full-family-representative:endure:durar:002` | `positive_active` | `replace` | `pending_user_review` |  | The new secretary had to endure a lot of unprofessional remarks | pending user review |
| `en-es:full-family-representative:endure:durar:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, endure referred to face and withstand with courage, not the target replacement. | pending user review |
| `en-es:full-family-representative:endure:durar:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | These superstitions endure in the backwaters of America | pending user review |
| `en-es:full-family-representative:endure:durar:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "endure" in the exported report. | pending user review |

### full_family_review:043: russian -> ruso

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `low_1_to_3` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `ruso`
- POS: `adjective`
- Label: russian -> ruso
- Gloss: of or pertaining to or characteristic of Russia or its people or culture or language

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `a` | of or pertaining to or characteristic of Russia or its people or culture or language | Russian dancing |
| 2 | `n` | a native or inhabitant of Russia |  |
| 3 | `n` | the Slavic language that is the official language of Russia |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:russian:ruso:001` | `positive_active` | `replace` | `pending_user_review` |  | Russian dancing | pending user review |
| `en-es:full-family-representative:russian:ruso:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, russian referred to a native or inhabitant of Russia, not the target replacement. | pending user review |
| `en-es:full-family-representative:russian:ruso:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, russian referred to the Slavic language that is the official language of Russia, not the target replacement. | pending user review |
| `en-es:full-family-representative:russian:ruso:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "russian" opened an empty archive page. | pending user review |

### full_family_review:044: smile -> sonreír

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `cross_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `sonreír`
- POS: `noun`
- Label: smile -> sonreír
- Gloss: a facial expression characterized by turning up the corners of the mouth; usually shows pleasure or amusement

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a facial expression characterized by turning up the corners of the mouth; usually shows pleasure or amusement |  |
| 2 | `v` | change one's facial expression by spreading the lips, often to signal pleasure |  |
| 3 | `v` | express with a smile | She smiled her thanks |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:smile:sonreir:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used smile to describe a facial expression characterized by turning up the corners of the mouth; usually shows pleasure or amusement. | pending user review |
| `en-es:full-family-representative:smile:sonreir:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, smile referred to change one's facial expression by spreading the lips, often to signal pleasure, not the target replacement. | pending user review |
| `en-es:full-family-representative:smile:sonreir:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, smile referred to express with a smile, not the target replacement. | pending user review |
| `en-es:full-family-representative:smile:sonreir:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "smile" opened an empty archive page. | pending user review |

### full_family_review:045: govern -> gobernar

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `medium_4_to_9` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `gobernar`
- POS: `verb`
- Label: govern -> gobernar
- Gloss: bring into conformity with rules or principles or usage; impose regulations

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `v` | bring into conformity with rules or principles or usage; impose regulations | We cannot regulate the way people dress; This town likes to regulate |
| 2 | `v` | direct or strongly influence the behavior of | His belief in God governs his conduct |
| 3 | `v` | exercise authority over; as of nations | Who is governing the country now? |
| 4 | `v` | require to be in a certain grammatical case, voice, or mood | most transitive verbs govern the accusative case in German |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:govern:gobernar:001` | `positive_active` | `replace` | `pending_user_review` |  | We cannot govern the way people dress | pending user review |
| `en-es:full-family-representative:govern:gobernar:002` | `positive_active` | `replace` | `pending_user_review` |  | This town likes to govern | pending user review |
| `en-es:full-family-representative:govern:gobernar:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, govern referred to direct or strongly influence the behavior of, not the target replacement. | pending user review |
| `en-es:full-family-representative:govern:gobernar:004` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, govern referred to exercise authority over; as of nations, not the target replacement. | pending user review |
| `en-es:full-family-representative:govern:gobernar:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "govern" opened an empty archive page. | pending user review |

### full_family_review:046: brother -> hermano

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `medium_4_to_9` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `hermano`
- POS: `noun`
- Label: brother -> hermano
- Gloss: a male with the same parents as someone else

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a male with the same parents as someone else | my brother still lives with our parents |
| 2 | `n` | a male person who is a fellow member (of a fraternity or religion or other group) | none of his brothers would betray him |
| 3 | `n` | used as a term of address for those male persons engaged in the same movement | Greetings, comrade! |
| 4 | `n` | a close male friend who accompanies his buddies in their activities |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:brother:hermano:001` | `positive_active` | `replace` | `pending_user_review` |  | my brother still lives with our parents | pending user review |
| `en-es:full-family-representative:brother:hermano:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, brother referred to a male person who is a fellow member (of a fraternity or religion or other group), not the target replacement. | pending user review |
| `en-es:full-family-representative:brother:hermano:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | Greetings, brother! | pending user review |
| `en-es:full-family-representative:brother:hermano:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "brother" in the exported report. | pending user review |

### full_family_review:047: acceptable -> razonable

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `medium_4_to_9` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `razonable`
- POS: `adjective`
- Label: acceptable -> razonable
- Gloss: worthy of acceptance or satisfactory

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `a` | worthy of acceptance or satisfactory | acceptable levels of radiation; performances varied from acceptable to excellent |
| 2 | `a` | judged to be in conformity with approved usage | acceptable English usage |
| 3 | `a` | meeting requirements | the step makes a satisfactory seat; I would kill for a decent cup of coffee |
| 4 | `a` | adequate for the purpose | the water was acceptable for drinking |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:acceptable:razonable:001` | `positive_active` | `replace` | `pending_user_review` |  | acceptable levels of radiation | pending user review |
| `en-es:full-family-representative:acceptable:razonable:002` | `positive_active` | `replace` | `pending_user_review` |  | performances varied from acceptable to excellent | pending user review |
| `en-es:full-family-representative:acceptable:razonable:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | acceptable English usage | pending user review |
| `en-es:full-family-representative:acceptable:razonable:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | the step makes a acceptable seat | pending user review |
| `en-es:full-family-representative:acceptable:razonable:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "acceptable" opened an empty archive page. | pending user review |

### full_family_review:048: altitude -> elevación

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `elevación`
- POS: `noun`
- Label: altitude -> elevación
- Gloss: elevation especially above sea level or above the earth's surface

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | elevation especially above sea level or above the earth's surface | the altitude gave her a headache |
| 2 | `n` | the perpendicular distance from the base of a geometric figure to the opposite vertex (or side if parallel) |  |
| 3 | `n` | angular distance above the horizon (especially of a celestial object) |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:altitude:elevacion:001` | `positive_active` | `replace` | `pending_user_review` |  | the altitude gave her a headache | pending user review |
| `en-es:full-family-representative:altitude:elevacion:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, altitude referred to the perpendicular distance from the base of a geometric figure to the opposite vertex (or side if parallel), not the target replacement. | pending user review |
| `en-es:full-family-representative:altitude:elevacion:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, altitude referred to angular distance above the horizon (especially of a celestial object), not the target replacement. | pending user review |
| `en-es:full-family-representative:altitude:elevacion:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "altitude_notes.txt". | pending user review |

### full_family_review:049: health -> salud

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `low_1_to_3` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `salud`
- POS: `noun`
- Label: health -> salud
- Gloss: a healthy state of wellbeing free from disease

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a healthy state of wellbeing free from disease | physicians should be held responsible for the health of their patients |
| 2 | `n` | the general condition of body and mind | his delicate health; in poor health |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:health:salud:001` | `positive_active` | `replace` | `pending_user_review` |  | physicians should be held responsible for the health of their patients | pending user review |
| `en-es:full-family-representative:health:salud:002` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | his delicate health | pending user review |
| `en-es:full-family-representative:health:salud:003` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "health" opened an empty archive page. | pending user review |

### full_family_review:050: sale -> deducción

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `medium_4_to_9` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `deducción`
- POS: `noun`
- Label: sale -> deducción
- Gloss: a particular instance of selling

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | a particular instance of selling | he has just made his first sale; they had to complete the sale before the banks closed |
| 2 | `n` | the general activity of selling | they tried to boost sales; laws limit the sale of handguns |
| 3 | `n` | an occasion (usually brief) for buying at specially reduced prices | they held a sale to reduce their inventory; I got some great bargains at their annual sale |
| 4 | `n` | the state of being purchasable; offered or exhibited for selling | you'll find vitamin C for sale at most pharmacies; the new line of cars will soon be on sale |
| 5 | `n` | an agreement (or contract) in which property is transferred from the seller (vendor) to the buyer (vendee) for a fixed price in money (paid or agreed to be paid by the buyer) | the salesman faxed the sales agreement to his home office |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:sale:deduccion:001` | `positive_active` | `replace` | `pending_user_review` |  | he has just made his first sale | pending user review |
| `en-es:full-family-representative:sale:deduccion:002` | `positive_active` | `replace` | `pending_user_review` |  | they had to complete the sale before the banks closed | pending user review |
| `en-es:full-family-representative:sale:deduccion:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | laws limit the sale of handguns | pending user review |
| `en-es:full-family-representative:sale:deduccion:004` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | they held a sale to reduce their inventory | pending user review |
| `en-es:full-family-representative:sale:deduccion:005` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "sale" in the exported report. | pending user review |

### full_family_review:051: shortage -> falta

- Source band: `zipf_3_to_4_mid`
- Target band: `zipf_5_plus_very_common`
- Polysemy/POS: `low_1_to_3` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `falta`
- POS: `noun`
- Label: shortage -> falta
- Gloss: the property of being an amount by which something is less than expected or required

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | the property of being an amount by which something is less than expected or required | new blood vessels bud out from the already dilated vascular bed to make up the nutritional deficit |
| 2 | `n` | an acute insufficiency |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:shortage:falta:001` | `positive_active` | `replace` | `pending_user_review` |  | new blood vessels bud out from the already dilated vascular bed to make up the nutritional shortage | pending user review |
| `en-es:full-family-representative:shortage:falta:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, shortage referred to an acute insufficiency, not the target replacement. | pending user review |
| `en-es:full-family-representative:shortage:falta:003` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The spreadsheet column was titled "shortage" in the exported report. | pending user review |

### full_family_review:052: except -> excepto

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `low_1_to_3` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `excepto`
- POS: `verb`
- Label: except -> excepto
- Gloss: object to

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `v` | object to | he demurred at my suggestion to work on Saturday |
| 2 | `v` | prevent from being included or considered or accepted | The bad results were excluded from the report; Leave off the top piece |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:except:excepto:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used except to describe object to. | pending user review |
| `en-es:full-family-representative:except:excepto:002` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | except the top piece | pending user review |
| `en-es:full-family-representative:except:excepto:003` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "except" as a saved search query. | pending user review |

### full_family_review:053: entirely -> enteramente

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited`

**Active Evidence**

- Target: `enteramente`
- POS: `adverb`
- Label: entirely -> enteramente
- Gloss: to a complete degree or to the full or entire extent; Completely or entirely

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `r` | to a complete degree or to the full or entire extent; Completely or entirely | he was wholly convinced; entirely satisfied with the meal |
| 2 | `r` | without any others being included or involved | was entirely to blame; a school devoted entirely to the needs of problem children |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:entirely:enteramente:001` | `positive_active` | `replace` | `pending_user_review` |  | he was entirely convinced | pending user review |
| `en-es:full-family-representative:entirely:enteramente:002` | `positive_active` | `replace` | `pending_user_review` |  | entirely satisfied with the meal | pending user review |
| `en-es:full-family-representative:entirely:enteramente:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | was entirely to blame | pending user review |
| `en-es:full-family-representative:entirely:enteramente:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "entirely_notes.txt". | pending user review |

### full_family_review:054: region -> comarca

- Source band: `zipf_5_plus_very_common`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `medium_4_to_9` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `comarca`
- POS: `noun`
- Label: region -> comarca
- Gloss: the extended spatial location of something

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | the extended spatial location of something | the farming regions of France; religions in all parts of the world |
| 2 | `n` | a part of an animal that has a special function or is supplied by a given artery or nerve | in the abdominal region |
| 3 | `n` | a large indefinite location on the surface of the Earth | penguins inhabit the polar regions |
| 4 | `n` | the approximate amount of something (usually used prepositionally as in ‘in the region of’) | it was going to take in the region of two or three months to finish the job; the price is in the neighborhood of $100 |
| 5 | `n` | a knowledge domain that you are interested in or are communicating about | it was a limited realm of discourse; here we enter the region of opinion |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:region:comarca:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used region to describe the extended spatial location of something. | pending user review |
| `en-es:full-family-representative:region:comarca:002` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | in the abdominal region | pending user review |
| `en-es:full-family-representative:region:comarca:003` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, region referred to a large indefinite location on the surface of the Earth, not the target replacement. | pending user review |
| `en-es:full-family-representative:region:comarca:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | A navigation tab labeled "region" opened an empty archive page. | pending user review |

### full_family_review:055: owe -> deber

- Source band: `zipf_4_to_5_common`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `low_1_to_3` / `same_pos_polysemy`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk`

**Active Evidence**

- Target: `deber`
- POS: `verb`
- Label: owe -> deber
- Gloss: be obliged to pay or repay

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `v` | be obliged to pay or repay |  |
| 2 | `v` | be indebted to, in an abstract or intellectual sense | This new theory owes much to Einstein's Relativity Theory |
| 3 | `v` | be in debt | She owes me $200; I still owe for the car |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:owe:deber:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used owe to describe be obliged to pay or repay. | pending user review |
| `en-es:full-family-representative:owe:deber:002` | `shadow_negative` | `abstain` | `pending_user_review` | evidence_context_overlap_risk, shadow_competitor_target_not_reviewed, shadow_negative_synthetic_definition_context | In this sentence, owe referred to be indebted to, in an abstract or intellectual sense, not the target replacement. | pending user review |
| `en-es:full-family-representative:owe:deber:003` | `shadow_negative` | `abstain` | `pending_user_review` | shadow_competitor_target_not_reviewed | I still owe for the car | pending user review |
| `en-es:full-family-representative:owe:deber:004` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "owe" as a saved search query. | pending user review |

### full_family_review:056: conversance -> notoriedad

- Source band: `missing`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `low_1_to_3` / `single_sense`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk, source_form_artifact_risk`

**Active Evidence**

- Target: `notoriedad`
- POS: `noun`
- Label: conversance -> notoriedad
- Gloss: personal knowledge or information about someone or something

**Candidate WordNet Senses**

| Rank | POS | Definition | Examples |
| ---: | --- | --- | --- |
| 1 | `n` | personal knowledge or information about someone or something |  |

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:conversance:notoriedad:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used conversance to describe personal knowledge or information about someone or something. | pending user review |
| `en-es:full-family-representative:conversance:notoriedad:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` | no_winner_token_boundary_artifact | The download list included a file named "conversance_notes.txt". | pending user review |

### full_family_review:057: femalejournalist -> periodista

- Source band: `missing`
- Target band: `zipf_4_to_5_common`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk, source_form_artifact_risk`

**Active Evidence**

- Target: `periodista`
- POS: ``
- Label: femalejournalist -> periodista
- Gloss: the intended dictionary sense of femalejournalist

**Candidate WordNet Senses**

_No candidate WordNet senses found._

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:femalejournalist:periodista:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used femalejournalist to describe the intended dictionary sense of femalejournalist. | pending user review |
| `en-es:full-family-representative:femalejournalist:periodista:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "femalejournalist" as a saved search query. | pending user review |

### full_family_review:058: mosaicwork -> mosaico

- Source band: `missing`
- Target band: `zipf_3_to_4_mid`
- Polysemy/POS: `missing` / `missing`
- Review status: `pending_user_review`
- Active sense status: `pending_user_review`
- Agent pre-triage weaknesses: `active_target_sense_not_audited, evidence_context_overlap_risk, source_form_artifact_risk`

**Active Evidence**

- Target: `mosaico`
- POS: ``
- Label: mosaicwork -> mosaico
- Gloss: the intended dictionary sense of mosaicwork

**Candidate WordNet Senses**

_No candidate WordNet senses found._

**Family Review Fields**

```text
human_review_status:
active_sense_status:
active_sense_notes:
corrected_active_evidence:
family_disposition:
```

**Case Rows**

| Case | Type | Gold | Proposed Quality | Weaknesses | Sentence | User Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `en-es:full-family-representative:mosaicwork:mosaico:001` | `positive_active` | `replace` | `pending_user_review` | active_context_template_circular, evidence_context_overlap_risk | The article used mosaicwork to describe the intended dictionary sense of mosaicwork. | pending user review |
| `en-es:full-family-representative:mosaicwork:mosaico:002` | `phrase_no_winner` | `abstain` | `no_winner_template_control` |  | The sidebar showed "mosaicwork" as a saved search query. | pending user review |


## Limitations

- `packet_is_for_user_review_not_scoring_promotion`
- `agent_proposals_are_not_ground_truth`
- `candidate_wordnet_senses_may_not_cover_rulegen_dictionary_source`
- `full_packet_still_requires_manual_or_user_approval_before_trusted_scoring`

## Next Steps

- User reviews active sense alignment for each source-target family.
- User approves, rejects, or rewrites each generated case row.
- Approved decisions become a separate reviewed-decision artifact before scoring.
- Score surfaces should split pending, approved, rejected, and diagnostic-only rows.
