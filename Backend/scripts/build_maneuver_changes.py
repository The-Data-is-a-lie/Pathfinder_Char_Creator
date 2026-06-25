"""Draft-generate pf1 CONDITIONAL MODIFIERS for Path of War STRIKES/BOOSTS/COUNTERS (manual tool,
never part of the generation pipeline).

Each strike/boost/counter is meant to become a default-off conditional modifier on the character's
MAIN WEAPON attack action (toggled per-roll from the attack dialog) -- unlike stances, which are
buffs. Buff "changes" can't roll per-hit dice (pf1 evaluates them once, maximized, to a flat
number), so per-hit damage dice belong here as action conditionals where the `formula` keeps real
dice.

Reads Backend/json/class_data/path_of_war/Martial_Disciplines.json, keeps strike/boost/counter
kinds (skips stances), and applies CONSERVATIVE regexes to each Description to extract:
  - per-hit damage dice  ("inflicts an additional 1d4 points of [type] damage")
  - flat damage          ("an additional 4 points of damage")
  - attack-roll bonuses  ("+2 [type] bonus to attack rolls")
Everything else (double damage, saves, conditions, skill-replaces-attack, delayed/secondary
effects) is left out on purpose -- those stay description-only on the maneuver item.

Output is a DRAFT keyed by maneuver display name; every entry carries "review": true plus matched
snippets, and is meant to be hand-curated into the FoundryVTT module's
templates/character_sheet_folder/maneuver_changes.json (strip review/_snippets/_discipline/_kind/
_level; keep only modifiers you trust). IL scaling uses @pow.initLevel with ifelse()/gte() -- no
JS ternaries (pf1 v11 constraint).

Output shape per kept maneuver:
  "Sting of the Rattler": {
    "modifiers": [
      {"formula": "1d4", "target": "damage", "subTarget": "allDamage",
       "type": "untyped", "damageType": [], "critical": "normal"}
    ]
  }

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_maneuver_changes.py [--out PATH]
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "Backend" / "json" / "class_data" / "path_of_war" / "Martial_Disciplines.json"
DEFAULT_OUT = SOURCE.parent / "maneuver_changes.draft.json"

_KIND_RE = re.compile(r'\b(strike|boost|counter|stance)\b', re.IGNORECASE)
_LEVEL_RE = re.compile(r'level\s*:?\s*(\d+)', re.IGNORECASE)

# pf1 bonus types for the modifier "type" field (untyped when absent).
_BONUS_TYPES = ('dodge|morale|insight|luck|competence|circumstance|profane|sacred|'
                'deflection|resistance|shield|enhancement|alchemical|racial|size')
# pf1 damage type ids for a damage modifier's damageType set (empty = untyped).
_DMG_TYPES = ('fire|cold|acid|electricity|sonic|force|negative|positive|'
              'bludgeoning|piercing|slashing|untyped')

# Per-hit damage dice: "inflicts an additional 1d4 points of [fire] damage", "deals an extra 2d6
# damage". The dice count must be NdM; flat-only damage is handled by _DMG_FLAT_RE below.
_DMG_DICE_RE = re.compile(
    r'(?:additional|extra|deals?|inflicts?|takes? an additional|suffers? an additional)'
    r'[^.]{0,40}?\+?(\d+d\d+)\s*(?:points?\s+of\s+)?(' + _DMG_TYPES + r')?\s*damage',
    re.IGNORECASE)
# Flat extra damage (no dice): "an additional 4 points of damage".
_DMG_FLAT_RE = re.compile(
    r'(?:additional|extra)\s+(\d+)\s+points?\s+of\s+(' + _DMG_TYPES + r')?\s*damage',
    re.IGNORECASE)
# Attack-roll bonus: "+2 competence bonus to attack rolls", "+4 bonus on his attack rolls".
_ATK_RE = re.compile(
    r'\+(\d+)\s*(' + _BONUS_TYPES + r')?\s*bonus\s+(?:to|on)\s+'
    r'(?:his|her|its|their|the)?\s*attack rolls?',
    re.IGNORECASE)
# Dice IL-scaling rider, for a curation note only (e.g. "increases to 2d8 ... initiator level 9").
_DICE_STEP_RE = re.compile(
    r'increases?\s+to\s+(\d+d\d+)[^.]{0,40}?initiator level (\d+)', re.IGNORECASE)
# A real dice term in a finished damage formula (1d6, 8d6, the "4d6" in "4d6 + @INITMOD").
_DICE_RE = re.compile(r'\d+d\d+')

# --- Rider detection (saves / conditions / combat maneuvers) -- drafts the inline [[ ]] name text --
# These feed the curated `rider` field (docs/pow_conditional_decision_rules.md). DRAFT-quality and
# flagged review:true -- the maneuver re-audit curates them into maneuver_overrides.json.
_SAVE_RE = re.compile(
    r'\b(Fortitude|Reflex|Will)\b\s+(?:save|saving throw)[^.]{0,60}?'
    r'(negates?|halves?|partial|or\b[^.]{0,40})', re.IGNORECASE)
_SAVE_DC_RE = re.compile(r'\bDC\s*(\d+)\b', re.IGNORECASE)
_CONDITIONS = ('staggered|sickened|nauseated|shaken|frightened|panicked|dazed|stunned|prone|'
               'blinded|dazzled|deafened|entangled|paralyzed|fatigued|exhausted|cowering|confused')
_COND_RE = re.compile(
    r'\b(' + _CONDITIONS + r')\b[^.]{0,30}?(?:for\s+)?(\d+(?:d\d+)?)\s+rounds?', re.IGNORECASE)
_CM_KEYWORDS = r'bull\s*rush|trip|disarm|grapple|reposition|drag|dirty trick|sunder|overrun'
_CM_RE = re.compile(r'\b(' + _CM_KEYWORDS + r')\b[^.]{0,50}?(?:combat maneuver|maneuver check|\bcmb\b)',
                    re.IGNORECASE)
_CM_NO_AOO_RE = re.compile(r'without provoking', re.IGNORECASE)


def _parse_rider(desc):
    """Draft a `rider` string of save/condition/combat-maneuver effects, or '' if none. Save DCs use
    the scraped DC as the IL-scaling base (`[[ <dc> + @INITMOD ]]`); combat maneuvers get a plain
    CMB roll (the curator swaps in @ATTACKCHECK/@SKILLCHECK or the str/dex CMB form as needed)."""
    parts = []
    s = _SAVE_RE.search(desc)
    if s:
        dc = _SAVE_DC_RE.search(s.group(0)) or _SAVE_DC_RE.search(desc[max(0, s.start() - 30):s.start()])
        dc_txt = f"[[ {dc.group(1)} + @INITMOD ]]" if dc else "[[ ? + @INITMOD ]]"
        result = re.sub(r'\s+', ' ', s.group(2).strip())[:40]
        parts.append(f"{s.group(1).capitalize()} Save {dc_txt} {result}".strip())
    c = _COND_RE.search(desc)
    if c:
        parts.append(f"{c.group(1).lower()} [[{c.group(2)}]] rounds")
    cm = _CM_RE.search(desc)
    if cm:
        maneuver = re.sub(r'\s+', ' ', cm.group(1).lower())
        aoo = " (no AoO)" if _CM_NO_AOO_RE.search(desc) else ""
        parts.append(f"{maneuver} [[ d20 + @attributes.cmb.total ]] vs CMD{aoo}")
    return "; ".join(parts)


def _crit_for(formula):
    """nonCrit when the damage formula carries dice (extra dice don't multiply on a crit), else
    normal. Flat / @-reference-only riders stay normal and scale with the crit like static damage."""
    return 'nonCrit' if _DICE_RE.search(str(formula)) else 'normal'


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


def _damage_modifier(formula, dtype):
    return {
        'formula': formula,
        'target': 'damage',
        'subTarget': 'allDamage',
        'type': 'untyped',
        'damageType': [dtype] if dtype and dtype.lower() != 'untyped' else [],
        'critical': _crit_for(formula),
    }


def _attack_modifier(value, btype):
    return {
        'formula': str(value),
        'target': 'attack',
        'subTarget': 'allAttack',
        'type': (btype or 'untyped').lower(),
        'damageType': [],
        'critical': 'normal',
    }


def _parse_modifiers(desc):
    """Conservatively pull conditional modifiers out of one maneuver Description.
    Returns (modifiers, snippets, notes)."""
    modifiers, snippets, notes = [], [], []

    m = _DMG_DICE_RE.search(desc)
    if m:
        modifiers.append(_damage_modifier(m.group(1), m.group(2)))
        snippets.append(m.group(0).strip())
        step = _DICE_STEP_RE.search(desc)
        if step:
            notes.append(f"scales to {step.group(1)} at initiator level {step.group(2)} "
                         f"(verify a computed-count die or hand-edit)")
    else:
        mf = _DMG_FLAT_RE.search(desc)
        if mf:
            modifiers.append(_damage_modifier(mf.group(1), mf.group(2)))
            snippets.append(mf.group(0).strip())

    a = _ATK_RE.search(desc)
    if a:
        modifiers.append(_attack_modifier(a.group(1), a.group(2)))
        snippets.append(a.group(0).strip())

    return modifiers, snippets, notes


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
            if kind not in ('strike', 'boost', 'counter'):
                continue
            total += 1
            desc = str(entry.get('Description', ''))
            mods, snippets, notes = _parse_modifiers(desc)
            rider = _parse_rider(desc)
            if not mods and not rider:
                continue
            parsed += 1
            out = {'modifiers': mods, 'review': True,
                   '_discipline': _display(disc_key), '_kind': kind, '_level': level,
                   '_snippets': snippets}
            if rider:
                out['rider'] = rider
            if notes:
                out['_notes'] = notes
            draft[_display(m_key)] = out
    print(f"strikes/boosts/counters with a parsed modifier or rider: {parsed}/{total}")
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
