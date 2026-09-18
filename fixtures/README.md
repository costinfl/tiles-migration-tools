# fixtures

Synthetic projects used to test the tools. They are not buildable
applications — the Java files have no dependencies resolved and the poms
reference modules only for structure. They exist so the scanners have
something realistic to walk.

## spring-mvc-tiles-clinic-suite

Four Maven modules (`shared`, `vets`, `visits`, `webapp`) with XML-based
Spring config and a `web.xml` listener. Deliberately contains:

- a wildcard definition (`vets.*.detail`) referenced as `vets.surgeon.detail`
- a `ViewPreparer` wired via the `preparer` attribute
- Tiles 1.x `<put>` syntax alongside Tiles 3 `<put-attribute>`
- a four-deep inheritance chain crossing two module boundaries
- a cross-module `<tiles:insertDefinition>` from a JSP
- the same definition name in two modules
- `extends` pointing at a nonexistent parent
- `setViewName(variable)` and a view name with no definition
- a definition file named in config that does not exist on disk
