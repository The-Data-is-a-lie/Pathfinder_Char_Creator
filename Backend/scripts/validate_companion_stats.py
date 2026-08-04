"""Gate the companion stat block: the advancement merge, and who owns the size increase.

    C:\\Python310\\python.exe Backend/scripts/validate_companion_stats.py
    C:\\Python310\\python.exe Backend/scripts/validate_companion_stats.py --verbose

Map #18, slice G (#31) and ticket 04. Ticket 04's ruling is a two-line rule with a wide blast
radius, and CLAUDE.md is explicit that a hard convention belongs in a validator rather than only in
a sentence -- a stale `critical: "onCrit"` in a doc silently broke six weapons until `MOD_CRITICAL`
caught it. This is that whitelist for the size package.

THE RULING IT ENFORCES
----------------------
The published per-species advancement deltas ALREADY contain the PF1e size-change package. The proof
is in the data: a Dex PENALTY appears only on size-increasing rows, and 149 of the 153 such rows
carry exactly the table's -2, while advancement blocks that do not change size never go negative at
all. So the split is:

  * the deltas own the STAT half  -- `str`/`dex`/`con` and natural armour apply verbatim;
  * `SIZE_GEOMETRY` owns the GEOMETRY -- AC, attack, CMB/CMD, Stealth and space, which appear
    nowhere in `animal_choices.json`.

Both halves are checked here, and both checks have teeth:

1. NO DOUBLE-COUNT. For every size-increasing species, the merged scores must equal starting +
   published delta. 35 of the 153 rows disagree with the size table on at least one of str/dex/con,
   so a merge that quietly "corrected" them to the table -- or added the table on top -- fails here
   rather than shipping a companion inflated by up to +8 Str. The count of teeth-bearing rows is
   asserted too: if a data change ever made every row agree with the table, this check would go
   quiet without saying so.
2. THE GEOMETRY IS APPLIED EXACTLY ONCE. Every derived number is recomputed from parts read straight
   out of the JSON and compared. Applying the size modifier twice, or not at all, fails.
3. `size_change` IS PROVENANCE, NOT AN INSTRUCTION. Its values must equal the difference between two
   `SIZE_GEOMETRY` rows, and it must be absent when the creature never grew -- a renderer that
   re-applies it would double-count the half we DO own.
4. THE MERGE LOSES NOTHING. `species_stats` on an entry stays RAW, because the frozen
   `animal_companion` alias reads the same object (D9), so `stats` is the only place the merge's
   output survives. Every merged key must be either consumed by a named stat field or carried in
   `stats.other` -- otherwise a one-off ability nobody enumerated (`sudden charge (ex)`, `cmd trip`)
   would vanish between the two.
5. THE ATTACK PARSER IS MEASURED, NOT TRUSTED. Attack routines are prose. Exactly one line in the
   file legitimately has no damage die; the count is asserted, so a parser regression cannot hide
   behind "it still runs".

Everything imports from `utils.class_func.companion_stats`; nothing is restated. Done when: exit 0
on the current data, non-zero if the merge, the geometry table or the ruling moves.
"""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "Backend"))
sys.path.insert(0, str(HERE))

from utils.class_func.companion_stats import (                       # noqa: E402
    ADV_RE, CONSUMED, SIZE_GEOMETRY, START_RE, TIER_HIT_DIE, DEFAULT_HIT_DIE,
    _mod, _natural_armor, _signed, companion_stats, merge_advancement)
from validate_companion_data import SIZE_CHANGE_TABLE                # noqa: E402

SPECIES = ROOT / "Backend/json/animal_choices.json"
CHASSIS = ROOT / "Backend/json/animal_companion.json"

# Homebrew ON, because that is what the generator defaults to and it makes HP deterministic (a
# maximised die at every HD). With it off, `_hit_points` rolls and nothing here could be pinned.
MASTER = SimpleNamespace(homebrew_feat_amount="Y")

# The teeth of check 1, measured on the current data. If a repair or a rescrape ever moved every
# published delta onto the table, the no-double-count check would still pass while proving nothing;
# this number is what makes that silence audible.
MIN_ROWS_DISAGREEING_WITH_TABLE = 30

