# Tiles migration - work split

3 definitions in 1 files across 1 modules.

## Phase 0 - shared base layouts (do these first)

_None: no definition is used across module boundaries. All modules can be migrated fully in parallel._

## Phase 1 - per-module packages

### alice  (load 15.1)

**<root>** - 3 definitions, score 15.1

- [ ] `welcome` (5.8)
- [ ] `ownersList` (5.8)
- [ ] `base-layout` (3.5)

### bob  (load 0.0)

_no module assigned_

## Phase 2 - teardown

Owner: **alice**, after every box above is ticked. See `tiles-config.md`.
