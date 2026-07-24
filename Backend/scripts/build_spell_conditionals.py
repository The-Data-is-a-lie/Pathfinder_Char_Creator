"""Draft-generate pf1 CONDITIONAL / rider data for SPELLS (manual tool, never part of the generation
pipeline).

Reads data/spells.csv (pipe-delimited; `short_description` holds a clean one-liner, `description`
the full text) and CONSERVATIVELY classifies every spell into one of two buckets, mirroring the
repo's house convention (the OKF pathfinder bundle oks/pathfinder/conditionals/,
docs/pow_conditional_decision_rules.md) and the feat split (feat_changes.json vs
feat_conditionals.json):

  Bucket B -- the spell IS a damaging attack (needs a melee/ranged TOUCH ATTACK and deals dice
              damage: Shocking Grasp, Scorching Ray, Vampiric Touch, Acid Arrow, Chill Touch). The
              pf1 compendium spell already carries its own attack + damage, so we DON'T re-emit
              damage; we surface only a formal `save` block + non-damage `riders` (ability damage,
              conditions) as inline-[[ ]] text. -> goes to spell_riders.json.

  Bucket A -- a buff that adds to ATTACK and/or DAMAGE rolls, or enhances a weapon (Bless, Divine
              Favor, True Strike, Magic Weapon, Bless Weapon, Flame Arrow). Becomes a default-off
              conditional TOGGLE on the wielder's main weapon. Two shapes:
                "A"        sustained typed bonus -> feat_changes-style {changes, contextNotes}
                "A-toggle" one-shot ("next attack") or dice-bearing bonus -> feat_conditionals-style
                           {name, default:false, modifiers:[...]} (a change maximizes dice; a
                           conditional modifier keeps real dice -- so True Strike's +20 and Flame
                           Arrow's +1d6 belong here).
              -> goes to spell_changes.json.

  Bucket C -- an OFFENSIVE non-touch spell: it deals dice damage in an area / at range with no
              attack roll (Fireball, Lightning Bolt), forces an enemy saving throw, and/or inflicts
              conditions / ability damage / penalties (Hold Person, Bane, Slow). The compendium
              spell item may already roll damage; per the house "always explicit" rule the entry
              still restates the save + full effect as default-on [[ ]] rider text, plus a formal
              `save` block for actions the compendium left save-less. Shape is identical to Bucket B
              minus the attack ("attack": null) -> ALSO curated into spell_riders.json (the module's
              addSpellRiders and the palette's build_rider_spells read only save/riders, so C flows
              through the Bucket-B plumbing unchanged).

Detection runs B FIRST, then A, then C; a spell lands in at most one bucket (B wins -- e.g.
Shocking Grasp also grants +3 to-hit vs metal armor, but it's a touch-attack damage spell; a
buff-with-a-rider stays A). Harmless-save-only spells and personal-range spells never land in C.
Everything the regexes can't confidently read stays out -- those spells are description-only (the
Foundry module renders the spell from the compendium).

Output is a DRAFT keyed by spell display name; every entry carries "_bucket", "review": true, the
matched "_snippets", and "_spell_level", and is meant to be hand-curated into
Backend/json/spells/spell_changes.json (bucket A) and Backend/json/spells/spell_riders.json
(bucket B) -- strip the review/_* keys, keep only entries you trust, finalize scaling formulas/caps.

Caster-level scaling ("+1 per three levels") is drafted as floor(@spells.primary.cl.total/N) (the
@-path from the foundry-sheet-references skill); caps/minimums are left for curation (flagged review).

Usage:
    C:\\Python310\\python.exe Backend/scripts/build_spell_conditionals.py [--out PATH]
"""
import argparse
import json
import re
import sys as _sys
from pathlib import Path

import pandas as pd

_sys.path.insert(0, str(Path(__file__).resolve().parent))
import conditional_clauses as cc                  # shared six-detail clause builders
from damage_types import normalize_damage_type    # prose word -> pf1 damage-type id

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "data" / "spells.csv"
DEFAULT_OUT = REPO / "Backend" / "json" / "spells" / "spell_conditionals.draft.json"

# pf1 bonus types for a modifier/change "type" field (untyped when absent).
_BONUS_TYPES = ('dodge|morale|insight|luck|competence|circumstance|profane|sacred|'
                'deflection|resistance|shield|enhancement|alchemical|racial|size|trait')
# pf1 built-in damage type ids for a damage modifier's damageType set (empty = untyped).
_DMG_TYPES = ('fire|cold|acid|electricity|sonic|force|negative|positive|'
              'bludgeoning|piercing|slashing|untyped')
_DICE_RE = re.compile(r'\d+d\d+')

