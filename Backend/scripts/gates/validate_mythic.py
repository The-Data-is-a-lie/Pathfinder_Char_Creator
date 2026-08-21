"""Gate the mythic config: the schedule, the data files, the call sites, and the payload key.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_mythic.py

Mythic map, ticket 07 -- the CONFIG half. Its sibling is `check_mythic` (plus the per-character
leak tripwire) in `tests/test_house_invariants.py`, which generates forced-mythic characters and
asserts what they received. The split is the class-choices split, for the class-choices reason:

    tests/  catches the CHOOSER drifting from the schedule -- it generates characters.
    gates/  catches the CONFIG drifting -- a path with no pool, a schedule row with no call site,
            a curation flag nothing reads, a payload key the renderers cannot see. Milliseconds.

**This file re-reads every JSON from disk and never imports `levels_for` or `mythic.py`'s
loaders.** A table can never be its own witness -- the self-comparison trap, named by
scripts-ticket 12 and proven by the class-choices map (perturbing the table passed its own
behaviour check, because the generator read the same file).

The mythic table is a PARALLEL AXIS file (ticket 03): keyed by tier, same schema, deliberately
outside class_choice_schedule.json so the 68-class roster gates never see it. This gate is the
sweep that ruling promised the table would get.
"""
import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _harness import REPO, Report                                       # noqa: E402

SCHEDULE_PATH = REPO / "Backend/json/mythic_schedule.json"
ABILITIES_PATH = REPO / "Backend/json/mythic_path_abilities.json"
TRADITIONS_PATH = REPO / "Backend/json/mythic_traditions.json"
MASTERIES_PATH = REPO / "Backend/json/mythic_sphere_masteries.json"
MYTHIC_PY = REPO / "Backend/utils/class_func/mythic.py"
MAIN = REPO / "Backend/main_test.py"
PAYLOAD_PY = REPO / "Backend/utils/payload.py"
FEATS_CSV = REPO / "data/feats.csv"

PATHS = ('archmage', 'champion', 'guardian', 'hierophant', 'marshal', 'trickster')
ABILITY_TIERS = {1, 3, 6}
SOURCES = {'raw', 'approximation', 'unverified', 'bug'}

REPORT = Report('validate_mythic')


