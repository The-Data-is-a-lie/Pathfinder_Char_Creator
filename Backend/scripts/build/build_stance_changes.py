"""Draft-generate pf1 buff "changes" for Path of War STANCES (manual tool, never part of the
generation pipeline).

Reads Backend/json/class_data/path_of_war/Martial_Disciplines.json, keeps entries whose kind
parses as "stance" (same regexes as utils/class_func/path_of_war.py), and applies CONSERVATIVE
regexes to each description to extract flat typed bonuses (+N <type> bonus to <target>) and the
two common initiator-level scaling shapes. Everything else (dice riders, conditional effects)
is left out on purpose -- those stay description-only per the feature spec.

Output is a DRAFT: every entry carries "review": true plus the matched source snippet, and is
meant to be hand-curated into the FoundryVTT module's
templates/character_sheet_folder/stance_changes.json (strip review/_snippet/_discipline/_level,
keep only entries you trust). Formulas use @pow.initLevel with ifelse()/gte()/floor()/max() --
pf1 v11 change formulas have no JS ternaries.

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_stance_changes.py [--out PATH]
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO   # noqa: E402
SOURCE = REPO / "Backend" / "json" / "class_data" / "path_of_war" / "Martial_Disciplines.json"
DEFAULT_OUT = SOURCE.parent / "stance_changes.draft.json"

_KIND_RE = re.compile(r'\b(strike|boost|counter|stance)\b', re.IGNORECASE)
_LEVEL_RE = re.compile(r'level\s*:?\s*(\d+)', re.IGNORECASE)

# pf1 bonus types the change "type" field accepts (untyped when absent).
_BONUS_TYPES = ('dodge|morale|insight|luck|competence|circumstance|profane|sacred|'
                'deflection|resistance|shield|enhancement|alchemical|racial|size|untypedPerm')

# Target phrase -> pf1 change target. Deliberately small; anything unmapped is skipped.
_TARGETS = [
    (r'armor class|\bac\b', 'ac'),
    (r'melee attack rolls', 'mattack'),
    (r'ranged attack rolls', 'rattack'),
    (r'attack rolls', 'attack'),
    (r'(?:weapon )?damage rolls', 'wdamage'),
    (r'all saving throws|saving throws|all saves', 'allSavingThrows'),
    (r'fortitude sav(?:es|ing throws)', 'fort'),
    (r'reflex sav(?:es|ing throws)', 'ref'),
    (r'will sav(?:es|ing throws)', 'will'),
    (r'\bcmd\b|combat maneuver defense', 'cmd'),
    (r'\bcmb\b|combat maneuver (?:bonus|checks)', 'cmb'),
    (r'initiative(?: checks)?', 'init'),
    (r'(?:base land|movement|land) speed', 'landSpeed'),
]

# Skill-check bonuses: "on <Skill> checks". pf1 skill ids.
_SKILLS = {
    'acrobatics': 'skill.acr', 'bluff': 'skill.blf', 'climb': 'skill.clm',
    'diplomacy': 'skill.dip', 'disable device': 'skill.dev', 'disguise': 'skill.dis',
    'escape artist': 'skill.esc', 'fly': 'skill.fly', 'heal': 'skill.hea',
    'intimidate': 'skill.int', 'perception': 'skill.per', 'ride': 'skill.rid',
    'sense motive': 'skill.sen', 'sleight of hand': 'skill.slt', 'stealth': 'skill.ste',
    'survival': 'skill.sur', 'swim': 'skill.swm',
}

_FLAT_RE = re.compile(
    r'(?:gains?|grants?|receives?|adds?)?[^.]{0,60}?'
    r'\+(\d+)\s*(' + _BONUS_TYPES + r')?\s*bonus\s+(?:to|on|against)\s+([^.,;]{1,60})',
    re.IGNORECASE)

# "upon reaching initiator level 9, this bonus increases to +2" and the ordinal variant
# "At initiator level 12th, these bonuses increase to +4." (the (?:st|nd|rd|th)? tolerates the
# scrape's ordinal suffixes, which previously broke the level->value transition).
_STEP_RE = re.compile(
    r'(?:upon reaching|at) initiator level (\d+)(?:st|nd|rd|th)?,?\s*(?:this|the|these)?\s*'
    r'bonus(?:es)?\s*increases? to \+?(\d+)', re.IGNORECASE)

# "increases by 1 for every four initiator levels (beyond 1st)"
_WORD_NUMS = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6}
_PER_RE = re.compile(
    r'increases? by \+?(\d+) for every (\d+|two|three|four|five|six)\s*initiator levels?'
    r'(?:[^.,;]{0,30}?beyond (\d+))?', re.IGNORECASE)


def _display(key):
    return re.sub(r'\s+', ' ', unquote(str(key)).replace('_', ' ').strip())


def _parse_kind_level(entry):
    disc_str = str(entry.get('Discipline', ''))
    kind_m = _KIND_RE.search(disc_str)
    kind = kind_m.group(1).lower() if kind_m else None
    level_m = _LEVEL_RE.search(disc_str)
    level = int(level_m.group(1)) if level_m else None
    if level is None:
        try:
            level = int(str(entry.get('Level', '')).strip())
        except (TypeError, ValueError):
            level = None
    return kind, level


def _match_target(phrase):
    p = phrase.strip().lower()
    for pat, target in _TARGETS:
        if re.search(pat, p):
            return target
    m = re.search(r'([a-z ]+?) checks', p)
    if m and m.group(1).strip() in _SKILLS:
        return _SKILLS[m.group(1).strip()]
    return None


def _match_targets(phrase):
    '''Distinct pf1 targets named in one bonus clause, in order. Compound phrases like
    "Initiative checks and Reflex saves" or "his Armor Class, CMD, and to his Initiative score"
    grant the same bonus to several targets; split on commas/"and"/"to" so each gets its own
    change instead of only the first-matched one. Deduped, original order preserved.'''
    targets = []
    for part in re.split(r',|\band\b|\bto\b', phrase):
        t = _match_target(part)
        if t and t not in targets:
            targets.append(t)
    return targets


def _scaling_formula(base, desc):
    """Wrap a flat base value in the common IL-scaling shapes when the text describes one.
    Returns (formula, snippet) or (str(base), None)."""
    steps = _STEP_RE.findall(desc)
    if steps:
        formula = str(base)
        prev = base
        for lvl, val in steps[:2]:
            lvl, val = int(lvl), int(val)
            if val <= prev:        # not a plausible escalation of THIS bonus
                continue
            formula += f" + ifelse(gte(@pow.initLevel, {lvl}), {val - prev}, 0)"
            prev = val
        if formula != str(base):
            return formula, _STEP_RE.search(desc).group(0)
    per = _PER_RE.search(desc)
    if per:
        inc = int(per.group(1))
        div = per.group(2).lower()
        div = int(div) if div.isdigit() else _WORD_NUMS[div]
        off = int(per.group(3)) if per.group(3) else 0
        return (f"{base} + {inc} * max(0, floor((@pow.initLevel - {off}) / {div}))",
                per.group(0))
    return str(base), None


def build_draft():
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    draft, parsed, total = {}, 0, 0
    for disc_key, maneuvers in data.items():
        if not isinstance(maneuvers, dict):
            continue
        for m_key, entry in maneuvers.items():
            if not isinstance(entry, dict):
                continue
            kind, level = _parse_kind_level(entry)
            if kind != 'stance':
                continue
            total += 1
            desc = str(entry.get('Description', ''))
            changes, snippets = [], []
            for m in _FLAT_RE.finditer(desc):
                base, btype, target_phrase = int(m.group(1)), m.group(2), m.group(3)
                targets = _match_targets(target_phrase)
                if not targets:
                    continue
                formula, scale_snippet = _scaling_formula(base, desc)
                for target in targets:
                    changes.append({
                        'formula': formula,
                        'target': target,
                        'type': (btype or 'untyped').lower(),
                        'operator': 'add',
                        'priority': 0,
                    })
                snippets.append(m.group(0) + (f' ... {scale_snippet}' if scale_snippet else ''))
            if not changes:
                continue
            parsed += 1
            draft[_display(m_key)] = {
                'changes': changes,
                'contextNotes': [],
                'review': True,
                '_discipline': _display(disc_key),
                '_level': level,
                '_snippets': snippets,
            }
    print(f"stances with at least one parsed change: {parsed}/{total}")
    return draft


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    draft = build_draft()
    args.out.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"wrote {len(draft)} draft entries -> {args.out}")


if __name__ == '__main__':
    main()