# --- Bucket B: spell delivered by an attack roll that deals dice damage ---------------------------
_RANGED_TOUCH_RE = re.compile(r'ranged touch', re.IGNORECASE)
_TOUCH_ATTACK_RE = re.compile(r'(?:melee|ranged)?\s*touch attack|ranged attack roll', re.IGNORECASE)
# Dice damage: "1d6 points of electricity damage", "4d6 fire damage", "1d6/level ... damage".
_DMG_DICE_RE = re.compile(
    r'(\d+d\d+)(?:/level)?\s*(?:points?\s+of\s+)?(' + _DMG_TYPES + r')?\s*damage', re.IGNORECASE)
# Ability damage rider: "1d4 points of Strength damage", "1 point of Constitution damage".
_ABILITIES = 'strength|dexterity|constitution|intelligence|wisdom|charisma'
_ABIL_DMG_RE = re.compile(
    r'(\d+(?:d\d+)?)\s+points?\s+of\s+(' + _ABILITIES + r')\s+(damage|drain)', re.IGNORECASE)
# Ongoing/secondary damage: "1d6 points of fire damage ... each round for 3 rounds".
_ONGOING_RE = re.compile(
    r'(\d+d\d+|\d+)\s*(?:points?\s+of\s+)?(' + _DMG_TYPES + r')?\s*damage[^.]{0,40}?'
    r'(?:each|per|every)\s+round(?:[^.]{0,30}?for\s+(\d+(?:d\d+)?)\s+rounds?)?', re.IGNORECASE)
# A condition inflicted for an explicit duration (high-signal): "blinded for 1d4 rounds".
_CONDITIONS = ('blinded|dazzled|dazed|staggered|stunned|sickened|nauseated|shaken|frightened|'
               'panicked|entangled|paralyzed|deafened|fatigued|exhausted|confused|cowering|prone|'
               'asleep|unconscious|helpless|blind|deaf')
_COND_DUR_RE = re.compile(
    r'(' + _CONDITIONS + r')\s+for\s+(\d+(?:d\d+)?)\s+rounds?', re.IGNORECASE)

# --- Bucket A: buff to attack/damage / weapon enhancement ----------------------------------------
# "+2 luck bonus on attack rolls" (bonus precedes "attack roll").
_ATK_FWD_RE = re.compile(
    r'\+(\d+)\s*(' + _BONUS_TYPES + r')?\s*bonus[^.]{0,40}?attack rolls?', re.IGNORECASE)
# True-Strike order: "... next single attack roll ... gains a +20 insight bonus" (bonus FOLLOWS it).
_ATK_REV_RE = re.compile(
    r'attack rolls?[^.]{0,80}?\+(\d+)\s+(' + _BONUS_TYPES + r')?\s*bonus', re.IGNORECASE)
# "+N <type> bonus on attack and (weapon) damage rolls" -> same bonus to BOTH.
_ATK_AND_DMG_RE = re.compile(
    r'\+(\d+)\s*(' + _BONUS_TYPES + r')?\s*bonus[^.]{0,30}?attack and (?:weapon )?damage rolls?',
    re.IGNORECASE)
# "+N <type> bonus on (weapon) damage rolls".
_DMG_BONUS_RE = re.compile(
    r'\+(\d+)\s*(' + _BONUS_TYPES + r')?\s*bonus[^.]{0,40}?(?:weapon )?damage rolls?', re.IGNORECASE)
# Weapon-enhancer that ADDS DICE: "arrows deal an additional 1d6 points of fire damage".
_WEAPON_CTX_RE = re.compile(
    r'\b(weapon|blade|sword|arrow(?!\s+slit)|ammunition|projectile)s?\b', re.IGNORECASE)
_WEAPON_DICE_RE = re.compile(
    r'(?:deals?|inflicts?|gains?|additional|extra)[^.]{0,40}?(\d+d\d+)\s*(?:points?\s+of\s+)?'
    r'(' + _DMG_TYPES + r')?\s*damage', re.IGNORECASE)
# Disqualifiers: an "attack roll" match that's really an AC/crit-confirmation bonus, or a bonus
# granted to the OPPONENT rather than the caster -- drop those (false positives, not weapon buffs).
_DISQUALIFY_ATK_RE = re.compile(
    r'\barmor class\b|\bac\b|confirmation|opponents?\s+gain|enem(?:y|ies)\s+gain|foes?\s+gain',
    re.IGNORECASE)
