"""Gate the gear-legality CONFIG layer: the derived proficiency table.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_gear_legality.py
    C:\\Python310\\python.exe Backend/scripts/gates/validate_gear_legality.py --print

WHY THIS EXISTS
---------------
`data.armor_type_mapping` was a hand-authored class->band map with nothing checking it, and it was
wrong in a way nobody noticed for the life of the repo: its keys were tuples, the lookup passed a
string, and every character silently fell through to 'H'. The wizard in Full plate and the druid in
Half-plate sat in the committed goldens the whole time, because a golden pins what the code DOES,
not what the rules SAY. A table replacing that map has to be defended by something that knows the
rules independently of the table -- otherwise it is the same arrangement with better spelling.

So this gate checks the table three ways that do not share code with each other:

  1. COVERAGE   -- every rollable class has a row, and no row names a class that does not exist.
                   The pool is `class_data.json` minus the holdback lists, imported from
                   validate_class_roster so the definition lives in exactly one place.
  2. STALENESS  -- re-running the parser reproduces the committed file exactly. This catches a
                   hand-edit and a re-scrape that moved the prose out from under the table. It
                   proves the file is CURRENT; it proves nothing about whether the parse is RIGHT.
  3. AGREEMENT  -- and this is the one that matters. Every row records the sentence its value was
                   read out of. This re-reads those sentences with a SECOND implementation --
                   token adjacency rather than regex -- and disagrees loudly. A regex that drifts
                   passes check 2 and fails here.

Plus the cheap internal invariants a table can be wrong about on its own: an ASF exemption for
armor the class may not wear, a shield exemption for a class with no shields, a druid allowlist
naming an armor outside the class's own band, a taboo material no shield in the pool is made of.

KNOWN GAPS, REPORTED RATHER THAN HIDDEN
---------------------------------------
Two things are legitimately unresolved and are printed on every run so they cannot rot quietly:

- The SHIFTER is metal-prohibited with no allowlist in its prose, and armor.json has no material
  column. Anything consuming `metal_prohibited` without `armor_allow` is making a ruling, not
  reading one.
- Six classes are non-shield-proficient by SILENCE rather than by a sentence. That is correct RAW,
  but it is one dropped sentence away from looking identical to a scrape failure, so the count is
  asserted: if it changes, the prose changed.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import JSON_DIR, Report, read_json                               # noqa: E402

import build_armor_proficiency as builder                                      # noqa: E402
from validate_class_roster import HOLDBACK_LISTS                               # noqa: E402
from utils import data as game_data                                            # noqa: E402

REPORT = Report('validate_gear_legality')

PROFICIENCY = JSON_DIR / 'armor_proficiency.json'
ARMOR_DATA = JSON_DIR / 'armor.json'
CLASS_DATA = JSON_DIR / 'class_data.json'

# armor.json's section names, in the same order as builder.ARMOR_BANDS' letters.
SECTION_BAND = {'Light': 'L', 'Medium': 'M', 'Heavy': 'H'}

ROW_KEYS = {'armor', 'shield', 'asf_exempt', 'armor_allow', 'metal_prohibited',
            'shield_material', 'evidence'}

# Classes that are non-shield-proficient because their prose never mentions shields at all, rather
# than because it denies them. Asserted as an exact set: a re-scrape that drops a sentence would
# otherwise silently move a class in here and read as a rules change.
SILENT_ON_SHIELDS = {'gunslinger', 'magus', 'shaman', 'spiritualist',
                     'summoner', 'summoner (unchained)'}


def rollable_classes():
    """`class_data.json` minus every holdback lever, per validate_class_roster's definition."""
    pool = set(read_json(CLASS_DATA))
    for name in HOLDBACK_LISTS:
        pool -= {x.lower() for x in getattr(game_data, name, [])}
    return pool


# --------------------------------------------------------------------------------------------- #
# Check 3: the second implementation.
#
# Deliberately NOT the builder's regexes. This walks word tokens backwards from each occurrence of
# "armor" and collects the adjective run in front of it, which is a different way of being wrong --
# a regex that stops matching and a token walk that stops walking do not fail on the same input.
# --------------------------------------------------------------------------------------------- #
RUN_WORDS = {'light', 'medium', 'heavy', 'all', 'types', 'of', 'and', 'or', 'with', 'the', 'in',
             'as', 'well', 'a', 'an'}
