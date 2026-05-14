# Rulegen LP Profiles

Status: active profile-directory guide
Role: Runbook / operational
Last updated: 2026-05-14
Last verified: 2026-05-14 metadata-only Lane 1 auxiliary README note; profile validators were not rerun
Source-of-truth: operational guide for static LP profile contracts; implemented/default-on/verified state remains in `docs/developer/feature_state_matrix.md`.

Purpose:
- Store machine-readable rulegen language-pair profiles.
- Make LP onboarding more systematic by separating static pair wiring from dynamic state/evidence.

Use:
- onboarding/process contract: `docs/rulegen/lp_onboarding_operating_model.md`
- pair current mechanism inventory: `docs/rulegen/rulegen_lp_support_guide.md`
- current verified status: `docs/developer/feature_state_matrix.md`

Validation:

```bash
npm --prefix scripts run check:lp-profiles
npm --prefix scripts run check:lp-conformance
```

Notes:
- These profiles are static onboarding contracts, not the source of truth for `implemented`, `default-on`, or `verified` state.
- Dynamic state claims stay in `docs/developer/feature_state_matrix.md`.
- The onboarding scaffold can also render template-driven pair/test starter files with `npm --prefix scripts run scaffold:rulegen:lp -- --pair <lp> --translation-family <family> --translation-pack-id <pack_id> --with-code-stubs`.
- The scaffold can also render a generated integration handoff with `--with-integration-handoff` so central registry/preset follow-ups stay explicit instead of being improvised.
- The scaffold can also render a generated benchmark preset starter with `--with-benchmark-preset-starter` so new pairs have a consistent first preset snippet before manual tuning.
