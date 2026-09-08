"""Gate the bonded-creature feat pool and the effect data that folds it into the stat block.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_companion_feats.py
    C:\\Python310\\python.exe Backend/scripts/gates/validate_companion_feats.py --compendium PATH

Spec section 8, D14/D15. Two independent failure modes live here, and both are silent:

1. A NAME THAT DOES NOT RESOLVE. The pool is read by two vocabularies -- `data/feats.csv`
   (prerequisites and feat tax) and the MODULE'S OWN feat catalog, `every_feat.json`, which is the
   `pf1e_random_char_generator.feats` pack and the row a companion's item is built from. The pool
   used to hold `"armor proficiency (light, medium, and heavy)"`, which is not a feat in either,
   plus a dozen lowercase spellings. A miss does not raise; the module just builds a bare item and
   the creature quietly loses the feat's text. Foundry inverts the comma on the three armour
   proficiencies (`Light Armor Proficiency` / `Armor Proficiency, Light`), so the check tries that
   inversion exactly as the module does.

   IT MATCHES THE WAY `build/catalog.js` MATCHES, not the way this file's `norm()` does, and that
   difference is ticket 07's residue. `norm()` strips every non-alphanumeric character, so
   `"Potent HolySymbol"` and `"Potent Holy Symbol"` are one string to it -- four pool names passed
   this gate while rendering bare on a real sheet. The renderer lowercases, cuts at the first
   `" ("`, and compares. Nothing more. So does this now.

2. A CHANGE THAT NEVER LANDS. `companion_feat_changes.json` is the ONLY source of a companion's feat
   arithmetic -- `createCompanions.js` strips `system.changes`, so nothing downstream would notice a
   target that maps nowhere or a formula the mini-language cannot read. Every entry is therefore run
   against a probe stat block here, and a feat that claims a change but moves nothing fails.

It also holds the DOUBLE-APPLY TRIPWIRE that made `companion_feat_changes.json` a separate file in
the first place: the catalog already automates 12 of these feats, and a PC keeps its
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

sys.path.insert(0, str(HERE.parent))
from _harness import REPO, Report                                        # noqa: E402

ROOT = REPO
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


def catalog_index(path):
    """`{base key: row}` over the module's `every_feat.json`, built the way `build/catalog.js` does.

    Its rule and nothing looser: lowercase, cut at the first `" ("`, skip `(Mythic)` rows, and the
    LOWEST source position wins where a key has more than one candidate -- 445 feat keys do, and a
    plain `Skill Focus` has 39. A gate that normalises harder than the renderer keeps passing names
    the renderer cannot find, which is exactly what this one did until ticket 07.
    """
    index = {}
    for row in json.loads(path.read_text(encoding="utf-8")):
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if not isinstance(name, str) or "(Mythic)" in name:
            continue
        index.setdefault(name.split(" (")[0].lower(), row)
    return index


def catalog_row(index, name):
    """The row the module would resolve `name` to, trying the comma inversion as it does."""
    for candidate in [name, *inversions(name)]:
        row = index.get(str(candidate).split(" (")[0].lower())
        if row is not None:
            return row
    return None


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
    # Through the module's own reader, not pandas: `on_bad_lines="skip"` drops the five
    # disjunction rows, and a gate that cannot see a row cannot gate it.
    from utils.class_func.companion_feats import _feat_rows
    by_norm = set(_feat_rows())
    for name in pool:
        if norm(name) not in by_norm:
            fail(f"{name!r} is not a feat in data/feats.csv; prerequisites and feat tax read that "
                 "file, so the pick can never be validated or taxed")

    if not compendium_path.exists():
        notes.append(f"catalog check SKIPPED -- {compendium_path} not present")
        return
    index = catalog_index(compendium_path)
    for name in pool:
        row = catalog_row(index, name)
        if row is None:
            fail(f"{name!r} has no every_feat.json row under that name or its comma inversion; the "
                 "module would attach a bare item with no rules text")
        elif not str(((row.get("system") or {}).get("description") or {}).get("value") or "").strip():
            fail(f"{name!r} resolves to an every_feat.json row whose description is EMPTY; the item "
                 "would carry a name and nothing else, which is a miss by another route")


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
    index = catalog_index(compendium_path) if compendium_path.exists() else None

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
        # A child is not an item of its own, but `featItems` appends its rules text under the
        # parent that paid for it -- so a child the catalog cannot find is a bundled name and
        # nothing else.
        if index is not None and catalog_row(index, name) is None:
            fail(f"tax_children: {name!r} has no every_feat.json row under that name or its "
                 "comma inversion")
        if norm(name) not in reachable:
            fail(f"tax_children: {name!r} is on no pool feat's derived tax chain, so feat tax can "
                 "never grant it -- the entry is dead data")
        ok, reason = legal_for_companion(name, owned, generous, 20)
        if not ok:
            fail(f"tax_children: {name!r} can never be granted -- legal_for_companion refuses it "
                 f"even on a Str 25 / BAB +20 body owning every pool feat ({reason}). Curate it "
                 "out, or teach the reader that prerequisite.")


def check_coverage(pool, changes, compendium_path):
    """Only a feat whose numbers WOULD OTHERWISE VANISH needs an entry here.

    This used to read pool-subset-of-changes over a 29-name allowlist. The pool is derived now and
    runs to ~850 names, most of which are text and always were, so demanding an entry for each would
    be busywork that hides the real invariant. The real one is narrow: `createCompanions.js` strips
    `system.changes` from every companion item (D14), so a pool feat whose pf1 COMPENDIUM item
    carries changes loses its arithmetic unless this file re-supplies it. That set is 24 feats.
    """
    pool_set = set(pool)
    for name in sorted(changes):
        if name not in pool_set:
            fail(f"{name!r} has companion_feat_changes.json data but is not in the creature feat "
                 "pool; it is either denied, gated on a body part, or gone from data/feats.csv")
    if not compendium_path.exists():
        notes.append(f"coverage check SKIPPED -- {compendium_path} not present")
        return
    index = catalog_index(compendium_path)
    # `bonusFeats` is not arithmetic. The catalog hangs it on feats a class grants as a bonus
    # feat (Deflect Arrows, Stunning Fist, Throw Anything, Leadership), and a companion's slot count
    # comes off the chassis table, so nothing is lost when the module strips it.
    def automated(name):
        row = catalog_row(index, name)
        declared = ((row or {}).get("system") or {}).get("changes") or (row or {}).get("changes") or []
        return any(str(change.get("target")) != "bonusFeats" for change in declared)
    for name in sorted(pool):
        if automated(name) and name not in changes:
            fail(f"{name!r} is automated by the pf1 compendium but has no "
                 "companion_feat_changes.json entry; the module strips a companion item's changes, "
                 "so the bonus would reach no sheet at all")


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


def check_census(rules):
    """A denylist's one real failure mode is silence. This is what removes it.

    Every `data/feats.csv` row of a creature type must be classified by SOMETHING -- a column the
    pool reads, one of the three hand-authored lists, or membership of the pool itself. A new feat
    that lands in the corpus and is absurd on a wolf cannot slip in unnoticed, because nothing here
    classifies it and this check names it.
    """
    from utils.class_func.companion_feats import CREATURE_FEAT_TYPES, _feat_rows, creature_feat_pool
    widest = {norm(name) for name in creature_feat_pool(has_hands=True, can_speak=True)}
    classified = widest | set(rules["denied"]) | rules["hands"] | rules["language"]
    stray = []
    for key, row in _feat_rows().items():
        if row.get("type") not in CREATURE_FEAT_TYPES:
            continue
        if str(row.get("teamwork") or "0").strip() != "0":
            continue
        if str(row.get("racial") or "0").strip() == "1":
            continue
        if key not in classified:
            stray.append(row.get("name"))
    for name in sorted(stray):
        fail(f"{name!r} is a creature-type feat that no rule and no list classifies -- put it in "
             "the pool deliberately, or name it in denied_feats / hands_required / "
             "language_required")

    # Mythic leaks through the TYPE filter, and only just. 161 `data/feats.csv` rows are sourced
    # Mythic Adventures; 158 are typed `Mythic` and one `Metamagic`, all of which CREATURE_FEAT_TYPES
    # already removes -- but two (`Marked For Glory`, `Mythic Companion`) are typed `General` and
    # reached the pool of a creature that will never have a tier. The type column cannot see them;
    # the source column can. This is the denylist-behind-a-census pattern rule 3 already uses: the
    # two names are denied by hand, and a third row typed the same way fails here rather than
    # arriving on a sheet.
    mythic = [row.get("name") for key, row in _feat_rows().items()
              if key in widest and str(row.get("source") or "").strip() == "Mythic Adventures"]
    for name in sorted(mythic):
        fail(f"{name!r} is a Mythic Adventures feat in the creature pool -- its data/feats.csv row "
             "is typed something CREATURE_FEAT_TYPES admits, so the type filter cannot see it. A "
             "bonded creature has no mythic tier; name it in denied_feats.")
    notes.append(f"census: {len(widest)} feats in the widest pool, {len(rules['denied'])} denied, "
                 f"{len(rules['hands'])} gated on hands, {len(rules['language'])} on language")


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

    sys.path.insert(0, str(ROOT / "Backend"))
    from utils.class_func.companion_feats import creature_exclusions, creature_feat_pool

    chassis = json.loads(CHASSIS.read_text(encoding="utf-8"))
    allowed = chassis.get("tax_children") or []
    rules = creature_exclusions()
    changes = feat_change_data()
    shared = json.loads(SHARED_CHANGES.read_text(encoding="utf-8"))

    # The widest body there is: an eidolon with arms and a language. Every narrower creature's pool
    # is a subset of it, so gating this one gates them all.
    pool = creature_feat_pool(has_hands=True, can_speak=True)

    if not pool:
        fail("the derived creature feat pool is empty; an exclusion rule is eating everything")
    if not allowed:
        fail("animal_companion.json carries no 'tax_children' allowlist; without it feat tax hands "
             "a wolf Drunken Brawler and Wand Dancer")
    for label, names in (("hands_required", chassis.get("hands_required") or []),
                         ("language_required", chassis.get("language_required") or []),
                         ("tax_children", allowed)):
        if len(names) != len(set(names)):
            duplicates = sorted({name for name in names if names.count(name) > 1})
            fail(f"duplicate entries in the {label}: {duplicates}")
        if names != sorted(names):
            fail(f"the {label} is not sorted; keep it alphabetical so a diff is readable")

    check_names(pool, args.compendium)
    check_tax_children(pool, allowed, args.compendium)
    check_coverage(pool, changes, args.compendium)
    check_no_shared_entry(pool, changes, shared)
    check_census(rules)
    check_effects(changes)

    folded = sum(1 for effect in changes.values() if effect.get("changes"))
    for note in notes:
        print(f"  note: {note}")
    return REPORT.finish(
        f"{len(pool)} feats in the widest creature pool, {folded} with folded arithmetic, "
        f"{len(changes) - folded} text-only; {len(allowed)} tax children allowed "
        f"-- every pool name resolves, every declared effect lands, and no creature-type feat "
        f"is unclassified",
        max_errors=25)


if __name__ == "__main__":
    sys.exit(main())
