# en-es Source Frame Gap Generation Safety

- Status: `ok`
- Generated: `2026-04-28T20:57:49Z`
- Plan: `/Users/takeyayuki/Documents/projects/LexiShift/docs/test_outputs/semantic_source_frame_gap_plan_en_es_latest.json`
- Source id: `llm_aligned_sentence_frame_rows`
- Prompt version: `aligned-sentence-frame-v1`
- Selected model: `gpt-5.4-mini`
- Pricing source: `https://openai.com/api/pricing/`

## Summary

- Selected requests: `97`
- Estimated input tokens: `36260`
- Expected output tokens: `4850`
- Max output tokens: `17460`
- Input rate per 1M: `$0.75`
- Output rate per 1M: `$4.5`
- Estimated cost expected: `$0.04902`
- Estimated cost ceiling: `$0.105765`

## Live Command Shape

Use `semantic_llm_example_frame_generation_run_en_es.py` with `--execute-live`, a non-empty `--run-id`, `--require-selected-request-count 97`, `--input-rate-per-1m 0.75`, `--output-rate-per-1m 4.50`, and explicit cost ceilings. Live generation still writes through the existing journal/raw/intake/normalized artifacts and must be followed by leakage audit plus source admission.