def load(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def check_schedule(schedule):
    """The table speaks exactly the class-schedule schema, under the single 'mythic' key."""
    classes = schedule.get('classes', {})
    REPORT.check(set(classes) == {'mythic'},
                 f"mythic_schedule.json classes are {sorted(classes)}, expected exactly "
                 f"['mythic'] -- a second key would be a new axis nobody ruled on")
    buckets = (classes.get('mythic') or {}).get('buckets', {})
    for name, row in buckets.items():
        compact = 'start' in row or 'every' in row
        listed = 'levels' in row
        REPORT.check(compact != listed,
                     f"schedule bucket {name!r} must declare EITHER {{start, every}} OR "
                     f"{{levels}}, not {'both' if compact and listed else 'neither'}")
        if compact:
            REPORT.check(isinstance(row.get('start'), int) and isinstance(row.get('every'), int),
                         f"schedule bucket {name!r} has a non-integer start/every")
        REPORT.check(row.get('source') in SOURCES,
                     f"schedule bucket {name!r} source={row.get('source')!r} is not in "
                     f"{sorted(SOURCES)}")
    return set(buckets)


def check_ability_pools(data):
    """Six paths, each whole: chassis meta, tier-gated abilities, the universal merge, and
    curation flags that are load-bearing strings."""
    paths = data.get('paths', {})
    REPORT.check(set(paths) == set(PATHS),
                 f"mythic_path_abilities.json paths are {sorted(paths)}, expected {sorted(PATHS)}")
    universal_sets = {}
    for name, meta in paths.items():
        REPORT.check(isinstance(meta.get('bonus_hp_per_tier'), int)
                     and 3 <= meta['bonus_hp_per_tier'] <= 5,
                     f"{name}: bonus_hp_per_tier={meta.get('bonus_hp_per_tier')!r}, RAW paths "
                     f"grant 3-5")
        feature = meta.get('tier1_feature') or {}
        REPORT.check(len(feature.get('options') or {}) >= 2,
                     f"{name}: tier-1 feature has {len(feature.get('options') or {})} options -- "
                     f"the sub-choice the chooser picks from is missing")
        REPORT.check(bool(meta.get('capstone')),
                     f"{name}: no 10th-tier capstone parsed")
        abilities = meta.get('abilities') or {}
        REPORT.check(len(abilities) >= 60,
                     f"{name}: only {len(abilities)} abilities -- the pool shrank below any "
                     f"plausible re-scrape (own ~50 + universal ~40)")
        for ability_name, entry in abilities.items():
            REPORT.check(entry.get('tier') in ABILITY_TIERS,
                         f"{name}/{ability_name}: tier={entry.get('tier')!r} not in 1/3/6")
            REPORT.check(bool(str(entry.get('description') or '').strip()),
                         f"{name}/{ability_name}: empty description -- it would render as a bare "
                         f"name")
            if 'flag' in entry:
                REPORT.check(bool(str(entry['flag']).strip()),
                             f"{name}/{ability_name}: empty curation flag -- the reason IS the "
                             f"record")
        universal_sets[name] = {a for a, e in abilities.items() if e.get('universal')}
    # The universal merge happened, identically, in every path -- a pool that lost its universal
    # half is the 27-unpickable-aspects failure wearing a new name.
    sets = list(universal_sets.values())
    REPORT.check(all(s == sets[0] for s in sets) and len(sets[0]) >= 30,
                 f"universal merge drifted: sizes {sorted(len(s) for s in sets)} -- every path "
                 f"must carry the same universal list")


def check_traditions(data):
    """Sections present and the machine-readable overrides still resolve -- every one is
    load-bearing in the chooser."""
    for section, floor in (('drawbacks', 15), ('qualities', 10), ('boons', 7)):
        entries = data.get(section) or {}
        REPORT.check(len(entries) >= floor,
                     f"mythic_traditions.{section}: {len(entries)} entries < {floor} -- the "
                     f"scrape lost content")
        for name, entry in entries.items():
            REPORT.check(bool(str(entry.get('description') or '').strip()),
                         f"traditions {section}/{name}: empty description")
    boons = data.get('boons') or {}
    expertise = boons.get('Expertise') or {}
    REPORT.check(expertise.get('auto') == 'missed_class_feature' and expertise.get('house_rule'),
                 "Expertise must carry auto='missed_class_feature' AND the house_rule note -- the "
                 "text stays RAW, the chooser implements the Sieg inversion, and this field pair "
                 "is what keeps that visible")
    gear = boons.get('Legendary Gear') or {}
    REPORT.check(gear.get('flag') and gear.get('cost') == 2,
                 "Legendary Gear must be flagged (artifact machinery) with cost 2")
    sealed = (data.get('drawbacks') or {}).get('Sealed') or {}
    REPORT.check(sealed.get('counts_as') == 2,
                 "Sealed must carry counts_as=2 -- RAW says it counts as two drawbacks")


def check_masteries(data):
    masteries = data.get('masteries') or {}
    REPORT.check(len(masteries) >= 55,
                 f"mythic_sphere_masteries: {len(masteries)} spheres < 55 -- the scrape lost "
                 f"content")
    for name, entry in masteries.items():
        REPORT.check(entry.get('tier') in ABILITY_TIERS,
                     f"mastery {name}: tier={entry.get('tier')!r} not in 1/3/6")


def _mythic_levels_for_calls(path):
    """(bucket, has_schedule_attr) for every levels_for call in `path` that names the mythic
    table. ast, not regex -- the bucket is a positional or keyword string and a regex would miss
    the day someone reformats the call."""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, 'id', None) or getattr(func, 'attr', None)
        if name != 'levels_for':
            continue
        kwargs = {k.arg: k.value for k in node.keywords}
        attr = kwargs.get('schedule_attr')
        if not (isinstance(attr, ast.Constant) and attr.value == 'mythic_schedule'):
            continue
        args = node.args
        bucket = None
        if len(args) >= 3 and isinstance(args[2], ast.Constant):
            bucket = args[2].value
        elif 'bucket' in kwargs and isinstance(kwargs['bucket'], ast.Constant):
            bucket = kwargs['bucket'].value
        calls.append(bucket)
    return calls


