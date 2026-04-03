# Rulegen Benchmark Cases

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