BANDS = {'light': 'L', 'medium': 'M', 'heavy': 'H'}


def words_of(sentence):
    return re.findall(r"[a-z']+", (sentence or '').lower())


def band_by_tokens(sentence):
    """Heaviest band named as an adjective ON an "armor" noun, by walking the token run back.

    "all" only decides the answer when no specific band is named, which is what separates the
    fighter's "all armor" (heavy) from the tactician's "all types of light and medium armor"
    (medium) -- the trap that a looser reading of "all" walks straight into.
    """
    words = words_of(sentence)
    named, saw_all = set(), False
    for index, word in enumerate(words):
        if word not in ('armor', 'armors'):
            continue
        cursor = index - 1
        while cursor >= 0 and words[cursor] in RUN_WORDS:
            if words[cursor] in BANDS:
                named.add(BANDS[words[cursor]])
            elif words[cursor] == 'all':
                saw_all = True
            cursor -= 1
    if named:
        return max(named, key=builder.ARMOR_BANDS.index)
    return 'H' if saw_all else None


def denies_by_tokens(sentence, noun):
    """True when the sentence refuses `noun` -- "not/nor ... any ... <noun>", or "not ... <noun>".

    Both shapes are needed: the wizard says "not with any type of armor", the alchemist says "not
    with shields", and the stalker says "not proficient with shields of any kind" -- where the
    "any" comes AFTER and must not be read as the armor shape.
    """
    words = words_of(sentence)
    for index, word in enumerate(words):
        if word not in ('not', 'nor'):
            continue
        window = words[index:index + 12]
        for offset, later in enumerate(window):
            if later.rstrip('s') != noun:
                continue
            if noun == 'shield':
                return True
            return 'any' in window[:offset]
    return False


def tower_by_tokens(sentence):
    """True/False/None -- granted, explicitly excepted, or not mentioned."""
    words = words_of(sentence)
    if 'tower' not in words:
        # The NPC classes' "all types of armor and shields" is every shield, tower included; the
        # SRD spells out the parenthetical this repo's scrape dropped. "all" has to actually
        # GOVERN the shields, though -- the warlord's "all simple weapons and martial weapons, and
        # with light and medium armor, and with shields" contains both words and grants no tower,
        # which is what a bare `'all' in words` reads wrong.
        for index, word in enumerate(words):
            if word not in ('shield', 'shields'):
                continue
            cursor = index - 1
            while cursor >= 0 and words[cursor] in ('armor', 'armors', 'and', 'types', 'of'):
                cursor -= 1
            if cursor >= 0 and words[cursor] == 'all':
                return True
        return None
    before = words[:words.index('tower')]
    if 'including' in before:
        return True
    if 'except' in before or 'not' in before:
        return False
    return None


