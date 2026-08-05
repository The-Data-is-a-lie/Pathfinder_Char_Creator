"""Gate for the per-level progression tables -- their CONTENTS, not their wiring.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_progression_tables.py

Four subsystems store "what you get at class level N" as an array and read it the same way:

    spells.py:105, :372        spells_known / spells_per_day   [capped_level - 1]
    psionics.py:136, :333      psionic_powers_known            [min(level, 20) - 1]
    path_of_war.py:186         path_of_war_maneuvers_known     [min(capped_level, 20) - 1]

`validate_caster_data.py` already checks that a declared caster HAS a row. Nothing checked what
was in it. The tables are webscraped, ~330 columns across four files, and a single shifted cell is
invisible: it does not raise, it does not fail a golden fixture unless that exact class and level
happen to be seeded, and on a Foundry sheet it looks like a character who simply has one fewer
spell slot than they should.

WHAT THIS ENFORCES, and why each rule is here rather than in a comment
---------------------------------------------------------------------
1. **Length is 20 or 21, never anything else.** `capped_level = min(lvl, 20)`
   (`level_and_bab.py:53`), so the largest index any reader can produce is 19. Every array in the
   repo turns out to be exactly 20 or 21 long: the scrape emits levels 1-21, and the 21st row is a
   level a 20-level class cannot reach. So a 21-int spell array is NOT a different indexing
   convention from a 20-int psionics/PoW array -- both are read at `level - 1` and both stop being
   read at level 20. `docs/CODEBASE_MAP.md` claimed the 21-vs-20 split was a real convention until
   this gate was written; it is an artifact of which scraper produced the file.

   The unreachable 21st row is deliberately NOT compared against the 20th. A progression still
   climbing at level 20 legitimately differs there -- a wizard's 9th-level spells known run
   2/4/6/8 at levels 17-20 and 10 at the level 21 that does not exist.

2. **Blank prefix, then values.** A blank after a real number means a caster loses access to a
   spell level by gaining one. Always a scrape artifact.

3. **Non-decreasing down the levels.** Same reason, one level weaker.

4. **Non-inverting across spell levels** (spells_per_day only). At any class level, a higher spell
   level never grants MORE slots than a lower one -- no PF1e caster has more 6th-level slots than
   5th-level ones. Does not hold for spells_known, where prepared casters store a learn-2-per-level
   count rather than a slot count, so it is applied only where it is true.

5. **The unlock level agrees with `caster_formula`.** The level at which spell level N first appears
   in the DATA must equal the level at which `spells.caster_formula` first says N is castable in the
   CODE. The two are independent expressions of one published table, so a shifted column shows up as
   a disagreement rather than as a number nobody recomputes. The rule's owner is imported and run,
   never restated -- the same idiom as `validate_caster_data.alias_of`.

Both of the first run's findings are now fixed, and neither rule carries an exemption any more:
rule 5's four spontaneous casters and `adept` are modelled in `spells.caster_formula`, and rule 4's
magus column was corrected against Archive of Nethys.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _harness import JSON_DIR, Report, read_json              # noqa: E402

from utils.class_func import spells as _spells                # noqa: E402

REPORT = Report('validate_progression_tables')

CLASS_DATA = JSON_DIR / 'class_data.json'
SPELL_TABLES = {
    'spells_per_day.json': JSON_DIR / 'spells_per_day.json',
    'spells_known.json': JSON_DIR / 'spells_known.json',
}
PSIONIC_TABLE = JSON_DIR / 'class_data' / 'psionics' / 'psionic_powers_known.json'
POW_TABLE = JSON_DIR / 'class_data' / 'path_of_war' / 'path_of_war_maneuvers_known.json'

# The highest class level any reader can index. Not 20-because-Pathfinder: because every reader
# clamps with min(..., 20) before subtracting 1. If that clamp ever changes, this changes with it.
MAX_LEVEL = 20

# How a table spells "this level is not available yet". The scrape emits the STRING 'null', not
# JSON null, so `is None` would silently treat every gap as a real value.
BLANK = ('null', None, '', '-')

# spells_known.json stores this instead of an array for a class that knows its ENTIRE list rather
# than a fixed number of spells -- every prepared caster, plus the spontaneous divine classes whose
# "known" is their mystery/domain list. It is a sentinel, not a progression, and `spells_known_attr`
# branches on it. Ten classes use it.
KNOWS_EVERYTHING = ['all']

# The tiers `caster_formula` branches on. A class declaring anything else falls through to its
# non-caster else-branch, where there is no unlock schedule for rule 5 to compare against.
TIERS = ('low', 'mid', 'high')

# KNOWN_MISALIGNED is GONE, and deliberately not replaced with an empty dict. It held the four
# spontaneous full casters and `adept`; `spells.caster_formula` now models both progressions
# (SPONTANEOUS_FULL_CASTERS and the adept ladder), so all 30 classes line up and there is nothing
# left to excuse. An exemption block that survives the bug it excused is how "temporary" becomes
# documentation -- deleting it is what closes the ticket.

# KNOWN_INVERTED is gone too. It held `magus`, whose 5th-level spells-per-day column granted 4 slots
# at level 20 while its 6th-level column granted 5 -- which no PF1e caster does. Checked against
# Archive of Nethys: the published row is 1/2/3/3/4/4/5/5 at class levels 13-20, and the scrape had
# 1/2/3/3/4/4/4/4 with the 5 pushed onto the unreachable 21st row. An extra 4 inserted at level 19
# ran the tail one row late. Fixed in spells_per_day.json (two cells), so there is nothing to excuse.
#
# STILL OPEN, deliberately not fixed here: the same AoN table says the magus **4th-level** column
# should read 3 at class level 12 and 5 at 18, where the scrape has 2 and 4 -- the same off-by-one,
# in a column no structural rule catches, because it never inverts against its neighbours. It is not
# patched blind: the evidence is one LLM-extracted table, and hand-editing game data on that basis is
# how a silent wrong-character bug gets introduced while fixing another. It needs a re-scrape of the
# magus table against the source, which is its own ticket.


def _is_blank(cell):
    return cell in BLANK


def unlock_levels(class_name, tier):
    """{spell level: the class level at which it first becomes castable} for ONE class, computed by
    running `caster_formula` rather than by restating the progressions here.

    Keyed by class rather than by tier since the spontaneous/adept fix: two classes can share a tier
    and unlock on different schedules, so a per-tier answer can no longer be right for both. The
    class NAME is passed through because that is what `caster_formula` branches on.

    caster_formula reads only `n` and `class_entry`, so the character argument is unused -- passing
    None keeps this from needing a stub that would drift.
    """
    first = {}
    for level in range(1, MAX_LEVEL + 1):
        highest = _spells.caster_formula(None, level, {'casting_level_string': tier,
                                                       'level': level,
                                                       'name': class_name})
        for spell_level in range(1, highest + 1):
            first.setdefault(spell_level, level)
    return first


def check_column(owner, values):
    """Rules 1-4 -- the ones that hold for every progression array in the repo regardless of what
    it counts. Returns False once it has reported a structural problem, so the caller stops making
    claims about an array it has already proved malformed."""
    if not isinstance(values, list):
        return REPORT.error(f'{owner}: expected a list, got {type(values).__name__}')

    if not REPORT.check(len(values) in (MAX_LEVEL, MAX_LEVEL + 1),
                        f'{owner}: {len(values)} entries. Readers index up to [{MAX_LEVEL - 1}], '
                        f'and every table in the repo is {MAX_LEVEL} rows (levels 1-{MAX_LEVEL}) or '
                        f'{MAX_LEVEL + 1} (with an unreachable level-{MAX_LEVEL + 1} row). A '
                        f'different length means the scrape shifted or truncated the column'):
        return False

    live = values[:MAX_LEVEL]
    seen_value = False
    for level, cell in enumerate(live, start=1):
        if _is_blank(cell):
            if not REPORT.check(not seen_value,
                                f'{owner}: level {level} is blank after level {level - 1} had a '
                                f'value -- a progression cannot un-grant what it granted'):
                return False
        else:
            seen_value = True

    numbers = [(level, cell) for level, cell in enumerate(live, start=1) if not _is_blank(cell)]
    for (prev_level, prev), (level, cell) in zip(numbers, numbers[1:]):
        if not isinstance(prev, int) or not isinstance(cell, int):
            return REPORT.error(f'{owner}: level {level} is {cell!r}, which is neither a number '
                                f'nor one of the blanks {BLANK}')
        REPORT.check(cell >= prev,
                     f'{owner}: drops from {prev} at level {prev_level} to {cell} at level {level}')
    return True


def first_value_level(values):
    """The class level at which a column stops being blank, or None if it never does."""
    return next((level for level, cell in enumerate(values[:MAX_LEVEL], start=1)
                 if not _is_blank(cell)), None)


def check_no_inversion(filename, class_name, columns):
    """Rule 4: at a given class level, spell level N+1 never grants more slots than N.

    Spell level 0 is excluded -- the prepared casters store an all-zero cantrip row, which would
    invert against every real column and drown the check in 559 findings that mean nothing.
    Returns True when the class is clean.
    """
    levels = sorted((int(key) for key in columns if int(key) > 0), reverse=True)
    clean = True
    for class_level in range(1, MAX_LEVEL + 1):
        for higher, lower in zip(levels, levels[1:]):
            top, below = columns[str(higher)][class_level - 1], columns[str(lower)][class_level - 1]
            if _is_blank(top) or _is_blank(below) or top <= below:
                continue
            clean = False
            REPORT.error(
                f'{filename}[{class_name}]: at class level {class_level}, spell level {higher} '
                f'grants {top} but spell level {lower} grants only {below} -- a caster never '
                f'has more high-level slots than low-level ones, so one column is shifted')
    return clean


def check_spell_tables():
    """Rules 1-3 over every spell column, rule 4 over the per-day tables, and rule 5 wherever a
    tier exists to check against.

    Returns two {class name: is it clean} maps; `main` uses the second to prove KNOWN_INVERTED is
    neither short nor stale, and reports the first as a count.
    """
    class_data = read_json(CLASS_DATA)
    aligned, uninverted = {}, {}
    checked = 0
    for filename, path in SPELL_TABLES.items():
        for class_name, columns in sorted(read_json(path).items()):
            # Rule 4 reads across columns, so it runs once per class rather than per column, and
            # only on the per-day tables -- see the rule's docstring for why not spells_known.
            if filename == 'spells_per_day.json' and columns.get('0') != KNOWS_EVERYTHING:
                uninverted[class_name] = check_no_inversion(filename, class_name, columns)
            tier = (class_data.get(class_name) or {}).get('casting level')
            for key, values in sorted(columns.items()):
                owner = f'{filename}[{class_name}][{key}]'

                if values == KNOWS_EVERYTHING:
                    continue          # the sentinel, not a progression -- see KNOWS_EVERYTHING
                checked += 1
                if not check_column(owner, values):
                    continue

                # Cantrips/orisons are exempt from rule 5: level 0 is not something caster_formula
                # ever returns, and the prepared casters store an all-zero row for it.
                if key == '0' or tier not in TIERS:
                    continue

                # Per CLASS, not per tier: since caster_formula learned the spontaneous and adept
                # progressions, two classes sharing a tier can unlock on different schedules.
                expected = unlock_levels(class_name, tier).get(int(key))
                first = first_value_level(values)
                lines_up = (first is None) if expected is None else (first == expected)
                aligned[class_name] = aligned.get(class_name, True) and lines_up
                if lines_up:
                    continue
                if expected is None:
                    REPORT.error(f'{owner}: has values from level {first}, but caster_formula says '
                                 f'a {tier!r} caster never reaches spell level {key}')
                else:
                    REPORT.error(f'{owner}: first value at class level {first}, but caster_formula '
                                 f'unlocks spell level {key} for a {tier!r} caster at level '
                                 f'{expected} -- the column is shifted by {(first or 0) - expected}')
    return checked, aligned, uninverted


def check_point_tables():
    """psionics and Path of War: same array contract, no caster_formula equivalent to cross-check
    against, so rules 1-4 only. The metzofitz entries nest one level deeper than the base ones
    (`rajah` splits into `manuevers` and `akasha`), so the walk recurses rather than assuming depth.
    """
    checked = 0

    def walk(owner, node):
        nonlocal checked
        if isinstance(node, list):
            checked += 1
            check_column(owner, node)
        elif isinstance(node, dict):
            for key, child in sorted(node.items()):
                walk(f'{owner}[{key}]', child)
        else:
            REPORT.error(f'{owner}: expected a table or an array, got {type(node).__name__}')

    walk('psionic_powers_known', read_json(PSIONIC_TABLE))
    walk('path_of_war_maneuvers_known', read_json(POW_TABLE))
    return checked


def main():
    # Anchor the formula before measuring anything against it. A prepared 'high' caster reaches 9th
    # at 17 and a 'mid' caster 6th at 16; a spontaneous one reaches 9th at 18. If those move, every
    # unlock check below is silently redefined rather than failing.
    wizard = unlock_levels('wizard', 'high')
    sorcerer = unlock_levels('sorcerer', 'high')
    bard = unlock_levels('bard', 'mid')
    adept = unlock_levels('adept', 'mid')
    REPORT.check(wizard.get(9) == 17 and bard.get(6) == 16 and sorcerer.get(9) == 18
                 and adept.get(5) == 16 and adept.get(6) is None,
                 f'caster_formula no longer unlocks the reference levels (prepared 9th@17, '
                 f'mid 6th@16, spontaneous 9th@18, adept 5th@16 and no 6th) -- every unlock check '
                 f'below is measured against it, so a change there silently redefines what this '
                 f'gate proves: wizard={wizard} sorcerer={sorcerer} adept={adept}')

    columns, aligned, uninverted = check_spell_tables()
    columns += check_point_tables()

    # Both exemption blocks are gone -- see the notes where they used to be. The ratchet they
    # implemented (an allowance that stops being needed must be DELETED, or the next reader believes
    # a fixed bug is still open) did its job: it is what made retiring them a required step rather
    # than an optional tidy-up.

    return REPORT.finish(
        f'{columns} progression columns -- every one 20 or 21 rows, gap-free and non-decreasing; '
        f'{sum(aligned.values())}/{len(aligned)} classes aligned with caster_formula, '
        f'{sum(uninverted.values())}/{len(uninverted)} per-day tables free of slot inversion')


if __name__ == '__main__':
    raise SystemExit(main())
