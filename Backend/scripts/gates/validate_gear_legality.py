"""Gate the gear-legality CONFIG layer: the proficiency, enabler and weapon-size tables.

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

TWO MORE TABLES, ON THE SAME PRINCIPLE
--------------------------------------
`two_hand_enablers.json` is a census of everything that one-hands a two-hander, oversizes a weapon
or reduces the penalty for it. Names are the thing most likely to be wrong about it -- the pool
spells them `Pikemans Training` and `Titan Grip (Combat)`, not `Pikeman's Training` and
`Titan Grip`, and a grant of a name that does not resolve is a silently dead branch of exactly the
kind this plan exists to remove. So every `in_pool: true` row is resolved against the file it
names, and every `in_pool: false` row is proved ABSENT -- a gap that quietly closes is a finding
too, not a free pass.

`weapon_size_damage.json` is Core Rulebook Table 6-5. Its values are external rules and this gate
does not pretend to re-derive them; what it checks is that the table is internally coherent (every
value is a real die expression, every `large` entry is strictly bigger than its Medium row) and
that its declared gap stays declared, so nobody grows a Huge column by hand without sourcing it.

KNOWN GAPS, REPORTED RATHER THAN HIDDEN
---------------------------------------
Two things are legitimately unresolved and are printed on every run so they cannot rot quietly:

- The SHIFTER is metal-prohibited with no allowlist in its prose, and armor.json has no material
  column. Anything consuming `metal_prohibited` without `armor_allow` is making a ruling, not
  reading one.
- Six classes are non-shield-proficient by SILENCE rather than by a sentence. That is correct RAW,
  but it is one dropped sentence away from looking identical to a scrape failure, so the count is
  asserted: if it changes, the prose changed.
- Two enablers are absent from every pool (Lighten Weapon, the Equipment sphere advanced talent),
  and a Medium wielder cannot be oversized by two steps because PF1e published no Huge weapon
  damage table.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import JSON_DIR, REPO, Report, read_json                         # noqa: E402

import build_armor_proficiency as builder                                      # noqa: E402
from validate_class_roster import HOLDBACK_LISTS                               # noqa: E402
from utils import data as game_data                                            # noqa: E402

REPORT = Report('validate_gear_legality')

PROFICIENCY = JSON_DIR / 'armor_proficiency.json'
ENABLERS = JSON_DIR / 'two_hand_enablers.json'
SIZE_DAMAGE = JSON_DIR / 'weapon_size_damage.json'
ARMOR_DATA = JSON_DIR / 'armor.json'
CLASS_DATA = JSON_DIR / 'class_data.json'
ARCHETYPES = JSON_DIR / 'archetypes.json'
DISCIPLINES = JSON_DIR / 'class_data' / 'path_of_war' / 'Martial_Disciplines.json'
FEATS_CSV = REPO / 'data' / 'feats_new.csv'

# armor.json's section names, in the same order as builder.ARMOR_BANDS' letters.
SECTION_BAND = {'Light': 'L', 'Medium': 'M', 'Heavy': 'H'}

ROW_KEYS = {'armor', 'shield', 'asf_sensitive', 'asf_exempt', 'armor_allow', 'metal_prohibited',
            'shield_material', 'evidence'}

# The ten classes whose spells arcane spell failure can actually spoil, and the whole basis of
# ruling D5's caster cap. Asserted by name rather than counted: this set decides whether a
# multiclass character is allowed into plate, so it must not drift on a re-scrape without somebody
# looking. Psionic classes are absent on purpose -- their prose says "Armor does not interfere with
# the manifestation of powers" -- and so are the psychic-magic occult classes.
ASF_SENSITIVE_CLASSES = {'arcanist', 'bard', 'bloodrager', 'magus', 'skald', 'sorcerer',
                         'summoner', 'summoner (unchained)', 'witch', 'wizard'}

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
    # An exemption from a thing you do not suffer is a parse that crossed two classes' sentences.
    if (exempt.get('armor') or exempt.get('shield')) and not row.get('asf_sensitive'):
        REPORT.error(f'{name}: carries an arcane-spell-failure exemption but is not marked '
                     f'asf_sensitive -- one of the two was read out of the wrong sentence')

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
# The enabler census.
# --------------------------------------------------------------------------------------------- #
ENABLER_KEYS = {'name', 'effect', 'kind', 'in_pool', 'where', 'visible_at_gear_time',
                'requires_shield', 'weapon', 'size_steps', 'attack_penalty', 'prerequisites',
                'note', 'reduces_penalty_by'}
EFFECTS = {'one_hand', 'oversize', 'penalty_reduction'}
KINDS = {'feat', 'class_feature', 'stance', 'talent'}


def feat_names():
    """Every `name` in feats_new.csv. Read as pipe-delimited text rather than with `csv` on
    purpose: the benefit fields contain commas and quotes and the delimiter is what matters."""
    names = set()
    with open(FEATS_CSV, encoding='utf-8') as handle:
        next(handle, None)
        for line in handle:
            head = line.split('|', 1)[0].strip()
            if head:
                names.add(head)
    return names


def resolve_enabler(row, feats, archetypes, disciplines):
    """(found, where it was looked for) -- the same lookup for present and absent rows alike.

    Absent rows go through this too. That is the point: 'not in the pool' is a claim, and a claim
    nothing checks is how a gap silently closes and a branch stays dead after the data arrives.
    """
    name, kind, where = row['name'], row['kind'], row.get('where') or {}
    if kind == 'feat':
        return name in feats, f'feats_new.csv name column'
    if kind == 'class_feature':
        block = (archetypes.get(where.get('class')) or {}).get(where.get('archetype')) or {}
        return where.get('feature') in block, (f'archetypes.json {where.get("class")}/'
                                               f'{where.get("archetype")}')
    if kind == 'stance':
        block = disciplines.get(where.get('discipline')) or {}
        return where.get('entry') in block, f'Martial_Disciplines.json {where.get("discipline")}'
    # A talent has no pool file to resolve against yet -- that IS the gap, and the only talent row
    # here is flagged absent. A talent claiming to be in the pool is therefore a contradiction.
    return False, 'no talent pool is wired up'


def check_enablers():
    payload = read_json(ENABLERS)
    rows = payload.get('enablers')
    if not isinstance(rows, list) or not rows:
        return REPORT.error(f'{ENABLERS.name}: no "enablers" list')

    feats = feat_names()
    archetypes = read_json(ARCHETYPES)
    disciplines = read_json(DISCIPLINES)

    seen, absent = set(), []
    for row in rows:
        name = row.get('name', '<unnamed>')
        unknown = set(row) - ENABLER_KEYS
        if unknown:
            REPORT.error(f'enabler {name}: unknown keys {sorted(unknown)}')
        if row.get('effect') not in EFFECTS:
            REPORT.error(f'enabler {name}: effect {row.get("effect")!r} not in {sorted(EFFECTS)}')
        if row.get('kind') not in KINDS:
            REPORT.error(f'enabler {name}: kind {row.get("kind")!r} not in {sorted(KINDS)}')
        if name in seen:
            REPORT.error(f'enabler {name}: duplicate row')
        seen.add(name)

        # An oversizer must say how far, and only an oversizer may. Absent rows are exempt and in
        # fact required to stay null: nothing has read those rules, so a number there would be
        # invented rather than sourced.
        steps = row.get('size_steps')
        if not row.get('in_pool'):
            if steps is not None or row.get('attack_penalty') is not None:
                REPORT.error(f'enabler {name}: flagged not-in-pool but carries mechanics '
                             f'(size_steps={steps!r}, attack_penalty='
                             f'{row.get("attack_penalty")!r}) -- nothing has read those rules')
        elif row.get('effect') == 'oversize':
            if steps not in (1, 2):
                REPORT.error(f'enabler {name}: oversize with size_steps={steps!r}, expected 1 or 2')
        elif steps is not None:
            REPORT.error(f'enabler {name}: size_steps={steps!r} on a {row.get("effect")!r} row')
        if (row.get('in_pool') and row.get('effect') == 'penalty_reduction'
                and not row.get('reduces_penalty_by')):
            REPORT.error(f'enabler {name}: a penalty_reduction row must say reduces_penalty_by')

        found, looked_in = resolve_enabler(row, feats, archetypes, disciplines)
        if row.get('in_pool'):
            if not found:
                REPORT.error(f'enabler {name!r} claims to be in the pool but does not resolve in '
                             f'{looked_in} -- check the exact spelling before anything grants it')
        else:
            absent.append(name)
            if found:
                REPORT.error(f'enabler {name!r} is flagged NOT in the pool, but it resolves in '
                             f'{looked_in} now. The gap closed -- wire it up or re-flag it.')

        # Only archetype features are visible at gear time; feats and stances are chosen in later
        # phases. This is the fact the whole D7 ladder is built on, so it is asserted rather than
        # left to a comment.
        if row.get('visible_at_gear_time') and row.get('kind') != 'class_feature':
            REPORT.error(f'enabler {name}: visible_at_gear_time on a {row.get("kind")!r} -- gear '
                         f'runs before both the feat and the Path of War phases')

    if absent:
        REPORT.skip(f'enablers absent from every pool, deliberately left visible: {absent}')
    return len(rows)


# --------------------------------------------------------------------------------------------- #
# The size table.
# --------------------------------------------------------------------------------------------- #
DIE = re.compile(r'^(\d+)d(\d+)$')


def average(expression):
    """Mean of an NdX expression; the bare '1' the table uses for the smallest step is 1.0."""
    if expression == '1':
        return 1.0
    match = DIE.match(expression or '')
    return None if match is None else int(match.group(1)) * (int(match.group(2)) + 1) / 2.0


def check_size_damage():
    """The HOUSE ladder is the authority here, not RAW.

    `Base_Weapon_Damage_Dice.JS` in the Handy Macros folder is the live implementation and this
    file is a transcription of it, so what can be checked from inside this repo is the ladder's own
    coherence: every entry a real die expression, every stated average the arithmetic mean of it,
    and the whole thing sorted -- because the macro steps a size category by moving TWO POSITIONS
    along it, which makes the ORDER load-bearing. A transposed pair is the realistic transcription
    error and it would silently make one weapon scale downwards.
    """
    payload = read_json(SIZE_DAMAGE)
    ladder = payload.get('ladder')
    if not isinstance(ladder, list) or len(ladder) < 4:
        return REPORT.error(f'{SIZE_DAMAGE.name}: no usable "ladder" list')

    if payload.get('attack_penalty_per_step') != -2:
        REPORT.error(f'{SIZE_DAMAGE.name}: attack_penalty_per_step is '
                     f'{payload.get("attack_penalty_per_step")!r}, and the Core Rulebook says -2')
    if 'HOUSE RULE' not in str(payload.get('authority') or ''):
        REPORT.error(f'{SIZE_DAMAGE.name}: the authority note no longer says this is a house rule. '
                     f'It diverges from Core Rulebook Table 6-5 on purpose -- if that changed, say '
                     f'so deliberately rather than by deleting the note.')

    previous = None
    for index, entry in enumerate(ladder):
        dice = (entry or {}).get('dice')
        stated = (entry or {}).get('average')
        actual = average(dice)
        if actual is None:
            REPORT.error(f'size ladder[{index}]: {dice!r} is not a die expression')
            continue
        if abs(float(stated or 0) - actual) > 1e-9:
            REPORT.error(f'size ladder[{index}] {dice}: average is stated as {stated} but is '
                         f'{actual}')
        if previous is not None and actual < previous:
            # A WARNING, not an error, and the distinction is the whole point. The macro's own
            # ladder has two such pairs, and this file copies the macro's ORDER rather than an
            # improved one -- re-sorting here would make the copy disagree with the source it
            # exists to mirror, which is worse than half a point of average damage on one step.
            # Fix the macro, then re-transcribe; do not fix it here.
            REPORT.warn(f'size ladder[{index}] {dice} (avg {actual}) sorts below the entry above '
                        f'it (avg {previous}) -- present in Base_Weapon_Damage_Dice.JS too, and '
                        f'copied deliberately; see "known_inversions" in the file')
        previous = actual
    # Two positions per size step, so the ladder has to be able to serve the largest step the
    # generator can ask for (D10's cap of 2) from its very first entry.
    REPORT.check(len(ladder) > 2 * 2,
                 f'size ladder has {len(ladder)} entries -- too short to serve a 2-step oversize')

    raw = (payload.get('raw_reference') or {}).get('by_medium_damage') or {}
    for medium, row in raw.items():
        base = average(medium)
        if base is None:
            REPORT.error(f'size table: {medium!r} is not a die expression')
            continue
        if set(row) != {'tiny', 'large'}:
            REPORT.error(f'size table {medium}: columns are {sorted(row)}, expected tiny + large')
            continue
        # Monotonicity is the check that catches a transposed cell, which is the realistic way a
        # hand-transcribed table goes wrong -- and the way that a spot-check of two or three rows
        # would not notice.
        larger = average(row['large'])
        if larger is None:
            REPORT.error(f'size table {medium}: large={row["large"]!r} is not a die expression')
        elif larger <= base:
            REPORT.error(f'size table {medium}: large={row["large"]!r} averages {larger}, which is '
                         f'not more than the Medium {base}')
        if row['tiny'] is not None:
            smaller = average(row['tiny'])
            if smaller is None:
                REPORT.error(f'size table {medium}: tiny={row["tiny"]!r} is not a die expression')
            elif smaller >= base:
                REPORT.error(f'size table {medium}: tiny={row["tiny"]!r} averages {smaller}, which '
                             f'is not less than the Medium {base}')
    return len(ladder)


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
    sensitive = {name for name, row in table.items() if row.get('asf_sensitive')}
    if sensitive != ASF_SENSITIVE_CLASSES:
        REPORT.error(f'the arcane-spell-failure-sensitive set changed: {sorted(sensitive)} '
                     f'(expected {sorted(ASF_SENSITIVE_CLASSES)}). D5 caps a multiclass band on '
                     f'exactly this set, so read the prose before updating the constant.')

    gapped = sorted(name for name, row in table.items()
                    if row['metal_prohibited'] and not row['armor_allow'])
    if gapped:
        REPORT.skip(f'metal-prohibited with no allowlist in the prose, and armor.json has no '
                    f'material column: {gapped} -- any consumer is making a ruling here, not '
                    f'reading one')

    enablers = check_enablers()
    size_rows = check_size_damage()

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
                         f'{shields} shield-proficient; {enablers} enablers; '
                         f'{size_rows} weapon-size rows')


if __name__ == '__main__':
    sys.exit(main())
