# en-es SRS Topic Release Readiness

- Status: `ok`
- Decision: `srs_topic_release_readiness_classified`
- Generated: `2026-05-19T04:54:43.675056+00:00`
- Frontier: `spalex_10k_research` (`10000` seeds)
- Default-visible candidates: `5`
- Limited-visible candidates: `8`
- Beta-visible candidates: `1`
- Hidden/source-blocked candidates: `3`

## Release Gate

- `release_ready`: >= 100 effective rows and >= 3 source difficulty bands
- `limited_release`: >= 50 effective rows and >= 2 source difficulty bands, or strong count with shallow depth explicitly labeled
- `beta_limited`: >= 30 effective rows with at least one source difficulty band; ship only with limited/beta UX copy
- `register_policy_review`: >= 100 review-only rows can be release candidates after register/style UX policy review
- `blocked`: 0 effective rows, legal-source gated rows, or topics without a reviewed/source-backed candidate path stay hidden

## Source Precision Review

- Review state: `agent_labeled_pending_user_approval`
- Reviewed rows: `54`
- Accepted rows: `32` (59.3%)
- Rejected rows: `22` (40.7%)
- Families needing guard review: `arts_literature_humanities, games, science_technology`

## Topic Matrix

| Family | Axis | Status | Visibility | Effective Rows | Source Rows | Overlay Rows | Bands | Next Work |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `medicine_health` | `topic` | `release_candidate_limited_depth` | `visible_with_limited_depth_note` | 172 | 172 | 0 | 2 | run sampled precision review; add mid/hard-band enrichment if release UX needs smoother progression; lab-smoke preference strength across proficiency values |
| `finance_business` | `topic` | `release_candidate_limited_depth` | `visible_with_limited_depth_note` | 102 | 102 | 0 | 2 | run sampled precision review; add mid/hard-band enrichment if release UX needs smoother progression; lab-smoke preference strength across proficiency values |
| `sports_fitness` | `topic` | `release_candidate` | `default_visible` | 208 | 208 | 0 | 3 | review light-topic scalar handling before default promotion; freeze release evidence in the readiness artifact; lab-smoke preference strength across proficiency values |
| `games` | `topic` | `release_candidate` | `default_visible` | 109 | 109 | 0 | 3 | tighten source-label guards before default promotion; freeze release evidence in the readiness artifact; lab-smoke preference strength across proficiency values |
| `music_media_entertainment` | `topic` | `release_candidate_limited_depth` | `visible_with_limited_depth_note` | 194 | 194 | 0 | 2 | run sampled precision review; add mid/hard-band enrichment if release UX needs smoother progression; lab-smoke preference strength across proficiency values |
| `law_politics_civics` | `topic` | `release_candidate` | `default_visible` | 256 | 256 | 0 | 3 | review light-topic scalar handling before default promotion; freeze release evidence in the readiness artifact; lab-smoke preference strength across proficiency values |
| `science_technology` | `topic` | `release_candidate` | `default_visible` | 629 | 629 | 0 | 4 | tighten source-label guards before default promotion; freeze release evidence in the readiness artifact; lab-smoke preference strength across proficiency values |
| `travel_places_transport` | `topic` | `release_candidate_limited_depth` | `visible_with_limited_depth_note` | 139 | 139 | 0 | 2 | run sampled precision review; add mid/hard-band enrichment if release UX needs smoother progression; lab-smoke preference strength across proficiency values |
| `arts_literature_humanities` | `topic` | `release_candidate` | `default_visible` | 168 | 168 | 0 | 4 | tighten source-label guards before default promotion; freeze release evidence in the readiness artifact; lab-smoke preference strength across proficiency values |
| `animals` | `topic` | `limited_release_candidate` | `visible_with_limited_depth_note` | 96 | 17 | 96 | 2 | run sampled precision review; add more reviewed rows if the lab still feels clumpy; lab-smoke preference strength across proficiency values |
| `plants_nature` | `topic` | `limited_release_candidate_overlay_only` | `visible_with_limited_depth_note` | 53 | 29 | 53 | 1 | derive difficulty-band coverage for reviewed overlay rows; run sampled precision review on the broader overlay; lab-smoke preference strength across proficiency values |
| `food_cooking` | `topic` | `limited_release_candidate` | `visible_with_limited_depth_note` | 91 | 17 | 91 | 2 | run sampled precision review; add more reviewed rows if the lab still feels clumpy; lab-smoke preference strength across proficiency values |
| `anime_manga_pop_culture` | `topic` | `blocked_source_required` | `hidden_until_source_backed` | 0 | 0 | 0 | 0 | identify a source or curated seed list; build a sampled review packet; generate a reviewed overlay and rerun the lab |
| `hobbies_crafts` | `topic` | `blocked_source_required` | `hidden_until_source_backed` | 0 | 0 | 0 | 0 | identify a source or curated seed list; build a sampled review packet; generate a reviewed overlay and rerun the lab |
| `casual_slang_register` | `register` | `register_release_candidate_policy_review` | `visible_after_policy_review` | 488 | 0 | 0 | 0 | run sampled precision review for register/style labels; decide whether this appears in the same UX section as topics; lab-smoke register preference behavior before promotion |
| `formal_professional_register` | `register` | `register_beta_candidate_policy_review` | `beta_after_policy_review` | 41 | 0 | 0 | 0 | expand or review register labels to reach the release-candidate floor; define register/style UX copy and storage semantics; lab-smoke register preference behavior before promotion |
| `sat_toefl_exam_prep` | `topic` | `blocked_legal_source_required` | `hidden_until_licensed_source` | 0 | 0 | 0 | 0 | identify a legally usable source or internal taxonomy; build a review packet from that source; generate a reviewed overlay and rerun release readiness |

## Findings

- `PASS` `frontier_available`: Release-readiness frontier is available.
- `PASS` `reviewed_overlays_available`: Reviewed topic overlay artifacts are available.
- `WARN` `some_topics_blocked`: Some topic families should stay hidden until source or legal blockers clear.
- `PASS` `release_candidates_present`: At least one topic family meets the default release-candidate floor.
- `PASS` `source_precision_review_available`: Sampled source precision review is available.
- `WARN` `source_precision_guards_needed`: Some default-visible source topics need guard review before promotion.

## Limitations

- This is a release-readiness classifier, not a new source audit.
- Reviewed overlay rows are counted separately from source-derived trusted rows.
- Effective rows use the larger of source-trusted and reviewed-overlay counts to avoid optimistic double counting.
- Difficulty bands currently come from the source-depth audit; overlay rows do not yet carry a calibrated difficulty-band distribution.
- Source precision review is sampled compact evidence, not a full-universe precision estimate.
- Register rows are policy-review candidates, not ordinary interest topics.
