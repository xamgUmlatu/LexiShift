# Core Tests Structure

Tests are grouped by domain to mirror `core/lexishift_core` ownership boundaries.

## Folders

- `architecture/`: architecture boundary and layering checks.
- `replacement/`: replacement pipeline, core replacer, and inflection behavior.
- `frequency/`: frequency store/provider behavior.
- `helper/`: helper engine/profiles/daemon/use-case integration tests.
- `persistence/`: settings/storage/import-export behavior.
- `resources/`: dictionary/script/resource loaders.
- `rulegen/`: rule-generation adapters and integrations.
- `srs/`: SRS policies, planner, scheduler, gate, and end-to-end scenarios.

## Running

- All tests: `python -m unittest discover -s core/tests`
