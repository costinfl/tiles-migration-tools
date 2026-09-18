#!/usr/bin/env python3
"""
tiles_split.py - inventory Apache Tiles definitions across a multi-module
Maven/Gradle project and split the migration work between colleagues.

Assumptions that match the common layout:
  * each submodule owns exactly one tiles definition file
  * Spring MVC controllers return ModelAndView (or set a view name)

Unit of assignment is the MODULE, because one tiles.xml per module means
one owner per file means no merge conflicts. Definitions that are shared
across modules (via extends= or nested put-attribute) are pulled out into
Phase 0 and given to a single owner to do first, since everyone else
depends on them.

Usage:
    python3 tiles_split.py /path/to/repo --owners alice,bob,carla
    python3 tiles_split.py . --owners a,b --out ./migration

Outputs:
    tiles-inventory.csv     one row per definition, with score + owner
    tiles-assignments.md    per-owner checklist, ordered by phase
    tiles-risks.md          orphans, missing views, dynamic view names
    tiles-config.md         config beans, deps, taglib usage - Phase 2 teardown
"""

import argparse
import csv
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------- discovery

DEF_FILE_RE = re.compile(r"^tiles[\w.-]*\.xml$|^tiles-def(inition)?s?\.xml$", re.I)
BUILD_FILES = ("pom.xml", "build.gradle", "build.gradle.kts")
SKIP_DIRS = {".git", ".idea", "target", "build", "node_modules", ".svn", "out"}


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        yield Path(dirpath), filenames


def find_definition_files(root):
    found = []
    for dirpath, filenames in walk(root):
        for fn in filenames:
            if DEF_FILE_RE.match(fn):
                found.append(dirpath / fn)
    return sorted(found)


def relpath(p, root):
    try:
        return Path(p).relative_to(root).as_posix()
    except ValueError:
        return str(p)


def module_of(path, root):
    """Nearest ancestor holding a build file; else first path segment."""
    p = path.parent
    while True:
        if any((p / b).exists() for b in BUILD_FILES):
            rel = p.relative_to(root).as_posix()
            return "<root>" if rel in ("", ".") else rel
        if p == root or p == p.parent:
            break
        p = p.parent
    rel = path.relative_to(root).parts
    return rel[0] if len(rel) > 1 else "<root>"


# ---------------------------------------------------------------- parsing


class Definition:
    __slots__ = ("name", "template", "extends", "preparer", "attrs",
                 "file", "module", "depth", "eff_template", "eff_attrs",
                 "def_deps", "jsp_files", "controllers", "jsp_refs", "score",
                 "phase", "owner", "notes")

    def __init__(self, name, template, extends, preparer, attrs, file, module):
        self.name = name
        self.template = template
        self.extends = extends
        self.preparer = preparer
        self.attrs = attrs              # own put-attribute only
        self.file = file
        self.module = module
        self.depth = 0
        self.eff_template = template
        self.eff_attrs = dict(attrs)
        self.def_deps = set()           # definitions referenced by attr value
        self.jsp_files = set()
        self.controllers = set()
        self.jsp_refs = set()
        self.score = 0.0
        self.phase = 1
        self.owner = ""
        self.notes = []


def strip_doctype(text):
    return re.sub(r"<!DOCTYPE[^>]*(\[[^\]]*\])?>", "", text, flags=re.S)


def parse_definitions(path, module, errors):
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        root = ET.fromstring(strip_doctype(raw))
    except Exception as exc:  # noqa: BLE001 - report and continue
        errors.append((str(path), str(exc)))
        return []

    defs = []
    for el in root.iter("definition"):
        name = el.get("name") or el.get("id")
        if not name:
            continue
        attrs = {}
        for pa in el.findall("put-attribute"):
            an = pa.get("name")
            if an:
                attrs[an] = pa.get("value") or (pa.text or "").strip()
        # tiles 1.x spelling
        for pa in el.findall("put"):
            an = pa.get("name")
            if an:
                attrs[an] = pa.get("value") or (pa.text or "").strip()
        defs.append(Definition(
            name=name,
            template=el.get("template") or el.get("path") or "",
            extends=el.get("extends") or "",
            preparer=el.get("preparer") or "",
            attrs=attrs,
            file=str(path),
            module=module,
        ))
    return defs


