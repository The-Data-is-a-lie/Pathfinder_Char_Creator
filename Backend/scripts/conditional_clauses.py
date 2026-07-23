"""Shared, pure, IDEMPOTENT clause builders for the six-detail conditional rider format.

A per-roll conditional's `rider` (spells) / `name` tail (talents) is a `; `-separated list of
LABELED clauses in a fixed order:

    Cost: ...; Activation: ...; Range: ...; Save: ...; Effect: ...

Damage stays on the structured `modifiers[]` (restated in `Effect:` only when the compendium rolls
it and no modifier exists). Every number is wrapped in a `[[ ]]` inline roll (foundry-conditionals
house rule) so the validators pass and the card renders clickable dice.

This module is imported by:
  * enrich_conditional_riders.py -- upgrades the already-curated finals (append only MISSING clauses,
    never clobber hand-written wording -- see that script).
  * build_spell_conditionals.py / build_talent_conditionals.py -- so newly generated DRAFTS start
    enriched.

Design rules (why it is safe to run repeatedly):
  * compose() appends a labeled clause only when no clause with that label already exists.
  * The caller additionally suppresses a clause when the same *content* is already stated unlabeled
    (states_save / states_cost / states_range) -- so we never duplicate a curated save/range/cost.
  * Distances / DCs scale with the actor via native roll-data tokens: `@spells.primary.cl.total` for
    caster level (resolves on both the applier weapon conditional and the module's spell-item rider);
    the spell save DC uses `@slvl` (spell level) + `@castMod` (casting-ability mod), which the
    consumer substitutes at attach time (applier macro + module addSpellRiders/addSpellConditionals).
"""
import re

# --- constants -----------------------------------------------------------------------------------
CL = "@spells.primary.cl.total"                 # caster level, actor-native on both consumers
DC_SPELL = "[[ 10 + @slvl + @castMod ]]"        # @slvl/@castMod substituted at attach time
CLAUSE_LABELS = ("Cost", "Activation", "Range", "Save", "Effect")
_ORDER = {lbl.lower(): i for i, lbl in enumerate(CLAUSE_LABELS)}

_LABEL_RE = re.compile(r'^\s*(Cost|Activation|Range|Save|Effect)\s*:', re.IGNORECASE)
_SAVE_WORD_RE = re.compile(r'\b(fortitude|reflex|will)\s+save\b', re.IGNORECASE)
_COST_WORD_RE = re.compile(r'spell\s+points?|martial\s+focus|\bgp\b', re.IGNORECASE)
# An unlabeled range/delivery already stated in curated text (avoid a duplicate Range clause).
_RANGE_WORD_RE = re.compile(
    r'\b(?:melee|ranged)\s+touch\b|\branged\s+attack\b|\btouch\s+attack\b|'
    r'\bwithin\s+\[\[|\bclose\s+range\b|\bmedium\s+range\b|\blong\s+range\b', re.IGNORECASE)


def brackify(text):
    """Wrap every standalone number in [[ ]] (dice first, then bare ints); an existing [[ ]] span is
    protected wholesale and a digit glued to a word (1st, the 4 in 2d4) is skipped. Mirrors
    build_spell_conditionals._brackify_numbers so clauses always pass the validators."""
    out = []
    for i, seg in enumerate(re.split(r'(\[\[.*?\]\])', text)):
        if i % 2 == 1:                          # an existing [[ ... ]] span -- leave it alone
            out.append(seg)
            continue
        seg = re.sub(r'\b(\d+d\d+)\b', r'[[\1]]', seg)
        seg = re.sub(r'(?<![\w])(\d+)(?![\w])', r'[[\1]]', seg)
        out.append(seg)
    return ''.join(out)


# --- clause inspection (idempotency) -------------------------------------------------------------
def split_clauses(rider):
    return [c.strip() for c in re.split(r';\s*', rider or '') if c.strip()]


def label_of(clause):
    m = _LABEL_RE.match(clause or '')
    return m.group(1).capitalize() if m else None


def has_label(clauses, label):
    lo = label.lower()
    return any((label_of(c) or '').lower() == lo for c in clauses)


def states_save(clauses):
    return has_label(clauses, 'Save') or any(_SAVE_WORD_RE.search(c) for c in clauses)


def states_cost(clauses):
    return has_label(clauses, 'Cost') or any(
        label_of(c) is None and _COST_WORD_RE.search(c) for c in clauses)


def states_range(clauses):
    return has_label(clauses, 'Range') or any(
        label_of(c) is None and _RANGE_WORD_RE.search(c) for c in clauses)