def check_agreement(name, row):
    """Re-read each recorded evidence sentence and insist it says what the row claims."""
    evidence = row.get('evidence') or {}

    armor_sentence = evidence.get('armor')
    if row['armor'] is None:
        if armor_sentence is None:
            REPORT.error(f'{name}: armor is null with no evidence sentence -- the prose neither '
                         f'grants nor denies armor, so the table is guessing')
        elif not denies_by_tokens(armor_sentence, 'armor'):
            REPORT.error(f'{name}: armor is null but the recorded sentence does not deny armor: '
                         f'{armor_sentence!r}')
    else:
        second = band_by_tokens(armor_sentence)
        if second != row['armor']:
            REPORT.error(f'{name}: armor={row["armor"]!r} but a token re-read of the recorded '
                         f'sentence says {second!r}: {armor_sentence!r}')

    shield_sentence = evidence.get('shield')
    if row['shield'] is None:
        if evidence.get('shield_stated'):
            if not denies_by_tokens(shield_sentence, 'shield'):
                REPORT.error(f'{name}: shield is null but the recorded sentence does not deny '
                             f'shields: {shield_sentence!r}')
        elif shield_sentence is not None:
            REPORT.error(f'{name}: shield is null and unstated, yet an evidence sentence was '
                         f'recorded: {shield_sentence!r}')
    else:
        words = words_of(shield_sentence)
        tower = tower_by_tokens(shield_sentence)
        if row['shield'] == 'tower':
            if tower is not True:
                REPORT.error(f'{name}: shield=tower but the recorded sentence does not grant '
                             f'tower shields: {shield_sentence!r}')
        elif tower is True:
            REPORT.error(f'{name}: shield={row["shield"]!r} but the recorded sentence grants '
                         f'tower shields: {shield_sentence!r}')
        if row['shield'] == 'buckler' and ('shield' in words or 'shields' in words):
            REPORT.error(f'{name}: shield=buckler but the recorded sentence says "shield": '
                         f'{shield_sentence!r}')
        if row['shield'] in ('shield', 'tower') and not ('shield' in words or 'shields' in words):
            REPORT.error(f'{name}: shield={row["shield"]!r} but the recorded sentence never says '
                         f'"shield": {shield_sentence!r}')

    asf_sentence = evidence.get('asf')
    exempt = row.get('asf_exempt') or {}
    if asf_sentence is None:
        if exempt.get('armor') or exempt.get('shield'):
            REPORT.error(f'{name}: claims an ASF exemption with no evidence sentence')
    else:
        clause = asf_sentence.split('without incurring')[0]
        if band_by_tokens(clause) != exempt.get('armor'):
            REPORT.error(f'{name}: asf_exempt.armor={exempt.get("armor")!r} but a token re-read '
                         f'of the exemption clause says {band_by_tokens(clause)!r}: {clause!r}')
        stated = 'shield' in words_of(clause) or 'shields' in words_of(clause)
        if stated != bool(exempt.get('shield')):
            REPORT.error(f'{name}: asf_exempt.shield={exempt.get("shield")!r} disagrees with the '
                         f'exemption clause: {clause!r}')


# --------------------------------------------------------------------------------------------- #
def check_internal(name, row, armor_sections):
    """Invariants a row can violate without any sentence being misread."""
    unknown = set(row) - ROW_KEYS
    if unknown:
        REPORT.error(f'{name}: unknown row keys {sorted(unknown)}')
    if row['armor'] not in builder.ARMOR_BANDS:
        REPORT.error(f'{name}: armor={row["armor"]!r} is not one of {builder.ARMOR_BANDS}')
    if row['shield'] not in builder.SHIELD_BANDS:
        REPORT.error(f'{name}: shield={row["shield"]!r} is not one of {builder.SHIELD_BANDS}')

    exempt = row.get('asf_exempt') or {}
    if set(exempt) != {'armor', 'shield'}:
        REPORT.error(f'{name}: asf_exempt keys are {sorted(exempt)}, expected armor + shield')
    # You cannot be exempt from spell failure in armor you are not allowed to wear. If this fires
    # the parse has crossed two sentences.
    if exempt.get('armor') is not None:
        if builder.ARMOR_BANDS.index(exempt['armor']) > builder.ARMOR_BANDS.index(row['armor']):
            REPORT.error(f'{name}: ASF-exempt in {exempt["armor"]!r} armor but only proficient to '
                         f'{row["armor"]!r}')
    if exempt.get('shield') and row['shield'] is None:
        REPORT.error(f'{name}: ASF-exempt while using a shield, but not shield-proficient')

    if row.get('shield_material') and row['shield'] is None:
        REPORT.error(f'{name}: shield_material={row["shield_material"]!r} but no shield '
                     f'proficiency to restrict')

    for armor_name in (row.get('armor_allow') or []):
        section = armor_sections.get(armor_name)
        if section is None:
            REPORT.error(f'{name}: armor_allow names {armor_name!r}, which is not in armor.json')
            continue
        band = SECTION_BAND.get(section)
        if band is None:
            REPORT.error(f'{name}: armor_allow names {armor_name!r}, which is a '
                         f'{section} -- not body armor')
        elif builder.ARMOR_BANDS.index(band) > builder.ARMOR_BANDS.index(row['armor']):
            REPORT.error(f'{name}: armor_allow names {armor_name!r} ({band}), heavier than the '
                         f'class\'s own {row["armor"]!r} band')


