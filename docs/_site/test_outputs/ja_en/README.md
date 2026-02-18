# JA→EN Review Outputs

This folder captures **human-review samples** and stable "golden" sets used to track quality changes as the rulegen algorithm evolves.

## Golden sample set
- `golden_samples_20260203_014029.json`  
  Curated from `samples_20260203_014029/samples.json`.  
  Each case has an `expected_bias` (keep / maybe_keep / filter) to guide future refinement.

## How to regenerate samples
Use the sampler to produce a new timestamped folder:

```
python scripts/testing/ja_en_sample_review.py \
  --bccwj "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-ja-bccwj.sqlite" \
  --jmdict "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/language_packs/JMdict_e" \
  --coca "/Users/takeyayuki/Library/Application Support/LexiShift/LexiShift/frequency_packs/freq-en-coca.sqlite" \
  --coca-column frequency \
  --top-n 2000 \
  --threshold 0.0 \
  --decay "1,0.7,0.5" \
  --sample 50
```

Then compare the new samples against the golden set for regressions or improvements.
