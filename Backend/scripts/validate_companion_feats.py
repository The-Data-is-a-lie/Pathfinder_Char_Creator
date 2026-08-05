"""Gate the bonded-creature feat pool and the effect data that folds it into the stat block.

    C:\\Python310\\python.exe Backend/scripts/validate_companion_feats.py
    C:\\Python310\\python.exe Backend/scripts/validate_companion_feats.py --compendium PATH

Spec section 8, D14/D15. Two independent failure modes live here, and both are silent:

1. A NAME THAT DOES NOT RESOLVE. The pool in `animal_companion.json['feats']` is read by two
   vocabularies -- `data/feats.csv` (prerequisites and feat tax) and the pf1 compendium (the Foundry
   item the module clones). The pool used to hold `"armor proficiency (light, medium, and heavy)"`,
   which is not a feat in either, plus a dozen lowercase spellings. A miss does not raise; the module
   just builds a bare item and the creature quietly loses the feat's text. Foundry inverts the comma
   on the three armour proficiencies (`Light Armor Proficiency` / `Armor Proficiency, Light`), so the
   check tries that inversion exactly as the module does.

2. A CHANGE THAT NEVER LANDS. `companion_feat_changes.json` is the ONLY source of a companion's feat
   arithmetic -- `createCompanions.js` strips `system.changes`, so nothing downstream would notice a
   target that maps nowhere or a formula the mini-language cannot read. Every entry is therefore run
   against a probe stat block here, and a feat that claims a change but moves nothing fails.

It also holds the DOUBLE-APPLY TRIPWIRE that made `companion_feat_changes.json` a separate file in
the first place: the pf1 compendium already automates 12 of these feats, and a PC keeps its
compendium item's changes. A pool feat carrying numeric `changes` in BOTH that file and the shared
`feat_changes.json` therefore fails. Mere overlap does not -- three pool feats are text-only in the
shared file already, which is correct curation, and is reported as a note.

The compendium check degrades to a SKIP when the module is not installed (CI is ubuntu; the module
lives under %LOCALAPPDATA%), because a missing checkout is not a data defect.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

sys.path.insert(0, str(ROOT / "Backend"))
from _harness import Report                                        # noqa: E402
# One owner for the vocabulary: the fold declares what it accepts, this file only checks against it.
from utils import data                                             # noqa: E402
from utils.class_func.companion_stats import (                     # noqa: E402
    FormulaError, MODIFIER_TARGETS, SKILL_TARGET_PREFIX, apply_modifiers, eval_formula,
    feat_change_data)

CHASSIS = ROOT / "Backend/json/animal_companion.json"
FEATS_CSV = ROOT / "data/feats.csv"
SHARED_CHANGES = ROOT / "Backend/json/feats/feat_changes.json"
DEFAULT_COMPENDIUM = (Path.home() / "AppData" / "Local" / "FoundryVTT" / "Data" / "modules"
                      / "pf1e_random_char_generator" / "templates" / "character_sheet_folder"
                      / "every_feat.json")

errors = []
notes = []
REPORT = Report('validate_companion_feats', errors=errors)


def fail(message):
    REPORT.error(message)


def norm(text):
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def inversions(name):
    """Every comma inversion of `name`, the module's own match fallback.

    `Light Armor Proficiency` -> `Armor Proficiency, Light`, and back the other way for a name that
    already carries a comma. Both directions exist because the two vocabularies disagree in both
    directions: `data/feats.csv` writes the qualifier first, the pf1 compendium writes it last.
    """
    if "," in name:
        head, tail = name.split(",", 1)
        return [f"{tail.strip()} {head.strip()}"]
    words = name.split()
    return [f"{' '.join(words[cut:])}, {' '.join(words[:cut])}" for cut in range(1, len(words))]


def probe_stats():
    """A stat block with every field the fold can touch, so a no-op change is detectable."""
    return {
        "hp": 30, "ac": 16, "touch_ac": 12, "flat_footed_ac": 14, "natural_armor": 4,
        "saves": {"fort": 7, "ref": 7, "will": 2}, "initiative": 2, "cmb": 7, "cmd": 19,
        # Every movement mode, so a movement-gated skill bonus is not refused by the probe itself.
        "speed": "50 ft. , fly 60 ft. (good), swim 30 ft. , climb 20 ft. ",
        "attacks": [{"atk": 7}], "skills": {"perception": {"ranks": 6, "total": 10}},
    }


# Two spreads, because a conditional formula lands in only one of them: Weapon Finesse's
# `max(0, @dex - @str)` is CORRECTLY zero on a Strength-heavy body, so a single probe would report a
# working feat as dead. A change must move at least one of the two.
PROBE_SPREADS = (
    {"str": 3, "dex": 2, "con": 2, "int": -4, "wis": 1, "cha": -3},   # Strength-heavy (wolf)
    {"str": 0, "dex": 5, "con": 1, "int": -4, "wis": 1, "cha": -3},   # Dexterity-heavy (cat)
)
PROBE_HD = 6


def check_names(pool, compendium_path):
    csv_names = pd.read_csv(FEATS_CSV, sep="|", on_bad_lines="skip")["name"].dropna().astype(str)
    by_norm = {norm(name) for name in csv_names}
    for name in pool:
        if norm(name) not in by_norm:
            fail(f"{name!r} is not a feat in data/feats.csv; prerequisites and feat tax read that "
                 "file, so the pick can never be validated or taxed")

    if not compendium_path.exists():
        notes.append(f"compendium check SKIPPED -- {compendium_path} not present")
        return
    items = json.loads(compendium_path.read_text(encoding="utf-8"))
    compendium = {norm(item.get("name")) for item in items if isinstance(item, dict)}
    for name in pool:
        if norm(name) in compendium:
            continue
        if any(norm(alt) in compendium for alt in inversions(name)):
            continue
        fail(f"{name!r} has no pf1 compendium feat under that name or its comma inversion; the "
             "module would attach a bare item with no rules text")


def check_tax_children(pool, allowed, compendium_path):
    """The curated `tax_children` allowlist: every name real, reachable, and not permanently dead.

    "Reachable" matters because a name no pool feat's chain can produce is a line of data that will
    never fire, and nothing else would ever say so. "Not permanently dead" matters more: a child
    gated on a ki pool or a fighter level passes curation review by looking plausible, and then
    `legal_for_companion` refuses it on every creature that will ever be generated.
    """
    from utils.class_func import feat_tax as tax_module
    from utils.class_func.companion_feats import legal_for_companion

    table = pd.read_csv(FEATS_CSV, sep="|", on_bad_lines="skip")["name"].dropna().astype(str)
    csv_norm = {norm(name) for name in table}
    compendium = set()
    if compendium_path.exists():
        items = json.loads(compendium_path.read_text(encoding="utf-8"))
        compendium = {norm(item.get("name")) for item in items if isinstance(item, dict)}

    config = json.loads((ROOT / "Backend/json/feat_tax.json").read_text(encoding="utf-8"))
    explicit = {tax_module._norm(k): v for k, v in config.get("feat_tax", {}).items()}
    blocked = {tax_module._norm(x) for x in config.get("tax_primary_blocklist", [])}
    reachable = set()
    for primary in pool:
        key = tax_module._norm(primary)
        if key in explicit or tax_module._is_primary(key, explicit, blocked):
            reachable |= {norm(child) for child in tax_module._derive_chain(key, explicit)}

    # A body generous enough that only a PERMANENT refusal fails here: high scores, high BAB, and
    # every pool feat already owned so a feat-prerequisite is never the thing that blocks.
    generous = {"str": 25, "dex": 20, "con": 20, "int": 10, "wis": 16, "cha": 12}
    owned = set(pool) | set(allowed)

    for name in allowed:
        if norm(name) not in csv_norm:
            fail(f"tax_children: {name!r} is not a feat in data/feats.csv")
            continue
        if compendium and norm(name) not in compendium and not any(
                norm(alt) in compendium for alt in inversions(name)):
            fail(f"tax_children: {name!r} has no pf1 compendium feat under that name or its "
                 "comma inversion")
        if norm(name) not in reachable:
            fail(f"tax_children: {name!r} is on no pool feat's derived tax chain, so feat tax can "
                 "never grant it -- the entry is dead data")
        ok, reason = legal_for_companion(name, owned, generous, 20)
        if not ok:
            fail(f"tax_children: {name!r} can never be granted -- legal_for_companion refuses it "
                 f"even on a Str 25 / BAB +20 body owning every pool feat ({reason}). Curate it "
                 "out, or teach the reader that prerequisite.")


def check_coverage(pool, changes):
    missing = [name for name in pool if name not in changes]
    orphans = [name for name in changes if name not in pool]
    for name in missing:
        fail(f"{name!r} is in the feat pool but has no companion_feat_changes.json entry; a "
             "companion's feat arithmetic has no other source")
    for name in orphans:
        fail(f"{name!r} has companion_feat_changes.json data but is not in the feat pool")


def check_no_shared_entry(pool, changes, shared):
    """The double-apply tripwire, scoped to the hazard this work can actually create.

    Three pool feats (Improved Bull Rush, Improved Overrun, Mobility) legitimately predate this file
    in the shared `feat_changes.json`, where they are contextNotes-only and the compendium automates
    nothing -- correct curation, not a defect. Overlap alone is therefore reported, not failed.

    What DOES fail is the same feat carrying numeric `changes` in both files. That is the copy that
    stacks a bonus on the PC (compendium automation plus the shared entry) while the companion folds
    it a third time, and it is the mistake a future edit is most likely to make.
    """
    for name in pool:
        entry = shared.get(name) or shared.get(name.title()) or {}
        if not entry:
            continue
        if entry.get("changes") and (changes.get(name) or {}).get("changes"):
            fail(f"{name!r} carries numeric changes in BOTH feat_changes.json and "
                 "companion_feat_changes.json; a PC would take it from the compendium and the "
                 "shared file, and a companion from the companion file -- pick one owner")
        else:
            notes.append(f"{name!r} also has a shared feat_changes.json entry (text-only, allowed)")


def check_effects(changes):
    skill_ids = set(data.SKILL_IDS.values())
    for name, effect in changes.items():
        declared = effect.get("changes") or []
        for change in declared:
            target = str(change.get("target") or "")
            if target.startswith(SKILL_TARGET_PREFIX):
                if target[len(SKILL_TARGET_PREFIX):] not in skill_ids:
                    fail(f"{name}: {target!r} is not a pf1 skill id (data.SKILL_IDS)")
            elif target not in MODIFIER_TARGETS:
                fail(f"{name}: change target {target!r} is not one apply_modifiers can place; "
                     f"known targets are {sorted(MODIFIER_TARGETS)} plus {SKILL_TARGET_PREFIX}<id>")
            for spread in PROBE_SPREADS:
                try:
                    eval_formula(change.get("formula"), dict(spread, hd=PROBE_HD))
                except FormulaError as error:
                    fail(f"{name}: {error}")
                    break

        if not declared and not (effect.get("contextNotes") or effect.get("unapplied")):
            fail(f"{name}: no changes, no contextNotes and no unapplied note -- an entry that says "
                 "nothing should not exist")

        # End to end: a declared change must actually move the probe block under at least one spread.
        landed = False
        for spread in PROBE_SPREADS:
            before, after = probe_stats(), probe_stats()
            apply_modifiers(after, [(name, effect)], spread, PROBE_HD)
            if any(before[key] != after[key] for key in before) or after.get("unapplied"):
                landed = True
                break
        if declared and not landed:
            fail(f"{name}: declares {len(declared)} change(s) but moved nothing in either probe "
                 "stat block and reported no holdback")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--compendium", type=Path, default=DEFAULT_COMPENDIUM,
                        help="the module's every_feat.json (skipped when absent)")
    args = parser.parse_args()

    chassis = json.loads(CHASSIS.read_text(encoding="utf-8"))
    pool = chassis.get("feats") or []
    allowed = chassis.get("tax_children") or []
    changes = feat_change_data()
    shared = json.loads(SHARED_CHANGES.read_text(encoding="utf-8"))

    if not pool:
        fail("animal_companion.json carries no 'feats' pool at all")
    if not allowed:
        fail("animal_companion.json carries no 'tax_children' allowlist; without it feat tax hands "
             "a wolf Drunken Brawler and Wand Dancer")
    for label, names in (("feat pool", pool), ("tax_children", allowed)):
        if len(names) != len(set(names)):
            duplicates = sorted({name for name in names if names.count(name) > 1})
            fail(f"duplicate entries in the {label}: {duplicates}")
        if names != sorted(names):
            fail(f"the {label} is not sorted; keep it alphabetical so a diff is readable")

    check_names(pool, args.compendium)
    check_tax_children(pool, allowed, args.compendium)
    check_coverage(pool, changes)
    check_no_shared_entry(pool, changes, shared)
    check_effects(changes)

    folded = sum(1 for effect in changes.values() if effect.get("changes"))
    for note in notes:
        print(f"  note: {note}")
    return REPORT.finish(
        f"{len(pool)} feats in the pool, {folded} with folded arithmetic, "
        f"{len(changes) - folded} text-only; {len(allowed)} tax children allowed "
        f"-- every pool name resolves and every declared effect lands",
        max_errors=25)


if __name__ == "__main__":
    sys.exit(main())
