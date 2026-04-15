# Rulegen Benchmark Cases

Pair-local benchmark case files in this directory are the development edit surface for language-pair tuning.

- `en_es.json`
- `en_de.json`
- `en_ja.json`
- `es_en.json`

The compatibility aggregate remains:

- `docs/test_inputs/rulegen_benchmark_cases.json`

After editing a pair-local file, refresh the aggregate with:

```bash
python scripts/testing/rulegen_benchmark_case_sync.py merge
```

To regenerate the pair-local files from the aggregate:

```bash
python scripts/testing/rulegen_benchmark_case_sync.py split
```
