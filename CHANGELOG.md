# Changelog

All notable changes to this project will be documented in this file.

## Unreleased
- Initial project scaffolding and tooling.
- Added Spanish LP support docs and operational references for `en-es`, `es-en`, and `es-es` resources.
- Documented Spanish conversion scripts (`convert_cde_frequency_to_sqlite.py`, `convert_freedict_spa_eng_to_sqlite.py`, `convert_freedict_eng_spa_to_sqlite.py`).
- Documented paired morphology metadata flow (`metadata.morphology.target_surface`) and canonical lemma behavior for SRS feedback/gating.
- Clarified frequency weighting behavior when `pmw` is missing (fallback to other numeric frequency columns).