# Crit-CONFIRMATION-only idiom: "+N on attack rolls TO CONFIRM a critical hit" (Unerring Weapon).
# The bonus rides only the confirm roll, not every attack, and pf1 has no crit-confirm-only change
# target -- so such spells stay description-only. The "to confirm" / "confirm(s) a critical" clause
# trails just PAST the "attack rolls" the bonus names, so it falls outside the bonus match span (and
# thus outside _DISQUALIFY_ATK_RE above); _disqualified_attack() looks a little further forward for
# it. The VERB "confirm" is the tell: Mirror Strike's NOUN "(and confirmation attack roll)" is a real
# general +N that merely also rides the confirm roll, so it must NOT match here.
_CRIT_CONFIRM_RE = re.compile(
    r'\bto\s+confirm\b|\bconfirm(?:s|ing|ed)?\s+(?:a\s+)?critical', re.IGNORECASE)
# One-shot ("your next attack") -> must be a toggle, never an always-on change.
_ONESHOT_RE = re.compile(r'next (?:single )?attack|on your next', re.IGNORECASE)
# Caster-level scaling: "for every three caster levels", "per two levels".
_SCALE_RE = re.compile(r'(?:per|every)\s+(two|three|four|five|\d+)\s+(?:caster\s+)?levels?',
                       re.IGNORECASE)
_WORD_NUM = {'two': 2, 'three': 3, 'four': 4, 'five': 5}
# Stated ceiling on a scaling bonus ("maximum +3", "maximum total bonus +7", "max +5").
_MAX_RE = re.compile(r'max(?:imum)?(?:\s+total\s+bonus)?\s*(?:of\s+)?\+?(\d+)', re.IGNORECASE)
# Stated floor on a scaling bonus ("at least +1").
_MIN_RE = re.compile(r'at least\s*\+?(\d+)', re.IGNORECASE)

# --- Combat-maneuver-on-hit riders (Bucket A): "free bull rush", "trip combat maneuver", etc. ----
# A buff spell that lets you make a combat maneuver gets a [[ ]] CMB roll in its conditional name,
# mirroring the Path of War convention (docs/pow_conditional_decision_rules.md). High-signal only.
_CM_KEYWORDS = r'bull\s*rush|trip|disarm|grapple|reposition|drag|dirty trick|sunder|overrun'
_CM_RE = re.compile(r'\b(' + _CM_KEYWORDS + r')\b[^.]{0,60}?(?:combat maneuver|maneuver check|\bcmb\b)',
                    re.IGNORECASE)
_CM_RE2 = re.compile(r'combat maneuver[^.]{0,40}?\b(' + _CM_KEYWORDS + r')\b', re.IGNORECASE)
# A flat bonus to the maneuver check ("+5 sacred bonus on your combat maneuver check").
_CM_BONUS_RE = re.compile(
    r'\+(\d+)\s*(?:' + _BONUS_TYPES + r')?\s*bonus[^.]{0,40}?(?:combat maneuver|maneuver check|\bcmb\b)',
    re.IGNORECASE)
# "use your caster level in place of your base attack bonus" -> CL replaces BAB in the CMB roll.
_CM_CL_FOR_BAB_RE = re.compile(r'caster level in place of [^.]{0,25}?base attack bonus', re.IGNORECASE)
_CM_NO_AOO_RE = re.compile(r'without provoking', re.IGNORECASE)
_CM_ONHIT_RE = re.compile(
    r'if (?:the|this|your|that) (?:attack|spell|ray|strike|weapon|blow)s? (?:hits?|deals?|strikes?)'
    r'|if it hits|on (?:a |each )?(?:successful )?hit', re.IGNORECASE)


def _combat_maneuver_rider(full):
    """High-signal combat-maneuver-on-hit clause -> a [[ ]] CMB-roll rider string, or None."""
    m = _CM_RE.search(full) or _CM_RE2.search(full)
    if not m:
        return None
    maneuver = re.sub(r'\s+', ' ', m.group(1).lower())
    if _CM_CL_FOR_BAB_RE.search(full):
        roll = "[[ d20 + @attributes.cmb.total - @attributes.bab.total + @spells.primary.cl.total ]]"
    else:
        b = _CM_BONUS_RE.search(full)
        roll = "[[ d20 + @attributes.cmb.total" + (f" + {b.group(1)}" if b else "") + " ]]"
    prefix = "on hit, " if _CM_ONHIT_RE.search(full) else ""
    aoo = " (no AoO)" if _CM_NO_AOO_RE.search(full) else ""
    return f"{prefix}free {maneuver} {roll} vs CMD{aoo}"


def _crit_for(formula):
    """nonCrit when the formula carries dice (extra dice don't multiply on a crit), else normal."""
    return 'nonCrit' if _DICE_RE.search(str(formula)) else 'normal'


