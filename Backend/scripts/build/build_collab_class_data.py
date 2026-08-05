"""Merge the omdura and vampire hunter into class_data.json, harvested from pf-content.

    C:\\Python310\\python.exe Backend/scripts/build_collab_class_data.py
    C:\\Python310\\python.exe Backend/scripts/build_collab_class_data.py --dry-run

These two are the last first-party Paizo base classes the generator lacked -- everything else on
d20pfsrd's class index (core, base, hybrid, unchained, occult, alternate, NPC) was already in
class_data.json as of 2026-08-04.

WHERE THEY LIVE, AND WHY THE FIRST CENSUS MISSED THEM. `pf1.classes` carries 49 class Items and
neither of these is among them; the first sweep for this work looked only at `pf1.classes`,
`pf1.class-abilities` and `pf-content.pf-class-abilities` and concluded they were unrenderable. A
sweep of *every* installed pack found both in **`pf-content.pf-collab-content`**, with a full
`classAssociations` chain -- 12 features for the omdura, 15 for the vampire hunter. The lesson is
the one docs/wayfinder/class-pool/issues/01 already recorded in a different form: grade the census
against every pack, because a class Item can live in a pack whose name does not say "classes".

WHAT THE PACK DOES NOT MODEL: SPELLCASTING. RAW gives the omdura spontaneous Charisma casting off
the cleric/inquisitor lists to 6th level, and the vampire hunter Wisdom casting off the inquisitor
list from 4th. The `pf-collab-content` class Items carry **no `casting` block at all**, so reading
the tier off the pack would ship two casters as non-casters. `CASTING_OVERRIDE` below asserts the
tier instead -- the one field on these two the pack does not decide.

WHY OVERRIDE RATHER THAN SHIP THEM QUIET. Both premises for the original ruling turned out to be
false. Neither class needs a new `data/spells.csv` column: `spells.py::class_for_spells_attr`
already aliases warpriest and oracle to the cleric column, witch and arcanist to the wizard one, so
pointing the omdura at `cleric` and the vampire hunter at `inquisitor` is the ordinary path, not an
exception. And the FoundryVTT module does NOT derive its spellbook from the class Item --
`configureSpellbook` writes `inUse`, `class`, `casterType`, `ability` and `kind` straight off the
payload, which is how `psion` and `aegis` get books while sitting at `casting level: none`.

The remaining fidelity gap is narrow and recorded in feature_spec_todo.md: RAW builds the omdura's
list as the UNION of the cleric's and the inquisitor's, and nobody has written that union down. It
reads the cleric column -- the superset at every level a `mid` caster reaches.

`check_casting_overrides()` fails the build the moment upstream ships a real casting block, so the
override cannot outlive the omission it exists for.

Idempotent: re-running replaces both entries in place.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BUILD, REPO as ROOT, SCRIPTS as HERE   # noqa: E402

from reconcile_psionics_names import find_classic_level          # noqa: E402 -- one owner
from build_npc_class_data import (                               # noqa: E402 -- one owner
    BAB_TIER, CASTING_TIER, SAVE_KEYS, check_good_saves, skill_names,
)
from build_occult_class_data import DEFAULT_SYSTEM_ROOT, plain    # noqa: E402 -- one owner

DUMPER = BUILD / "dump_foundry_pack.mjs"
CLASS_DATA = ROOT / "Backend/json/class_data.json"
FOUNDRY_DATA = Path(os.environ.get("LOCALAPPDATA", "")) / "FoundryVTT/Data"
DEFAULT_PACK = FOUNDRY_DATA / "modules/pf-content/packs/pf-collab-content"

CLASS_ITEM = {"omdura": "Omdura", "vampire hunter": "Vampire Hunter"}

# The one field the pack does NOT decide, and the reason. `casting level` is read off the class
# Item for every other class this script family builds; these two class Items carry no `casting`
# block at all, which would land them as non-casters. That is a pack omission, not a rule -- see
# the docstring -- so the tier is asserted here instead.
#
# check_casting_overrides() below turns "the fix is upstream" into something the build DETECTS:
# the moment pf-collab-content ships a casting block for either class, this script fails and names
# the disagreement rather than silently keeping a hand-written tier that upstream has superseded.
CASTING_OVERRIDE = {
    "omdura": ("mid", "RAW: spontaneous Charisma casting to 6th level. spells_per_day.json's "
                      "`omdura` row is the standard six-level table (the inquisitor's), and "
                      "class_for_spells_attr points it at the cleric column."),
    "vampire hunter": ("low", "RAW: Wisdom casting from 4th level, capped at 4th-level spells -- "
                              "the ranger/paladin shape. spells_per_day.json's `vampire hunter` "
                              "row is the standard four-level table (the ranger's), read off the "
                              "inquisitor column."),
}

# pf1's proficiency codes. Neither class ships a "Weapon and Armor Proficiency" feature Item -- the
# proficiencies live as enum fields on the class Item instead -- so the prose is rendered from
# these. An unknown code is a hard error rather than a silent omission: a class that quietly loses
# its armour proficiency looks exactly like one that never had it.
ARMOR_PROF = {"lgt": "light armor", "med": "medium armor", "hvy": "heavy armor",
              "shl": "shields (except tower shields)", "twr": "tower shields"}
WEAPON_PROF = {"simple": "all simple weapons", "martial": "all martial weapons",
               "exotic": "all exotic weapons"}

# plain() resolves @UUID[...]{label} but not the older @Compendium[pack.id]{label} form, which is
# what this pack uses. Same intent, different spelling: keep the label, drop the link.
COMPENDIUM_RE = re.compile(r"@Compendium\[[^\]]+\]\{([^}]*)\}")

# class_data.json wants a main_stat and an alignment line; the pack's description carries the
# alignment rule in prose but not as a field, and has no notion of a "main stat" at all.
PROSE = {
    "omdura": {
        "main_stat": "cha",
        "alignment": "An omdura's alignment must be within one step of her deity's.",
    },
    "vampire hunter": {
        "main_stat": "wis",
        "alignment": "Any.",
    },
}

# The class Item's description holds role prose AND the class-skill sentence, run together. Cut at
# the class-skill heading so `role` stays prose and the skills go where every other entry keeps
# them -- the `starting wealth` blob.
SKILLS_HEADING = "Class Skills"
WEALTH_PROSE = "{wealth} Class Skills The {name}'s class skills are {skills}."


def dump_packs(packs: list, classic_level: Path) -> list:
    """Every document in the given packs. Copied out from under a possibly-running Foundry.

    Both packs are needed, not just the one holding the class Items: four of the two classes'
    granted features are @UUIDs into `pf1.class-abilities` (the generic Weapon and Armor
    Proficiency / Bonus Feat items every class shares). Reading only pf-collab-content drops them,
    which is how the omdura first came out with no proficiency line at all.
    """
    scratch = Path(tempfile.mkdtemp(prefix="collab-packs-"))
    try:
        copies = []
        for pack in packs:
            target = scratch / pack.name
            shutil.copytree(pack, target, ignore=shutil.ignore_patterns("LOCK"))
            (target / "LOCK").unlink(missing_ok=True)
            copies.append(target)
        command = ["node", str(DUMPER), "--classic-level", str(classic_level), "--full",
                   *[str(p) for p in copies]]
        # encoding= is load-bearing on Windows: the pack prose is UTF-8 and cp1252 dies on the
        # first typographic dash.
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            sys.exit(f"pack dump failed:\n{result.stderr.strip()}")
        raw = json.loads(result.stdout)
        return [entry["doc"] for pack in raw.values() for entry in pack
                if not entry["key"].startswith("!folders")]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def clean(value: str) -> str:
    return COMPENDIUM_RE.sub(r"\1", plain(value or ""))


def proficiency_prose(name: str, system: dict) -> str:
    """The proficiency sentence, rendered from the class Item's own enum fields."""
    weapons = [WEAPON_PROF.get(code) for code in (system.get("weaponProf") or [])]
    armor = [ARMOR_PROF.get(code) for code in (system.get("armorProf") or [])]
    unknown = [code for code, label in
               zip((system.get("weaponProf") or []) + (system.get("armorProf") or []),
                   weapons + armor) if label is None]
    if unknown:
        sys.exit(f"{name}: unknown pf1 proficiency code(s) {unknown} -- extend ARMOR_PROF/"
                 f"WEAPON_PROF rather than letting the class lose a proficiency silently")
    article = "An" if name[0] in "aeiou" else "A"
    parts = []
    if weapons:
        parts.append("is proficient with " + ", ".join(weapons))
    if armor:
        parts.append(("and with " if parts else "is proficient with ") + ", ".join(armor))
    if not parts:
        return "The compendium class item lists no weapon or armor proficiencies."
    return f"{article} {name} " + " ".join(parts) + "."