# ------------------------------------------------------- inheritance resolve


def resolve(defs_by_name):
    """Flatten extends chains: effective template + merged attributes."""
    resolving = set()

    def _resolve(name):
        d = defs_by_name.get(name)
        if d is None or d.depth:           # already done (depth>0) or missing
            return d
        if name in resolving:
            d.notes.append("CYCLE in extends chain")
            return d
        if not d.extends:
            d.depth = 1
            return d
        resolving.add(name)
        parent = _resolve(d.extends)
        resolving.discard(name)
        if parent is None:
            d.notes.append(f"extends missing definition '{d.extends}'")
            d.depth = 1
            return d
        d.depth = parent.depth + 1
        merged = dict(parent.eff_attrs)
        merged.update(d.attrs)
        d.eff_attrs = merged
        d.eff_template = d.template or parent.eff_template
        if parent.module != d.module:
            d.notes.append(f"extends across module ({parent.module})")
        return d

    for n in list(defs_by_name):
        _resolve(n)
    # anything still depth 0 is a leaf we never touched
    for d in defs_by_name.values():
        d.depth = d.depth or 1


JSP_RE = re.compile(r"\.jspx?$", re.I)


def link_dependencies(defs_by_name):
    for d in defs_by_name.values():
        values = [d.eff_template] + list(d.eff_attrs.values())
        for v in values:
            if not v:
                continue
            if JSP_RE.search(v) or v.startswith("/"):
                d.jsp_files.add(v)
            elif v in defs_by_name:
                d.def_deps.add(v)
                if defs_by_name[v].module != d.module:
                    d.notes.append(f"nests definition from {defs_by_name[v].module}")


# ------------------------------------------------------- controller scanning

MAV_NEW_RE = re.compile(r'new\s+ModelAndView\s*\(\s*("([^"]+)"|([A-Za-z_][\w.]*))')
SET_VIEW_RE = re.compile(r'\.setViewName\s*\(\s*("([^"]+)"|([A-Za-z_][\w.]*))')
CONST_RE = re.compile(
    r'static\s+final\s+String\s+(\w+)\s*=\s*"([^"]+)"')
RETURN_STR_RE = re.compile(r'return\s+"([^"]+)"\s*;')
PREPARER_IMPL_RE = re.compile(r'implements\s+[\w.<>, ]*\bViewPreparer\b')


def scan_java(root):
    """Return (view_name -> set(files), dynamic_sites, preparer_files)."""
    refs = defaultdict(set)
    dynamic = []
    preparers = []
    for dirpath, filenames in walk(root):
        for fn in filenames:
            if not fn.endswith(".java"):
                continue
            p = dirpath / fn
            try:
                src = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "ModelAndView" not in src and "setViewName" not in src \
                    and "ViewPreparer" not in src:
                continue
            if PREPARER_IMPL_RE.search(src):
                preparers.append(str(p))
            consts = dict(CONST_RE.findall(src))
            for rx in (MAV_NEW_RE, SET_VIEW_RE):
                for m in rx.finditer(src):
                    literal, ident = m.group(2), m.group(3)
                    if literal:
                        refs[literal].add(str(p))
                    elif ident in consts:
                        refs[consts[ident]].add(str(p))
                    elif ident and ident[0].isupper() is False:
                        dynamic.append((str(p), m.group(0).strip()))
            # controllers returning a bare String view name
            if "@Controller" in src or "@RestController" not in src:
                for m in RETURN_STR_RE.finditer(src):
                    refs[m.group(1)].add(str(p))
    return refs, dynamic, preparers


# ------------------------------------------------------- config surface scan

CONFIG_SIGNALS = [
    (re.compile(r'\bTilesConfigurer\b'), "TilesConfigurer"),
    (re.compile(r'\bTilesViewResolver\b'), "TilesViewResolver"),
    (re.compile(r'\bTilesView\b(?!Resolver)'), "TilesView"),
    (re.compile(r'\bAbstractTilesInitializer\b|\bTilesInitializer\b'),
     "custom TilesInitializer"),
    (re.compile(r'\bTilesRequestContext\b|\bAttributeContext\b'),
     "Tiles runtime API"),
    (re.compile(r'\bTilesListener\b|org\.apache\.tiles[\w.]*Listener'),
     "Tiles servlet listener"),
    (re.compile(r'org\.apache\.tiles'), "org.apache.tiles reference"),
    (re.compile(r'\btiles[23]\b'), "spring tiles integration package"),
]

