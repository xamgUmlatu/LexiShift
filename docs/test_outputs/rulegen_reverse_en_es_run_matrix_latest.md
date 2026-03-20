# Reverse-Check Run Matrix (en-es)

Purpose:
- Keep the important reverse-check parameter sets and their benchmark outcomes in one durable table.
- Separate the canonical baseline lane from reverse-specific experiment lanes.

| Label | Lane | Selector | Rev | Match | Near | NearMax | FarPenalty | MissPenalty | MaxRules | Top1 | Top3 | ForbidTop1 | ForbidAny | AvgRules | Triage | Remaining Failures |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Canonical Latest | baseline | canonical latest / best | off | 0.20 | 0.10 | 2 | 0.00 | 0.20 | none | 78.95% | 94.74% | 21.05% | 21.05% | 2.11 | 11 | madre:bed, planta:sole, derecho:claim, cuadro:bed, orden:order, cargo:accusal, plaza:plaza, masa:lump, caso:affair, parte:part, vista:appearance |
| Far-Hit Experiment | dated experiment | 2026-03-13 experiment / best | on | 0.60 | 0.10 | 2 | 0.05 | 0.80 | none | 95.83% | 100.00% | 4.17% | 12.50% | 1.67 | 3 | madre:mother, derecho:right, cuadro:bed |
| Reverse Latest | named reverse lane | reverse latest / best | on | 0.60 | 0.10 | 2 | 0.05 | 0.80 | 1 | 97.37% | 97.37% | 2.63% | 2.63% | 1.00 | 1 | cuadro:bed |
| Reverse Latest (No Cap) | named reverse lane | reverse latest / best_rev_on_no_cap | on | 0.60 | 0.10 | 2 | 0.05 | 0.80 | none | 97.37% | 100.00% | 2.63% | 2.63% | 1.76 | 1 | cuadro:bed |

Notes:
- `canonical latest` is the required default benchmark lane and currently still measures `rev=off` by default.
- `reverse latest` is the named reverse-check lane exposed via `npm --prefix scripts run quality:rulegen:reverse:en-es`.
- `reverse latest (no cap)` keeps the reverse lane parameters but selects the best `max_rules_per_target=none` run for comparison.
