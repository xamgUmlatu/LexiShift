# en-es SRS Beta Preflight

- Status: `REVIEW`
- Decision: manual beta signoff is required before external testers.
- Generated: `2026-05-28T00:41:57.665810+00:00`

## Automated Checks

| Level | Code | Message | Details |
| --- | --- | --- | --- |
| `PASS` | `taxonomy_readable` | Taxonomy JSON is readable. | - |
| `PASS` | `options_html_readable` | Options HTML is readable. | - |
| `PASS` | `taxonomy_visibility_metadata_valid` | All taxonomy families declare MVP picker visibility. | - |
| `PASS` | `strict_mvp_picker_matches_taxonomy` | Options topic picker exactly matches strict-MVP taxonomy families. | medicine_health, finance_business, sports_fitness, games, music_media_entertainment, law_politics_civics, science_technology, arts_literature_humanities, animals, food_cooking |
| `PASS` | `hidden_topics_absent_from_picker` | Beta, hidden, register, and legal-gated families are absent from the picker. | - |
| `PASS` | `strict_topic_locale_keys_present` | Every strict-MVP topic chip has locale messages. | - |
| `PASS` | `taxonomy_audit_latest_ok` | Latest taxonomy audit is ok and includes visibility validation. | - |
| `PASS` | `srs_quality_harness_latest_clean` | SRS quality harness latest artifact has no failing or warning findings. | status=PASS; pass=22; warn=0; fail=0 |
| `WARN` | `en_es_profile_journey_latest_review` | en-es profile-preference journey latest artifact has review-only warnings. | SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED (phase=high_retention_growth admitted=5 due=3 published=5) |
| `WARN` | `en_es_installed_journey_latest_review` | en-es installed-resource journey latest artifact has review-only warnings. | SRS_JOURNEY_REAL_PUBLICATION_COMPLETE_FOR_DUE (phase=recovery_resume due_not_published=movimiento), SRS_JOURNEY_PUBLICATION_SCOPE_OBSERVED (phase=high_retention_growth admitted=5 due=3 published=5) |

## Strict MVP Topic Picker

The ordinary options-page picker should expose exactly these topics:

- `medicine_health`
- `finance_business`
- `sports_fitness`
- `games`
- `music_media_entertainment`
- `law_politics_civics`
- `science_technology`
- `arts_literature_humanities`
- `animals`
- `food_cooking`

## Manual Beta Signoff

| Status | Check | Verification |
| --- | --- | --- |
| `PENDING` | Fresh install can connect extension options to helper. | Load the beta extension/helper, open Options, refresh profiles, and confirm helper/profile status is understandable. |
| `PENDING` | Fresh en-es profile can initialize SRS and populate the dashboard. | Use a throwaway beta profile, choose proficiency/topics, initialize S, and refresh Learning words. |
| `PENDING` | Published rules replace page text and feedback syncs. | Open a simple English page, confirm due SRS replacements, submit Good/Easy feedback, and refresh the dashboard. |
| `PENDING` | Post-feedback auto-refresh can admit more profile-shaped words. | After enough successful Good/Easy feedback, confirm refresh output shows capacity, selected lemmas, and preferred-topic share. |
| `PENDING` | Tester recovery paths are understandable. | Discard one dashboard word, then delete the throwaway profile's en-es SRS story and confirm the profile can initialize again cleanly. |

## Deferred From Beta

- plants_nature and travel_places_transport stay hidden from the ordinary picker.
- Anime, hobbies, SAT/TOEFL, and register/style controls stay deferred.
- Browsing-based admission remains preview/planning, not mutating production admission.
- Right-click discard, restore/mastered/release controls, and due-only publication remain future work.

## Recommended Final Commands

```bash
python3 scripts/testing/srs_beta_preflight_en_es.py
npm --prefix scripts run quality:srs:harness
npm --prefix scripts run quality:srs:summary
npm --prefix scripts run quality:srs:journey:en-es:profile
npm --prefix scripts run quality:srs:journey:en-es:profile:summary
npm --prefix scripts run check
npm --prefix scripts run build
npm --prefix scripts run preflight:cws
```
