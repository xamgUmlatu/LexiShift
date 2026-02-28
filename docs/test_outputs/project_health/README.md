# Project Health Artifacts

This folder stores machine-readable outputs for project maintainability health checks.

Primary script:

```bash
node scripts/dev/check_project_health.js
```

Recommended flows:

1. Advisory report snapshot:

```bash
cd scripts
npm run health:project:report
```

2. Baseline snapshot (policy anchor for delta gating):

```bash
cd scripts
npm run health:project:baseline
```

3. Changed-file strict delta gate:

```bash
cd scripts
npm run health:project:changed
```

CI integration:

1. Pull requests run `.github/workflows/ci.yml` job `project-health-changed`.
2. The CI gate uses the same baseline-delta policy as `health:project:changed`
   (`fail-on-new`, `fail-on-regressions`).

Artifacts:

- `project_health_latest.json`: latest advisory scan payload.
- `project_health_baseline.json`: accepted debt baseline used for `new/regression` gating.