def _scale_formula(value, window):
    """Literal `value` (str) unless THIS bonus's local `window` scales it per N levels ->
    floor(@CL/N), bounded by a stated ceiling/floor when the window names one: a "maximum +3" wraps it
    in min(..., 3), an "at least +1" wraps it in max(..., 1) (so Divine Favor -> min(max(.,1),3)).
    `window` must be a small slice anchored on the bonus match -- a global search would wrongly scale
    a flat bonus off an unrelated "per N levels" clause elsewhere in the description (a temp-HP /
    healing / duration line) or pick up an unrelated maximum."""
    m = _SCALE_RE.search(window)
    if not m:
        return str(value), False
    g = m.group(1).lower()
    n = _WORD_NUM.get(g) or int(g)
    formula = f"floor(@spells.primary.cl.total/{n})"
    mn = _MIN_RE.search(window)
    if mn:
        formula = f"max({formula}, {int(mn.group(1))})"
    mx = _MAX_RE.search(window)
    if mx:
        formula = f"min({formula}, {int(mx.group(1))})"
    return formula, True


def _win(full, m):
    """Small slice around bonus match `m` -- where its own per-level scaling clause and any
    "(at least +1, maximum +3)" bound would live (the bound trails the bonus, so reach further out)."""
    return full[max(0, m.start() - 25): m.end() + 95]


def _save_block(save_raw):
    """{type, dc:'', description, harmless} from the saving_throw column, or None if there's no save."""
    s = (save_raw or '').strip()
    if not s or s.lower() in ('none', 'no', 'null'):
        return None
    m = re.search(r'\b(fortitude|reflex|will)\b', s, re.IGNORECASE)
    if not m:
        return None
    return {'type': m.group(1).lower(), 'dc': '', 'description': s,
            'harmless': 'harmless' in s.lower()}


def _classify_B(name, full, short, save_raw, level):
    """Bucket B if a touch attack/ranged attack roll delivers dice damage; else None."""
    m = _TOUCH_ATTACK_RE.search(full) or _RANGED_TOUCH_RE.search(full)
    if not m:
        return None
    # A touch attack aimed at scenery, not the victim ("hit the opening with a ranged touch attack"
    # -- Fireball through an arrow slit) is not a touch-attack DELIVERY; let the spell fall to C.
    if re.search(r'opening|arrow slit|narrow|cover', full[max(0, m.start() - 60): m.end() + 40]):
        return None
    dmg = _DMG_DICE_RE.search(full)
    if not dmg:
        return None
    ranged = bool(_RANGED_TOUCH_RE.search(full))
    snippets = [dmg.group(0).strip()]
    riders = []

    def _add(rider, snippet):
        if rider not in riders:
            riders.append(rider)
            snippets.append(snippet.strip())

    for m in _ABIL_DMG_RE.finditer(full):
        _add(f"[[{m.group(1)}]] {m.group(2).capitalize()} {m.group(3)}.", m.group(0))
    for m in _ONGOING_RE.finditer(full):
        dtype = f"{m.group(2)} " if m.group(2) else ""
        dur = f" for [[{m.group(3)}]] rounds" if m.group(3) else ""
        _add(f"Ongoing [[{m.group(1)}]] {dtype}damage each round{dur}.", m.group(0))
    for m in _COND_DUR_RE.finditer(full):
        _add(f"Target {m.group(1).lower()} for [[{m.group(2)}]] rounds.", m.group(0))
    entry = {
        '_bucket': 'B-ranged' if ranged else 'B-melee',
        'attack': 'ranged' if ranged else 'melee',
        'save': _save_block(save_raw),
        'riders': riders,
        'review': True,
        '_base_damage': f"{dmg.group(1)} {dmg.group(2) or 'untyped'}",
        '_spell_level': level,
        '_snippets': snippets,
    }
    return entry


# --- Bucket C: offensive non-touch spell (area/save damage, debuff, condition) --------------------
# "1d6 per caster level (maximum 10d6)" -> a computed-dice inline roll the sheet can actually roll.
_PER_CL_DMG_RE = re.compile(
    r'(\d+)d(\d+)\s*(?:points?\s+of\s+)?(?:(' + _DMG_TYPES + r')\s+)?damage'
    r'[^.+]{0,40}?(?:per|for (?:each|every))\s+(?:(two|three|four|five|\d+)\s+)?(?:caster\s+)?levels?',
    re.IGNORECASE)   # window excludes '+': "1d8 damage + 1 per level" scales the +1, NOT the dice
_PER_CL_SLASH_RE = re.compile(
    r'(\d+)d(\d+)(?:\s*(?:points?\s+of\s+)?(?:(' + _DMG_TYPES + r')\s+)?damage)?/(?:caster\s+)?level',
    re.IGNORECASE)
