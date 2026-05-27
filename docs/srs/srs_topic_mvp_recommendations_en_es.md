# en-es SRS Topic MVP Recommendations

Status: current recommendation
Last updated: 2026-05-27
Role: Product-facing decision note for the first en-es topic-preference MVP
Source-of-truth inputs:

- `../test_outputs/srs_topic_release_readiness_en_es_latest.md`
- `../test_outputs/srs_admission_calibration_en_es_latest.md`
- `srs_topic_coverage_pause_state_en_es.md`
- `srs_interest_tailored_admission_algorithm.md`

## Recommendation

Ship topic preferences for en-es as an MVP-quality personalization control, not
as a complete topical vocabulary catalogue.

The selector behavior is coherent enough for MVP. The current blocker is not
the admission algorithm. The remaining risk is topic inventory quality: some
topics have shallow difficulty depth, clumpy examples, or source gaps. UX copy
should therefore frame these as interests that make matching words appear more
often, not as exhaustive topic courses or guaranteed share percentages.

Use the capped reserved topic lane for explicit topic preferences. Do not use
full-pool weighted sampling as the MVP topic policy; the calibration report
still warns that full-pool weighted sampling is too diffuse. Keep top-k
weighted sampling as a diagnostic/future exploration option.

## MVP Topic Visibility

### Show In MVP

These topics have source-backed rows, visible admission movement, and
expected-vs-observed reserved-lane counts that match current policy. Show them
with limited-depth wording.

| Topic | Recommendation | Why |
| --- | --- | --- |
| `medicine_health` | show | Strong coverage count; admission calibration matches expected `5/10`; depth still shallow. |
| `finance_business` | show | Limited-release coverage; admission calibration matches expected `5/10`. |
| `sports_fitness` | show | Strong coverage count; admission calibration matches expected `5/10`; depth still shallow. |
| `games` | show | Release-candidate count; admission calibration matches expected `5/10`. |
| `music_media_entertainment` | show | Release-candidate count; admission calibration matches expected `5/10`; runtime overlay rows are lower than effective source count but usable. |
| `law_politics_civics` | show | Strong coverage count; admission calibration matches expected `5/10`; depth still shallow. |
| `science_technology` | show | Strong source count; admission calibration matches expected `5/10`; runtime overlay rows are lower than source count but usable. |
| `arts_literature_humanities` | show | Release-candidate count; admission calibration now includes this scenario and matches expected `5/10`. |
| `animals` | show | Product-important and user-delight topic; admission calibration matches expected `5/10`; inventory is useful but incomplete. |
| `food_cooking` | show | Limited-release count; admission calibration matches expected `5/10`; examples may still feel clumpy. |

### Beta Or Optional

These can be exposed only if the UX is comfortable labeling them as limited or
experimental. They should not be used as proof that all topics are equally deep.

| Topic | Recommendation | Why |
| --- | --- | --- |
| `plants_nature` | beta/optional | Product-important, but only one source difficulty band and thin depth. Calibration matches expected `5/10`, so the selector is not the issue. |
| `travel_places_transport` | beta/optional | Useful topic, but release-readiness marks it beta-limited with only one band and a small runtime overlay. Calibration matches expected `5/10`. |

### Keep Hidden

These should not be visible in the ordinary en-es MVP topic picker.

| Topic | Recommendation | Why |
| --- | --- | --- |
| `anime_manga_pop_culture` | hide | No reviewed/source-backed rows yet. |
| `hobbies_crafts` | hide | No reviewed/source-backed rows yet. |
| `sat_toefl_exam_prep` | hide for en-es | English-target only, and still legal/source gated. |

### Keep Separate From Topics

Register/style controls are promising, but they should not quietly appear as
ordinary topics until we decide the UX model.

| Preference | Recommendation | Why |
| --- | --- | --- |
| `casual_slang_register` | future style/register control | Large review-only candidate set, but it needs policy review and UX copy. |
| `formal_professional_register` | future style/register control | Smaller beta candidate set and still needs register-specific UX semantics. |

## Product Copy Guidance

Use preference-strength language:

- "More often" rather than "50% of words."
- "Interests guide new admissions" rather than "topic packs."
- "Some topics are still growing" for limited-depth topics.

Avoid promising:

- exhaustive topic coverage;
- equal depth across topics;
- a fixed share of topic words in every new batch;
- topic-only SRS paths.

The current mathematical expectation is policy-facing only. For a strong
preference and a batch of `10`, the reserved lane often produces about `5`
topic words when source/readiness support exists. That is not product copy and
should not be shown as a guarantee.

## Remaining MVP Checks

Before external testers evaluate this flow:

1. Use the local admission lab to manually inspect the visible topics at a few
   proficiency values.
2. Confirm the topic picker can visually distinguish ordinary topics from
   beta/optional topics if beta topics are exposed.
3. Keep register/style controls out of the ordinary topic list unless a
   separate UX section is implemented.
4. Treat any complaint about "not enough topic words" as a coverage issue first
   if the calibration report says expected and observed counts match.
5. Revisit topic coverage only after a tester-facing issue points to a specific
   topic, source gap, or depth gap.
