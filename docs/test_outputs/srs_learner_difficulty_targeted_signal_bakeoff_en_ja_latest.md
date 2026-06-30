# en-ja Targeted Signal Bakeoff

- Generated: `2026-06-23T21:41:32Z`
- Runtime/model behavior changed: `false`
- Variants tested: `3087`
- Baseline: `srcarb_pmin_nmean_bped_native_min_ps1_tsbase_tl0p5_tu0p85_bmmean_bd0p05_ed0_egweak_td0_tgrarity_oc0p58_ocmhard_ocs1_ogmean_rg0_tf0_tfmnone_ssf0_ssfmnone_s2f0p42_s2fmpedagogical_family_only_rare_pollution_unprotected_exact_ssa0_ssamnone_jpmeffective_jeb0_jegnone_jemg0_jip0_jipmnone_gsd0p05_gsgmarked_rarity_ged0p04_gemenglish_freq_gjb0_jbmnone_jmar0_jbs1_bfrm0p06_bfrs1_bfrgscore_gap`

## Headline

- Baseline holdout balanced: `0.914576`
- Best holdout balanced: `0.915124`
- Best recommendation: `clear_benefit`
- Best variant: `targeted_dom_domain_c0p86_s1`

## Signal Coverage

```json
{
  "base_family_gate_rows": 259,
  "base_family_score_rows": 266,
  "domain_or_marked_rows": 72502,
  "domain_signal_rows": 72269,
  "gairaigo_origin_ease_rows": 7043,
  "gairaigo_origin_known_rows": 9721,
  "jmdict_domain_or_marked_rows": 19239,
  "jmdict_domain_signal_rows": 11388,
  "jmdict_marked_signal_rows": 11686,
  "marked_signal_rows": 11686
}
```

## Leaderboard