_MAX_DICE_RE = re.compile(r'max(?:imum)?(?:\s+of)?\s+(\d+)d(\d+)', re.IGNORECASE)
# "takes a -2 penalty on attack rolls", "suffer a -4 penalty to AC" (en-dash or hyphen).
_PENALTY_RE = re.compile(
    r'[−–\-](\d+)\s+penalty\s+(?:on|to)\s+([^,.;]{3,70})', re.IGNORECASE)
# A condition inflicted without an explicit "for N rounds" duration -- require an inflicting verb
# within a short reach of a subject noun so bare rules-text mentions ("as the sickened condition")
# don't false-positive ("creature in the cloud becomes nauseated" must still match).
_COND_INFLICT_RE = re.compile(
    r'(?:target|subject|creature|it|they)s?[^.;]{0,40}?\s(?:is|are|becomes?|remains?)\s+'
    r'(' + _CONDITIONS + r')\b', re.IGNORECASE)
# Duration variants beyond "for N rounds": "for N minutes/hours", "for 1 round per level".
_COND_DUR_UNIT_RE = re.compile(
    r'(' + _CONDITIONS + r')\s+for\s+(\d+(?:d\d+)?)\s+(round|minute|hour)s?'
    r'(\s*(?:per|/)\s*(?:caster\s+)?level)?', re.IGNORECASE)


def _save_rider_prefix(save_raw):
    """"Reflex half" -> "Reflex Save half" (the explicit save clause that leads every C rider).
    Returns '' when there is no real save."""
    s = re.sub(r'\s+', ' ', (save_raw or '').strip())
    m = re.search(r'\b(Fortitude|Reflex|Will)\b', s, re.IGNORECASE)
    if not m:
        return ''
    word = m.group(1).capitalize()
    rest = (s[:m.start()] + s[m.end():]).strip(' ;,')
    # A multi-save column ("none and Will negates (object)") leaves a dangling "none and/or" once the
    # save word is excised -- drop that artifact and collapse the double space it leaves behind.
    rest = re.sub(r'^(?:none|no)\s*(?:and|or|,)?\s*', '', rest, flags=re.IGNORECASE)
    rest = re.sub(r'\s{2,}', ' ', rest)
    return f"{word} Save {rest}".strip() if rest else f"{word} Save"


def _cl_damage_formula(full):
    """Per-caster-level dice damage -> (inline formula, matched snippet) or None.
    "1d6 per caster level (maximum 10d6)" -> (min(10, @spells.primary.cl.total))d6;
    "1d8 per two caster levels" -> (floor(@spells.primary.cl.total/2))d8, min 1 die."""
    m = _PER_CL_DMG_RE.search(full) or _PER_CL_SLASH_RE.search(full)
    if not m:
        return None
    n, die = int(m.group(1)), m.group(2)
    dtype = (m.group(3) or '').lower()
    per = m.group(4) if m.re is _PER_CL_DMG_RE else None
    per_n = 1
    if per:
        per_n = _WORD_NUM.get(per.lower(), int(per) if per.isdigit() else 1)
    count = "@spells.primary.cl.total" if per_n == 1 else f"floor(@spells.primary.cl.total/{per_n})"
    if n != 1:
        count = f"({count})*{n}" if per_n != 1 else f"{n}*@spells.primary.cl.total"
    mx = _MAX_DICE_RE.search(full)
    if mx and mx.group(2) == die:
        count = f"min({int(mx.group(1))}, {count})"
    formula = f"({count})d{die}"
    return formula, dtype, m.group(0).strip()


