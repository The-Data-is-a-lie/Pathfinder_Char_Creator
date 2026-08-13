"""Every item the generator can roll must resolve to a FoundryVTT name (map: optimal-builder).

    C:/Python310/python.exe Backend/scripts/gates/validate_item_names.py

WHY THIS GATE EXISTS
--------------------
This directory exists because of one repeated failure: a curated name that matches nothing, which
crashes nothing and fails no test. This gate is here because of the worst instance the stack has
had.

`item_chooser` rolls a slot from `items_best.json`, normalises the name, and tests it against
`foundry_item_names.json`. The normaliser was `capitalize_first_letter_each_word`, so
"belt of mighty constitution +4" went in as "Belt **Of** Mighty Constitution +4". The name list
stores `of` lowercase. **1,888 of the 6,035 names contain " of " and not one survived the
round-trip** -- the entire wondrous-item catalogue, which in PF1e is the entire gear half of a
high-level sheet: Ring of Protection, Amulet of Natural Armor, Cloak of Resistance, every stat belt
and headband.

The retry loop swallowed it. It re-rolled the rejects until something resolved, so the generator
never errored, never warned above a summary line, and shipped to Render and Foundry for as long as
the normaliser existed. The measured cost at level 20 was that **88x the gold bought +4 AC and
nothing else**, with hit points, saves and damage byte-identical across 300x wealth -- and a
power baseline that read the resulting weakness as "generated characters fall behind the CR curve".

A one-line change to a name normaliser must never be able to blank a third of the catalogue in
silence again. Hence a floor, asserted against two independent artifacts: the roll pool
(`items_best.json`) and the name list (`foundry_item_names.json`).

WHY THE CEILING IS ~20% AND NOT ~0
----------------------------------
After the resolver fix, ~17% of the pool STILL does not resolve -- and that residue is genuinely
absent from the name list under any spelling (homebrew and setting-specific pieces: belt of
trelmarixian, coven charm, vest of endure elements...). Cleaning that up is a data job, ticketed on
the optimal-builder map (Daniel's ruling, 2026-08-11: honest ceiling + cleanup ticket, not silent
scope growth). An absolute-zero ceiling would go red on unrelated data edits and get ignored, which
is how a gate dies. This ceiling is set just above the measured residue so DRIFT is what trips it:
a normaliser regression takes the rate off a cliff (the old Title-Case strands ~67% of the pool),
and even a modest data regression crosses 20%. Lower it as the cleanup lands; raise it only with
the reason in the commit message.
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import JSON_DIR, Report                                              # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.class_func.item_and_price import (ItemNameResolver,                     # noqa: E402
                                             capitalize_first_letter_each_word,
                                             convert_price)

REPORT = Report('validate_item_names')

# The share of the roll pool allowed not to resolve. Measured residue after the resolver fix is
# ~17% (genuinely-absent names, see the docstring); the broken normaliser put the rate at ~67%.
UNRESOLVED_CEILING = 0.20

# Items whose absence is not a cosmetic gap but a hole in the character's defence or offence. PF1e
# expects a level-appropriate character to carry these; if the pool cannot produce them, the
# generator cannot build a character that survives its own CR. Named individually because a rate
# floor alone would happily pass while every one of them was unreachable -- which is precisely what
# happened.
BIG_SIX = (
    'ring of protection +1',
    'amulet of natural armor +1',
    'cloak of resistance +1',
    'belt of giant strength +2',
    'headband of vast intelligence +2',
    'belt of mighty constitution +2',
)


def load(name):
    return json.loads((JSON_DIR / name).read_text(encoding='utf-8'))


def foundry_names():
    """foundry_item_names.json is a plain LIST of names; tolerate a dict for symmetry with the
    resolver, which accepts both."""
    raw = load('foundry_item_names.json')
    return list(raw.keys()) if isinstance(raw, dict) else list(raw)


def roll_pool():
    """[(slot, raw name)] -- every item item_chooser can draw, exactly as it draws them."""
    return [(slot, name) for slot, entries in load('items_best.json').items()
            for name in entries]


def check_resolution(pool, names, resolver):
    """The roll pool resolves against the name list at or above the floor."""
    lookup = set(names)
    unresolved = [(slot, name) for slot, name in pool
                  if resolver.resolve(name) not in lookup]
    rate = len(unresolved) / len(pool) if pool else 1.0
    ok = REPORT.check(
        rate <= UNRESOLVED_CEILING,
        f"{len(unresolved)} of {len(pool)} rollable items ({rate:.1%}) do not resolve against "
        f"foundry_item_names.json, over the {UNRESOLVED_CEILING:.0%} ceiling. The generator "
        f"silently re-rolls every one of them, so this does not crash -- it just quietly shrinks "
        f"the catalogue. First 10: {[f'{s}/{n}' for s, n in unresolved[:10]]}")
    if ok and unresolved:
        REPORT.warn(f"{len(unresolved)} of {len(pool)} rollable items ({rate:.1%}) are absent from "
                    f"foundry_item_names.json and are re-rolled (ticketed data gap): "
                    f"{[f'{s}/{n}' for s, n in unresolved[:5]]}")
    return len(unresolved)


def check_big_six(names, resolver):
    """The items a level-appropriate PF1e character is built around are actually reachable."""
    lowered = {str(n).strip().lower() for n in names}
    lookup = set(names)
    for probe in BIG_SIX:
        present = probe in lowered
        if not REPORT.check(present,
                            f"{probe!r} is not in foundry_item_names.json at all -- the roll pool "
                            f"cannot produce it, so no generated character can carry one"):
            continue
        REPORT.check(resolver.resolve(probe) in lookup,
                     f"{probe!r} is in foundry_item_names.json but does not survive name "
                     f"resolution, so item_chooser rejects and re-rolls it. This is the casing "
                     f"defect returning; see item_and_price.ItemNameResolver")


def check_duplicate_casings(names):
    """Names that exist twice differing only in casing are surfaced, not silently deduped.

    Eight such pairs exist today ("Signal Horn" / "Signal horn"). The resolver sorts before
    first-wins so production is at least DETERMINISTIC about which spelling FoundryVTT receives --
    but only one of the pair can be the one Foundry's compendium actually knows, so each pair is a
    coin that has been forced to land the same way every time rather than a coin removed. The fix
    is deleting the wrong spelling from the data; until then this WARN is the reminder.
    """
    counts = Counter(str(n).strip().lower() for n in names)
    dupes = sorted(key for key, n in counts.items() if n > 1)
    if dupes:
        REPORT.warn(f"{len(dupes)} name(s) appear more than once in foundry_item_names.json "
                    f"differing only in casing; the resolver picks the sorted-first spelling "
                    f"deterministically, but the losing spellings are dead data: {dupes[:10]}")
    return len(dupes)


_BLOB_NUMBER = __import__('re').compile(r'\d{1,3}(?:,\d{3})+|\d+')

# The share of the pool allowed to be unpriceable (convert_price -> None -> the slot skips it).
# Measured after the pricing fix; a rise means price blobs stopped parsing.
UNPRICEABLE_CEILING = 0.05


def check_prices():
    """Every rollable item prices to a sane number -- the anti-windfall gate.

    The casing bug and the pricing bug masked each other: while "+N" names could not be rolled,
    nobody noticed that when they WERE rolled they cost nothing (find_number was handed a list) or
    pennies (the word regex's empty alternative made find_word capture the '000' of '12,000').
    The moment name resolution was fixed, a golden bought Ring of Protection +5 for 0 gp. So this
    check prices the ENTIRE pool the way item_chooser would and asserts two things per item: a
    parsed price is positive, and it is never under 1% of the largest number in its own price
    blob -- which is exactly the shape both windfalls had.
    """
    pool = load('items_best.json')
    total = unpriceable = 0
    for slot, entries in pool.items():
        for name, spec in entries.items():
            total += 1
            blob = str((spec or {}).get('price'))
            price = convert_price(None, blob, name)
            if price is None:
                unpriceable += 1
                continue
            if not REPORT.check(price > 0,
                                f"{slot}/{name}: priced at {price!r} from {blob!r} -- a zero or "
                                f"negative price is the free-item windfall returning"):
                continue
            numbers = [int(m.replace(',', '')) for m in _BLOB_NUMBER.findall(blob)]
            biggest = max(numbers) if numbers else 0
            REPORT.check(biggest < 1000 or price * 100 >= biggest,
                         f"{slot}/{name}: priced at {price} but its own price text carries "
                         f"{biggest:,} -- a partial-digit capture ('12' from '12,000'), not a "
                         f"real variant price")
    rate = unpriceable / total if total else 1.0
    REPORT.check(rate <= UNPRICEABLE_CEILING,
                 f"{unpriceable} of {total} rollable items ({rate:.1%}) cannot be priced at all "
                 f"and are silently skipped, over the {UNPRICEABLE_CEILING:.0%} ceiling")

    # The named witness: the exact item the windfall was caught on, at its exact PF price.
    rings = pool.get('rings') or {}
    probe = next((n for n in rings if str(n).strip().lower() == 'ring of protection +5'), None)
    if probe is not None:
        got = convert_price(None, str(rings[probe].get('price')), probe)
        REPORT.check(got == 50000,
                     f"'ring of protection +5' prices at {got!r}, not 50,000 -- the +N variant "
                     f"extraction has regressed (it bought this ring for 0 once already)")
    return total, unpriceable


def check_normaliser_would_fail(pool, names):
    """The old Title-Case normaliser must still be demonstrably worse than the current one.

    A gate that has never failed has never been tested. Rather than trust that, this re-runs the
    pool through the normaliser the fix REPLACED and asserts it blows the ceiling -- so if someone
    reverts to Title-Casing, or the two paths quietly converge into being the same thing again,
    this check is the one that says so. (If the item data were ever cleaned so thoroughly that
    Title-Case genuinely worked, this would false-fail -- today it strands ~67% of the pool against
    a 20% ceiling, so that day is far away, and reaching it would deserve a human look anyway.)
    """
    lookup = set(names)
    broken = sum(1 for _slot, name in pool
                 if capitalize_first_letter_each_word(name) not in lookup)
    rate = broken / len(pool) if pool else 0.0
    REPORT.check(
        rate > UNRESOLVED_CEILING,
        f"the pre-fix Title-Case normaliser now resolves {1 - rate:.1%} of the pool, which means "
        f"this gate can no longer tell the two apart and has stopped witnessing anything. Either "
        f"the name data changed shape or the fix was reverted into a no-op -- check "
        f"item_and_price.ItemNameResolver before relaxing this")
    return rate


def main():
    names = foundry_names()
    pool = roll_pool()
    if not REPORT.check(bool(names), 'foundry_item_names.json is empty') or \
       not REPORT.check(bool(pool), 'items_best.json holds no rollable items'):
        return REPORT.finish()

    resolver = ItemNameResolver(names)
    unresolved = check_resolution(pool, names, resolver)
    check_big_six(names, resolver)
    dupes = check_duplicate_casings(names)
    broken_rate = check_normaliser_would_fail(pool, names)
    priced_total, unpriceable = check_prices()

    return REPORT.finish(f'{len(pool)} rollable items over {len(set(s for s, _ in pool))} slots, '
                         f'{len(names)} FoundryVTT names, {unresolved} unresolved '
                         f'({unresolved / len(pool):.1%}), {unpriceable} unpriceable '
                         f'({unpriceable / priced_total:.1%}), {dupes} duplicate casings; the '
                         f'pre-fix normaliser would strand {broken_rate:.0%}')


if __name__ == '__main__':
    sys.exit(main())