def check_materials(table, armor_json):
    """Every restricted material must actually match something in the shield section."""
    materials = {row['shield_material'] for row in table.values() if row.get('shield_material')}
    shields = list(armor_json.get('Shields', {}))
    for material in materials:
        matched = [n for n in shields if material.lower() in n.lower()]
        REPORT.check(matched, f'shield_material {material!r} matches no shield in armor.json -- '
                              f'a class restricted to it could never be given one')


# --------------------------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--print', dest='show', action='store_true',
                        help='print the table as the gate reads it')
    args = parser.parse_args()

    payload = read_json(PROFICIENCY)
    table = payload.get('classes')
    if not isinstance(table, dict) or not table:
        REPORT.error(f'{PROFICIENCY.name}: no "classes" object -- nothing to gate')
        return REPORT.finish()

    armor_json = read_json(ARMOR_DATA)
    armor_sections = {n: section for section, entries in armor_json.items() for n in entries}

    # 1. Coverage.
    pool = rollable_classes()
    known = set(read_json(CLASS_DATA))
    missing = sorted(pool - set(table))
    if missing:
        REPORT.error(f'rollable classes with no row: {missing}')
    stray = sorted(set(table) - known)
    if stray:
        REPORT.error(f'rows for classes not in class_data.json: {stray}')

    # 2. Staleness. A re-parse must reproduce the committed file exactly; anything the parser
    # cannot read at all is a loud failure here rather than a silent null in the table.
    reparsed, problems = builder.parse_all(armor_json=armor_json)
    for problem in problems:
        REPORT.error(f'unparseable: {problem}')
    if reparsed != table:
        differing = sorted(set(reparsed) ^ set(table)) or sorted(
            name for name in table if reparsed.get(name) != table[name])
        REPORT.error(f'{PROFICIENCY.name} is stale -- a re-parse of class_data.json disagrees on '
                     f'{differing[:8]}{" ..." if len(differing) > 8 else ""}. Re-run '
                     f'Backend/scripts/build/build_armor_proficiency.py')

    # 3 + internals.
    for name in sorted(table):
        check_agreement(name, table[name])
        check_internal(name, table[name], armor_sections)
    check_materials(table, armor_json)

    # The two known gaps, asserted rather than described.
    silent = {name for name, row in table.items()
              if row['shield'] is None and not (row.get('evidence') or {}).get('shield_stated')}
    if silent != SILENT_ON_SHIELDS:
        REPORT.error(f'the set of classes non-shield-proficient by SILENCE changed: '
                     f'{sorted(silent)} (expected {sorted(SILENT_ON_SHIELDS)}). Either the prose '
                     f'moved or a scrape dropped a sentence -- re-read it before updating this.')
    gapped = sorted(name for name, row in table.items()
                    if row['metal_prohibited'] and not row['armor_allow'])
    if gapped:
        REPORT.skip(f'metal-prohibited with no allowlist in the prose, and armor.json has no '
                    f'material column: {gapped} -- any consumer is making a ruling here, not '
                    f'reading one')

    if args.show:
        for name in sorted(table):
            row = table[name]
            print(f'{name:<22} armor={str(row["armor"]):<5} shield={str(row["shield"]):<8} '
                  f'asf={row["asf_exempt"]}')

    bands = {}
    for row in table.values():
        bands[row['armor']] = bands.get(row['armor'], 0) + 1
    shape = ', '.join(f'{bands[b]} {b or "no-armor"}'
                      for b in builder.ARMOR_BANDS if b in bands)
    shields = sum(1 for row in table.values() if row['shield'])
    return REPORT.finish(f'{len(table)} classes ({len(pool)} rollable) -- {shape}; '
                         f'{shields} shield-proficient')


if __name__ == '__main__':
    sys.exit(main())
