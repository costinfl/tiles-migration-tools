# Tiles migration - work split

10 definitions in 3 files across 3 modules.

## Phase 0 - shared base layouts (do these first)

Owner: **alice**. Everyone else is blocked on these.

- [ ] `base.sidebar` (shared, score 8.5) - /WEB-INF/views/layouts/main.jsp
- [ ] `vets.list` (vets, score 7.8) - /WEB-INF/views/layouts/main.jsp
- [ ] `base.print` (shared, score 5.0) - /WEB-INF/views/layouts/main.jsp
- [ ] `base.layout` (shared, score 3.0) - /WEB-INF/views/layouts/main.jsp

## Phase 1 - per-module packages

### alice  (load 24.3)

_no module assigned - Phase 0 only_

### bob  (load 26.5)

**visits** - 4 definitions, score 26.5

- [ ] `visits.detail` (10.2) ⚠
- [ ] `visits.calendar` (9.8) ⚠
- [ ] `common.error` (5.0) ⚠
- [ ] `visits.archived` (1.5) ⚠

### carla  (load 16.0)

**vets** - 2 definitions, score 16.0

- [ ] `vets.*.detail` (10.8) ⚠
- [ ] `vets.legacy` (5.2) ⚠

## Phase 2 - teardown

Owner: **alice**, after every box above is ticked. See `tiles-config.md`.