def compose(rider, prepend):
    """Return `rider` with each labeled clause in `prepend` prepended IN FIXED ORDER, skipping any
    whose label is already present. Existing clauses are never reworded or reordered."""
    clauses = split_clauses(rider)
    add = []
    for c in prepend:
        if not c:
            continue
        lbl = label_of(c)
        if lbl and has_label(clauses, lbl):
            continue                            # already there -- idempotent no-op
        add.append(c)
    add.sort(key=lambda c: _ORDER.get((label_of(c) or '').lower(), 99))
    return "; ".join(add + clauses)


# --- SPELL clause builders -----------------------------------------------------------------------
def spell_delivery(attack, description):
    """melee touch / ranged touch / ranged attack from the entry's `attack` + the spell text; None
    for area / no-attack-roll (Bucket C) spells."""
    d = (description or '').lower()
    if attack == 'melee':
        return 'melee touch'
    if attack == 'ranged':
        if 'ranged touch' in d:
            return 'ranged touch'
        if 'ranged attack roll' in d:
            return 'ranged attack'
        return 'ranged touch'
    return None


def spell_range_clause(range_raw, delivery=None):
    """`Range: <delivery>, <distance>` from the CSV `range` column. Abstract bands expand to
    CL-scaled inline-roll feet; literals pass through; unknown text passes through brackified."""
    r = (range_raw or '').strip().lower()
    dist = None
    if r.startswith('close'):
        per2 = '2 level' in r                   # "5 ft./2 levels" vs the rarer "5 ft./level"
        dist = f"[[25 + 5*floor({CL}/2)]] ft" if per2 else f"[[25 + 5*{CL}]] ft"
    elif r.startswith('medium'):
        dist = f"[[100 + 10*{CL}]] ft"
    elif r.startswith('long'):
        dist = f"[[400 + 40*{CL}]] ft"
    elif r == 'touch':
        dist = 'touch'
    elif r == 'personal':
        dist = 'personal'
    elif re.match(r'^\d+\s*ft', r):
        feet = re.match(r'^(\d+)', r).group(1)
        dist = f"[[{feet}]] ft"
    elif r and r not in ('', 'see text'):
        dist = brackify((range_raw or '').strip())   # "1 mile/level", "unlimited", ...
    if dist == 'touch' and delivery and 'touch' in delivery:
        dist = None                             # "melee touch, touch" -> "melee touch"
    parts = [p for p in (delivery, dist) if p]
    if not parts:
        return None
    return "Range: " + ", ".join(parts)


_MAT_PAREN_RE = re.compile(r'\bM\b\s*(?:/\s*DF)?\s*\(([^)]*)\)', re.IGNORECASE)


def spell_cost_clause(components, material_costs):
    """`Cost: [[N]] gp material component (<name>)` when the spell has a gp-valued material component;
    None otherwise. Plain V/S/F and the daily slot are not costs (per the locked decision)."""
    mc = (material_costs or '').strip()
    if not mc or mc.upper() == 'NULL' or not re.match(r'^\d', mc):
        return None
    n = re.match(r'^(\d[\d,]*)', mc).group(1).replace(',', '')
    if int(n) <= 0:
        return None
    label = f"Cost: [[{n}]] gp material component"
    mp = _MAT_PAREN_RE.search(components or '')
    if mp:
        desc = re.sub(r'\s*(?:,?\s*worth\s+[\d,]+\s*gp.*|,?\s*worth\s+.*)$', '', mp.group(1),
                      flags=re.IGNORECASE).strip()
        desc = re.sub(r'^(?:an?|the)\s+', '', desc, flags=re.IGNORECASE).strip(' .,')
        if desc and len(desc) < 60:
            label += f" ({desc})"
    return brackify(label)                       # bracket any bare number left in the component name


_SAVE_INJECT_RE = re.compile(r'\b(Fortitude|Reflex|Will)\s+Save\b(?!\s+DC)', re.IGNORECASE)


def inject_dc(text):
    """Insert the computed spell DC right after an already-written `<Type> Save` that lacks one.
    Surgical + idempotent (the negative lookahead skips a clause that already has `DC`); it adds the
    missing number without touching the surrounding curated wording."""
    return _SAVE_INJECT_RE.sub(lambda m: f"{m.group(0)} DC {DC_SPELL}", text or '')


def spell_save_dc_clause(save_block):
    """`Save: <Type> DC [[ 10 + @slvl + @castMod ]] <result>` from a spell's save block. Used ONLY
    when the curated riders don't already state the save (non-destructive)."""
    if not save_block:
        return None
    t = str(save_block.get('type', '')).strip().capitalize()
    if t.lower() not in ('fortitude', 'reflex', 'will'):
        return None
    res = str(save_block.get('description') or '').strip()
    res = re.sub(r'^(?:fortitude|reflex|will)\s+', '', res, flags=re.IGNORECASE).strip(' ;,')
    res = re.sub(r'\s{2,}', ' ', res) or 'negates'
    return f"Save: {t} DC {DC_SPELL} {res}".strip()