CONFIG_EXTS = (".java", ".xml", ".jsp", ".jspx", ".tag", ".tagx",
               ".gradle", ".kts", ".properties", ".yml", ".yaml")

MAVEN_DEP_RE = re.compile(r"<artifactId>\s*(tiles[-\w]*)\s*</artifactId>")
GRADLE_DEP_RE = re.compile(r"""['"]org\.apache\.tiles:([\w.-]+)""")
TAGLIB_URI_RE = re.compile(r"tiles\.apache\.org/tags-tiles[\w-]*")
TILES_TAG_RE = re.compile(r"<tiles:(\w+)")
INSERT_DEF_RE = re.compile(
    r'<tiles:(?:insertDefinition|insertTemplate)[^>]*?'
    r'name\s*=\s*"([^"]+)"', re.S)
SET_DEFS_JAVA_RE = re.compile(r"setDefinitions\s*\((.*?)\)\s*;", re.S)
SET_DEFS_XML_RE = re.compile(
    r'name\s*=\s*"definitions"(.*?)</property>', re.S)
STRING_LIT_RE = re.compile(r'"([^"]+)"')
XML_VALUE_RE = re.compile(r"<value>\s*([^<]+?)\s*</value>")


def scan_config(root):
    """Find everything outside tiles.xml that wires Tiles in.

    Returns (findings, deps, taglib, configured_defs) where
      findings      list of (relpath, label)
      deps          relpath -> set of tiles artifact names
      taglib        relpath -> (module, count of <tiles:*> tags)
      configured_defs  set of definition paths named in config
      jsp_def_refs  definition name -> set of (relpath, module)
    """
    findings = []
    deps = defaultdict(set)
    taglib = {}
    configured = set()
    jsp_def_refs = defaultdict(set)

    for dirpath, filenames in walk(root):
        for fn in filenames:
            if not fn.endswith(CONFIG_EXTS):
                continue
            p = dirpath / fn
            if DEF_FILE_RE.match(fn):
                continue                      # the definitions themselves
            try:
                src = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "tiles" not in src.lower():
                continue
            rel = relpath(p, root)

            labels = [lab for rx, lab in CONFIG_SIGNALS if rx.search(src)]
            # don't report the generic catch-alls when a specific one matched
            specific = [l for l in labels
                        if l not in ("org.apache.tiles reference",
                                     "spring tiles integration package")]
            for lab in (specific or labels):
                findings.append((rel, lab))

            if fn == "pom.xml":
                for art in MAVEN_DEP_RE.findall(src):
                    deps[rel].add(art)
            if fn.endswith((".gradle", ".kts")):
                for art in GRADLE_DEP_RE.findall(src):
                    deps[rel].add(art)

            if TAGLIB_URI_RE.search(src) or TILES_TAG_RE.search(src):
                n = len(TILES_TAG_RE.findall(src))
                mod = module_of(p, root)
                taglib[rel] = (mod, n)
                for dname in INSERT_DEF_RE.findall(src):
                    jsp_def_refs[dname].add((rel, mod))

            for blob in SET_DEFS_JAVA_RE.findall(src):
                configured.update(STRING_LIT_RE.findall(blob))
            for blob in SET_DEFS_XML_RE.findall(src):
                configured.update(XML_VALUE_RE.findall(blob))
                configured.update(
                    v.strip() for v in re.split(r"[,\s]+", blob)
                    if v.strip().endswith(".xml"))

    return findings, deps, taglib, configured, jsp_def_refs


# ---------------------------------------------------------------- scoring

WILDCARD_RE = re.compile(r"[*{}]")


