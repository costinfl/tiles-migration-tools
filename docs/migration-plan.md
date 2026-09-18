# Removing Apache Tiles from a Spring MVC project

Apache Tiles was retired by the ASF in 2021, and Spring Framework 6 / Boot 3
dropped `TilesConfigurer` entirely. This is usually a forced migration.

## 1. Inventory what Tiles actually does for you

- Definition files: `tiles.xml`, `tiles-defs.xml`, `**/tiles/*.xml`
- Config: `TilesConfigurer`, `TilesViewResolver`, `TilesView`,
  `UrlBasedViewResolver` with a Tiles view class
- Templates: `<tiles:insertAttribute>`, `insertDefinition`, `getAsString`,
  `importAttribute`, and the taglib declarations
- Code: `ViewPreparer` implementations, `TilesRequestContext` usage
- Build: `tiles-core`, `tiles-jsp`, `tiles-servlet`, `tiles-el`,
  `tiles-extras`, `tiles-request-*`

`scripts/tiles_split.py` automates this step and produces the work split.

## 2. Choose the target

- **Thymeleaf + Layout Dialect** — closest conceptual match (layout
  inheritance, fragments), best if you are moving to Boot 3 anyway
- **Plain JSP with `<jsp:include>` / tag files** — cheapest if you must keep
  JSP and the definitions are shallow
- **SiteMesh** — decorator model, good if layouts are mostly "wrap the page
  in chrome"

## 3. Flatten the definition tree first

Tiles definitions inherit via `extends` and cascade attributes. Resolve each
definition into its fully effective attribute set before touching code. This
is where migrations go wrong, and it is what the `effective_template` and
`num_attrs` columns of `tiles-inventory.csv` give you.

## 4. Migrate incrementally with both resolvers active

Keep `TilesViewResolver` and add the new resolver with an explicit `order`.
Put the new one first; unresolved names fall through to Tiles. Migrate page
by page, keeping view names identical so controllers do not change.

## 5. Replace the awkward parts

- `ViewPreparer` → `@ControllerAdvice` / `@ModelAttribute` / `HandlerInterceptor`
- Wildcard definitions (`*.details`) → convention in the resolver, or
  explicit fragments
- Tiles-rendered error pages and `404`/`500` mappings — easy to miss, they
  bypass normal controller flow

## 6. Strip it out

Delete definition files, the `TilesConfigurer` bean, taglib declarations and
dependencies. Then grep the tree for `tiles` case-insensitively, including
`web.xml`, `*.properties` and `*.yml`. This is what `tiles-config.md` is for.

## 7. Verify

Hit every view. Tiles fails at render time, not compile time, so the compiler
will not help. A smoke test that GETs every mapped URL and asserts HTTP 200
plus a known layout element catches most of it.

## Splitting the work

One definition file per module means one owner per file means no merge
conflicts. The serialization point is shared base definitions crossing module
lines: those are Phase 0 and everyone else is blocked on them. See
[tiles_split.md](tiles_split.md).
