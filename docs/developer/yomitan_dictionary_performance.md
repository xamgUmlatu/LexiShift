# Synthetic Yomitan Dictionary Performance

Use the generated Yomitan format-3 fixture to measure importer and lookup
changes without relying on commercial or locally owned dictionary data:

```bash
npm --prefix scripts run quality:dictionary:yomitan
```

The default run generates eight term banks and 200,000 deterministic synthetic
entries in a temporary directory. It measures fixture generation, initial
import/indexing, exact repeat import, repeated lookup, and cancellation after
the first bank. It writes:

- `docs/test_outputs/dictionary/yomitan_performance_latest.json`
- `docs/test_outputs/dictionary/yomitan_performance_latest.md`

Correctness and timing policy are intentionally separate. A failed import,
lookup, repeat-import, cancellation, or cleanup assertion always makes the
command fail. Timings are reported but do not fail by default because absolute
thresholds vary by machine.

Stable CI runners may add explicit budgets:

```bash
npm --prefix scripts run quality:dictionary:yomitan -- \
  --max-import-ms 15000 \
  --max-repeat-import-ms 1000 \
  --max-lookup-p95-ms 20 \
  --max-cancel-ms 5000
```

Treat those values as runner policy, not universal product limits. Establish a
baseline on the same runner before tightening them. `--banks`,
`--terms-per-bank`, and `--lookup-repetitions` can make local smoke runs smaller.
`--archive-out` retains the generated ZIP for inspection; otherwise all fixture
and imported dictionary data is deleted when the run ends.
