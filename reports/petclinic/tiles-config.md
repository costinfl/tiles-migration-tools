# Tiles configuration surface - teardown checklist

Not per-definition work. This is what has to be deleted once every definition above is migrated, and it should be done by one person in a single commit.

## Config and code references (2 files)

- [ ] `pom.xml` - org.apache.tiles reference
- [ ] `src/main/java/com/example/config/WebConfig.java` - TilesConfigurer, TilesViewResolver

## Build dependencies (1 files)

- [ ] `pom.xml` - tiles-jsp

## JSPs using the tiles taglib (1 files, 5 tag uses)

These are edited by whoever owns the module, alongside the definitions.

**<root>** - alice

- [ ] `src/main/webapp/WEB-INF/views/layouts/defaultLayout.jsp` (5 tags)


## Configured vs discovered definition files

- `/WEB-INF/tiles/tiles-definitions.xml` - ok
