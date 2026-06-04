# Pack Lifecycle Audit

- Generated at: `2026-05-16T18:40:40+00:00`
- Data root: `/private/tmp/lexishift-spalex-audit/data-root`
- Pair/profile: `en-es` / `default`
- Status: `review`
- Installed pack count: `1`
- Missing provenance sidecars: `0`
- Invalid provenance sidecars: `0`
- Provenance review required: `1`
- Source policy decision items: `1`
- Missing installed artifacts: `0`

## Installed Pack Families

| Family | Packs | Missing Manifest | Missing Artifact | Missing Provenance | Invalid Provenance | Provenance Review |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| language | 0 | 0 | 0 | 0 | 0 | 0 |
| frequency | 1 | 0 | 0 | 0 | 0 | 1 |
| embedding | 0 | 0 | 0 | 0 | 0 | 0 |

## Semantic Pack Copies

- Pack count: `0`
- Missing inventory count: `0`
- Missing provenance count: `0`
- Provenance review required: `0`

## Provenance Review

| Family | Pack | Policy | License | Source Pointer | Source Identity | Raw Checksums | Artifact Checksum | Review Reasons |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| frequency | freq-es-spalex-expanded-v1 | review | requires_review | source_url | source_version | 1/1 | True | license_status_requires_review |

## Source Policy Decision Queue

- Decision items: `1`

| Family | Pack | Category | Review Reason | Recommended Action | Observed |
| --- | --- | --- | --- | --- | --- |
| frequency | freq-es-spalex-expanded-v1 | license_review | license_status_requires_review | record_source_license_decision | requires_review |

## Source/Build Lineage

| Family | Pack | Source Version | Source Bundle | Build Command | Parser Config/Profile | Converter Version |
| --- | --- | --- | --- | --- | --- | --- |
| frequency | freq-es-spalex-expanded-v1 | 10.6084/m9.figshare.5924794.v4 | freq-es-spalex-expanded-v1:spalex_cde_kaikki_v1 (3/3 component checksums) | python3 scripts/data/build_spalex_frequency_pack_en_es.py | current_seed, expansion_source, pos_policy, rank_policy, runtime_pmw, topic_policy | build_spalex_frequency_pack_en_es_v1 |

## Publication Manifests

- Manifest count: `0`
- Invalid count: `0`
- Source lineage count: `0`

## Manual Resource Settings

- Settings path: `/private/tmp/lexishift-spalex-audit/data-root/settings.json`
- Status: `ok`
- Manual path count: `0`
- Manual path review count: `0`
- Managed artifact manual paths: `0`

## Candidate SQLite

- `/private/tmp/lexishift-spalex-audit/data-root/frequency_packs/freq-es-spalex-expanded-v1/main.sqlite`: status=`ok`, primary_table=`frequency`, row_count=`45131`