def wildcard_matcher(defs_by_name):
    """Tiles resolves 'orders.x.detail' against a def named 'orders.*.detail'.
    Build regexes so controller refs are matched the way Tiles matches them."""
    pats = []
    for name in defs_by_name:
        if "*" in name:
            rx = "^" + ".*?".join(re.escape(p) for p in name.split("*")) + "$"
            pats.append((re.compile(rx), name))
    pats.sort(key=lambda t: -len(t[1]))     # most specific pattern first

    def match(view):
        if view in defs_by_name:
            return view
        for rx, name in pats:
            if rx.match(view):
                return name
        return None

    return match


def score(d):
    s = 1.0
    s += 0.5 * len(d.eff_attrs)
    s += 2.0 * max(0, d.depth - 1)
    if WILDCARD_RE.search(d.name) or any(
            WILDCARD_RE.search(v or "") for v in d.eff_attrs.values()):
        s += 3.0
        d.notes.append("wildcard/substitution definition")
    if d.preparer:
        s += 3.0
        d.notes.append(f"ViewPreparer: {d.preparer}")
    s += 2.0 * len(d.def_deps)
    s += min(3.0, 0.25 * len(d.controllers))
    return round(s, 1)


# ---------------------------------------------------------------- packaging


def assign(modules_scored, owners, seed=None):
    """Longest-processing-time-first bin packing over modules.

    seed pre-loads an owner (the Phase 0 owner already has work) so the
    packer doesn't hand them the biggest module on top of it.
    """
    loads = {o: 0.0 for o in owners}
    if seed:
        for o, v in seed.items():
            loads[o] = loads.get(o, 0.0) + v
    plan = {}
    for module, total in sorted(modules_scored.items(),
                                key=lambda kv: -kv[1]):
        owner = min(loads, key=lambda o: loads[o])
        plan[module] = owner
        loads[owner] += total
    return plan, loads


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="repository root")
    ap.add_argument("--owners", required=True,
                    help="comma-separated names to split work between")
    ap.add_argument("--out", default=".", help="output directory")
    ap.add_argument("--no-java-scan", action="store_true",
                    help="skip controller scanning (faster)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    owners = [o.strip() for o in args.owners.split(",") if o.strip()]
    outdir = Path(args.out).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    errors = []
    def_files = find_definition_files(root)
    if not def_files:
        sys.exit(f"No tiles definition files found under {root}")

    all_defs = []
    for f in def_files:
        all_defs.extend(parse_definitions(f, module_of(f, root), errors))

    by_name = {}
    dupes = []
    for d in all_defs:
        if d.name in by_name:
            dupes.append((d.name, by_name[d.name].file, d.file))
        by_name[d.name] = d

    resolve(by_name)
    link_dependencies(by_name)

    refs, dynamic, preparer_files = ({}, [], [])
    unmatched = []
    match_view = wildcard_matcher(by_name)
    if not args.no_java_scan:
        refs, dynamic, preparer_files = scan_java(root)
        for view, files in refs.items():
            target = match_view(view)
            if target:
                by_name[target].controllers |= files
                if target != view:
                    by_name[target].notes.append(
                        f"matched via wildcard from '{view}'")
            else:
                unmatched.append(view)

    findings, deps, taglib, configured, jsp_def_refs = scan_config(root)
    for dname, uses in jsp_def_refs.items():
        d = by_name.get(dname)
        if d is None:
            unmatched.append(dname)
            continue
        for rel, mod in uses:
            d.jsp_refs.add(rel)
            if mod != d.module:
                d.notes.append(f"inserted from a JSP in {mod}")

    # which definitions are depended on from another module -> Phase 0
    shared = set()
    for d in by_name.values():
        for rel, mod in jsp_def_refs.get(d.name, ()):
            if mod != d.module:
                shared.add(d.name)
    for d in by_name.values():
        for dep_name in list(d.def_deps) + ([d.extends] if d.extends else []):
            dep = by_name.get(dep_name)
            if dep and dep.module != d.module:
                shared.add(dep.name)

    for d in by_name.values():
        d.score = score(d)
        if d.name in shared:
            d.phase = 0
            d.notes.append("SHARED across modules - migrate first")

    module_scores = defaultdict(float)
    for d in by_name.values():
        if d.phase == 1:
            module_scores[d.module] += d.score
    phase0_total = sum(d.score for d in by_name.values() if d.phase == 0)
    plan, loads = assign(module_scores, owners,
                         seed={owners[0]: phase0_total})

    phase0_owner = owners[0]
    for d in by_name.values():
        d.owner = phase0_owner if d.phase == 0 else plan.get(d.module, "")

    # ------------------------------------------------------------ outputs
    csv_path = outdir / "tiles-inventory.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["phase", "owner", "module", "definition", "extends",
                    "depth", "effective_template", "num_attrs", "preparer",
                    "nested_definitions", "jsp_files", "controller_refs",
                    "score", "notes"])
        for d in sorted(by_name.values(),
                        key=lambda x: (x.phase, x.owner, x.module, x.name)):
            w.writerow([d.phase, d.owner, d.module, d.name, d.extends,
                        d.depth, d.eff_template, len(d.eff_attrs), d.preparer,
                        ";".join(sorted(d.def_deps)),
                        ";".join(sorted(d.jsp_files)),
                        ";".join(relpath(c, root) for c in sorted(d.controllers)),
                        d.score, " | ".join(dict.fromkeys(d.notes))])

    md = outdir / "tiles-assignments.md"
    with md.open("w", encoding="utf-8") as fh:
        fh.write("# Tiles migration - work split\n\n")
        fh.write(f"{len(by_name)} definitions in {len(def_files)} files "
                 f"across {len(set(d.module for d in by_name.values()))} modules.\n\n")
        fh.write("## Phase 0 - shared base layouts (do these first)\n\n")
        p0 = [d for d in by_name.values() if d.phase == 0]
        if not p0:
            fh.write("_None: no definition is used across module boundaries. "
                     "All modules can be migrated fully in parallel._\n\n")
        else:
            fh.write(f"Owner: **{phase0_owner}**. "
                     "Everyone else is blocked on these.\n\n")
            for d in sorted(p0, key=lambda x: -x.score):
                fh.write(f"- [ ] `{d.name}` ({d.module}, score {d.score}) "
                         f"- {d.eff_template or 'no template'}\n")
            fh.write("\n")
        fh.write("## Phase 1 - per-module packages\n\n")
        for owner in owners:
            mods = [m for m, o in plan.items() if o == owner]
            fh.write(f"### {owner}  (load {loads[owner]:.1f})\n\n")
            if not mods:
                fh.write("_no module assigned"
                         + (" - Phase 0 only_\n\n" if owner == phase0_owner
                            else "_\n\n"))
                continue
            for m in sorted(mods):
                ds = [d for d in by_name.values()
                      if d.module == m and d.phase == 1]
                fh.write(f"**{m}** - {len(ds)} definitions, "
                         f"score {module_scores[m]:.1f}\n\n")
                for d in sorted(ds, key=lambda x: -x.score):
                    flag = " ⚠" if d.notes else ""
                    fh.write(f"- [ ] `{d.name}` ({d.score}){flag}\n")
                fh.write("\n")
        fh.write("## Phase 2 - teardown\n\n")
        fh.write(f"Owner: **{phase0_owner}**, after every box above is "
                 "ticked. See `tiles-config.md`.\n")

    risks = outdir / "tiles-risks.md"
    with risks.open("w", encoding="utf-8") as fh:
        fh.write("# Tiles migration - risks and loose ends\n\n")

        orphans = [d for d in by_name.values()
                   if not d.controllers and not d.jsp_refs
                   and not args.no_java_scan
                   and d.name not in shared
                   and not any(d.name in o.def_deps or o.extends == d.name
                               for o in by_name.values())]
        fh.write(f"## Unreferenced definitions ({len(orphans)}) "
                 "- delete candidates\n\n")
        for d in sorted(orphans, key=lambda x: (x.module, x.name)):
            fh.write(f"- `{d.name}` ({d.module})\n")

        missing = sorted(unmatched)
        fh.write(f"\n## View names with no definition ({len(missing)})\n\n")
        fh.write("Probably JSP paths resolved by another ViewResolver, "
                 "or wildcard matches. Check before deleting anything.\n\n")
        for v in missing:
            fh.write(f"- `{v}`\n")

        fh.write(f"\n## Non-literal view names ({len(dynamic)}) "
                 "- manual audit\n\n")
        for f, snippet in dynamic:
            fh.write(f"- {relpath(f, root)}: `{snippet}`\n")

        fh.write(f"\n## ViewPreparer implementations ({len(preparer_files)})\n\n")
        fh.write("Each needs rehoming to @ControllerAdvice / "
                 "HandlerInterceptor.\n\n")
        for f in preparer_files:
            fh.write(f"- {relpath(f, root)}\n")

        if dupes:
            fh.write(f"\n## Duplicate definition names ({len(dupes)})\n\n")
            fh.write("Tiles lets the last file loaded win, and so does this "
                     "script - so the FIRST file below is shadowed and does "
                     "NOT appear in anyone's checklist. Assign it by hand.\n\n")
            for name, a, b in dupes:
                fh.write(f"- `{name}`: shadowed in `{relpath(a, root)}`, "
                         f"kept from `{relpath(b, root)}`\n")

        if errors:
            fh.write(f"\n## Unparseable files ({len(errors)})\n\n")
            for f, e in errors:
                fh.write(f"- {f}: {e}\n")

    # ------------------------------------------------- config surface report
    cfg = outdir / "tiles-config.md"
    with cfg.open("w", encoding="utf-8") as fh:
        fh.write("# Tiles configuration surface - teardown checklist\n\n")
        fh.write("Not per-definition work. This is what has to be deleted "
                 "once every definition above is migrated, and it should be "
                 "done by one person in a single commit.\n\n")

        by_file = defaultdict(list)
        for rel, lab in findings:
            if lab not in by_file[rel]:
                by_file[rel].append(lab)
        fh.write(f"## Config and code references ({len(by_file)} files)\n\n")
        for rel in sorted(by_file):
            fh.write(f"- [ ] `{rel}` - {', '.join(sorted(by_file[rel]))}\n")
        if not by_file:
            fh.write("_none found_\n")

        fh.write(f"\n## Build dependencies ({len(deps)} files)\n\n")
        for rel in sorted(deps):
            fh.write(f"- [ ] `{rel}` - {', '.join(sorted(deps[rel]))}\n")
        if not deps:
            fh.write("_none found_\n")

        tl_by_mod = defaultdict(list)
        for rel, (mod, n) in taglib.items():
            tl_by_mod[mod].append((rel, n))
        total_tags = sum(n for _, n in taglib.values())
        fh.write(f"\n## JSPs using the tiles taglib "
                 f"({len(taglib)} files, {total_tags} tag uses)\n\n")
        fh.write("These are edited by whoever owns the module, alongside "
                 "the definitions.\n\n")
        for mod in sorted(tl_by_mod):
            owner = plan.get(mod, "")
            fh.write(f"**{mod}**{f' - {owner}' if owner else ''}\n\n")
            for rel, n in sorted(tl_by_mod[mod]):
                fh.write(f"- [ ] `{rel}` ({n} tags)\n")
            fh.write("\n")
        if not taglib:
            fh.write("_none found_\n")

        fh.write("\n## Configured vs discovered definition files\n\n")
        discovered = {relpath(f, root) for f in def_files}
        for c in sorted(configured):
            hit = [d for d in discovered if d.endswith(c.lstrip("/"))
                   or Path(d).name == Path(c).name]
            mark = "ok" if hit else "NOT FOUND on disk"
            fh.write(f"- `{c}` - {mark}\n")
        named = {Path(c).name for c in configured}
        for d in sorted(discovered):
            if named and Path(d).name not in named:
                fh.write(f"- `{d}` - on disk but not named in any config "
                         "(loaded by wildcard, or dead file)\n")
        if not configured:
            fh.write("_no definition paths found in config; "
                     "Tiles may be using its default location_\n")

    print(f"definitions      : {len(by_name)}")
    print(f"definition files : {len(def_files)}")
    print(f"phase 0 (shared) : {len(p0)}")
    print(f"modules          : {len(module_scores)}")
    print(f"config refs      : {len(set(r for r, _ in findings))} files")
    for o in owners:
        print(f"  {o:<12} load {loads[o]:.1f}")
    print(f"\nwrote {csv_path}\n      {md}\n      {risks}\n      {cfg}")


if __name__ == "__main__":
    main()
