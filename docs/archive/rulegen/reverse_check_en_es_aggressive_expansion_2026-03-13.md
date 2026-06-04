# Reverse-Check EN-ES Aggressive Expansion (2026-03-13)

Status: dated reverse-check evidence snapshot
Role: Archive / legacy
Last updated: 2026-03-13
Last verified: 2026-05-14 metadata-only Lane 1 rulegen authority note; expansion evidence not rerun
Source-of-truth: historical reverse-check review evidence only; current rulegen status lives in code, benchmark/gate/triage artifacts, and `docs/developer/feature_state_matrix.md`.

Purpose:
- widen the `en-es` benchmark much more aggressively before further non-reverse scoring changes
- keep the exact added words and proposed labels visible for manual review
- anchor the additions in observed current outputs under both `rev=off` and the named reverse lane

Artifacts used:
- `docs/test_inputs/rulegen_benchmark_cases/en_es.json`
- `docs/test_outputs/experiments/rulegen_en_es_reverse_check_20260313/rulegen_probe_en_es_expansion_selected_rev_off_2026-03-13.json`
- `docs/test_outputs/experiments/rulegen_en_es_reverse_check_20260313/rulegen_probe_en_es_expansion_selected_rev_on_2026-03-13.json`

- Added `en-es` cases in this pass: `14`
- Total `en-es` cases after this pass: `38`

## Added Cases

| Target | Bucket | Zipf (es) | `rev=off` top outputs | `rev=on` top outputs | Reverse snapshot (`rev=on`) | Proposed label intent | Why included |
|---|---|---:|---|---|---|---|---|
| `orden` | Gray | `5.30` | `order, warrant, writ` | `order, warrant` | `order:0/8; warrant:2/9` | top1 any: order, command; forbid top1: warrant, writ | Common control for order/command without letting legal-document senses take over. |
| `punto` | Gray | `5.50` | `dot, period, point` | `dot, point` | `dot:0/1; point:0/22` | top1 any: point, dot; forbid top1: - | Frequent polysemy with stable acceptable outputs; useful regression guard. |
| `cuenta` | Gray | `5.78` | `account, bill, invoice` | `account, bill` | `account:0/10; bill:8/13` | top1 any: account, bill; forbid top1: calculation | Common consumer noun with account/bill default and arithmetic drift risk. |
| `cargo` | Red | `5.15` | `accusal, accusation, function` | `function, charge` | `function:1/6; charge:7/22` | top1 any: charge, position, post, office, function; forbid top1: accusal, accusation, complaint, indictment | Strong reverse-sensitive red case; `rev=off` surfaces accusation senses. |
| `firma` | Gray | `4.66` | `company, firm, signature` | `company, signature, firm` | `company:4/6; signature:0/4; firm:2/9` | top1 any: company, signature, firm; forbid top1: - | Business/document polysemy that should stay broad but sane. |
| `campo` | Gray | `5.18` | `country, countryside, field` | `countryside, country, field` | `countryside:0/4; country:5/11; field:0/13` | top1 any: field, countryside, country; forbid top1: - | Broad geography/domain polysemy; good for rank-stability checks. |
| `plaza` | Green | `5.13` | `plaza, square, publicsquare` | `plaza, square` | `plaza:0/3; square:8/22` | top1 any: plaza, square; forbid top1: publicsquare | Simple public-space control plus obvious bad concatenated candidate. |
| `masa` | Red | `4.63` | `lump, mass, dough` | `dough, paste, mass` | `dough:0/11; paste:0/8; mass:5/9` | top1 any: mass, dough; forbid top1: lump | Strong reverse-sensitive red case; `rev=off` surfaces `lump`. |
| `red` | Green | `5.10` | `net, network` | `net, network` | `net:2/4; network:0/9` | top1 any: net, network; forbid top1: - | Common net/network control where both senses are acceptable. |
| `lengua` | Gray | `4.92` | `tongue, language` | `tongue, language` | `tongue:0/4; language:0/4` | top1 any: tongue, language; forbid top1: - | Body-part/language polysemy with balanced reverse support. |
| `cura` | Gray | `4.46` | `treatment, pastor, vicar` | `priest, treatment, pastor` | `priest:1/4; treatment:miss/2; pastor:miss/2` | top1 any: priest, treatment, cure; forbid top1: - | Shows reverse rescue toward clergy sense without over-hardening labels. |
| `caso` | Red | `5.71` | `affair, case, matter` | `case` | `case:0/12` | top1 any: case, matter; forbid top1: affair | Strong reverse-sensitive red case; `rev=off` surfaces `affair`. |
| `parte` | Green | `6.00` | `part, parthian, share` | `part` | `part:1/18` | top1 any: part, piece, share; forbid top1: parthian | Catches false-friend leakage such as `parthian`. |
| `vista` | Red | `5.20` | `appearance, aspect, look` | `sight, view` | `sight:0/9; view:4/14` | top1 any: sight, view; forbid top1: appearance, aspect, look | Strong reverse-sensitive red case; `rev=off` surfaces abstract glosses above `sight/view`. |

## Read Before Tuning Again

1. The new Red cases are `cargo`, `masa`, `caso`, and `vista`.
2. Those four cases all show a meaningful `rev=off` -> `rev=on` cleanup signal.
3. The added Gray/Green cases mostly widen coverage of common polysemous nouns so future tuning is less likely to overfit `madre`/`cuadro` alone.
4. Some labels are intentionally broad because the benchmark schema still rewards allowed/forbidden sets better than single-sense forcing.
5. Manual review should focus on whether any expected/forbidden set is too narrow or too permissive before treating these as long-term hard gates.