def check_casting_overrides(pack_tiers: dict) -> list:
    """Fail if the pack has caught up with a CASTING_OVERRIDE, or if data.py has drifted from one.

    Two ways an override goes stale, and both are silent without this:
      * upstream ships a `casting` block -- the override is now second-guessing real pack data;
      * somebody edits class_data.json or data.py by hand and the two disagree with the override.
    """
    from utils import data as _data                                   # noqa: E402

    problems = []
    for name, (tier, _why) in sorted(CASTING_OVERRIDE.items()):
        pack_tier = pack_tiers.get(name)
        if pack_tier not in (None, "none"):
            problems.append(
                f"  {name}: the pack now says {pack_tier!r} -- pf-collab-content has shipped a "
                f"casting block. Drop the CASTING_OVERRIDE entry (or reconcile it with {tier!r}).")
        if name not in _data.base_classes:
            problems.append(f"  {name}: casts {tier!r} but is not in data.base_classes, which "
                            f"spells.py uses as the spellbook gate -- it would cast nothing.")
    return problems


def entry(name: str, cls: dict, docs: dict, system_root: Path) -> tuple:
    """One class_data.json entry: pack chassis + pack feature prose, in the required key order."""
    system = cls["system"]
    prose = PROSE[name]
    saves = {key: system["savingThrows"][key]["value"] for key in SAVE_KEYS}

    described = clean(system.get("description", {}).get("value") or "")
    role = described.split(SKILLS_HEADING)[0].strip()
    skills = skill_names(system_root, system.get("classSkills") or {})
    wealth = system.get("wealth") or ""
    wealth = f"{wealth} gp." if wealth else "Not given on the class table."

    pack_tier = CASTING_TIER[(system.get("casting") or {}).get("progression")]

    built = {
        "main_stat": prose["main_stat"],
        "bab": BAB_TIER[system["bab"]],
        "casting level": CASTING_OVERRIDE[name][0] if name in CASTING_OVERRIDE else pack_tier,
        "role": role,
        "alignment": prose["alignment"],
        "hit die": f"d{system['hd']}.",
        "starting wealth": WEALTH_PROSE.format(wealth=wealth, name=name, skills=skills),
        "skill points at each level": str(system["skillsPerLevel"]),
        "weapon and armor proficiency": proficiency_prose(name, system),
    }

    # The granted features, in level order, as ordinary feature keys. Everything after
    # "weapon and armor proficiency" is a class ability to class_abilities.py, so this is the
    # whole feature list the sheet and the payload will show.
    links = (system.get("links") or {}).get("classAssociations") or []
    unresolved = []
    for link in links:
        source = str(link.get("uuid", "")).split(".")[-1]
        feature = docs.get(source)
        if feature is None:
            unresolved.append(link.get("uuid"))
            continue
        text = clean(feature.get("system", {}).get("description", {}).get("value") or "")
        label = feature["name"].strip()
        if label.lower().startswith("weapon and armor proficiency"):
            built["weapon and armor proficiency"] = text     # prefer the pack's own wording
            continue
        # The pack disambiguates same-named features across classes with a suffix -- "Aura (OMD)",
        # "Quarry (VAM)". That suffix is a compendium bookkeeping detail, not a rules name.
        label = label.split(" (")[0] if label.endswith(")") and len(label.split(" (")) == 2 \
            else label
        built[label.lower()] = text or f"See the {label} class feature."

    return built, saves, unresolved, pack_tier


