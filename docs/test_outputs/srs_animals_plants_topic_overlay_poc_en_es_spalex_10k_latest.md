# en-es Animals/Plants Topic Overlay PoC

- Status: `ok`
- Decision: `srs_animals_plants_topic_overlay_poc_ready`
- Generated: `2026-05-19T04:08:00+00:00`
- Frequency DB: `/private/tmp/lexishift-spalex-audit/data-root/frequency_packs/freq-es-spalex-expanded-v1/main.sqlite`
- Overlay rows: `149`
- Overlay topics: `{'animals': 96, 'plants_nature': 53}`

## Findings

- `PASS` `topic_overlay_ready`: Topic overlay candidate was built.
- `PASS` `seed_frontier_loaded`: SRS seed frontier loaded.
- `PASS` `overlay_lifts_profile:animals`: Overlay increases topic-labeled rows in the profile preview.
- `PASS` `overlay_lifts_profile:plants_nature`: Overlay increases topic-labeled rows in the profile preview.

## Profile Scenarios

### `animals`

- baseline overlay hits in top preview: `2`
- with-overlay hits in top preview: `24`
- overlay hit delta: `22`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `ave` | 84 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 2 | `ciervo` | 319 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 3 | `cachorro` | 332 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 4 | `loro` | 388 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 5 | `víbora` | 397 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 6 | `chivo` | 574 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 7 | `mico` | 612 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 8 | `chancho` | 744 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 9 | `chacal` | 758 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 10 | `milano` | 857 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 11 | `faisán` | 875 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 12 | `galgo` | 900 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 13 | `perro` | 1672 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 14 | `zorro` | 1781 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 15 | `tigre` | 2407 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 16 | `oveja` | 2646 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 17 | `mono` | 2762 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 18 | `pájaro` | 2838 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 19 | `can` | 2878 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 20 | `cerdo` | 3042 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 21 | `vaca` | 3099 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 22 | `pato` | 3121 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 23 | `gallina` | 3167 | `animals` | `animals` | 1.0 | `topic_hint:animals` |
| 24 | `oso` | 3203 | `animals` | `animals` | 1.0 | `topic_hint:animals` |

### `plants_nature`

- baseline overlay hits in top preview: `0`
- with-overlay hits in top preview: `24`
- overlay hit delta: `24`

| Rank | Lemma | Neutral Rank | Topics | Overlay Topics | Topic Affinity | Source |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | `sauce` | 431 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 2 | `granado` | 632 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 3 | `manzano` | 782 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 4 | `flor` | 2191 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 5 | `maíz` | 2441 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 6 | `mata` | 2535 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 7 | `trigo` | 2567 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 8 | `hierba` | 3061 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 9 | `pino` | 3198 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 10 | `parra` | 3526 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 11 | `cebada` | 4301 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 12 | `roble` | 4367 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 13 | `encina` | 5104 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 14 | `vid` | 5184 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 15 | `palmera` | 6059 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 16 | `arbusto` | 6139 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 17 | `cardo` | 6235 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 18 | `ruda` | 6316 | `plants_nature` | `plants_nature` | 1.0 | `topic_hint:plants_nature` |
| 19 | `árbol` | 1882 | `nautical, plants_nature, transport` | `plants_nature` | 0.57735 | `topic_hint:plants_nature` |
| 20 | `brote` | 4719 | `biology, botany, natural_sciences, plants_nature` | `plants_nature` | 0.5 | `topic_hint:plants_nature` |
| 21 | `jacinto` | 851 | `human_sciences, mysticism, mythology, philosophy, plants_nature, sciences` | `plants_nature` | 0.45 | `topic_hint:plants_nature` |
| 22 | `planta` | 1632 | `anatomy, architecture, biology, botany, medicine, natural_sciences, plants_nature, sciences` | `plants_nature` | 0.45 | `topic_hint:plants_nature` |
| 23 | `rosa` | 1765 | `government, heraldry, hobbies, lifestyle, monarchy, nobility, plants_nature, politics` | `plants_nature` | 0.45 | `topic_hint:plants_nature` |
| 24 | `raíz` | 1978 | `computing, engineering, human_sciences, linguistics, mathematics, natural_sciences, physical_sciences, plants_nature` | `plants_nature` | 0.45 | `topic_hint:plants_nature` |


## Limitations

- This PoC does not install or enable a product overlay.
- Light accepted labels are included with lower membership in the artifact, but are not injected into profile_topics in this PoC because current profile-bootstrap scoring consumes topic presence rather than scalar membership.
- The result proves an integration path for reviewed labels; it does not prove complete animal or plant topic coverage.
