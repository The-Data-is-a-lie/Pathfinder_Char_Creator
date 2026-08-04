"""Merge the five Paizo NPC classes into class_data.json, sourcing their chassis from pf1.

    C:\\Python310\\python.exe Backend/scripts/build_npc_class_data.py
    C:\\Python310\\python.exe Backend/scripts/build_npc_class_data.py --system-root <dir> --dry-run

Adept, aristocrat, commoner, expert and warrior are the last first-party Paizo classes the
generator lacked. They are what an *NPC* generator is for -- the town guard, the shopkeeper, the
village priest -- and until now a random innkeeper had to be a bard.

WHY THE PACK AND NOT THE BOOK. Every number on these classes' tables is already in `pf1.classes`
as a class Item: hit die, BAB tier, skill ranks, the three save tiers and the class-skill set. Only
the prose is hand-supplied here. That is the same split build_occult_class_data.py cut, and it
means a pf1 update is the thing that has to change for these rows to go stale, not somebody's
memory of the table.

The one number the pack gets WRONG for our purposes is the adept's spell progression: pf1 tags it
`med`, which is the cleric's 6-spell-level table, but the adept caps at 5th level and `spells.csv`
carries no adept spell above 5th. So `casting level` stays `mid` -- that is the tier
caster_formula understands, and the tier is what the payload and the Foundry sheet agree on --
while ADEPT_PER_DAY below is RAW's actual table, whose 6th-level row is entirely `null`.

That row is load-bearing, not decorative. spells_per_day_attr loops `range(0, highest_spell_known
+ 1)` and indexes this JSON by key, so a 16th-level adept KeyErrors without a `"6"` entry; the
all-`null` row makes spells_known_selection break at level 6 instead. The data enforces the cap and
no branch in spells.py had to learn about the adept.

WHAT THE NULL ROW DOES NOT REACH: FOUNDRY, AND THAT IS ALLOWED TO STAND. The module's
configureSpellbook sends pf1 only `casterType`, so pf1 fills slots from its own `med` table and a
16th+ adept sees a 6th-level slot no adept spell can fill. Ruled acceptable 2026-08-04: closing it
means `autoSpellLevels = false` and writing `spellN.max` from the payload, which hands the generator
every caster's slots -- thirty classes pf1 already gets right -- for one empty row on a class that
will rarely be rolled. See feature_spec_todo.md section 12.

If that is ever revisited, the trap: write N = 1..9 ONLY. The `"0"` row is all zeros for 27 of the
28 classes and means "orisons are at-will, not tracked", NOT "no orisons" -- the adept has 10 of
them in spells.csv. Writing row 0 verbatim would strip cantrips from every Foundry caster.

Idempotent: re-running replaces the five entries in place. Refuses to write if the pack disagrees
with data.py's good_saves, because that table is hand-maintained and a silent mismatch there gives a
class all-poor saves without anything failing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reconcile_psionics_names import find_classic_level          # noqa: E402 -- one owner
from build_occult_class_data import (                            # noqa: E402 -- one owner
    DEFAULT_MODULE_ROOT, DEFAULT_SYSTEM_ROOT, ROW_LENGTH, _block, documents, dump,
)

ROOT = HERE.parents[1]
CLASS_DATA = ROOT / "Backend/json/class_data.json"
SPELLS_KNOWN = ROOT / "Backend/json/spells_known.json"
SPELLS_PER_DAY = ROOT / "Backend/json/spells_per_day.json"

# class_data.json key -> the pf1 class Item's name.
CLASS_ITEM = {
    "adept": "Adept", "aristocrat": "Aristocrat", "commoner": "Commoner",
    "expert": "Expert", "warrior": "Warrior",
}

BAB_TIER = {"low": "L", "med": "M", "high": "H"}
# pf1 spells the middle tier "med"; every consumer in this repo says "mid" (see
# build_occult_class_data.reconcile_casting_level, which had to make the same translation).
CASTING_TIER = {"low": "low", "med": "mid", "high": "high", None: "none"}
SAVE_KEYS = ("fort", "ref", "will")

# --------------------------------------------------------------------------------------------- #
# The prose. Everything else is read off the class Item.
#
# `role` and `alignment` follow the shape of the entries already in class_data.json. Feature keys
# MUST come after "weapon and armor proficiency" -- class_abilities.py::get_class_abilities only
# starts collecting once it has seen that key. None of these five carry racial favoured-class
# bonuses, so nothing follows the features.
# --------------------------------------------------------------------------------------------- #
PROSE = {
    "adept": {
        "main_stat": "wis",
        "alignment": "Any.",
        "role": "Adepts are the spellcasters of the wider world -- village healers, tribal "
                "shamans, hedge witches and back-country priests who never trained at a temple or "
                "a college. An adept's magic is thin next to a cleric's, but in a settlement with "
                "no cleric at all it is the only magic there is.",
        "weapon and armor proficiency": "Adepts are skilled with all simple weapons. Adepts are "
                "not proficient with any type of armor or shield.",
        "features": {
            "spells": "An adept casts divine spells, which are drawn from the adept spell list. "
                      "Like a cleric, an adept must choose and prepare her spells in advance. "
                      "Unlike a cleric, an adept cannot spontaneously cast cure or inflict "
                      "spells. To prepare or cast a spell, an adept must have a Wisdom score "
                      "equal to at least 10 + the spell level. The Difficulty Class for a saving "
                      "throw against an adept's spell is 10 + the spell level + the adept's "
                      "Wisdom modifier. Adepts meditate or pray for their spells, receiving them "
                      "through their own strength of faith or from a patron.",
            "summon familiar": "At 2nd level, an adept can call a familiar, just as a wizard can "
                               "using the arcane bond ability.",
        },
    },
    "aristocrat": {
        "main_stat": "cha",
        "alignment": "Any.",
        "role": "Aristocrats are the nobles, merchant princes and landed gentry who rule by birth "
                "and by influence rather than by force. Trained in courtly graces and the "
                "weapons of the duel, an aristocrat's real power is who owes them a favour.",
        "weapon and armor proficiency": "Aristocrats are proficient with all simple and martial "
                "weapons and with all types of armor and shields.",
        "features": {},
    },
    "commoner": {
        "main_stat": "str",
        "alignment": "Any.",
        "role": "Commoners are farmers, labourers, servants and the ordinary folk who make up "
                "most of the world. They have no training worth the name, and that is the point: "
                "a commoner is who the adventurers are protecting.",
        "weapon and armor proficiency": "The commoner is proficient with one simple weapon. He is "
                "not proficient with any other weapons, nor is he proficient with any type of "
                "armor or shield.",
        "features": {},
    },
    "expert": {
        "main_stat": "int",
        "alignment": "Any.",
        "role": "Experts are the skilled professionals of the world -- blacksmiths, scribes, "
                "guides, sailors, spymasters and master craftsmen. An expert is dangerous the way "
                "a locksmith is dangerous: not in a fight, but in what they can do.",
        "weapon and armor proficiency": "The expert is proficient in the use of all simple "
                "weapons and with light armor, but not shields.",
        # The pack tags the expert with Lore alone, which is correct and useless: RAW gives the
        # expert any ten skills of its choosing, so there is no fixed list to read off the Item.
        # The one case where the prose has to override the source rather than quote it.
        "class_skills": "any ten skills, chosen when the expert is made",
        "features": {},
    },
    "warrior": {
        "main_stat": "str",
        "alignment": "Any.",
        "role": "Warriors are the rank and file of the world's militaries -- town guards, "
                "caravan escorts, levies and hired swords. A warrior fights as well as a fighter "
                "of the same level would have at the start of a career, and never learns the "
                "tricks that follow.",
        "weapon and armor proficiency": "Warriors are proficient with all simple and martial "
                "weapons and with all types of armor and shields.",
        "features": {},
    },
}

# NPC classes have no starting-wealth line of their own -- they are equipped with NPC gear, and
# createACharacter.py uses wealth-by-level regardless. The key still has to exist and hold the
# class-skill prose, because that is where every other entry in class_data.json keeps it and
# class_abilities.py slices on the key AFTER it.
WEALTH_PROSE = ("NPC classes have no starting wealth of their own; an NPC is equipped by its role. "
                "Class Skills The {name}'s class skills are {skills}.")

# --------------------------------------------------------------------------------------------- #
# The adept's spells per day, RAW (Adept, Pathfinder RPG Core Rulebook / d20pfsrd NPC classes).
#
# NOT taken from pf1's `med` progression, which is the cleric's and would hand a 16th-level adept
# 6th-level slots it can never fill: `data/spells.csv`'s adept column runs 1st-5th (62 spells, plus
# 10 orisons). Rows are per spell level, indexed by class level - 1, in the shape
# spells_per_day.json already uses ('null' before the level opens).
#
# The "0" row is all zeroes rather than RAW's 3 orisons per day, matching every other entry in the
# file (see cleric): 0 there means "at-will, not tracked", not "none". The "6" row exists only
# because caster_formula's `mid` tier asks for spell level 6 at class level 16+; it is all 'null',
# which is what caps the adept at 5th-level spells.
# --------------------------------------------------------------------------------------------- #
N = "null"
ADEPT_PER_DAY = {
    "0": [0] * 20,
    "1": [1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    "2": [N, N, N, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    "3": [N, N, N, N, N, N, N, 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3],
    "4": [N, N, N, N, N, N, N, N, N, N, N, 0, 1, 1, 2, 2, 2, 2, 3, 3],
    "5": [N, N, N, N, N, N, N, N, N, N, N, N, N, N, N, 0, 1, 1, 2, 2],
    "6": [N] * 20,
}


def class_items(system_root: Path, classic_level: Path) -> dict:
    """The five NPC class Items, by pf1 name."""
    raw = dump(system_root, DEFAULT_MODULE_ROOT, classic_level)
    wanted = set(CLASS_ITEM.values())
    found = {doc["name"]: doc for doc in documents(raw, "classes")
             if doc.get("type") == "class" and doc.get("name") in wanted}
    missing = sorted(wanted - set(found))
    if missing:
        sys.exit(f"pf1.classes has no class Item for: {missing} -- pf1 changed its packs")
    return found


def skill_names(system_root: Path, class_skills: dict) -> str:
    """The class-skill abbreviations on a class Item, as readable names, for the prose blob.

    Two hops, both out of pf1: `config.skills` maps the abbreviation to an i18n key
    ("kar" -> "PF1.SkillKAr"), and lang/en.json resolves that to "Knowledge (Arcana)". The lang
    file is NESTED under a "PF1" object, so the key has to be walked, not looked up flat.
    """
    lang = json.loads((system_root / "lang/en.json").read_text(encoding="utf-8"))
    sourcemap = json.loads((system_root / "pf1.js.map").read_text(encoding="utf-8"))
    sources = dict(zip(sourcemap["sources"], sourcemap["sourcesContent"]))
    config = sources["module/config.mjs"]
    at = config.index("export const skills")
    body = config[at:config.index("});", at)]
    keys = dict(part.split(": ") for part in
                [line.strip().rstrip(",") for line in body.splitlines() if ": " in line])

    def translate(key: str) -> str | None:
        node = lang
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node if isinstance(node, str) else None

    out = []
    for abbr, on in sorted(class_skills.items()):
        if not on:
            continue
        label = translate(keys.get(abbr, "").strip('"'))
        if label is None:
            sys.exit(f"pf1 has no name for skill {abbr!r} -- pf1 changed its config or lang file")
        out.append(label)
    return ", ".join(sorted(out))


def entry(name: str, item: dict, system_root: Path) -> dict:
    """One class_data.json entry: pack numbers + hand-written prose, in the required key order."""
    system = item["system"]
    prose = PROSE[name]
    saves = {key: system["savingThrows"][key]["value"] for key in SAVE_KEYS}
    skills = prose.get("class_skills") or skill_names(system_root, system.get("classSkills") or {})
    built = {
        "main_stat": prose["main_stat"],
        "bab": BAB_TIER[system["bab"]],
        "casting level": CASTING_TIER[(system.get("casting") or {}).get("progression")],
        "role": prose["role"],
        "alignment": prose["alignment"],
        "hit die": f"d{system['hd']}.",
        "starting wealth": WEALTH_PROSE.format(name=name, skills=skills),
        "skill points at each level": str(system["skillsPerLevel"]),
        "weapon and armor proficiency": prose["weapon and armor proficiency"],
    }
    built.update(prose["features"])
    return built, saves


def check_good_saves(pack_saves: dict) -> list:
    """data.py's good_saves is hand-maintained; make the pack the thing that decides it."""
    sys.path.insert(0, str(ROOT / "Backend"))
    from utils import data as _data                                   # noqa: E402

    problems = []
    for name, saves in sorted(pack_saves.items()):
        want = sorted(key for key in SAVE_KEYS if saves[key] == "high")
        have = sorted(_data.good_saves.get(name, []))
        if name not in _data.good_saves:
            problems.append(f"  data.py good_saves has no '{name}' -- add {want!r}")
        elif have != want:
            problems.append(f"  data.py good_saves[{name!r}] is {have!r}, pf1 says {want!r}")
    return problems