def write(entries: dict, dry_run: bool) -> None:
    data = json.loads(CLASS_DATA.read_text(encoding="utf-8"))
    for name, built in entries.items():
        data.pop(name, None)                       # idempotent
        data[name] = built
    if dry_run:
        print("  --dry-run: class_data.json not written")
        return
    CLASS_DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {CLASS_DATA.relative_to(ROOT)}  ({len(entries)} entries)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pack", default=str(DEFAULT_PACK),
                        help="the pf-collab-content pack directory")
    parser.add_argument("--system-root", default=str(DEFAULT_SYSTEM_ROOT),
                        help="the installed pf1 system directory (for the skill-name table)")
    parser.add_argument("--classic-level", default=None,
                        help="directory of an installed classic-level package")
    parser.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = parser.parse_args()

    pack = Path(args.pack)
    abilities = Path(args.system_root) / "packs/class-abilities"
    missing_packs = [p for p in (pack, abilities) if not p.exists()]
    if missing_packs:
        sys.exit(f"pack(s) not found: {[str(p) for p in missing_packs]}")
    classic_level = find_classic_level(args.classic_level)
    print(f"classic-level: {classic_level}")

    documents = dump_packs([pack, abilities], classic_level)
    docs = {doc["_id"]: doc for doc in documents}
    by_name = {doc["name"]: doc for doc in documents if doc.get("type") == "class"}
    missing = [item for item in CLASS_ITEM.values() if item not in by_name]
    if missing:
        sys.exit(f"{pack.name} has no class Item for: {missing}")

    entries, pack_saves, pack_tiers = {}, {}, {}
    for name, item_name in sorted(CLASS_ITEM.items()):
        built, saves, unresolved, pack_tier = entry(
            name, by_name[item_name], docs, Path(args.system_root))
        entries[name] = built
        pack_saves[name] = saves
        pack_tiers[name] = pack_tier
        features = len(built) - 9
        good = ", ".join(k for k in SAVE_KEYS if saves[k] == "high") or "none"
        overridden = " (override; pack has no casting block)" if name in CASTING_OVERRIDE else ""
        print(f"  {name:<15} {built['hit die']:<5} BAB {built['bab']}  "
              f"{built['skill points at each level']} skills  saves: {good}  "
              f"{features} features  casting: {built['casting level']}{overridden}")
        if unresolved:
            # These point into pf1.class-abilities, a different pack -- generic shared features
            # (Weapon and Armor Proficiency, Bonus Feat). Named, never silently dropped.
            print(f"    {len(unresolved)} association(s) point outside this pack and were skipped: "
                  + ", ".join(str(u) for u in unresolved))

    problems = check_good_saves(pack_saves)
    if problems:
        print("\ndata.py good_saves disagrees with the pack -- fix data.py, then re-run:")
        print("\n".join(problems))
        return 1

    problems = check_casting_overrides(pack_tiers)
    if problems:
        print("\nCASTING_OVERRIDE is stale -- reconcile it, then re-run:")
        print("\n".join(problems))
        return 1

    write(entries, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
