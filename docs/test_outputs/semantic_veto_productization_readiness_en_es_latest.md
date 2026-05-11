# en-es Semantic Veto Productization Readiness

- Status: `ok`
- Decision: `active_only_candidate_ready_for_manual_testing`
- Runtime publication status: `manual_testing_ready`
- Generated: `2026-05-09T02:08:16Z`

## Candidate

- Prompt variant: `v5_refresh_control`
- Application mode: `generated_active_only`
- Postprocess view: `no_high_eval_overlap_sentence_only`
- Admitted active evidence items: `48`
- Rejected generated items: `0`
- Score cases: `91`
- Decision accuracy: `0.7363` (`+0.2308`)
- Replace recall: `0.5000` (`+0.4167`)
- False abstains: `24` (`-20`)
- Harmful replaces: `0` (`-1`)

## Runtime State

- Current policy: `en_es_sentence_veto_v3`
- Scorer/evidence: `sentence_transformer_cosine` / `all_evidence_text`
- Thresholds: min active `0.0`, min margin `0.0`
- LLM rows compiled into runtime inventory: `True`
- Canonical source packaging available: `True`
- Packaged canonical rows: `45`
- Inventory-shaped replay available: `True`
- Inventory replay cases: `91`
- Helper runtime smoke available: `True`
- Helper runtime smoke cases: `91`
- Helper runtime fallback decisions: `0`
- Helper runtime accuracy/recall: `0.7692` / `0.5833`
- Helper runtime harmful/false abstain: `1` / `20`

## Readiness Checks

| Check | Result | Detail |
| --- | --- | --- |
| `prompt_candidate_selected` | `pass` | best primary prompt is v5_refresh_control; expected v5_refresh_control |
| `admission_clean` | `pass` | 48 admitted; 0 rejected; 0 shortfall |
| `offline_lift_observed` | `pass` | accuracy delta +0.2308; false abstain delta -20 |
| `soft_assist_harm_budget_preserved` | `pass` | harmful replaces 0; delta -1 |
| `same_denominator_confirmed` | `pass` | prompt, admission, and score artifacts are all status ok |
| `source_packaging_done` | `pass` | 45 canonical rows; 0 runtime-publishable rows |
| `inventory_replay_done` | `pass` | 91 cases; 45 applied rows; accuracy delta +0.2308 |
| `helper_runtime_smoke_done` | `pass` | 91 cases; 0 fallback decisions; accuracy 0.7692; recall 0.5833; harmful 1 |

## Blocking Next Work

- Use the isolated helper fixture for manual browser/helper testing before mutating any real profile data.
- If manual behavior is acceptable, package a bounded real helper candidate or stop the veto lane as a soft-assist PoC.
- Keep broader paid generation blocked until the manual smoke confirms the user-facing replace-or-abstain behavior is acceptable.

## Non-Goals

- `do not tune runtime thresholds`
- `do not promote v6 prompt wording`
- `do not use generated shadows or no-winner rows for production`
- `do not claim full en-es product accuracy from the 24-family PoC denominator`
