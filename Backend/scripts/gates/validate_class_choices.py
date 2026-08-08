"""Gate the class-choice schedule against the pool, the buckets and the call sites.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_class_choices.py

Class-choices map, ticket 05 -- the CONFIG half. Its sibling is the behaviour half, the
`check_class_choices` block in `tests/test_house_invariants.py`, which asserts generated characters
against the same table. The split is the point, and it is not arbitrary:

    tests/  catches the CHOOSER drifting from the schedule -- it generates characters.
    gates/  catches the CONFIG drifting -- a class with no row, a row with no chooser, a chooser
            with no row, a verdict with no reason. It generates nothing and runs in milliseconds.

**This file re-reads the JSON from disk and never imports `generic_func.levels_for`.** A gate that
derived the schedule from the generator's own accessor would compare the data with itself and
confirm nothing -- the self-comparison trap scripts-ticket 12 named. The behaviour check makes the
same choice for the same reason, expanding the table a second time in `_harness`.

WHAT NO GATE CAN DO is re-derive the `source` field: whether a hand-authored number matches Sieg's
Guide is a one-time human judgment. That is why it is a field rather than an assumption, and why
this gate checks only that every row HAS one from the vocabulary.

The most valuable assertion here is the cheapest: a class that joins the rollable pool without a
schedule row fails immediately, so onboarding cannot skip the class-choices map.
"""
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from _harness import REPO, Report                                       # noqa: E402
from validate_class_roster import expected_roster                       # noqa: E402
from validate_class_roster import _data                                 # noqa: E402

SCHEDULE_PATH = REPO / "Backend/json/class_choice_schedule.json"
MAIN = REPO / "Backend/main_test.py"
INVARIANTS = REPO / "Backend/scripts/tests/test_house_invariants.py"
CLASS_DATA_DIR = REPO / "Backend/json/class_data"

sys.path.insert(0, str(REPO / "Backend"))
from utils.class_func.chooseable import ARCHETYPE_PREREQ_COLLISIONS   # noqa: E402

PREREQ_KEYS = ("prerequisites", "prerequisite", "prereq")


def _walk_options(node):
    """Every (name, option) in a pool file, at whatever depth the pool nests it."""
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        if isinstance(value, dict):
            if {k.lower() for k in value} & set(PREREQ_KEYS):
                yield key, value
            else:
                yield from _walk_options(value)


# RAW's base Animal Focus list -- the aspects a hunter with no archetype may take. Everything else
# in the pool is archetype-gated and reached through the prerequisite engine.
HUNTER_BASE_ASPECTS = {"bat", "bear", "bull", "falcon", "frog", "monkey", "mouse", "owl", "snake",
                       "stag", "tiger", "wolf"}

# Options whose name matches one of their own class's feature keys, which makes them unpickable
# (see check 5d). All four are ONE option in a large pool, and all four are plausibly benign: the
# option duplicates a feature the class already has, so skipping it is arguably correct -- every
# alchemist has `mutagen`, so a discovery of that name is redundant. Recorded rather than fixed,
# because "fixing" means editing authored game data on a reading nobody has checked.
#
# The pathological case this check exists for is different in kind: the shifter's 27 aspects lived
# in BOTH places, so its entire pool was unpickable and the chooser returned nothing with no error.
# A whole pool must never be baselined -- move it out of class_data.json instead.
SHADOWED_BASELINE = {
    ("alchemist", "mutagen"),
    ("fighter", "weapon mastery"),
    ("ninja", "ki pool"),
    ("slayer", "swift tracker"),
}

REASONS = {"none-by-design", "other-subsystem", "other-effort", "aliased", "gap"}
SOURCES = {"raw", "approximation", "unverified", "bug"}

# Ticket 03: every path by which one class can satisfy another's prerequisite runs between classes
# that interoperate in RAW, measured two ways. These three are the whole set -- a fourth appearing
# means a re-scrape introduced a cross-class dependency nobody ruled on, which is a finding rather
# than a pass.
FOREIGN_CLASS_REFS = {("ninja", "rogue"), ("slayer", "rogue"), ("skald", "barbarian")}

# Buckets the behaviour check cannot attribute, each a known ticket-04 defect. Kept in sync here so
# that fixing the defect FORCES the skip to be deleted: a skip that outlives its cause is a hole.
EXPECTED_SKIPS = {
    ("oracle", "mysteries"),
    ("sorcerer", "Talents"), ("bloodrager", "Talents"), ("cavalier", "Talents"),
    ("samurai", "Talents"), ("warpriest", "Talents"), ("inquisitor", "Talents"),
}

