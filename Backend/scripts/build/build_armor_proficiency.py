"""Derive Backend/json/armor_proficiency.json from class_data.json's proficiency prose.

    C:\\Python310\\python.exe Backend/scripts/build/build_armor_proficiency.py
    C:\\Python310\\python.exe Backend/scripts/build/build_armor_proficiency.py --print

WHY THIS EXISTS (gear-legality plan, D2)
----------------------------------------
`data.armor_type_mapping` was the previous answer and it never once fired: its keys are TUPLES
(`('rogue','bard','brawler'): 'L'`) and `armor_chooser` looks up a plain string, so every character
in the repo's history fell through to the `'H'` default -- which is how a golden wizard ended up in
Full plate and a golden druid in Half-plate. Flattening those tuple keys was rejected as the fix:
it would have been a hand-authored list of 68 classes with nothing checking it against the rules,
which is the same arrangement that failed, just spelled correctly.

So the authority is DERIVED. `class_data.json` already carries every class's
`weapon and armor proficiency` paragraph, scraped from the source books -- the rule is already in
the repo, in prose. This script parses that prose once, at build time, into a table; a gate
(`gates/validate_gear_legality.py`) re-parses and refuses to pass if the committed table has
drifted. Runtime prose parsing was rejected for the obvious reason: a regex that silently stops
matching at runtime yields a falsy default, which is the exact failure mode this whole plan is
about.

WHAT A ROW HOLDS
----------------
    armor            'H' | 'M' | 'L' | None   heaviest band the class may wear; None = no armor
    shield           'tower' | 'shield' | 'buckler' | None      the shield ladder, same idea
    asf_exempt       {'armor': 'L'|'M'|None, 'shield': bool}    arcane spell failure exemptions
    armor_allow      [names] | None           druid's exact allowlist, as armor.json names
    metal_prohibited bool                     druid AND shifter; see the gap note below
    evidence         {armor, shield, asf}     the sentence each value was read out of

`evidence` is not decoration. It is what lets the gate check the table a SECOND way -- re-parsing
proves the file is not stale, but re-parsing with the same code proves nothing about whether the
parse is right. The gate re-reads the recorded sentence with different logic and disagrees loudly.

THE ONE GAP, LEFT VISIBLE
-------------------------
The druid's taboo is an exact allowlist in its own prose ("they may wear only padded, leather, or
hide armor"). The SHIFTER's is not: it says "prohibited from wearing metal armor" and never names
what is left. armor.json has no material column, so there is nothing here to resolve that against.
Rather than quietly copying the druid's list onto the shifter, this emits
`metal_prohibited: true, armor_allow: null` and the gate reports it as a known gap -- the same
pattern as the 246 missing item names. The consumer decides what to do with it, in the open.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import JSON_DIR, REPO, read_json                                 # noqa: E402

CLASS_DATA = JSON_DIR / 'class_data.json'
ARMOR_DATA = JSON_DIR / 'armor.json'
OUT_PATH = JSON_DIR / 'armor_proficiency.json'

PROSE_KEY = 'weapon and armor proficiency'

# Ladders, weakest first. Index into these is the comparison the multiclass union (D5) needs, so
# they are exported rather than hidden -- gates/validate_gear_legality.py and the runtime chooser
# both order bands with them.
ARMOR_BANDS = (None, 'L', 'M', 'H')
SHIELD_BANDS = (None, 'buckler', 'shield', 'tower')

# --------------------------------------------------------------------------------------------- #
# Sentence-level parsing.
#
# Everything below reads ONLY sentences containing "proficient". That is not tidiness -- it is the
# whole trick. Four classes describe heavier armor in a sentence that is about arcane spell
# failure, not about proficiency ("a bard wearing medium or heavy armor incurs..."), and a naive
# search for "heavy armor" over the paragraph promotes the bard, bloodrager, magus and summoner
# into plate. Narrowing to proficiency sentences also drops the monk's "carrying a medium or heavy
# load" and the ranger's scraped-in creature-type list.
# --------------------------------------------------------------------------------------------- #
SENTENCE_SPLIT = re.compile(r'(?<=\.)\s+')

# "Adepts are skilled with all simple weapons" is the one class that opens on a synonym; its armor
# clause still says "proficient", so only the positive-band scan needs the alternative.
PROFICIENCY_WORD = re.compile(r'\bproficien(?:t|cy|cies)\b', re.I)

# A negation is "not/nor ... any ... armor" within one clause. Deliberately narrow: "but not with
# shields" must NOT read as an armor negation, and "not proficient with shields of any kind" must
# not either -- both need "any" to be followed by armor, not preceded by it.
NEG_ARMOR = re.compile(r'\b(?:not|nor)\b[^.;]{0,40}?\bany\b[^.;]{0,30}?\barmors?\b', re.I)
NEG_SHIELD = re.compile(r'\b(?:not|nor)\b[^.;]{0,60}?\bshields?\b', re.I)

# Positive bands. "all armor" / "all types of armor" must be LITERAL and adjacent: the tactician's
# "all types of light and medium armor" is a medium class, not a heavy one, and a looser pattern
# promotes it. Likewise "heavy armor" adjacent, so the wizard's "heavy crossbow" is not armor.
BAND_HEAVY = re.compile(r'\bheavy armor\b|\ball armor\b|\ball types of armor\b', re.I)
BAND_MEDIUM = re.compile(r'\bmedium armor\b|\blight and medium armor\b|\blight or medium armor\b',
                         re.I)
BAND_LIGHT = re.compile(r'\blight armors?\b', re.I)

# Tower is decided before shields are, and the clause is then REMOVED, because "shields (but not
# tower shields)" contains a "not ... shield" that would otherwise read as a flat denial.
TOWER_YES = re.compile(r'\bincluding tower shields?\b', re.I)
TOWER_NO = re.compile(r'\s*\(?\b(?:except|but not)(?: for)? tower shields?\b\)?', re.I)
# "all types of armor and shields" is the NPC classes' phrasing and it does mean every shield --
# the SRD spells it "(including tower shields)" and this repo's scrape lost the parenthetical.
ALL_SHIELDS = re.compile(r'\ball (?:types of )?armor and shields?\b', re.I)
SHIELD_WORD = re.compile(r'\bshields?\b', re.I)
BUCKLER_WORD = re.compile(r'\bbucklers?\b', re.I)

# Druid / shifter.
METAL_BAN = re.compile(r'prohibited from wearing metal armor', re.I)
ALLOWLIST = re.compile(r'may wear only\s+([^.;]+?)\s+armor\b', re.I)
WOOD_SHIELD = re.compile(r'crafted from wood', re.I)

# Arcane spell failure exemption. One sentence shape across all five classes that have one.
ASF_SENTENCE = re.compile(r'without incurring the normal arcane spell failure', re.I)
ASF_CLAUSE = re.compile(r'\bwhile wearing\s+(.*?)\s*without incurring', re.I | re.DOTALL)

# WHO suffers arcane spell failure at all, which is a different question from who is exempt from
# some of it, and the one ruling D5's cap turns on. Derived from the prose rather than from a
# caster list because `data.base_classes` is the Paizo base-class ROSTER (it contains the fighter)
# and there is no arcane/psychic/divine split anywhere else that covers all 70 rows. The three
# phrasings below are every way the books say it: the five classes with an exemption say "arcane
# spell failure" outright, and the four full arcane casters with no armour proficiency say their
# spells "fail" or point at "Arcane Spells and Armor". Psionic classes are correctly EXCLUDED --
# their prose says the opposite in as many words ("Armor does not interfere with the manifestation
# of powers"), and psychic magic has no somatic components to spoil.
ASF_SENSITIVE = re.compile(
    r'arcane spell failure'
    r'|Arcane Spells and Armor'
    r'|spells with somatic components to fail', re.I)


def sentences(prose):
    return [s.strip() for s in SENTENCE_SPLIT.split(prose or '') if s.strip()]


def proficiency_sentences(prose):
    return [s for s in sentences(prose) if PROFICIENCY_WORD.search(s)]


def band_of(text):
    """Heaviest armor band named in `text`, or None if it names none."""
    if BAND_HEAVY.search(text):
        return 'H'
    if BAND_MEDIUM.search(text):
        return 'M'
    if BAND_LIGHT.search(text):
        return 'L'
    return None


def parse_armor(prose):
    """(band, evidence sentence, resolved?) -- resolved is False when the prose said nothing."""
    negated = None
    for sentence in proficiency_sentences(prose):
        band = band_of(sentence)
        if band is not None:
            return band, sentence, True
        if NEG_ARMOR.search(sentence):
            negated = sentence
    if negated is not None:
        return None, negated, True
    return None, None, False


def parse_shield(prose):
    """(band, evidence sentence, resolved?).

    An UNRESOLVED shield is legitimate and common -- the gunslinger, shaman, spiritualist, magus
    and both summoners simply never mention shields, and RAW that means not proficient. It is
    reported separately from a stated denial so the gate can list which classes are riding on
    silence rather than on a sentence.
    """
    negated = None
    for sentence in proficiency_sentences(prose):
        if not SHIELD_WORD.search(sentence) and not BUCKLER_WORD.search(sentence):
            continue
        tower = bool(TOWER_YES.search(sentence)) or bool(ALL_SHIELDS.search(sentence))
        stripped = TOWER_NO.sub('', TOWER_YES.sub('', sentence))
        if NEG_SHIELD.search(stripped):
            negated = sentence
            continue
        if tower:
            return 'tower', sentence, True
        if SHIELD_WORD.search(stripped):
            return 'shield', sentence, True
        if BUCKLER_WORD.search(stripped):
            return 'buckler', sentence, True
    if negated is not None:
        return None, negated, True
    return None, None, False


def parse_asf(prose):
    """({'armor': band, 'shield': bool}, evidence sentence)."""
    for sentence in sentences(prose):
        if not ASF_SENTENCE.search(sentence):
            continue
        match = ASF_CLAUSE.search(sentence)
        clause = match.group(1) if match else sentence
        return {'armor': band_of(clause),
                'shield': bool(SHIELD_WORD.search(clause))}, sentence
    return {'armor': None, 'shield': False}, None


def parse_allowlist(prose, armor_names):
    """(canonical armor.json names, metal_prohibited, problems).

    The names are canonicalised against armor.json rather than left as prose words, so a taboo that
    no longer resolves to a real armor fails HERE, at build time, instead of quietly allowing
    nothing at runtime.
    """
    problems = []
    prohibited = bool(METAL_BAN.search(prose or ''))
    match = ALLOWLIST.search(prose or '')
    if not match:
        return None, prohibited, problems
    allowed = []
    # The Oxford comma is the whole reason for the optional `or` inside the comma branch: on
    # "padded, leather, or hide" a plain `,\s*|\s+or\s+` splits at the comma first and leaves
    # "or hide" as a word.
    for word in re.split(r',\s*(?:or\s+)?|\s+or\s+', match.group(1)):
        word = word.strip().lower()
        if not word or word == 'or':
            continue
        hits = [n for n in armor_names if n.lower() == word]
        if len(hits) != 1:
            problems.append(f'allowlist word {word!r} matches {len(hits)} armor.json entries')
            continue
        allowed.append(hits[0])
    return allowed or None, prohibited, problems


def parse_class(name, entry, armor_names):
    prose = entry.get(PROSE_KEY) if isinstance(entry, dict) else None
    problems = []
    if not isinstance(prose, str) or not prose.strip():
        return None, [f'{name}: no {PROSE_KEY!r} prose to parse']

    armor, armor_evidence, armor_resolved = parse_armor(prose)
    if not armor_resolved:
        problems.append(f'{name}: no proficiency sentence names an armor band or denies armor -- '
                        f'prose: {prose[:160]!r}')
    shield, shield_evidence, shield_resolved = parse_shield(prose)
    asf, asf_evidence = parse_asf(prose)
    allow, metal_prohibited, allow_problems = parse_allowlist(prose, armor_names)
    problems += [f'{name}: {p}' for p in allow_problems]

    row = {
        'armor': armor,
        'shield': shield,
        'asf_sensitive': bool(ASF_SENSITIVE.search(prose)),
        'asf_exempt': asf,
        'armor_allow': allow,
        'metal_prohibited': metal_prohibited,
        'shield_material': 'wood' if WOOD_SHIELD.search(prose) else None,
        'evidence': {
            'armor': armor_evidence,
            # Recorded so the gate can tell "the book says no" from "the book never said". The
            # second is far more fragile: a re-scrape that drops a sentence looks identical to a
            # class that genuinely has no shields.
            'shield': shield_evidence,
            'shield_stated': shield_resolved,
            'asf': asf_evidence,
        },
    }
    return row, problems


def parse_all(class_data=None, armor_json=None):
    """({class: row}, [problems]) -- the whole table, in class_data.json's own key order."""
    class_data = class_data if class_data is not None else read_json(CLASS_DATA)
    armor_json = armor_json if armor_json is not None else read_json(ARMOR_DATA)
    armor_names = [n for section in armor_json.values() for n in section]

    rows, problems = {}, []
    for name, entry in class_data.items():
        row, issues = parse_class(name, entry, armor_names)
        problems += issues
        if row is not None:
            rows[name] = row
    return rows, problems


