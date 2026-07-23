import re

from utils.paths import repo_path

# Canonical spell spellings, keyed by a fold that ignores case and apostrophes. data/spells.csv is the
# same canon the FoundryVTT module's every_spell.json is built from, so resolving against it is what
# makes a bonus spell render as the real compendium spell rather than a synthesized stand-in.
_CANON = None


def _canon_map():
    global _CANON
    if _CANON is None:
        import pandas as pd
        try:
            names = pd.read_csv(repo_path('data/spells.csv'), sep='|')['name'].dropna()
            _CANON = {_fold(n): str(n) for n in names}
        except (OSError, ValueError, KeyError):
            _CANON = {}
    return _CANON


def _fold(name):
    """Match key: lowercase, apostrophes dropped, whitespace collapsed."""
    text = str(name).lower().replace("'", "").replace('’', '').replace('`', '')
    return re.sub(r'\s+', ' ', text).strip()


# Words Paizo leaves lowercase inside a spell title ("Breath of Life", "Find the Path"). Only used
# for the fallback path -- anything present in spells.csv takes the CSV's exact spelling instead.
_MINOR_WORDS = {'of', 'the', 'to', 'and', 'or', 'a', 'an', 'in', 'on', 'from', 'with', 'for', 'at'}
_ROMAN = re.compile(r'^[ivx]+$', re.I)


def _titlecase_words(name):
    """Capitalize word-wise. str.title() is wrong three ways at once here: it uppercases after an
    apostrophe ("Bull'S Strength"), capitalizes connecting words ("Breath Of Life"), and destroys
    Roman numerals ("Beast Shape Iii")."""
    words = str(name).split()
    out = []
    for i, word in enumerate(words):
        if _ROMAN.match(word):
            out.append(word.upper())
        elif i > 0 and word.lower() in _MINOR_WORDS:
            out.append(word.lower())
        else:
            out.append(word[:1].upper() + word[1:])
    return ' '.join(out)


# Bloodlines
def add_bonus_spells(character, bomus_spells, spell_groups=None):
    # spell_groups targets a specific class's spellbook list (multiclass); defaults to the
    # legacy scalar (the primary spellbook — same object, so in-place appends stay in sync).
    if spell_groups is None:
        spell_groups = character.spell_list_choose_from
    for i,spell in enumerate(bomus_spells):
        if i + 1 < len(spell_groups):
            if spell in spell_groups[i + 1]:
                continue
            spell = clean_bonus_spells(spell)
            spell_groups[i + 1].append(spell)

def clean_bonus_spells(spell):
    """Normalize a scraped bonus-spell name to its canonical Paizo spelling.

    The scraped pools store these loosely -- lowercased, sometimes with the apostrophe stripped
    ("orders wrath"), sometimes carrying the granting level ("bull's strength (5th)"). This used to
    finish with str.title(), which shipped 180 wrong names across cleric_domains, druid_domains,
    bloodlines and wizard_schools: "Breath Of Life" (Paizo lowercases connecting words), "Beast Shape
    Iii" (Roman numerals destroyed) and "Bull'S Strength" (uppercase after the apostrophe) -- plus it
    could not restore an apostrophe the source data had already lost.

    Resolving against data/spells.csv fixes all four at once, because the fold ignores apostrophes and
    case: "orders wrath" and "bull's strength (5th)" both land on the CSV's exact spelling. Names the
    CSV doesn't carry (homebrew, or a scrape typo) fall back to word-wise capitalization, which is at
    least not actively wrong.

    This matters beyond the curated buff maps: the FoundryVTT module resolves a spell by NAME against
    its every_spell.json compendium, so a mis-spelled bonus spell renders as a synthesized stand-in
    instead of the real spell.
    """
    # drop the granting-level suffix, e.g. "cone of cold (11th)"
    spell = re.sub(r'\s*\(\d+(?:st|nd|rd|th)\)', '', str(spell))
    canon = _canon_map()
    for candidate in _name_candidates(spell):
        hit = canon.get(_fold(candidate))
        if hit:
            return hit
    return _titlecase_words(_strip_markers(spell))


# Sourcebook tags the scrape appends straight onto the name ("frightful aspectUC"), and the asterisk
# some pools use to flag a modified spell.
_SOURCE_TAG = re.compile(r'(?:UC|UM|UI|APG|ACG|ARG|OA|HA|UE)\b\*?\s*$')
# spells.csv files these as a comma suffix ("Command, Greater"); the pools write them parenthesized
# ("command (greater)"). These name a DIFFERENT spell from the stem -- Cure Critical Wounds, Mass is
# 8th level against the base spell's 4th -- so a qualifier that doesn't resolve must NOT fall back to
# the stem, or the character silently receives the weaker spell.
_QUALIFIERS = ('greater', 'lesser', 'mass')


def _strip_markers(name):
    name = re.sub(r'\*+', '', str(name))
    return re.sub(r'\s+', ' ', _SOURCE_TAG.sub('', name)).strip()


def _name_candidates(spell):
    """Spellings to try, in order. Each is only ACCEPTED if it resolves against spells.csv, so a
    wrong guess costs nothing -- that is what makes these rewrites safe rather than speculative."""
    base = _strip_markers(spell)
    yield spell
    yield base

    # Some pools already write the qualifier as a prefix ("greater command", "mass fly") while
    # spells.csv files it as a comma suffix. Same safety rule: only accepted if it resolves.
    leading = re.match(r'^(greater|lesser|mass)\s+(.*)$', base, re.I)
    if leading:
        yield f'{leading.group(2).strip()}, {leading.group(1).lower()}'

    trailing = re.search(r'^(.*?)\s*\(([^()]*)\)\s*$', base)
    if not trailing:
        return
    stem, inner = trailing.group(1).strip(), trailing.group(2).strip().lower()

    # "command (greater)" -> "Command, Greater"; "cure critical wounds (mass)" -> "..., Mass".
    for qualifier in _QUALIFIERS:
        if inner.startswith(qualifier):
            yield f'{stem}, {qualifier}'
            return          # a qualifier names a DIFFERENT spell -- never degrade to the stem

    # "animal shapes (birds only)" -> "Animal Shapes". Here the parenthetical is a domain restriction
    # on which form the spell may take, not part of the spell's name, so the stem is correct.
    yield stem

def add_bonus_spells_from_dict(character, bonus_spells_dict, spell_groups=None):
    if spell_groups is None:
        spell_groups = character.spell_list_choose_from
    i = 0
    for level, spells in bonus_spells_dict.items():
        i += 1
        # Convert level to an integer index if possible (e.g., '1st' -> 1)
        try:
            level_index = int(level[0])  # Extract the numeric part of the level
        except ValueError:
            level_index = i  # Default to i for invalid keys

        # Ensure the level index is within the bounds of spell_list_choose_from
        if level_index < len(spell_groups):
            for spell in spells:
                if spell in spell_groups[level_index]:
                    continue
                spell = clean_bonus_spells(spell)
                spell_groups[level_index].append(spell)