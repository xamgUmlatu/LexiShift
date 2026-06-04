# Rulegen Benchmark Cases

Status: active dataset guide
Role: Canonical current
Last updated: 2026-05-14
Last verified: 2026-05-14 metadata-only Lane 1 auxiliary README note; benchmark cases were not revalidated
Purpose: document the LP-specific benchmark-case directory and authoring rules for rulegen benchmark labels
Source-of-truth: directory guide plus LP-specific JSON files; current quality state remains in benchmark/gate/triage artifacts and `docs/developer/feature_state_matrix.md`.

Source-of-truth benchmark labels now live in LP-specific JSON files in this directory.

- `en_de.json`
- `en_es.json`
- `en_ja.json`
- `es_en.json`

Authoring rule:
- edit the LP-specific file for the lane you are tuning
- keep `case_id` directional (`source-target:Target`)
- omit per-case `pair` when the file already declares top-level `pair`

Tooling rule:
- `scripts/testing/rulegen_benchmark.py` accepts this directory directly
- the loader merges all `*.json` files deterministically
- pair-scoped loops can still target a single LP with `--pairs`