def write_class_data(entries: dict, dry_run: bool) -> None:
    data = json.loads(CLASS_DATA.read_text(encoding="utf-8"))
    for name, built in entries.items():
        data.pop(name, None)                       # idempotent: re-append in a stable position
        data[name] = built
    if dry_run:
        print("  --dry-run: class_data.json not written")
        return
    CLASS_DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {CLASS_DATA.relative_to(ROOT)}  ({len(entries)} entries)")


def _row(values: list) -> list:
    """Pad to the 21 entries these files carry -- spells_*_attr indexes [capped_level - 1] and
    nothing clamps a 21st level, so every existing row has one spare."""
    return values + [values[-1]] * (ROW_LENGTH - len(values))


def write_spell_tables(dry_run: bool) -> None:
    """The adept's two rows. Prepared divine caster, so spells_known is cleric-shaped ('all').

    Spliced as text, not re-serialised: `indent=` would reflow all ~25 existing classes and bury a
    one-class addition in a 7,000-line diff. Same reason, same helper, as the occult builder.
    """
    for path, rows in ((SPELLS_PER_DAY, {k: _row(v) for k, v in ADEPT_PER_DAY.items()}),
                       (SPELLS_KNOWN, {k: ["all"] for k in ADEPT_PER_DAY})):
        if dry_run:
            continue
        text = path.read_text(encoding="utf-8")
        # Idempotent: drop any block a previous run wrote, then re-add at the top.
        text = re.sub(r'\n[ ]{4}"adept":[ ]*\{.*?\n[ ]{4}\},?', "", text, flags=re.DOTALL)
        opening = text.index("{") + 1
        text = text[:opening] + "\n" + _block("adept", rows) + text[opening:].lstrip("\n")
        json.loads(text)                            # never write a file that stopped being JSON
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}  (adept 0-{max(int(k) for k in rows)})")
    if dry_run:
        print("  --dry-run: spell tables not written")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--system-root", default=str(DEFAULT_SYSTEM_ROOT),
                        help="the installed pf1 system directory")
    parser.add_argument("--classic-level", default=None,
                        help="directory of an installed classic-level package")
    parser.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = parser.parse_args()

    system_root = Path(args.system_root)
    classic_level = find_classic_level(args.classic_level)
    print(f"classic-level: {classic_level}")
    items = class_items(system_root, classic_level)

    entries, pack_saves = {}, {}
    for name, item_name in sorted(CLASS_ITEM.items()):
        built, saves = entry(name, items[item_name], system_root)
        entries[name] = built
        pack_saves[name] = saves
        good = ", ".join(k for k in SAVE_KEYS if saves[k] == "high") or "none"
        print(f"  {name:<11} {built['hit die']:<5} BAB {built['bab']}  "
              f"{built['skill points at each level']} skills  good saves: {good}")

    problems = check_good_saves(pack_saves)
    if problems:
        print("\ndata.py good_saves disagrees with pf1 -- fix data.py, then re-run:")
        print("\n".join(problems))
        return 1

    write_class_data(entries, args.dry_run)
    write_spell_tables(args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