# Attack routines are prose, so the parser is measured rather than trusted. Exactly one line in the
# whole file legitimately has no damage die -- the octopus's `tentacles (grab)`, which is a grapple,
# not a hit. Everything else parses, including the eight routines with commas inside parentheses,
# the four written without parentheses at all, and the axe beak's spelled-out `+ 1-1/2 str`. If this
# number climbs, the parser lost a shape; if it drops to 0, the octopus changed and the allowance
# should go with it.
MAX_ATTACKS_WITHOUT_DAMAGE = 1

errors = []
notes = []


def fail(message):
    errors.append(message)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def blocks(body):
    """(starting statistics, [(trigger level, advancement block)]) for one species body."""
    start = next((v for k, v in body.items()
                  if START_RE.match(str(k)) and isinstance(v, dict)), None)
    advancements = []
    for key, value in body.items():
        match = ADV_RE.match(str(key))
        if match and isinstance(value, dict):
            advancements.append((int(match.group(1)), value))
    return start, sorted(advancements)


def check_no_double_count(where, start, advancement, merged):
    """The merged score is starting + the PUBLISHED delta. Never the table, never both."""
    teeth = 0
    start_scores = start.get("ability scores") or {}
    deltas = (advancement.get("ability scores") or {})
    table = SIZE_CHANGE_TABLE.get(str(advancement.get("size", "")).strip().lower()) or {}
    for stat in ("str", "dex", "con"):
        base = start_scores.get(stat)
        if base is None:
            continue
        delta = _signed(deltas.get(stat)) or 0
        want = int(base) + delta
        got = (merged.get("ability scores") or {}).get(stat)
        if got != want:
            fail(f"{where}: {stat} merged to {got!r}, expected {want} "
                 f"(starting {base} + published {delta:+d}). The published entry is the authority; "
                 f"the size table must not be added, substituted or stripped.")
        if table and delta != table.get(stat, 0):
            teeth += 1
    return teeth


def check_natural_armor(where, start, advancement, merged):
    want = _natural_armor(start.get("ac")) + _natural_armor(advancement.get("ac"))
    got = _natural_armor(merged.get("ac"))
    if got != want:
        fail(f"{where}: natural armour merged to {got:+d}, expected {want:+d} "
             f"(the advancement's `ac` ADDS to the starting one -- see the spec's merge rules)")


def check_replace_and_append(where, start, advancement, merged):
    for field in ("size", "attack", "speed"):
        if field in advancement and merged.get(field) != advancement[field]:
            fail(f"{where}: {field!r} is a REPLACE field but merged to {merged.get(field)!r} "
                 f"instead of {advancement[field]!r}")
        if field not in advancement and field in start and merged.get(field) != start[field]:
            fail(f"{where}: {field!r} is absent from the advancement block, so the starting "
                 f"value {start[field]!r} must survive; got {merged.get(field)!r}")
    for field in ("special qualities", "special attacks"):
        for source in (start, advancement):
            text = source.get(field)
            if text and str(text) not in str(merged.get(field) or ""):
                fail(f"{where}: {field!r} APPENDS, but {text!r} is missing from "
                     f"{merged.get(field)!r}")


