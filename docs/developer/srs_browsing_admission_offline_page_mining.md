# SRS Browsing Admission Offline Page Mining

This harness tests saved/local pages before live browser runtime testing. It is
intended for quick LP expansion checks without touching live user data.

## Command

```bash
python3 scripts/testing/srs_browsing_admission_offline_page_mining.py \
  --json-out docs/test_outputs/srs_browsing_admission_offline_page_mining_latest.json \
  --markdown-out docs/test_outputs/srs_browsing_admission_offline_page_mining_latest.md
```

## What It Covers

- Parses local HTML fixtures into visible text and ruby pairs.
- Executes the real extension mining modules in Node.
- Builds the same browsing signal packets the extension sends to the native host.
- Ingests packets through an isolated native-host helper store.
- Optionally simulates admission from the ingested aggregate store.
- Checks that configured private strings do not appear in emitted packets/reports.

This is not a live Chrome runtime test. It does not cover SPA lifecycle timing,
CSS layout visibility, iframes, shadow DOM, extension reload behavior, or scan
cadence.

## Adding A Case

Add a case to
`docs/test_inputs/srs_browsing_admission_offline_page_mining_cases.json` with:

- `name`: stable descriptive id.
- `pair`: language pair under test, for example `en-ja` or `en-es`.
- `documents`: saved page fixture paths with `side` set to `source` or `target`.
- `active_rules`: active SRS rules available to source-language mining.
- `expectations`: packet, signal, aggregate, privacy, and optional admission checks.

For a positive mining case, assert expected targets with
`required_payload_targets` and `required_aggregate_targets`. For a future LP that
is not supported by the current mining code, keep the case explicit by setting
`min_packet_count: 0`, `max_packet_count: 0`, and `require_native_ingest: false`.

If admission behavior matters, add an `admission` block with lightweight
candidate rows and add `expectations.admission.required_rows` for the expected
browsing-lane effect.
