# en-es SRS Beta Preflight Runbook

Status: active beta-preflight runbook
Last updated: 2026-06-01
Scope: en-es SRS preference beta readiness
Source of truth:

- [SRS topic MVP recommendations](../srs/srs_topic_mvp_recommendations_en_es.md)
- [Interest-tailored admission algorithm](../srs/srs_interest_tailored_admission_algorithm.md)
- [SRS practice layer design](../srs/srs_practice_layer_design.md)
- [Packaged GUI startup performance plan](../developer/packaged_gui_startup_performance_plan.md)
- [Feature state matrix](../developer/feature_state_matrix.md)

## Goal

Use this runbook immediately before handing the en-es SRS preference flow to
testers. It separates automated evidence from manual extension smoke testing.

The beta is allowed to have documented limitations. It is not allowed to have an
unclear setup path, hidden data-pack failure, broken strict topic picker, broken
dashboard recovery path, or unverified feedback/refresh loop.

## Automated Preflight

Run the composed preflight report:

```bash
npm --prefix scripts run preflight:srs:beta:en-es
```

The generated artifacts are:

- [latest JSON](../test_outputs/srs_beta_preflight_en_es_latest.json)
- [latest Markdown](../test_outputs/srs_beta_preflight_en_es_latest.md)

Expected pre-tester status is usually `REVIEW`, not `PASS`, because the manual
fresh-install checks remain intentionally pending until a human runs them in the
real extension/helper environment.

The automated checks verify:

- the options-page topic picker exactly matches taxonomy families marked
  `mvp_picker_visibility=strict_mvp_visible`;
- beta, hidden, register, and legal/source-gated families are absent from the
  ordinary picker;
- strict topic chips have locale messages;
- the latest taxonomy audit includes visibility validation;
- SRS quality and en-es journey artifacts have no failing findings.

## Manual Beta Signoff

Run these on a throwaway beta profile. Do not use a real learner profile.

| Check | Required result |
| --- | --- |
| Fresh install/helper connection | Options can refresh profiles and show understandable helper/profile state. |
| Data-pack readiness | en-es frequency/dictionary/topic resources resolve. If frequency/dictionary data is missing, the guided SRS setup modal names learner-facing resource categories, opens LexiShift GUI Resource settings through the helper with the en-es card added/focused in Learning Languages, reuses the existing GUI instance when it is already open, lets the user install app-managed dictionary resources (`wiktionary-es-en`, `freedict-es-en`), shows package sizes and per-resource progress, routes license-restricted `freq-es-cde` through Learning Languages manual setup, imports a user-supplied licensed `spanish_lemmas20k.txt` into managed local SQLite after rights confirmation, reveals installed file locations, and retrying after install uses the same setup flow. |
| Resource setup launch performance | Existing-GUI activation should feel immediate, and cold packaged launch should be measured against the startup-performance plan targets before the setup flow is treated as product-ready. |
| Strict topic picker | The ordinary picker shows only the strict MVP topics and excludes Plants/Nature and Travel. |
| Fresh SRS initialize | A new profile can initialize SRS and populate Learning words. |
| Dashboard visibility | Learning words shows active/queued/due/removed counts, rule summaries, and advanced details when toggled. |
| Runtime replacement | A simple English test page receives due SRS replacements after publication. |
| Feedback sync | Good/Easy feedback reaches the helper and is reflected after refreshing the dashboard. |
| Auto refresh | After enough Good/Easy feedback, automatic refresh can admit new profile-shaped words. |
| Discard recovery | Dashboard discard removes a word from active inventory and prevents immediate readmission. |
| Delete recovery | Delete the throwaway profile's en-es SRS story and confirm the profile is ready to initialize again. |

## Final Gate Commands

Run these once after the manual signoff passes:

```bash
npm --prefix scripts run quality:srs:harness
npm --prefix scripts run quality:srs:summary
npm --prefix scripts run quality:srs:journey:en-es:profile
npm --prefix scripts run quality:srs:journey:en-es:profile:summary
npm --prefix scripts run check
npm --prefix scripts run build
npm --prefix scripts run preflight:cws
```

If a final gate fails, fix the underlying issue or document why it is not part
of the beta scope before testers receive the build.

## Deferred From Beta

- Plants/Nature and Travel remain hidden from the ordinary topic picker.
- Anime, hobbies, SAT/TOEFL, and register/style controls remain deferred.
- Browsing-based admission remains preview/planning, not mutating production
  admission.
- Right-click discard, restore/mastered/release controls, and due-only
  publication remain future work.
