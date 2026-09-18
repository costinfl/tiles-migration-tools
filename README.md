# tiles-migration-tools

Tooling for removing Apache Tiles from multi-module Spring MVC projects.

Apache Tiles was retired by the ASF in 2021, and Spring Framework 6 / Boot 3
dropped `TilesConfigurer` entirely. For most codebases this is a forced
migration rather than a cleanup, and the hard part is not the mechanical
edit — it is knowing how much work there is, who can do which part in
parallel, and what will silently break at render time.

## Layout

```
scripts/     runnable tools
docs/        migration plan, tool documentation
reports/     output from real runs, committed as a baseline
fixtures/    synthetic projects used to test the tools
```

## Quick start

```bash
python3 scripts/tiles_split.py /path/to/repo --owners alice,bob,carla
```

Python 3.8+, standard library only. No network access, no dependencies,
read-only against the target repository.

## What it produces

| File | Contents |
|---|---|
| `tiles-inventory.csv` | one row per definition: flattened template and attributes, nested definitions, referencing controllers, complexity score, assigned owner |
| `tiles-assignments.md` | Phase 0 (shared base layouts), Phase 1 (per-module checklists), Phase 2 (teardown) |
| `tiles-risks.md` | unreferenced definitions, view names with no definition, non-literal view names, `ViewPreparer` implementations, shadowed duplicate names |
| `tiles-config.md` | config beans, build dependencies, JSPs using the tiles taglib, configured-vs-discovered definition files |

See [docs/tiles_split.md](docs/tiles_split.md) for the full description and
[docs/migration-plan.md](docs/migration-plan.md) for the migration approach
the tool is built around.

## Status

Tested against two projects: a single-module reference app and a synthetic
four-module fixture (`fixtures/spring-mvc-tiles-clinic-suite`). Committed
output from both runs is in `reports/`, so changes to the script produce a
visible diff there.

Known limitations are listed at the end of `docs/tiles_split.md`. The most
important one: definition names built at runtime cannot be resolved
statically, so on a codebase that uses `setViewName(someVariable)` heavily,
the "unreferenced definitions" list will contain false positives. Do not
delete from it without checking.