def _classify_C(name, full, save_raw, level, rng):
    """Bucket C if a non-touch spell is offensive: dice damage with no attack roll, an enemy save,
    and/or an inflicted condition / ability damage / penalty. Personal-range and harmless-save-only
    spells are skipped. Riders are ALWAYS explicit (house rule): the save clause leads, then damage /
    conditions / penalties, every number in [[ ]]."""
    if 'personal' in (rng or '').lower():
        return None
    save = _save_block(save_raw)
    harmless = bool(save and save.get('harmless'))
    snippets, riders = [], []

    def _add(rider, snippet):
        if rider and rider not in riders:
            riders.append(rider)
            snippets.append(snippet.strip())

    # Damage: per-CL scaling first (rollable computed dice), else flat dice.
    dmg_rider = None
    cl_dmg = _cl_damage_formula(full)
    if cl_dmg:
        formula, dtype, snip = cl_dmg
        dmg_rider = (f"[[ {formula} ]] {dtype + ' ' if dtype else ''}damage", snip)
    else:
        dm = _DMG_DICE_RE.search(full)
        if dm:
            dtype = (dm.group(2) or '').lower()
            dmg_rider = (f"[[{dm.group(1)}]] {dtype + ' ' if dtype else ''}damage", dm.group(0))

    # Conditions (explicit duration first, then bare inflictions), ability damage, ongoing, penalties.
    cond_riders = []
    seen_conds = set()
    for m in _COND_DUR_UNIT_RE.finditer(full):
        cond = m.group(1).lower()
        per_lvl = ' per caster level' if m.group(4) else ''
        cond_riders.append((f"target {cond} for [[{m.group(2)}]] {m.group(3)}s{per_lvl}", m.group(0)))
        seen_conds.add(cond)
    for m in _COND_INFLICT_RE.finditer(full):
        cond = m.group(1).lower()
        if cond not in seen_conds:
            cond_riders.append((f"target {cond}", m.group(0)))
            seen_conds.add(cond)
    abil_riders = [(f"[[{m.group(1)}]] {m.group(2).capitalize()} {m.group(3)}", m.group(0))
                   for m in _ABIL_DMG_RE.finditer(full)]
    ongoing_riders = []
    for m in _ONGOING_RE.finditer(full):
        dtype = f"{m.group(2)} " if m.group(2) else ""
        dur = f" for [[{m.group(3)}]] rounds" if m.group(3) else ""
        ongoing_riders.append((f"ongoing [[{m.group(1)}]] {dtype}damage each round{dur}", m.group(0)))
    pen_riders = []
    for m in _PENALTY_RE.finditer(full):
        what = re.sub(r'\s+', ' ', m.group(2)).strip()
        if len(what) >= 68:              # regex window ceiling hit -- last token is likely clipped
            what = ' '.join(what.split()[:-1])
        words = what.split()             # strip dangling connectives left by the cut
        while words and words[-1].lower() in ('and', 'or', 'of', 'the', 'to', 'a', 'an', 'their',
                                              'its', 'his', 'her', 'with', 'in', 'on', 'for'):
            words.pop()
        what = ' '.join(words)
        if what:
            pen_riders.append((f"-[[{m.group(1)}]] penalty to {what}", m.group(0)))

    offensive = bool(dmg_rider or cond_riders or abil_riders or ongoing_riders or pen_riders)
    if harmless and not offensive:
        return None                      # a buff's harmless save, not an offensive spell
    if not offensive and not save:
        return None
    if not offensive and save:
        # Save with no readable effect (charms, gaze effects, "see text") -- still worth an explicit
        # save rider; the effect stays on the spell description. Review will catch junk.
        pass

    prefix = _save_rider_prefix(save_raw)
    effects = ([dmg_rider] if dmg_rider else []) + cond_riders + abil_riders + ongoing_riders + pen_riders
    if prefix and effects:
        body = "; ".join(e[0] for e in effects)
        _add(f"{prefix} — {body}", "; ".join(e[1] for e in effects))
    elif prefix:
        _add(f"{prefix} (see spell description)", save_raw)
    else:
        for e in effects:
            _add(e[0], e[1])
    if not riders:
        return None
    return {
        '_bucket': 'C',
        'attack': None,
        'save': save,
        # Bracket every remaining bare number (a penalty clause can carry a second, unmatched "-1")
        # -- existing [[ ]] spans are protected wholesale by _brackify_numbers.
        'riders': [_brackify_numbers(r) for r in riders],
        'review': True,
        '_spell_level': level,
        '_snippets': snippets,
    }


def _atk_modifier(value, btype):
    return {'formula': str(value), 'target': 'attack', 'subTarget': 'allAttack',
            'type': (btype or 'untyped').lower(), 'damageType': [], 'critical': 'normal'}


def _dmg_modifier(formula, btype, dtype):
    return {'formula': str(formula), 'target': 'damage', 'subTarget': 'allDamage',
            'type': (btype or 'untyped').lower(),
            # normalize: the regex matches the RULES-PROSE word ("electricity"), pf1 wants its id
            # ("electric") -- see damage_types.py.
            'damageType': [normalize_damage_type(dtype)] if dtype and dtype.lower() != 'untyped' else [],
            'critical': _crit_for(formula)}


def _atk_change(formula, btype):
    return {'formula': str(formula), 'target': 'attack', 'type': (btype or 'untyped').lower(),
            'operator': 'add', 'priority': 0}


def _wdamage_change(formula, btype):
    return {'formula': str(formula), 'target': 'wdamage', 'type': (btype or 'untyped').lower(),
            'operator': 'add', 'priority': 0}