README = (
    'DERIVED FILE -- do not hand-edit. Built by Backend/scripts/build/build_armor_proficiency.py '
    'from class_data.json\'s "weapon and armor proficiency" prose, and re-parsed on every run of '
    'Backend/scripts/gates/validate_gear_legality.py, which fails if this file has drifted from '
    'the prose. armor: heaviest legal band (H/M/L or null for none). shield: ladder '
    'tower > shield > buckler, null for none. asf_exempt: the class\'s own arcane-spell-failure '
    'exemption, which is a CHARACTER-level fact the payload does not apply to the item\'s printed '
    'value. armor_allow / metal_prohibited / shield_material: the druid and shifter taboos.'
)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--print', dest='show', action='store_true',
                        help='print the table instead of writing it')
    args = parser.parse_args()

    rows, problems = parse_all()
    if problems:
        for problem in problems:
            print(f'  {problem}')
        print(f'\nFAILED: {len(problems)} class(es) did not parse -- nothing written')
        return 1

    if args.show:
        width = max(len(n) for n in rows)
        for name, row in rows.items():
            exempt = row['asf_exempt']
            note = ''
            if row['metal_prohibited']:
                note = f'  taboo: {row["armor_allow"] or "metal-prohibited, no allowlist"}'
            print(f'{name:<{width}}  armor={str(row["armor"]):<4} '
                  f'shield={str(row["shield"]):<8} '
                  f'asf={str(exempt["armor"]):<4}/{"shield" if exempt["shield"] else "-":<6}{note}')
        return 0

    payload = {'_readme': README, 'classes': rows}
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n',
                        encoding='utf-8')
    bands = {}
    for row in rows.values():
        bands[row['armor']] = bands.get(row['armor'], 0) + 1
    shape = ', '.join(f'{count} {band or "none"}' for band, count in sorted(
        bands.items(), key=lambda kv: ARMOR_BANDS.index(kv[0])))
    print(f'wrote {OUT_PATH.relative_to(REPO)}: {len(rows)} classes -- {shape}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
