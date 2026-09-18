# reports

Committed output from real runs, kept as a regression baseline: changing
`scripts/tiles_split.py` should produce a visible diff here.

| Directory | Source project |
|---|---|
| `petclinic/` | single-module Spring MVC reference app, Java config, 3 definitions |
| `clinic-suite/` | `fixtures/spring-mvc-tiles-clinic-suite`, 4 modules, XML config, 10 definitions |

Regenerate:

```bash
cd fixtures/spring-mvc-tiles-clinic-suite
python3 ../../scripts/tiles_split.py . --owners alice,bob,carla \
        --out ../../reports/clinic-suite
```

Owner names in these reports are placeholders. The `petclinic/` report was
generated from a project that is not committed here, so it cannot be
regenerated from this repository.