def _disqualified_attack(full, m):
    """True if the attack-roll bonus matched at `m` is NOT a general to-hit buff and must be dropped:
    an AC / confirmation / bonus-to-the-opponent false positive inside the matched span
    (_DISQUALIFY_ATK_RE), OR a crit-CONFIRMATION-only bonus whose "to confirm a critical hit" clause
    trails just past the "attack rolls" the bonus names (_CRIT_CONFIRM_RE, checked a little past the
    match end). Keeps Mirror Strike's "(and confirmation attack roll)" -- a real +N that also rides
    the confirm roll -- because that's the noun, not the verb idiom."""
    if _DISQUALIFY_ATK_RE.search(m.group(0)):
        return True
    return bool(_CRIT_CONFIRM_RE.search(full[m.start(): m.end() + 30]))


def _brackify_numbers(text):
    """Wrap every standalone number in a toggle label in [[ ]] so it renders as a clickable inline
    roll on the card (foundry-conditionals convention). Dice (NdM) first, then bare integers; an
    existing `[[ ... ]]` span is protected wholesale and a digit glued to a word (1st, 2d4's 4) is
    skipped. Signs stay OUTSIDE the brackets ("+5" -> "+[[5]]")."""
    out = []
    for i, seg in enumerate(re.split(r'(\[\[.*?\]\])', text)):
        if i % 2 == 1:                      # an existing [[ ... ]] span -- leave it alone
            out.append(seg)
            continue
        seg = re.sub(r'\b(\d+d\d+)\b', r'[[\1]]', seg)
        seg = re.sub(r'(?<![\w])(\d+)(?![\w])', r'[[\1]]', seg)
        out.append(seg)
    return ''.join(out)