def check_geometry(where, entry, stats, merged, chassis):
    """Every derived number, recomputed from parts. Applying size twice fails here."""
    size = str(merged.get("size") or "medium").strip().lower()
    geometry = SIZE_GEOMETRY.get(size)
    if geometry is None:
        fail(f"{where}: size {size!r} has no SIZE_GEOMETRY row")
        return
    if stats["size"] != size:
        fail(f"{where}: stats.size {stats['size']!r} != merged size {size!r}")
    if stats["space"] != geometry["space"]:
        fail(f"{where}: space {stats['space']} != {geometry['space']} for {size}")

    abilities = stats["abilities"]
    dex_mod = _mod(abilities.get("dex")) or 0
    str_mod = _mod(abilities.get("str")) or 0
    con_mod = _mod(abilities.get("con")) or 0
    natural = _natural_armor(merged.get("ac")) + int(chassis.get("natural armor bonus") or 0)
    bab = int(chassis.get("bab") or 0)

    expect = {
        "natural_armor": natural,
        "ac": 10 + geometry["ac"] + dex_mod + natural,
        "touch_ac": 10 + geometry["ac"] + dex_mod,
        "flat_footed_ac": 10 + geometry["ac"] + natural,
        "bab": bab,
        "cmb": bab + str_mod + geometry["special"],
        "cmd": 10 + bab + str_mod + dex_mod + geometry["special"],
    }
    for field, want in expect.items():
        if stats[field] != want:
            fail(f"{where}: {field} = {stats[field]}, expected {want} "
                 f"(size {size} contributes ac {geometry['ac']:+d}, cmb/cmd "
                 f"{geometry['special']:+d} -- exactly once)")

    saves = stats["saves"]
    for name, base, mod in (("fort", "fort", con_mod), ("ref", "ref", dex_mod),
                            ("will", "will", _mod(abilities.get("wis")) or 0)):
        want = int(chassis.get(base) or 0) + mod
        if saves[name] != want:
            fail(f"{where}: {name} save {saves[name]}, expected {want}")

    hd = int(chassis.get("hd") or 1)
    die = TIER_HIT_DIE.get(entry.get("kind"), DEFAULT_HIT_DIE)
    want_hp = max(1, hd * die + con_mod * hd)
    if stats["hp"] != want_hp:
        fail(f"{where}: hp {stats['hp']}, expected {want_hp} (house rule: a maximised d{die} at "
             f"every one of {hd} HD, plus Con {con_mod:+d} per HD)")

    for attack in stats["attacks"]:
        if attack["atk"] is not None and attack["atk"] != bab + str_mod + geometry["ac"]:
            fail(f"{where}: attack {attack['name']!r} at {attack['atk']:+d}, expected "
                 f"{bab + str_mod + geometry['ac']:+d} (BAB + Str + size, all natural attacks "
                 f"in a printed routine are primary)")
    if merged.get("attack") and not stats["attacks"]:
        fail(f"{where}: attack routine {merged['attack']!r} parsed to no attack lines")

    stealth = stats["skills"].get("stealth")
    if stealth and stealth["ranks"]:
        floor_value = stealth["ranks"] + dex_mod + 3 + geometry["stealth"]
        if stealth["total"] < floor_value:
            fail(f"{where}: stealth {stealth['total']} is below ranks + Dex + trained + size "
                 f"({floor_value}); the size modifier looks applied twice or not at all")


def check_size_change(where, stats, start, merged):
    was = str(start.get("size") or "").strip().lower()
    now = str(merged.get("size") or "").strip().lower()
    record = stats.get("size_change")
    if was == now or not was or not now:
        if record is not None:
            fail(f"{where}: size never changed ({was!r}) but size_change is {record!r}")
        return
    if record is None:
        fail(f"{where}: grew {was} -> {now} but size_change is None")
        return
    before, after = SIZE_GEOMETRY[was], SIZE_GEOMETRY[now]
    for field, want in (("ac", after["ac"] - before["ac"]),
                        ("attack", after["ac"] - before["ac"]),
                        ("cmb_cmd", after["special"] - before["special"]),
                        ("stealth", after["stealth"] - before["stealth"]),
                        ("space", after["space"])):
        if record[field] != want:
            fail(f"{where}: size_change.{field} = {record[field]}, expected {want} "
                 f"(the difference between the {was} and {now} rows of SIZE_GEOMETRY)")
    if "already applied" not in str(record.get("note", "")):
        fail(f"{where}: size_change.note must say the values are already in the block, or a "
             f"renderer will apply them a second time")


