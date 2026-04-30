# en-es Wave7 Residual Blocker Probe

- Status: `review`
- Decision: `targeted_remediation_required`
- Generated: `2026-04-30T19:56:00Z`
- Residual cases: `10`
- Active/shadow failures: `4`
- Phrase/no-winner failures: `6`
- Combined passing policies already available: `0`

## Class Summaries

| Class | Cases | Triggers | Lane | Diagnosis | Next Hypothesis |
| --- | ---: | --- | --- | --- | --- |
| `phrase_control_overlap_overblocks_active` | 1 | `meet` | `overlap_evidence_repair` | Phrase-control evidence semantically overlaps the active sentence and overblocks it. | Repair phrase-control evidence or add overlap-aware guard tests before scalar tuning. |
| `phrase_preemption_overreach_on_strong_active` | 1 | `even` | `phrase_preemption_guard` | Phrase preemption overrides a strong active score. | Add a focused preemption guard or scorer-backed rerun for strong-active preposition frames. |
| `shadow_overlap_overblocks_active` | 1 | `fix` | `shadow_evidence_repair` | Shadow evidence scores above the correct active sense. | Improve active-vs-shadow evidence contrast for the family before scalar tuning. |
| `shadow_quantity_evidence_underweighted` | 1 | `gross` | `shadow_evidence_repair` | Quantity shadow evidence is present but loses to the active disgust sense. | Strengthen or separate source evidence for quantity/commercial frames before threshold tuning. |
| `surface_rescue_leaks_when_phrase_control_close` | 3 | `foul`, `score`, `squeeze` | `phrase_no_winner_rescue_guard` | Surface-POS rescue leaks when phrase-control evidence is close to the best sense. | Test a close-phrase guard instead of increasing the global active margin. |
| `surface_rescue_overrode_dominant_phrase_control` | 3 | `cast`, `stretch`, `wrong` | `phrase_no_winner_rescue_guard` | Surface-POS rescue permits replace despite dominant phrase-control evidence. | Make phrase/no-winner rescue guard account for dominant phrase-control evidence. |

## Residual Cases

| Case | Suite | Error | Class | Active | Shadow | Phrase | Margin | Phrase Lead | Signals | Evidence |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:gross:002` | `active_shadow` | `harmful_replace` | `shadow_quantity_evidence_underweighted` | `0.6767` | `0.6376` | `0.6307` | `0.0391` | `-0.046` | active_modifier_frame | gross adjective sense: causing disgust / gross noun sense: twelve dozen / lacking fine distinctions or detail example: the gross details of the structure a... |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:fix:001` | `active_shadow` | `false_abstain` | `shadow_overlap_overblocks_active` | `0.626` | `0.7449` | `0.7136` | `-0.1189` | `-0.0313` | shadow_verb_frame | fix noun sense: a difficult situation or dilemma / restore something broken / a determination of the place where something is example: he got a good fix on the... |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:even:001` | `active_shadow` | `false_abstain` | `phrase_preemption_overreach_on_strong_active` | `0.7265` | `0.5392` | `0.5687` | `0.1873` | `-0.1578` | phrase_preempt, at even the | time of evening before nightfall / even verb sense: to make even / symmetrically arranged example: even features |
| `en-es:source-non-v10-wave7-source-class-breadth-heldout:v1:meet:001` | `active_shadow` | `false_abstain` | `phrase_control_overlap_overblocks_active` | `0.5444` | `0.6926` | `0.7272` | `-0.1482` | `0.0346` |  | suitable and proper / I'll probably see you at the meeting / come together example: I'll probably see you at the meeting |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:cast:001` | `phrase_no_winner` | `harmful_replace` | `surface_rescue_overrode_dominant_phrase_control` | `0.5626` | `0.6113` | `0.7274` | `-0.0487` | `0.1161` | active_noun_frame | cast noun sense: act of throwing / cast verb sense: to perform, bring forth a magical spell or enchantment / assign the roles of (a movie or a play) to actors example: Who cast this beautifu... |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:wrong:001` | `phrase_no_winner` | `harmful_replace` | `surface_rescue_overrode_dominant_phrase_control` | `0.679` | `0.6892` | `0.7113` | `-0.0102` | `0.0221` | active_modifier_frame | incorrect or improper / treat unjustly; do wrong to / that which is contrary to the principles of justice or law example: he feels that... |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:stretch:001` | `phrase_no_winner` | `harmful_replace` | `surface_rescue_overrode_dominant_phrase_control` | `0.7496` | `0.7342` | `0.8221` | `0.0154` | `0.0725` | active_noun_frame | stretch noun sense: act of stretching / become longer by being stretched and pulled / the capacity for being stretched |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:score:001` | `phrase_no_winner` | `harmful_replace` | `surface_rescue_leaks_when_phrase_control_close` | `0.7298` | `0.7096` | `0.7387` | `0.0202` | `0.0089` | active_noun_frame | score noun sense: number of points earned / score noun sense: number of points accrued / a written form of a musical composition; parts for different instruments appear o... |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:squeeze:001` | `phrase_no_winner` | `harmful_replace` | `surface_rescue_leaks_when_phrase_control_close` | `0.683` | `0.734` | `0.7523` | `-0.051` | `0.0183` | active_noun_frame | squeeze noun sense: difficult position / squeeze like a wedge into a tight space / a twisting squeeze example: gave the wet cloth a wring |
| `en-es:source-non-v10-wave7-source-class-breadth-phrase:v1:foul:001` | `phrase_no_winner` | `harmful_replace` | `surface_rescue_leaks_when_phrase_control_close` | `0.5938` | `0.6342` | `0.6349` | `-0.0404` | `0.0007` | active_noun_frame | foul noun sense: offence in sports / The industrial wastes polluted the lake / spot, stain, or pollute example: The townspeople defiled the river by emptying ra... |

## Policy Context

| Artifact | Status | Decision | Policies/Rows | Passing | Path |
| --- | --- | --- | ---: | ---: | --- |
| `rescue_sweep` | `review` | `rescue_policy_review` | 25 | 0 | `docs/test_outputs/semantic_surface_pos_rescue_policy_sweep_wave7_source_class_breadth_v1_phrase_control_triage_latest.json` |
| `no_surface_margin_sweep` | `review` | `margin_review` | 40 | 0 | `docs/test_outputs/semantic_source_margin_policy_sweep_wave7_source_class_breadth_v1_phrase_control_no_surface_latest.json` |

## Next Steps

- Repair or split shadow/active evidence for `gross`, `fix`, and similar overlap cases.
- Design a focused phrase-preemption guard for strong-active cases such as `even`.
- Audit phrase-control overlap before letting phrase evidence veto active adjective cases.
- Constrain surface-POS rescue against phrase/no-winner rows with dominant or close phrase evidence.
- Do not tune one global scalar policy yet; the current sweeps have zero combined passing policies.
- After a targeted guard or evidence patch, rerun both wave7 heldout suites, rescue sweep, no-surface margin sweep, failure mining, registry summary, focused tests, doc-reference checks, and git diff whitespace checks.

## Limitations

- `fixed_trace_probe_not_runtime_policy`
- `does_not_rescore_or_regenerate_evidence`
- `classifies_current_wave7_phrase_control_triage_reports_only`
