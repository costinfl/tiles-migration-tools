# Tiles configuration surface - teardown checklist

Not per-definition work. This is what has to be deleted once every definition above is migrated, and it should be done by one person in a single commit.

## Config and code references (8 files)

- [ ] `pom.xml` - org.apache.tiles reference
- [ ] `shared/pom.xml` - org.apache.tiles reference
- [ ] `shared/src/main/java/com/example/shared/MenuPreparer.java` - Tiles runtime API
- [ ] `vets/pom.xml` - org.apache.tiles reference
- [ ] `visits/pom.xml` - org.apache.tiles reference
- [ ] `webapp/pom.xml` - org.apache.tiles reference
- [ ] `webapp/src/main/resources/mvc-config.xml` - TilesConfigurer, TilesViewResolver
- [ ] `webapp/src/main/webapp/WEB-INF/web.xml` - Tiles servlet listener

## Build dependencies (5 files)

- [ ] `pom.xml` - tiles-core
- [ ] `shared/pom.xml` - tiles-jsp
- [ ] `vets/pom.xml` - tiles-jsp
- [ ] `visits/pom.xml` - tiles-jsp
- [ ] `webapp/pom.xml` - tiles-core, tiles-extras

## JSPs using the tiles taglib (3 files, 7 tag uses)

These are edited by whoever owns the module, alongside the definitions.

**shared**

- [ ] `shared/src/main/webapp/WEB-INF/views/fragments/header.jsp` (1 tags)
- [ ] `shared/src/main/webapp/WEB-INF/views/layouts/main.jsp` (5 tags)

**vets** - carla

- [ ] `vets/src/main/webapp/WEB-INF/views/vets/list.jsp` (1 tags)


## Configured vs discovered definition files

- `/WEB-INF/tiles/tiles-defs.xml` - ok
- `/WEB-INF/tiles/tiles-reports.xml` - NOT FOUND on disk
- `/WEB-INF/tiles/tiles.xml` - ok