def check_call_sites(schedule_buckets):
    """Every schedule row has a call site and every call site has a row -- in both directions,
    because an orphan on either side is a silent nothing."""
    called = []
    for source in (MYTHIC_PY, MAIN):
        called.extend(_mythic_levels_for_calls(source))
    REPORT.check(None not in called,
                 "a mythic levels_for call passes a non-literal bucket -- the gate cannot check "
                 "what it cannot read; use a string literal")
    called_set = {c for c in called if c}
    REPORT.check(called_set == schedule_buckets,
                 f"schedule buckets {sorted(schedule_buckets)} != mythic levels_for call sites "
                 f"{sorted(called_set)} -- an orphan row grants nothing, an orphan call reads "
                 f"nothing")


def check_payload_key():
    """'mythic' is in PAYLOAD_KEYS and the export actually splices a block under it."""
    payload_src = PAYLOAD_PY.read_text(encoding='utf-8')
    REPORT.check(re.search(r"^\t'mythic',", payload_src, re.M) is not None,
                 "payload.py PAYLOAD_KEYS has no 'mythic' entry -- validate_payload_shape would "
                 "fail next, but this says WHY")
    main_src = MAIN.read_text(encoding='utf-8')
    REPORT.check('"mythic": _mythic_block' in main_src,
                 "main_test.py never splices the mythic block into the payload -- generated but "
                 "invisible, the failure this stack keeps rediscovering")


def check_feat_exclusions():
    """The chooser's V1 exclusions name real Mythic rows -- a renamed row would silently turn a
    ruling into a no-op. String-level read of the CSV: 158 rows, pipe-delimited."""
    src = MYTHIC_PY.read_text(encoding='utf-8')
    excluded = re.findall(r"^\s+'([a-z][^']*)':\s+\"",
                          src[src.find('V1_EXCLUDED_MYTHIC_FEATS'):src.find('def mythic_feat_rows')],
                          re.M)
    REPORT.check(len(excluded) >= 2,
                 f"V1_EXCLUDED_MYTHIC_FEATS parse found {excluded} -- the gate lost sight of the "
                 f"exclusion dict")
    mythic_rows = set()
    with open(FEATS_CSV, encoding='utf-8', errors='replace') as fh:
        header = fh.readline().split('|')
        name_i, type_i = header.index('name'), header.index('type')
        for line in fh:
            parts = line.split('|')
            if len(parts) > type_i and parts[type_i] == 'Mythic':
                mythic_rows.add(parts[name_i].strip().lower())
    REPORT.check(len(mythic_rows) >= 150,
                 f"data/feats.csv holds {len(mythic_rows)} Mythic rows, expected ~158")
    for name in excluded:
        REPORT.check(name in mythic_rows,
                     f"excluded feat {name!r} is not a Mythic row in data/feats.csv -- the "
                     f"exclusion no longer excludes anything")


def main():
    schedule_buckets = check_schedule(load(SCHEDULE_PATH))
    check_ability_pools(load(ABILITIES_PATH))
    check_traditions(load(TRADITIONS_PATH))
    check_masteries(load(MASTERIES_PATH))
    # The path-choice single-pick row is read through levels_for too; mythic_feats is read in
    # main_test's phase. Both directions asserted:
    check_call_sites(schedule_buckets)
    check_payload_key()
    check_feat_exclusions()
    return REPORT.finish(f'{REPORT.checks} checks')


if __name__ == '__main__':
    sys.exit(main())