REPORT = Report("validate_class_choices")


def check(cond, msg):
    return REPORT.check(cond, msg)


def call_sites(src):
    """{(class, bucket)} for every class-choice chooser call in main_test.py.

    Parsed with `ast` rather than a regex: the call sites carry six optional keyword arguments in
    varying order, and the bucket is `dict_name` when present and the chooser's own default when
    not -- a default that differs per chooser. A regex that got that wrong would produce a gate
    which passes by failing to see things.
    """
    found = set()
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        fn = node.func.id
        kw = {k.arg: k.value for k in node.keywords if k.arg}

        def const(x):
            return x.value if isinstance(x, ast.Constant) and isinstance(x.value, str) else None

        pos = [const(a) for a in node.args[1:]]      # drop `character`
        if fn in ("generic_class_option_chooser", "get_data_without_prerequisites"):
            cls = pos[0] if pos else const(kw.get("class_1"))
            if not cls:
                continue
            # dict_name defaults to "Talents" on the option chooser; the prereq chooser always
            # passes one explicitly, and a missing one there is itself worth failing on.
            bucket = const(kw.get("dict_name"))
            if bucket is None:
                bucket = "Talents" if fn == "generic_class_option_chooser" else None
            if bucket:
                found.add((cls, bucket))
        elif fn == "generic_multi_chooser":
            cls = pos[0] if pos else const(kw.get("class_1"))
            dataset = pos[1] if len(pos) > 1 else const(kw.get("dataset_name"))
            if cls and dataset:
                found.add((cls, dataset))          # this chooser buckets by dataset name
        elif fn == "simple_list_chooser":
            cls = pos[0] if pos else None
            for dataset in pos[1:]:
                if cls and dataset:
                    found.add((cls.lower(), dataset))
    # choose_gun_func is not a generic chooser -- it is the fifth convention, with its class and
    # bucket both hardcoded inside gunslinger.py. Named here so the table's row is not orphaned.
    if "choose_gun_func(" in src:
        found.add(("gunslinger", "gun training"))
    return found


