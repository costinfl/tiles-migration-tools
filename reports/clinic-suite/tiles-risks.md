# Tiles migration - risks and loose ends

## Unreferenced definitions (2) - delete candidates

- `common.error` (visits)
- `visits.archived` (visits)

## View names with no definition (1)

Probably JSP paths resolved by another ViewResolver, or wildcard matches. Check before deleting anything.

- `visits.export.pdf`

## Non-literal view names (1) - manual audit

- visits/src/main/java/com/example/visits/VisitController.java: `.setViewName(chosen`

## ViewPreparer implementations (1)

Each needs rehoming to @ControllerAdvice / HandlerInterceptor.

- shared/src/main/java/com/example/shared/MenuPreparer.java

## Duplicate definition names (1)

Tiles lets the last file loaded win, and so does this script - so the FIRST file below is shadowed and does NOT appear in anyone's checklist. Assign it by hand.

- `common.error`: shadowed in `vets/src/main/webapp/WEB-INF/tiles/tiles-defs.xml`, kept from `visits/src/main/webapp/WEB-INF/tiles/tiles.xml`