# --- CLASS FEATURE clause builders ---------------------------------------------------------------
# section -> (class whose level scales the DC, key ability, how the ability was decided). Read off
# the pools' own DC sentences where they exist; see class_feature_save_dc() for what the confidence
# values mean. Fighter trainings state no DCs at all.
CLASS_FEATURE_DC = {
    'rage_powers':          ('barbarian',    'str', 'varies'),
    'ki_powers':            ('monk',         'wis', 'assumed'),
    'discoveries':          ('alchemist',    'int', 'assumed'),
    'hexes':                ('witch',        'int', 'varies'),
    'rogue_talents':        ('rogue',        'int', 'assumed'),
    # Cha 9 / Int 6 across the pool's own DC sentences, plus stray Wis/Dex from shared rogue talents:
    # ki-powered tricks key off Charisma, the inherited rogue ones off Intelligence. Read the power.
    'ninja_talents':        ('ninja',        'cha', 'varies'),
    'slayer_talents':       ('slayer',       'int', 'stated'),
    'investigator_talents': ('investigator', 'int', 'assumed'),
    'vigilante_talents':    ('vigilante',    'cha', 'assumed'),
    'social_talents':       ('vigilante',    'cha', 'assumed'),
    'arcana':               ('magus',        'int', 'stated'),
    'mercy':                ('paladin',      'cha', 'assumed'),
    'cruelty':              ('antipaladin',  'cha', 'assumed'),
    'exploits':             ('arcanist',     'cha', 'stated'),
    'mysteries':            ('oracle',       'cha', 'stated'),
    'curses':               ('oracle',       'cha', 'stated'),
    'armor_training':       (None,           None,  'none'),
    'weapon_training':      (None,           None,  'none'),
}


# --- TALENT clause builders ----------------------------------------------------------------------
_SP_ANY_RE = re.compile(
    r'spend(?:s|ing)?\s+(?:\[\[)?\s*(?:a|\d+)\s*(?:\]\])?\s+spell\s+points?', re.IGNORECASE)
_SP_BENEFIT_RE = re.compile(r'spend(?:s|ing)?\s+(a|\d+)\s+spell\s+points?', re.IGNORECASE)


def talent_spellpoint_count(benefit):
    """Real spell-point count named in the talent benefit ('a' -> 1), or None."""
    m = _SP_BENEFIT_RE.search(benefit or '')
    if not m:
        return None
    return 1 if m.group(1).lower() == 'a' else int(m.group(1))


def talent_fix_spellpoint(rider, benefit):
    """Replace the seed's hardcoded `spend [[1]] spell point` with the REAL count from the benefit
    (fixes build_talent_conditionals._rider_seed's always-1 bug). Idempotent."""
    n = talent_spellpoint_count(benefit)
    if n is None:
        return rider
    plural = 's' if n != 1 else ''
    return _SP_ANY_RE.sub(f"spend [[{n}]] spell point{plural}", rider)


def class_feature_save_dc(section):
    """(dc_formula, confidence) for a class-choice pool's save DC, or (None, 'none').

    A power's own text almost never states its DC (rage powers 0 of 173, ki powers 0 of 9, hexes 6 of
    59, arcana 17 of 122), so the formula comes from the POOL: PF1's "10 + 1/2 class level + key
    ability". Confidence says how the ability was decided, and is carried into the worklist so a
    curator knows when to check the power's own words first:
      stated  -- the pool's own text spells this ability out
      varies  -- the pool mixes abilities (rage powers use Str, Cha and Con; the hexes pool holds
                 shaman hexes, which key off Wis rather than the witch's Int)
      assumed -- no DC anywhere in the pool; the class's key ability, to be confirmed on use
    See docs/class_feature_conditional_decision_rules.md.
    """
    entry = CLASS_FEATURE_DC.get(section)
    if not entry or not entry[0]:
        return None, 'none'
    cls, ability, confidence = entry
    formula = f"[[ 10 + floor(@classes.{cls}.level / 2) + @abilities.{ability}.mod ]]"
    return formula, confidence


def talent_range_clause(benefit):
    """Conservative `Range:` from a talent benefit -- only when clearly derivable, else None."""
    b = benefit or ''
    if re.search(r'ranged\s+touch', b, re.IGNORECASE):
        return "Range: ranged touch"
    m = re.search(r'(\d+)[\s-]*(?:foot|ft\.?)[\s-]*(cone|line|burst|radius)', b, re.IGNORECASE)
    if m:
        return f"Range: [[{m.group(1)}]] ft {m.group(2).lower()}"
    m = re.search(r'within\s+(\d+)\s*(?:feet|ft\.?)', b, re.IGNORECASE)
    if m:
        return f"Range: ranged, [[{m.group(1)}]] ft"
    if re.search(r'\btouch\s+attack\b', b, re.IGNORECASE):
        return "Range: melee touch"
    return None