def _dedup_rolled_damage(label, modifiers):
    """Drop a clause that restates a damage modifier's dice from the toggle label -- that damage is
    on the roll (source-labeled by the module), so it must not also live in the name
    (foundry-conditionals rule). Removes "deal/inflict <formula> [points of] [type] damage" forms."""
    for m in modifiers:
        if m.get('target') != 'damage':
            continue
        f = re.escape(str(m.get('formula', '')))
        if not f:
            continue
        label = re.sub(
            r'(?i)\b(?:deals?|dealing|inflicts?|inflicting|takes?|taking|for)?\s*' + f +
            r'(?:/level)?\s*(?:points?\s+of\s+)?[a-z]*\s*damage[,.]?', ' ', label)
    label = re.sub(r'^\s*(?:and|then)\b', '', label, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', label).strip(' ,.;')


def _classify_A(name, full, short, level, save_raw="", desc=""):
    """Bucket A if the spell buffs attack/damage rolls or enhances a weapon; else None.
    Returns a feat_conditionals-style toggle (A-toggle) or a feat_changes-style entry (A).
    A combat-maneuver-on-hit clause adds a `rider` (CMB roll); a save is surfaced as the review-only
    `_save_raw` hint (NOT auto-committed -- a buff's save often belongs to a different spell effect)."""
    snippets = []
    atk_val = atk_type = atk_win = None
    dmg_val = dmg_type = dmg_win = None
    both = False

    m = _ATK_AND_DMG_RE.search(full)
    if m and not _disqualified_attack(full, m):
        atk_val, atk_type, atk_win = m.group(1), m.group(2), _win(full, m)
        dmg_val, dmg_type, dmg_win = m.group(1), m.group(2), atk_win
        both = True
        snippets.append(m.group(0).strip())
    else:
        m = _ATK_FWD_RE.search(full) or _ATK_REV_RE.search(full)
        if m and not _disqualified_attack(full, m):
            atk_val, atk_type, atk_win = m.group(1), m.group(2), _win(full, m)
            snippets.append(m.group(0).strip())
        md = _DMG_BONUS_RE.search(full)
        if md and not _DISQUALIFY_ATK_RE.search(md.group(0)):
            dmg_val, dmg_type, dmg_win = md.group(1), md.group(2), _win(full, md)
            snippets.append(md.group(0).strip())

    # Weapon-enhancer that adds dice (Flame Arrow): only when a weapon noun is present and it's not
    # already captured as a flat damage bonus.
    wpn_dice = None
    if dmg_val is None and _WEAPON_CTX_RE.search(full):
        wd = _WEAPON_DICE_RE.search(full)
        if wd:
            wpn_dice = (wd.group(1), wd.group(2))
            snippets.append(wd.group(0).strip())

    if atk_val is None and dmg_val is None and wpn_dice is None:
        return None

    # Combat-maneuver rider (committed) + a review-only save hint for the curator.
    _extra = {}
    cm_rider = _combat_maneuver_rider(full)
    if cm_rider:
        _extra['rider'] = cm_rider
    _sv = (save_raw or '').strip()
    if _sv and _sv.lower() not in ('none', 'no', 'null'):
        _extra['_save_raw'] = _sv

    one_shot = bool(_ONESHOT_RE.search(full))
    has_dice = wpn_dice is not None
    # Full, UNTRUNCATED toggle label: prefer the original-case short_description, else the full
    # description. No character cap -- the name must carry the whole effect (DCs, range, duration).
    label = (short.strip() or re.sub(r'\s+', ' ', desc).strip())

    if one_shot or has_dice:
        modifiers = []
        if atk_val is not None:
            atk_f, scaled = _scale_formula(atk_val, atk_win)
            modifiers.append(_atk_modifier(atk_f, atk_type))
        if dmg_val is not None:
            dmg_f, _ = _scale_formula(dmg_val, dmg_win)
            modifiers.append(_dmg_modifier(dmg_f, dmg_type, None))
        if wpn_dice is not None:
            modifiers.append(_dmg_modifier(wpn_dice[0], None, wpn_dice[1]))
        # Strip any restated rolled damage from the name, then bracket every remaining number.
        label = _brackify_numbers(_dedup_rolled_damage(label, modifiers))
        return {'_bucket': 'A-toggle', 'name': f"{name}: {label}", 'default': False,
                'modifiers': modifiers, 'review': True, '_spell_level': level,
                '_snippets': snippets, **_extra}

    # Sustained typed bonus -> feat_changes-style always-on change set.
    changes = []
    if atk_val is not None:
        atk_f, _ = _scale_formula(atk_val, atk_win)
        changes.append(_atk_change(atk_f, atk_type))
    if dmg_val is not None:
        dmg_f, _ = _scale_formula(dmg_val, dmg_win)
        changes.append(_wdamage_change(dmg_f, dmg_type))
    return {'_bucket': 'A', 'changes': changes, 'contextNotes': [], 'review': True,
            '_spell_level': level, '_snippets': snippets, **_extra}


def build_draft():
    df = pd.read_csv(SOURCE, sep="|", on_bad_lines="skip", dtype=str, keep_default_na=False)
    draft = {}
    total = a_change = a_toggle = b_melee = b_ranged = c_count = neither = 0
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        total += 1
        short = str(row.get("short_description", ""))
        desc = str(row.get("description", ""))
        full = (short + " " + desc).lower()
        level = str(row.get("spell_level", "")).strip()
        save_raw = str(row.get("saving_throw", ""))
        rng = str(row.get("range", ""))

        entry = _classify_B(name, full, short, save_raw, level)
        if entry is None:
            entry = _classify_A(name, full, short, level, save_raw, desc)
        if entry is None:
            entry = _classify_C(name, full, save_raw, level, rng)
        if entry is None:
            neither += 1
            continue
        # Seed the labeled Range/Cost clauses so a curated draft starts with the six-detail format
        # (the same shape enrich_conditional_riders.py maintains on the finals).
        if entry.get('riders'):
            delivery = cc.spell_delivery(entry.get('attack'), full)
            prepend = [cc.spell_cost_clause(str(row.get('components', '')),
                                            str(row.get('material_costs', ''))),
                       cc.spell_range_clause(rng, delivery)]
            clauses = cc.split_clauses(entry['riders'][0])
            prepend = [p for p in prepend if p and not (
                (cc.states_cost(clauses) and p.startswith('Cost')) or
                (cc.states_range(clauses) and p.startswith('Range')))]
            entry['riders'][0] = cc.brackify(cc.compose(cc.inject_dc(entry['riders'][0]), prepend))
        b = entry['_bucket']
        a_change += b == 'A'
        a_toggle += b == 'A-toggle'
        b_melee += b == 'B-melee'
        b_ranged += b == 'B-ranged'
        c_count += b == 'C'
        draft[name] = entry

    flagged = sum(1 for v in draft.values() if v.get('review'))
    print(f"spells scanned: {total}")
    print(f"  Bucket A  (buff to attack/damage):     {a_change + a_toggle}")
    print(f"      A       sustained changes:         {a_change}")
    print(f"      A-toggle one-shot/dice conditional: {a_toggle}")
    print(f"  Bucket B  (spell is a damaging attack): {b_melee + b_ranged}")
    print(f"      B-melee  melee touch attack:        {b_melee}")
    print(f"      B-ranged ranged touch attack:       {b_ranged}")
    print(f"  Bucket C  (offensive save/area/debuff): {c_count}")
    print(f"  neither (description-only):             {neither}")
    print(f"  total drafted (eligible):               {len(draft)}")
    print(f"  flagged review:                         {flagged}")
    return draft


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    draft = build_draft()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(draft)} draft entries -> {args.out}")


if __name__ == "__main__":
    main()