def check_lossless(where, stats, merged):
    """Nothing the merge produced may fall out between `merged` and the emitted block.

    `species_stats` on the entry stays RAW because the frozen `animal_companion` alias reads the same
    object (D9), so `stats` is the only place the merge's output survives. A species that invents a
    key nobody enumerated -- `sudden charge (ex)`, `cmd trip`, `bonus feat` -- would silently vanish
    if `stats.other` ever stopped being the catch-all.
    """
    other = stats.get('other')
    if not isinstance(other, dict):
        fail(f"{where}: stats.other is {type(other).__name__}, not a dict")
        return
    for key, value in merged.items():
        if key in CONSUMED or value in (None, '', {}, []):
            continue
        if key not in other:
            fail(f"{where}: merged key {key!r} is neither consumed by a named stat field nor "
                 f"carried in stats.other -- it would be dropped from the payload entirely")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true", help="print every species checked")
    args = parser.parse_args()

    species_data = load(SPECIES)
    chassis_table = load(CHASSIS)["companion"]

    checked = grew = teeth = 0
    undamaged = []
    for tier, bucket in species_data.items():
        for name, body in bucket.items():
            start, advancements = blocks(body)
            if start is None:
                fail(f"{tier}/{name}: no starting statistics block")
                continue
            # Level 1 (nothing merged) and one level at or above each trigger, which is the only
            # place the merge can go wrong.
            levels = [1] + [trigger for trigger, _ in advancements]
            for level in levels:
                chassis = chassis_table.get(str(level)) or chassis_table["1"]
                entry = {"species": name, "kind": tier, "effective_level": level,
                         "species_stats": body, "chassis": chassis}
                where = f"{tier}/{name} @ level {level}"
                stats = companion_stats(MASTER, entry)
                if stats is None:
                    fail(f"{where}: produced no stat block")
                    continue
                merged, _ = merge_advancement(body, level)
                checked += 1

                for trigger, advancement in advancements:
                    if level >= trigger:
                        teeth += check_no_double_count(where, start, advancement, merged)
                        check_natural_armor(where, start, advancement, merged)
                        check_replace_and_append(where, start, advancement, merged)
                check_geometry(where, entry, stats, merged, chassis)
                check_size_change(where, stats, start, merged)
                check_lossless(where, stats, merged)
                if level == 1:      # count each species once, not once per level checked
                    undamaged += [f"{tier}/{name}: {a['name']!r} in {merged.get('attack')!r}"
                                  for a in stats['attacks']
                                  if not a.get('alternative') and not a.get('damage')]
                if stats["hp"] < 1:
                    fail(f"{where}: hp {stats['hp']}")
                if str(start.get("size", "")).strip().lower() != \
                        str(merged.get("size", "")).strip().lower():
                    grew += 1
                if args.verbose:
                    print(f"  {where}: {stats['size']} hp {stats['hp']} ac {stats['ac']} "
                          f"cmb {stats['cmb']}/cmd {stats['cmd']}")

    if len(undamaged) > MAX_ATTACKS_WITHOUT_DAMAGE:
        fail(f"{len(undamaged)} attack line(s) parsed with no damage, above the allowance of "
             f"{MAX_ATTACKS_WITHOUT_DAMAGE} -- the routine parser lost a shape:\n    " +
             "\n    ".join(undamaged[:10]))
    notes.append(f"{len(undamaged)} attack line(s) legitimately carry no damage die")

    if teeth < MIN_ROWS_DISAGREEING_WITH_TABLE:
        fail(f"only {teeth} published delta(s) disagree with the size-change table, below the "
             f"{MIN_ROWS_DISAGREEING_WITH_TABLE} this file was written against. The no-double-count "
             f"check is only meaningful because the two sources DIFFER -- if the data really did "
             f"move onto the table, lower the constant deliberately and say why.")

    print(f"stat blocks checked: {checked} across {len(species_data)} tiers "
          f"({grew} with a size increase, {teeth} published deltas that differ from the size table)")
    for note in notes:
        print(f"  note: {note}")
    if errors:
        print(f"\nFAILED -- {len(errors)} problems")
        for message in errors[:25]:
            print(f"  {message}")
        if len(errors) > 25:
            print(f"  ... and {len(errors) - 25} more")
        return 1
    print("PASS -- the size package is counted exactly once and the merge follows the spec")
    return 0


if __name__ == "__main__":
    sys.exit(main())