def main():
    doc = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    table = doc.get("classes") or {}
    pool, _groups = expected_roster()

    # ---- 1. the roster and the table are the same set -------------------------------------
    missing = sorted(pool - set(table))
    extra = sorted(set(table) - pool)
    check(not missing,
          f"rollable classes with NO schedule row: {missing} -- a class joined the pool without "
          f"passing through the class-choices map, so nobody decided what it picks")
    check(not extra,
          f"schedule rows for classes that are not rollable: {extra} -- either the holdback lists "
          f"moved or the row is dead")

    # ---- 2. every row is well formed -------------------------------------------------------
    for name in sorted(set(table) & pool):
        row = table[name]
        buckets = row.get("buckets") or {}
        if not buckets:
            reason = row.get("reason")
            check(reason in REASONS,
                  f"{name}: empty row carries reason {reason!r}, not one of {sorted(REASONS)}")
            check(bool((row.get("note") or "").strip()),
                  f"{name}: empty row has reason {reason!r} but no note -- the verdict is the "
                  f"reason PLUS why, or the next sweep re-derives it")
            check("reason" not in row or row.get("buckets") is not None,
                  f"{name}: row has neither buckets nor a buckets key")
            continue
        check("reason" not in row,
              f"{name}: row has buckets AND a reason {row.get('reason')!r} -- the buckets are the "
              f"verdict, so the reason is stale")
        for bucket, spec in buckets.items():
            tag = f"{name}.{bucket}"
            compact = "start" in spec and "every" in spec
            explicit = "levels" in spec
            check(compact ^ explicit,
                  f"{tag}: declares {'both' if compact and explicit else 'neither'} a compact "
                  f"{{start, every}} rule nor an explicit {{levels}} list -- exactly one")
            check(spec.get("source") in SOURCES,
                  f"{tag}: source {spec.get('source')!r} not one of {sorted(SOURCES)}")
            if explicit:
                lv = spec["levels"]
                check(isinstance(lv, list) and lv and all(isinstance(x, int) for x in lv),
                      f"{tag}: levels must be a non-empty list of ints, got {lv!r}")
                check(lv == sorted(lv),
                      f"{tag}: levels {lv} are not ascending -- the k-th pick's stamp is "
                      f"levels[k-1], so an unsorted list mis-dates every pick")
                check(not (spec.get("repeat") and spec.get("then_every")),
                      f"{tag}: declares both `repeat` and `then_every`; they are alternatives")
            else:
                check(spec.get("every", 0) > 0, f"{tag}: `every` must be positive")
                check(spec.get("start", 0) > 0, f"{tag}: `start` must be positive")
            check(spec.get("bucket", bucket) == bucket,
                  f"{tag}: row's `bucket` field says {spec.get('bucket')!r} but it is keyed "
                  f"{bucket!r}")

    # ---- 3. call sites and rows agree, both ways -------------------------------------------
    sites = call_sites(MAIN.read_text(encoding="utf-8"))
    declared = {(n, b) for n, r in table.items() for b in (r.get("buckets") or {})}

    for cls, bucket in sorted(sites):
        # An unchained variant picks through its base row on purpose (ticket 02, `aliased`), and
        # the call sites name the base class, so a site is satisfied by the base class's row.
        if (cls, bucket) in declared:
            continue
        check(False,
              f"chooser call site {cls!r} -> bucket {bucket!r} has NO schedule row. Its count and "
              f"level stamp are therefore whatever the chooser falls back to, which is the state "
              f"ticket 01 existed to remove")

    for cls, bucket in sorted(declared):
        check((cls, bucket) in sites,
              f"schedule row {cls}.{bucket} has no chooser call site in main_test.py -- either the "
              f"call was deleted and the row is dead, or the bucket was renamed and the picks are "
              f"now landing somewhere the table does not describe")

    # ---- 4. the datasets a row names actually exist ----------------------------------------
    for cls, bucket in sorted(declared):
        spec = table[cls]["buckets"][bucket]
        dataset = spec.get("dataset")
        if not dataset:
            continue
        # A pool lives in ONE of two places, and which one depends on the chooser: the generic
        # choosers read class_data/<class>.json, while simple_list_chooser does
        # getattr(data, dataset_name) against data.py. Resolving in either is enough -- an earlier
        # version of this check knew only about the first and failed the ranger's two rows, which
        # is the gate correctly refusing to pass something it did not understand.
        if hasattr(_data, dataset):
            continue
        path = CLASS_DATA_DIR / f"{cls}.json"
        if not path.exists():
            continue                    # the gunslinger's firearms pool is built, not authored
        keys = json.loads(path.read_text(encoding="utf-8"))
        check(dataset in keys,
              f"{cls}.{bucket}: dataset {dataset!r} is neither an attribute of data.py nor a key "
              f"of class_data/{cls}.json (has {sorted(keys)[:6]}...) -- the chooser would draw "
              f"from an empty pool")

    # ---- 5. ticket 03's measured bounds stay measured --------------------------------------
    foreign = set()
    level_ref = re.compile(r"\b(" + "|".join(sorted((re.escape(c) for c in pool), key=len,
                                                    reverse=True)) + r")\b\s*\d+", re.I)
    for path in sorted(CLASS_DATA_DIR.glob("*.json")):
        if path.stem not in pool:
            continue
        try:
            blob = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for other in {m.group(1).lower() for m in level_ref.finditer(blob)}:
            if other != path.stem.lower() and other in pool:
                foreign.add((path.stem.lower(), other))
    check(foreign <= FOREIGN_CLASS_REFS,
          f"a pool's prerequisites now name a class outside the measured interop set: "
          f"{sorted(foreign - FOREIGN_CLASS_REFS)}. Ticket 03 ruled `chooseable` may stay shared "
          f"BECAUSE every cross-class path runs between classes that interoperate in RAW; a new "
          f"pair means that ruling needs re-taking, not that this line needs relaxing")

    # ---- 5b. the archetype-name collision baseline is still the truth -----------------------
    # chooseable.py seeds rolled archetype names so archetype-gated options can meet their
    # prerequisites, EXCEPT names that are also the name of a selectable option -- 'brawler' is
    # both an archetype and a rage power, and a prereq string cannot say which it meant. That
    # exclusion list is a constant there (computing it means reading ~73 pool files, and it runs
    # inside every generation), so the real intersection is computed HERE and the constant is
    # checked against it. A new same-named archetype is then a failure rather than a silent unlock.
    arch = json.loads((REPO / "Backend/json/archetypes.json").read_text(encoding="utf-8"))
    arch_names = {k.lower().strip() for v in arch.values() if isinstance(v, dict) for k in v}
    option_names = set()
    for path in sorted(CLASS_DATA_DIR.rglob("*.json")):
        try:
            option_names |= {n.lower().strip() for n, _ in _walk_options(
                json.loads(path.read_text(encoding="utf-8")))}
        except (OSError, ValueError):
            continue
    collisions = arch_names & option_names
    check(collisions == set(ARCHETYPE_PREREQ_COLLISIONS),
          f"ARCHETYPE_PREREQ_COLLISIONS in chooseable.py is stale. Newly colliding: "
          f"{sorted(collisions - set(ARCHETYPE_PREREQ_COLLISIONS))}; no longer colliding: "
          f"{sorted(set(ARCHETYPE_PREREQ_COLLISIONS) - collisions)}. A name in both sets cannot be "
          f"told apart from the option in a prereq string, so seeding it would unlock options the "
          f"character has not earned")

    # ---- 5c. the hunter's base Animal Focus list is exactly RAW's twelve --------------------
    # Pinned because this pool arrived DAMAGED: one aspect's name cell was empty in the scrape, so
    # the prereq-free list read as 11 with a blank twelfth. Filtering blanks would have silently
    # dropped Snake; ticket 02 repaired the key instead. A re-scrape that loses a name again would
    # otherwise reintroduce exactly that, and the symptom is a blank pick on a sheet.
    hunter = CLASS_DATA_DIR / "hunter.json"
    if hunter.exists():
        aspects = json.loads(hunter.read_text(encoding="utf-8")).get("aspects") or {}
        base = {n for n, opt in aspects.items() if not (opt.get("prerequisites") or "").strip()}
        check(base == HUNTER_BASE_ASPECTS,
              f"the hunter's prereq-free aspects are {sorted(base)}, not RAW's twelve. Missing: "
              f"{sorted(HUNTER_BASE_ASPECTS - base)}; unexpected: {sorted(base - HUNTER_BASE_ASPECTS)}"
              f" -- a blank or renamed key here reaches a sheet as a nameless pick")
        blank = sorted(n for n in aspects if not n.strip())
        check(not blank,
              f"hunter aspects contain {len(blank)} blank key(s) -- a blank name is selectable and "
              f"renders as an empty row")

    # ---- 5d. an option pool may not ALSO be class_data.json feature keys --------------------
    # chooseable_list_class_features seeds every class_data.json feature key into
    # character.chooseable, and no_prereq_loop SKIPS any option already there. So an option that is
    # also a feature key is silently unselectable -- the shifter's 27 aspects lived in both places
    # and the chooser returned nothing at all, with no error. Extraction has to MOVE a pool, not
    # copy it, and this is what says so.
    class_data = json.loads((REPO / "Backend/json/class_data.json").read_text(encoding="utf-8"))
    shadowed_seen = set()
    for cls, bucket in sorted(declared):
        spec = table[cls]["buckets"][bucket]
        path = CLASS_DATA_DIR / f"{cls}.json"
        if not path.exists():
            continue
        options = json.loads(path.read_text(encoding="utf-8")).get(spec.get("dataset")) or {}
        if not isinstance(options, dict):
            continue
        shadowed = sorted(set(options) & set(class_data.get(cls) or {}))
        shadowed_seen |= {(cls, name) for name in shadowed}
        unexpected = [n for n in shadowed if (cls, n) not in SHADOWED_BASELINE]
        check(not unexpected,
              f"{cls}.{bucket}: {len(unexpected)} option(s) are ALSO feature keys in class_data.json "
              f"({unexpected[:5]}) -- chooseable_list_class_features seeds those, and no_prereq_loop "
              f"skips anything already in chooseable, so they can never be picked. Move the pool out "
              f"of class_data.json rather than adding it to SHADOWED_BASELINE")
    # Aggregated across every bucket, not per bucket: the fighter's `weapon mastery` shadows in
    # weapon_training and not in armor_training, so a per-bucket staleness test calls it stale while
    # looking at the other bucket.
    stale = sorted(SHADOWED_BASELINE - shadowed_seen)
    check(not stale,
          f"SHADOWED_BASELINE lists {stale}, which no longer shadow anything -- delete the entry so "
          f"the baseline keeps meaning what it says")

    # ---- 6. the behaviour check's skip list matches its stated cause ------------------------
    inv = INVARIANTS.read_text(encoding="utf-8")
    for cls, bucket in sorted(EXPECTED_SKIPS):
        check(f"('{cls}', '{bucket}')" in inv,
              f"CHOICE_SKIP in test_house_invariants.py no longer skips {cls}.{bucket} -- if the "
              f"ticket-04 defect behind it is fixed, delete it from EXPECTED_SKIPS here too")

    print(f"  {len(pool)} rollable classes, {len(declared)} bucket rows, {len(sites)} call sites, "
          f"{sum(1 for r in table.values() if not r.get('buckets'))} verdicts")
    return REPORT.finish(f"{REPORT.checks} checks")


if __name__ == "__main__":
    sys.exit(main())