| Variant | Rec | Holdout bal | Δ holdout | First60 MAE score Δ | All-label MAE score Δ | Changed | Changed ≤0.70 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `targeted_dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000296 | +0.001557 | 4468 | 0 |
| `targeted_fam_m0p06_s0p5__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000296 | +0.001557 | 4563 | 77 |
| `targeted_fam_m0p06_s1__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000296 | +0.001557 | 4563 | 77 |
| `targeted_fam_m0p1_s0p5__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000296 | +0.001557 | 4522 | 39 |
| `targeted_fam_m0p1_s1__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000296 | +0.001557 | 4522 | 39 |
| `targeted_fam_m0p14_s0p5__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000296 | +0.001557 | 4468 | 0 |
| `targeted_fam_m0p14_s1__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000296 | +0.001557 | 4468 | 0 |
| `targeted_gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000069 | +0.001362 | 10325 | 3224 |
| `targeted_fam_m0p06_s0p5__gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000069 | +0.001362 | 10420 | 3301 |
| `targeted_fam_m0p06_s1__gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000069 | +0.001362 | 10420 | 3301 |
| `targeted_fam_m0p1_s0p5__gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000069 | +0.001362 | 10379 | 3263 |
| `targeted_fam_m0p1_s1__gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000069 | +0.001362 | 10379 | 3263 |
| `targeted_fam_m0p14_s0p5__gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000069 | +0.001362 | 10325 | 3224 |
| `targeted_fam_m0p14_s1__gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000069 | +0.001362 | 10325 | 3224 |
| `targeted_gai_ascii_origin_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000049 | +0.001345 | 10597 | 3478 |
| `targeted_fam_m0p06_s0p5__gai_ascii_origin_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000049 | +0.001345 | 10692 | 3555 |
| `targeted_fam_m0p06_s1__gai_ascii_origin_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000049 | +0.001345 | 10692 | 3555 |
| `targeted_fam_m0p1_s0p5__gai_ascii_origin_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000049 | +0.001345 | 10651 | 3517 |
| `targeted_fam_m0p1_s1__gai_ascii_origin_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000049 | +0.001345 | 10651 | 3517 |
| `targeted_fam_m0p14_s0p5__gai_ascii_origin_d0p02__dom_domain_c0p86_s1` | `clear_benefit` | 0.915124 | +0.000548 | +0.000049 | +0.001345 | 10597 | 3478 |

## Best Variant Working Set Impact

| Row | Expected | Baseline | Candidate | Error Δ | Signals |
| --- | ---: | ---: | ---: | ---: | --- |
| `饗する/きょうする` | 0.75 | 0.852735 | 0.852735 | +0 | rarity=0.993169; marked=0.0; domain=0.408248; gairaigo=0.0 |
| `饐える/すえる` | 0.85 | 0.812107 | 0.812107 | +0 | rarity=0.983041; marked=1.0; domain=0.5; gairaigo=0.0 |
| `齲蝕/うしょく` | 0.85 | 0.793551 | 0.793551 | +0 | rarity=0.926787; marked=1.0; domain=1.0; gairaigo=0.0 |
| `翻って/ひるがえって` | 0.6 | 0.599449 | 0.599449 | +0 | rarity=0.993169; marked=1.0; domain=0.5; gairaigo=0.0 |
| `歳神/としがみ` | 0.7 | 0.820814 | 0.820814 | +0 | rarity=0.880598; marked=1.0; domain=0.57735; gairaigo=0.0 |
| `龍舟/りゅうしゅう` | 0.75 | 0.936648 | 0.936648 | +0 | rarity=0.999118; marked=0.0; domain=0.0; gairaigo=0.0 |
| `殯/あがり` | 0.97 | 0.982631 | 0.924391 | +0.032977 | rarity=0.953039; marked=1.0; domain=0.540062; gairaigo=0.0 |
| `云為/うんい` | 0.92 | 0.915337 | 0.915337 | +0 | rarity=0.999118; marked=0.0; domain=0.286643; gairaigo=0.0 |
| `井蛙/せいあ` | 0.88 | 0.887082 | 0.887082 | +0 | rarity=0.965999; marked=0.0; domain=0.456435; gairaigo=0.0 |
| `セル画/せるが` | 0.6 | 0.912157 | 0.912157 | +0 | rarity=0.999118; marked=0.0; domain=0.0; gairaigo=0.0 |
| `歯齦/しぎん` | 0.85 | 0.982597 | 0.86 | -0.122597 | rarity=0.996521; marked=1.0; domain=1.0; gairaigo=0.0 |
| `完黙/かんもく` | 0.75 | 0.920341 | 0.920341 | +0 | rarity=0.999118; marked=0.0; domain=0.353553; gairaigo=0.0 |
| `ゲバ棒/げばぼう` | 0.72 | 0.85896 | 0.85896 | +0 | rarity=0.942866; marked=0.0; domain=0.456435; gairaigo=0.0 |
| `鬚鯨/ひげくじら` | 0.78 | 0.842804 | 0.842804 | +0 | rarity=0.964993; marked=1.0; domain=0.5; gairaigo=0.0 |
| `邏卒/らそつ` | 0.92 | 0.997567 | 0.942845 | -0.054722 | rarity=0.965827; marked=1.0; domain=0.408248; gairaigo=0.0 |
| `仄めく/ほのめく` | 0.65 | 0.830525 | 0.830525 | +0 | rarity=0.892557; marked=1.0; domain=0.645497; gairaigo=0.0 |
| `サビ残/さびざん` | 0.64 | 0.848022 | 0.848022 | +0 | rarity=0.993169; marked=0.0; domain=0.0; gairaigo=0.0 |
| `デバッグ/でばっぐ` |  | 0.93673 | 0.86 |  | rarity=0.943411; marked=1.0; domain=1.0; gairaigo=1.0 |
| `ジェラート/じぇらーと` |  | 0.936785 | 0.914268 |  | rarity=0.955748; marked=0.0; domain=0.612372; gairaigo=1.0 |
| `キュイジーヌ/きゅいじーぬ` |  | 0.936703 | 0.901005 |  | rarity=0.969344; marked=0.0; domain=0.707107; gairaigo=1.0 |
| `ワンピ/わんぴ` |  | 0.936821 | 0.86 |  | rarity=0.92317; marked=1.0; domain=0.57735; gairaigo=1.0 |

## Best Variant Regressions

| Row | Expected | Baseline | Candidate | Error Δ |
| --- | ---: | ---: | ---: | ---: |
| `holdout:殯/あがり` | 0.97 | 0.982631 | 0.924391 | +0.032977 |
| `calibration:靉靆/あいたい` | 0.98 | 0.999183 | 0.960252 | +0.000565 |
| `calibration:的/まと` | 0.4 | 0.204597 | 0.204597 | +0 |
| `holdout:印鑑/いんかん` | 0.6 | 0.413415 | 0.413415 | +0 |
| `holdout:他害/たがい` | 0.6 | 0.676544 | 0.676544 | +0 |
| `holdout:京劇/きょうげき` | 0.6 | 0.562538 | 0.562538 | +0 |
| `holdout:亥/い` | 0.6 | 0.491712 | 0.491712 | +0 |
| `holdout:亡骸/なきがら` | 0.58 | 0.47952 | 0.47952 | +0 |
| `holdout:トロ箱/とろばこ` | 0.66 | 0.831028 | 0.831028 | +0 |
| `holdout:ゲバ棒/げばぼう` | 0.72 | 0.85896 | 0.85896 | +0 |
| `holdout:鼻頭/はながしら` | 0.62 | 0.74939 | 0.74939 | +0 |
| `holdout:鰤/ぶり` | 0.55 | 0.587564 | 0.587564 | +0 |

## Clear Winners

- `targeted_dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000296`
- `targeted_fam_m0p06_s0p5__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000296`
- `targeted_fam_m0p06_s1__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000296`
- `targeted_fam_m0p1_s0p5__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000296`
- `targeted_fam_m0p1_s1__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000296`
- `targeted_fam_m0p14_s0p5__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000296`
- `targeted_fam_m0p14_s1__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000296`
- `targeted_gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000069`
- `targeted_fam_m0p06_s0p5__gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000069`
- `targeted_fam_m0p06_s1__gai_ascii_origin_english_only_d0p02__dom_domain_c0p86_s1` holdout `0.915124`, first60 Δ `+0.000069`
