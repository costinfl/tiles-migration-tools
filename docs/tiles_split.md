# tiles_split.py

Inventories Apache Tiles definitions across a multi-module Maven/Gradle
project and splits the migration work between people.

## Usage

```bash
python3 scripts/tiles_split.py /path/to/repo --owners alice,bob,carla
python3 scripts/tiles_split.py . --owners a,b --out ./migration
python3 scripts/tiles_split.py . --owners a,b --no-java-scan
```

| Option | Meaning |
|---|---|
| `root` | repository root (positional, required) |
| `--owners` | comma-separated names to split work between (required) |
| `--out` | output directory, default `.` |
| `--no-java-scan` | skip controller scanning; faster, but disables reference detection and therefore the orphan analysis |

Nothing is written inside the target repository.

## How the split works

**Unit of assignment is the module.** The design assumption is one tiles
definition file per module. Assign whole modules and nobody edits the same
file, so there are no merge conflicts.

**Phase 0 comes first.** Any definition used from outside its own module —
via `extends`, via a nested `put-attribute`, or via `<tiles:insertDefinition>`
in a JSP — is a blocker. It goes to one owner to migrate before anyone else
starts. If Phase 0 is empty, the modules are independent and everything can
run in parallel immediately.

**Phase 1 is bin-packed.** Modules are assigned longest-processing-time-first
by total score, seeded with the Phase 0 owner's existing load so they are not
handed the heaviest module on top of it. A module is never split between two
people.

**Phase 2 is teardown** — config beans, dependencies, taglib declarations —
done by one person in a single commit once every box above is ticked.

## Scoring

The score is a rough effort estimate, not a measurement:

| Signal | Weight |
|---|---|
| base | 1.0 |
| each effective attribute | 0.5 |
| each level of inheritance depth beyond the first | 2.0 |
| wildcard or substitution in the name or an attribute | 3.0 |
| `preparer` attribute | 3.0 |
| each nested definition | 2.0 |
| controller references | 0.25 each, capped at 3.0 |

Run it once, look at the ranking, and adjust `score()` if it disagrees with
your sense of which pages are actually painful. The ordering matters more
than the absolute numbers.

## What it understands

- `tiles.xml`, `tiles-defs.xml`, `tiles-definitions.xml` and similar names
- Tiles 3 `put-attribute` and Tiles 1.x `put` spellings
- `extends` chains, flattened to effective template and merged attributes
- Wildcard definitions (`orders.*.detail`), matched the way Tiles matches them
- Controller references: `new ModelAndView("x")`, `setViewName("x")`, bare
  `return "x";` from an `@Controller`, and view names held in
  `static final String` constants
- JSP references via `<tiles:insertDefinition name="x">`
- Config surface: `TilesConfigurer`, `TilesViewResolver`, `TilesView`,
  custom initializers, servlet listeners, `org.apache.tiles` imports,
  Maven and Gradle `tiles-*` dependencies, taglib usage
- Definition file paths declared in config, reconciled against files on disk

## Limitations

These are real and worth reading before acting on the output.

**Runtime view names cannot be resolved.** `setViewName(someVariable)` lands
in `tiles-risks.md` under "non-literal view names" and needs a human. On a
codebase that does this a lot, controller-reference counts undercount and the
"unreferenced definitions" list will contain false positives. It is a review
list, not a delete list.

**Duplicate names shadow each other.** When two modules define the same name,
the last file loaded wins — which is what Tiles does too — so the earlier
definition does not appear in anyone's checklist. It is reported under
"duplicate definition names" and must be assigned by hand.

**One definition file per module is assumed.** Multiple files per module
still parse correctly, but the conflict-free-assignment guarantee weakens,
because two owners could end up editing the same module's files.

**Scoring is a guess.** See above.

**Tiles EL in attribute values is not evaluated.** Expressions are treated as
opaque strings.

## Testing

`fixtures/spring-mvc-tiles-clinic-suite` is a synthetic four-module project
that deliberately contains a wildcard definition, a `ViewPreparer`, Tiles 1.x
`put` syntax, a four-deep inheritance chain crossing two module boundaries, a
duplicate name in two modules, an `extends` to a nonexistent parent, a
non-literal view name, a view name with no definition, and a config path
pointing at a file that does not exist.

Committed output for it is in `reports/clinic-suite`. Re-run after changing
the script and diff:

```bash
cd fixtures/spring-mvc-tiles-clinic-suite
python3 ../../scripts/tiles_split.py . --owners alice,bob,carla --out /tmp/check
diff -r /tmp/check ../../reports/clinic-suite
```

A caveat on this fixture: it was written by the same author as the script, so
it tests the failure modes that author already had in mind. A fixture written
without sight of the implementation, or a real codebase, is a stronger test.
