"""Harvest the six Occult Adventures classes' option pools out of the pf1 system compendium.

    C:\\Python310\\python.exe Backend/scripts/build_occult_class_data.py
    C:\\Python310\\python.exe Backend/scripts/build_occult_class_data.py --system-root <dir>

Map: docs/wayfinder/class-pool. Writes Backend/json/class_data/<class>.json in the
{dataset: {name: description}} shape `generic_class_option_chooser` already consumes -- the same
seam build_psionic_class_data.py cut for the twelve psionic classes, so no new chooser module
exists here either.

WHY THE COMPENDIUM AND NOT A SCRAPE (ticket 04). Occult Adventures is first-party Paizo and the
`pf1` system ships all six classes itself: `pf1.classes` has a rollable class Item for every one,
and `pf1.class-abilities` has their features AND their selectable options as `feat` Items. §8's
familiar harvest tried compendium-first and lost -- `pf-content` was too thin to generate from --
so this was checked rather than assumed. It is not thin: 694 selectable options across the six.
No OGL entry is needed; this is Paizo content read out of the system's own pack.

The two fields that make the pack a *source* rather than just a renderer:

  system.associations.classes           on an ability Item -- the class tag. An exact list, not a
                                        name match, so nothing is guessed.
  system.links.classAssociations        on the class Item -- the AUTO-GRANTED features, by level.
                                        Its complement is the selectable pool. Without this the
                                        harvest would shelve "Hypnotic Stare" (granted at 1st)
                                        next to the stares a mesmerist actually picks.

Foundry may be running. LevelDB is single-writer, so each pack is copied to a scratch directory
and the copy's LOCK dropped before it is read; the installed packs are never opened or written.

Idempotent: re-running replaces the six files in place.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reconcile_psionics_names import find_classic_level   # noqa: E402  -- one owner for the hunt

ROOT = HERE.parents[1]
DUMPER = HERE / "dump_foundry_pack.mjs"
CLASS_DIR = ROOT / "Backend/json/class_data"

FOUNDRY_DATA = Path(os.environ.get("LOCALAPPDATA", "")) / "FoundryVTT/Data"
DEFAULT_SYSTEM_ROOT = FOUNDRY_DATA / "systems/pf1"
DEFAULT_MODULE_ROOT = FOUNDRY_DATA / "modules/pf-content"

# Both are required, and neither is optional in practice: `pf1.classes` owns the class Items and
# most of the options, but the occultist's eight implement schools and the spiritualist's phantom
# emotional foci live ONLY in `pf-content`. Reading just the system pack silently produces an
# occultist with nothing to pick -- which is how this was found.
SYSTEM_PACKS = ("classes", "class-abilities")
MODULE_PACKS = ("pf-class-abilities",)
ABILITY_PACKS = ("class-abilities", "pf-class-abilities")

# The pf1 class Item's own name, per class_data.json key.
CLASS_ITEM = {
    "occultist": "Occultist", "kineticist": "Kineticist", "medium": "Medium",
    "mesmerist": "Mesmerist", "psychic": "Psychic", "spiritualist": "Spiritualist",
}


# --------------------------------------------------------------------------------------------- #
# Bucketing. Four of the twelve pools are identified by the pack's own `tags` and are exact; the
# rest need a name pattern or a phrase from the description, because the pack tags unevenly.
#
# Per CLAUDE.md a heuristic like that belongs in a validator, not a comment -- so every rule here
# is re-checked by Backend/scripts/gates/validate_occult_data.py, which fails if a bucket empties or
# collects something it should not. Tune the rules here; the gate is what keeps them honest.
# --------------------------------------------------------------------------------------------- #

def tagged(*wanted):
    """Item carries any of these `system.tags` entries."""
    want = {w.lower() for w in wanted}
    return lambda d, text: bool(want & {t.lower() for t in (d["system"].get("tags") or [])})


def name_ends(suffix):
    return lambda d, text: d["name"].endswith(suffix)


def untagged_saying(*phrases):
    """Untagged item whose description contains any of these phrases."""
    low = [p.lower() for p in phrases]
    return lambda d, text: (not d["system"].get("tags")
                            and any(p in text for p in low))


def any_of(*rules):
    return lambda d, text: any(rule(d, text) for rule in rules)


def not_(rule):
    return lambda d, text: not rule(d, text)


def both(a, b):
    return lambda d, text: a(d, text) and b(d, text)


# class -> dataset name -> rule. Dataset names are what data.amount and the
# generic_class_option_chooser calls in main_test.py key off; changing one means changing all three.
BUCKETS = {
    "occultist": {
        # The eight implement schools. "<School> Resonant School" items are the resonant power each
        # school grants automatically -- excluded, they are not a second choice.
        "implements": tagged("Occultist Implement"),
        "focus powers": both(
            any_of(tagged("Focus Power", "Base Focus Power"),
                   untagged_saying("mental focus")),
            not_(name_ends("Resonant School"))),
    },
    "kineticist": {
        "elemental focus": tagged("Kineticist Element"),
        "wild talents": tagged("Utility Wild Talent"),
        "infusions": tagged("Form Infusion", "Substance Infusion"),
    },
    "medium": {
        # The six legends a medium channels. The pack also carries 25 "Legendary Spirit" and 9
        # "Outsider Spirit" variants; those are alternate seance targets, not the base six, and are
        # left out of v1 rather than diluting the roll 1-in-7 toward a named NPC.
        "spirits": both(name_ends(" Spirit"), not_(tagged("Medium Legendary Spirit",
                                                          "Medium Outsider Spirit"))),
    },
    "mesmerist": {
        "bold stare": name_ends("(Stare)"),
        "mesmerist tricks": both(
            any_of(tagged("Mesmerist Trick", "Mesmerist Masterful Trick"),
                   untagged_saying("this trick")),
            not_(name_ends("(Stare)"))),
    },
    "psychic": {
        "disciplines": name_ends(" Discipline"),
        # An amplification spends phrenic points to modify the spell being cast, which is what
        # separates it from a discipline-granted power that spends from the same pool.
        "phrenic amplifications": both(
            untagged_saying("phrenic pool"),
            both(any_of(untagged_saying("linked spell"), untagged_saying("amplification")),
                 not_(name_ends(" Discipline")))),
    },
    "spiritualist": {
        "emotional focus": tagged("Phantom Emotional Focus"),
    },
}

# --------------------------------------------------------------------------------------------- #
# Spell progressions. Five of the six cast; the kineticist does not (its `casting` block in the
# pack is literally absent, which is the pack agreeing with data.py:288 that burn is not
# spellcasting). The tables are READ OUT OF pf1 rather than typed from the book: the class Item
# carries only `casting.progression` + `casting.type`, and pf1 derives every number from
# `config.casterProgression`. Copying its tables is what makes the payload and the Foundry sheet
# show the same spell counts -- a hand-typed table would be a second authority that can drift.
#
# pf1 ships one table per (type, progression), so all four `med` spontaneous casters share the
# bard's numbers by construction, and the medium takes the `low` row. Cross-check: the derived
# occultist row reproduces the repo's existing `bard` spells-known row exactly, and the derived
# psychic row reproduces `sorcerer` in BOTH files -- two independently-authored sources agreeing.
#
# ONE FLAGGED ROW -- the medium. pf1's `low` spontaneous table is shaped for the bloodrager, whose
# first 1st-level spell lands at class level 4, and pf1 applies it to the medium unchanged (its
# `cantrips` flag does not shift the table). RAW's medium casts from 1st. We take pf1's numbers so
# the payload and the Foundry sheet agree rather than disagreeing in opposite directions, and §10
# records it as the medium's open rules question. Fix here if it is ruled a bug.
CASTERS = {
    "occultist": "med", "medium": "low", "mesmerist": "med",
    "psychic": "high", "spiritualist": "med",
}
SPELLS_KNOWN = ROOT / "Backend/json/spells_known.json"
SPELLS_PER_DAY = ROOT / "Backend/json/spells_per_day.json"
CLASS_DATA = ROOT / "Backend/json/class_data.json"
CONFIG_SOURCE = "module/config.mjs"

TAG_RE = re.compile(r"<[^>]+>")
UUID_RE = re.compile(r"@UUID\[[^\]]+\]\{([^}]*)\}")
WS_RE = re.compile(r"[ \t\r\f\v]+")


def plain(value: str, tags=()) -> str:
    """Compendium HTML -> the plain prose the option files and both sheets carry.

    Paragraph breaks come from the OPENING <p> as well as the closing one: several occult items
    are written as `<p><em>...</em><p><b>Spirit Bonus:</b>...` with no `</p>` at all, and splitting
    only on the close would run the flavour line into the mechanics.
    """
    text = UUID_RE.sub(r"\1", value or "")          # @UUID[...]{mental focus} -> mental focus
    text = re.sub(r"</?p[^>]*>|<br\s*/?>", "\n", text, flags=re.I)
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = WS_RE.sub(" ", text)
    lines = [line.strip() for line in text.split("\n")]
    # The pack renders an item's category as the first line of its own description ("Occultist
    # Implement", "Phantom Emotional Focus"). It is the tag we already bucketed on, so carrying it
    # into every description would repeat the section header on the sheet, once per option.
    lowered = {t.lower() for t in tags}
    while lines and (not lines[0] or lines[0].lower() in lowered):
        lines.pop(0)
    return "\n".join(line for line in lines if line).strip()


def dump(system_root: Path, module_root: Path, classic_level: Path) -> dict:
    """Copy each pack to scratch, drop the copy's LOCK, read it, throw the copy away."""
    packs = ([system_root / "packs" / name for name in SYSTEM_PACKS] +
             [module_root / "packs" / name for name in MODULE_PACKS])
    missing = [p for p in packs if not p.exists()]
    if missing:
        sys.exit(f"missing packs: {[str(p) for p in missing]}")

    scratch = Path(tempfile.mkdtemp(prefix="occult-packs-"))
    try:
        copies = []
        for pack in packs:
            target = scratch / pack.name
            # An open Foundry holds LOCK itself, so it cannot be copied -- ignoring it is the point.
            shutil.copytree(pack, target, ignore=shutil.ignore_patterns("LOCK"))
            (target / "LOCK").unlink(missing_ok=True)
            copies.append(target)
        command = ["node", str(DUMPER), "--classic-level", str(classic_level), "--full",
                   *[str(p) for p in copies]]
        # encoding= is load-bearing: the pack prose is UTF-8 and Windows would otherwise decode
        # node's stdout as cp1252 and die on the first typographic dash.
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            sys.exit(f"pack dump failed:\n{result.stderr.strip()}")
        return json.loads(result.stdout)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _balanced(text: str, start: int, open_ch: str, close_ch: str) -> str:
    """The substring from `start` (which must be `open_ch`) through its matching close."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == open_ch:
            depth += 1
        elif text[i] == close_ch:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("unbalanced")


def caster_tables(system_root: Path) -> dict:
    """pf1's own casterProgression, as {section: {progression: [row per class level]}}.

    The system ships minified `pf1.js` with a sourcemap beside it; `sourcesContent` still carries
    the readable `module/config.mjs`, which is where the tables live. Same trick the trait-migration
    work used to read pf1 internals.
    """
    sourcemap = json.loads((system_root / "pf1.js.map").read_text(encoding="utf-8"))
    sources = dict(zip(sourcemap["sources"], sourcemap["sourcesContent"]))
    config = sources.get(CONFIG_SOURCE)
    if not config:
        sys.exit(f"{CONFIG_SOURCE} is not in pf1.js.map -- pf1 changed its build")

    # Anchor on the export and search forward. Slicing the whole object first does not work: the
    # declaration carries a `/** @type {const} */` cast, whose brace would be matched instead.
    anchor = config.index("export const casterProgression")
    out = {}
    for section in ("castsPerDay", "spellsPreparedPerDay"):
        section_at = config.index(section + ":", anchor)
        section_body = _balanced(config, config.index("{", section_at), "{", "}")
        spont = _balanced(section_body, section_body.index("{", section_body.index("spontaneous:")),
                          "{", "}")
        rows = {}
        for progression in ("low", "med", "high"):
            literal = _balanced(spont, spont.index("[", spont.index(progression + ":")), "[", "]")
            # Cantrips are unlimited casts; JSON has no infinity, and the repo's tables already
            # write 0 in the 0-level per-day row (see the bard), so the sentinel lands correctly.
            literal = literal.replace("Number.POSITIVE_INFINITY", "0")
            literal = re.sub(r",(\s*[\]}])", r"\1", literal)      # trailing commas
            rows[progression] = json.loads(literal)
        out[section] = rows
    return out


# The existing rows run to 21 entries, not 20: spells_known_attr indexes [capped_level - 1] and
# nothing clamps a 21st level, so every row in these files carries one spare. Match it.
ROW_LENGTH = 21


def progression_row(table: list, spell_level: int) -> list:
    """pf1's per-class-level rows -> the repo's per-spell-level column, indexed by level - 1."""
    row = [entry[spell_level] if spell_level < len(entry) else "null" for entry in table]
    return row + [row[-1]] * (ROW_LENGTH - len(row))


def _block(name: str, rows: dict) -> str:
    """One class, in the hand-written style these two files already use (compact rows, 4/8 indent).

    Written as text rather than re-serialised with json.dump on purpose: `indent=` would reflow all
    ~20 existing classes and bury a five-class addition in a 7,000-line diff.
    """
    body = "\n".join(f'        "{level}": [' + ",".join(json.dumps(v) for v in rows[level]) + "],"
                     for level in sorted(rows, key=int))
    return f'    "{name}": {{\n{body.rstrip(",")}\n    }},\n'


def write_spell_tables(tables: dict) -> None:
    for path, section in ((SPELLS_PER_DAY, "castsPerDay"),
                          (SPELLS_KNOWN, "spellsPreparedPerDay")):
        text = path.read_text(encoding="utf-8")
        blocks = ""
        for name, progression in sorted(CASTERS.items()):
            table = tables[section][progression]
            depth = max(len(entry) for entry in table)
            rows = {str(level): progression_row(table, level) for level in range(depth)}
            # Idempotent: drop any block this script wrote before, then re-add.
            text = re.sub(r'\n[ ]{4}"' + re.escape(name) + r'":[ ]*\{.*?\n[ ]{4}\},?',
                          "", text, flags=re.DOTALL)
            blocks += _block(name, rows)
        opening = text.index("{") + 1
        text = text[:opening] + "\n" + blocks + text[opening:].lstrip("\n")
        json.loads(text)      # never write a file that stopped being JSON
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}  " +
              ", ".join(f"{n} 0-{max(len(e) for e in tables[section][p]) - 1}"
                        for n, p in sorted(CASTERS.items())))


def reconcile_casting_level(class_items: dict) -> None:
    """Make class_data.json's `casting level` agree with the pack's own casting block.

    Two of the six were wrong, both in ways that matter: the kineticist was `mid` although it has
    no `casting` block at all (burn is a Constitution-priced resource, which is exactly what
    data.py:288 says the caster map cannot express), and the medium was `mid` where pf1 says `low`.
    A wrong value here is not cosmetic -- spells.py branches on it, so `mid` would have handed the
    kineticist a spellbook and the medium two spell levels it never gets.
    """
    data = json.loads(CLASS_DATA.read_text(encoding="utf-8"))
    changed = []
    for name, item_name in sorted(CLASS_ITEM.items()):
        casting = class_items[item_name]["system"].get("casting") or {}
        # pf1 spells the middle tier "med"; every consumer in this repo -- spells.py's branches,
        # level_and_bab's _CASTER_TIER_RANK, class_data.json's other 15 mid casters -- says "mid".
        want = {"med": "mid"}.get(casting.get("progression"), casting.get("progression") or "none")
        if data[name].get("casting level") != want:
            changed.append(f"{name} {data[name].get('casting level')!r} -> {want!r}")
            data[name]["casting level"] = want
    if changed:
        CLASS_DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  casting level: {', '.join(changed) if changed else 'all six already agree'}")


def documents(raw: dict, pack: str) -> list:
    """The pack's real documents. Folders share the keyspace as !folders!<id>."""
    return [entry["doc"] for entry in raw[pack] if not entry["key"].startswith("!folders")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--system-root", default=str(DEFAULT_SYSTEM_ROOT),
                        help="the installed pf1 system directory")
    parser.add_argument("--module-root", default=str(DEFAULT_MODULE_ROOT),
                        help="the installed pf-content module directory")
    parser.add_argument("--classic-level", default=None,
                        help="directory of an installed classic-level package")
    args = parser.parse_args()

    classic_level = find_classic_level(args.classic_level)
    print(f"classic-level: {classic_level}")
    raw = dump(Path(args.system_root), Path(args.module_root), classic_level)

    class_items = {d["name"]: d for d in documents(raw, "classes") if d["type"] == "class"}
    abilities = [d for pack in ABILITY_PACKS for d in documents(raw, pack)]

    for name in sorted(BUCKETS):
        item_name = CLASS_ITEM[name]
        class_item = class_items.get(item_name)
        if class_item is None:
            sys.exit(f"no class Item named {item_name!r} in pf1.classes -- the census is stale")

        granted = {a["uuid"].rsplit(".", 1)[-1]
                   for a in (class_item["system"].get("links") or {}).get("classAssociations", [])}
        pool = [d for d in abilities
                if item_name in ((d["system"].get("associations") or {}).get("classes") or [])
                and d["_id"] not in granted]

        sections = {}
        for dataset, rule in BUCKETS[name].items():
            picked = {}
            for doc in pool:
                text = plain((doc["system"].get("description") or {}).get("value") or "",
                             doc["system"].get("tags") or ())
                if rule(doc, text.lower()):
                    picked[doc["name"]] = text
            if not picked:
                sys.exit(f"{name}/{dataset} came back EMPTY -- the pack changed shape, "
                         f"fix the rule in BUCKETS rather than shipping a hollow class")
            sections[dataset] = dict(sorted(picked.items()))

        path = CLASS_DIR / f"{name}.json"
        path.write_text(json.dumps(sections, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        counts = ", ".join(f"{k} {len(v)}" for k, v in sections.items())
        print(f"  wrote {path.relative_to(ROOT)}  ({len(pool)} selectable) -> {counts}")

    reconcile_casting_level(class_items)
    write_spell_tables(caster_tables(Path(args.system_root)))

    print("\nnow run Backend/scripts/gates/validate_occult_data.py, then test_house_invariants.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
