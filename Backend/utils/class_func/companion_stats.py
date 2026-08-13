"""The numbers on a bonded creature: the advancement merge, then the stat block.

Map #18, slice G / ticket #31. `animal_companions.py` decides WHICH creature exists and at what
effective level; this module is the only thing that turns that entry into numbers. It writes
`entry['stats']` and nothing else, so the resolver stays a resolver.

D2 makes the backend the sole source of these numbers -- the standalone web sheet has no game system
to derive anything from, so every value here is FINAL. A renderer displays `stats`; it must never
re-derive or re-apply any part of it. That is the whole reason `size_change` below is a record and
not an instruction.

WHO OWNS THE SIZE INCREASE (ticket 04, decided 2026-08-03 from the census)
-------------------------------------------------------------------------
When an advancement block grows a companion, the PF1e size-change table and the published
per-species deltas overlap, and applying both counts the increase twice. The census settles which
one already holds it:

  * 153 of 196 advancement blocks increase size, every one by a single step.
  * Str/Dex/Con match the size table exactly in 118 of those 153 (77%); Dex alone matches in 149
    (97%).
  * Advancement blocks that do NOT change size never carry a negative Dex -- they read `dex +2` or
    `+4`. A `-2` Dex appears ONLY on a size-increasing row.

That last line is the proof: a Dex penalty has no source other than growing, so the published
deltas demonstrably contain the size package already. The ruling therefore splits the table in half
by what the data can be shown to hold:

  * THE DELTAS OWN THE STAT HALF. `str`/`dex`/`con` and the natural-armour delta apply verbatim,
    exactly as published. Nothing is stripped, nothing is topped up to the table, and the 77% / 50%
    raggedness never has to be reconciled -- the published entry is the authority for a companion
    (the standing ruling in `validate_companion_data.py`, which is why it WARNs rather than fails).
  * THE GEOMETRY IS OURS. The size-category modifiers -- AC, attack, CMB/CMD, Stealth and space --
    appear nowhere in `animal_choices.json`, which records only the word `large`. `SIZE_GEOMETRY`
    below supplies them, keyed off the creature's FINAL size, so a companion that was born Small
    gets its +1 too. `size_change` then records the from/to and the modifier deltas the growth
    contributed, purely so a sheet can explain the number. It is provenance, not a second
    application: the values are already inside `ac`, `attacks[].atk`, `cmb`, `cmd` and `skills`.

`Backend/scripts/gates/validate_companion_stats.py` is the gate that keeps this from drifting back.

WHERE EVERY NUMBER COMES FROM (ticket 01, same grill)
-----------------------------------------------------
`abilities`  species `starting statistics` (absolute) + merged deltas + the chassis row's
             `str/dex bonus`, which PF1e adds to BOTH Str and Dex.
`hp`         chassis `hd` x the creature's hit die + Con mod per HD. Maximised under the house rule,
             rolled without it -- `hp_rolls.roll_hp` is class-shaped and cannot be called for a
             creature with no class, so the RULE is shared via `homebrew_enabled`, not the code.
`ac`         10 + size + Dex + natural armour (species base + merged delta + the chassis row's own
             `natural armor bonus`). `touch` drops natural armour, `flat_footed` drops Dex.
`saves`      chassis `fort`/`ref`/`will` (these ARE the base saves) + Con / Dex / Wis.
`bab`        chassis `bab`, verbatim.
`initiative` Dex alone; a companion has no class feature that touches it.
`cmb`/`cmd`  PF1e: BAB + Str + size special; 10 + BAB + Str + Dex + size special.
`attacks`    parsed out of the `attack` prose. Natural attacks are primary, so each is at full BAB +
             Str + size. Damage is as printed; a creature with exactly ONE natural attack adds 1.5x
             Str, per PF1e.
`skills`     the chassis row's `skills` total, spent over the RAW animal list and capped at HD.
`speed`      the merged `speed` string, verbatim.

Then, LAST, the feats and flaws the resolver rolled are folded on top -- see "The modifier fold"
below. Everything above is the chassis; `applied_changes` is the diff.

THE HOUSE RULES THAT CARRY, AND THE ONE THAT DOES NOT
-----------------------------------------------------
Maximised HP carries: `hp_rolls.roll_hp`'s rule is about hit dice, and a companion has hit dice.
The skill-rank floor does NOT. `skill_ranks.class_skill_points` floors a *2-ranks-per-level class*
to 4, and an animal has no class and no per-level rate -- the chassis row hands over one absolute
total. There is nothing for the floor to key off, so it does not apply. The per-skill cap is RAW
(HD), not the house 3x-level cap, for the same reason. The feat economy already went this way in
`animal_companions.animal_feats`.
"""
import json
import os
import random
import re
import zlib
from math import floor

from utils import data
from utils.class_func.skill_ranks import homebrew_enabled

# PF1e Table: Size Modifiers. Keyed by the creature's CURRENT size, not by the step it took --
# `size_change` derives its deltas by differencing two rows of this table. `special` is the size
# modifier to CMB and CMD, which runs opposite to the one on AC and attack rolls. `space` is in feet.
# Reach is deliberately absent: it depends on whether the body is tall or long, and
# `animal_choices.json` records neither.
SIZE_GEOMETRY = {
    'fine':       {'ac': 8,  'special': -8, 'stealth': 16,  'space': 0.5},
    'diminutive': {'ac': 4,  'special': -4, 'stealth': 12,  'space': 1},
    'tiny':       {'ac': 2,  'special': -2, 'stealth': 8,   'space': 2.5},
    'small':      {'ac': 1,  'special': -1, 'stealth': 4,   'space': 5},
    'medium':     {'ac': 0,  'special': 0,  'stealth': 0,   'space': 5},
    'large':      {'ac': -1, 'special': 1,  'stealth': -4,  'space': 10},
    'huge':       {'ac': -2, 'special': 2,  'stealth': -8,  'space': 15},
    'gargantuan': {'ac': -4, 'special': 4,  'stealth': -12, 'space': 20},
    'colossal':   {'ac': -8, 'special': 8,  'stealth': -16, 'space': 30},
}

# Merge rules, per the spec's "The advancement merge". A field named nowhere here APPENDS, which is
# what keeps one-off keys (`sudden charge (ex)`, `bonus feat`, `climb`, `cmd trip`, ...) from being
# lost when a species invents a new one.
REPLACE_FIELDS = ('size', 'attack', 'speed')
ADD_FIELDS = ('ac',)
NEVER_MERGE = ('ability scores', 'source', 'description')

STATS = ('str', 'dex', 'con', 'int', 'wis', 'cha')

# The hit die a bonded creature rolls, by the `animal_choices.json` tier it came from. PF1e types:
# animals, plants and vermin are d8; magical beasts are d10.
TIER_HIT_DIE = {'normal': 8, 'plant': 8, 'vermin': 8, 'magical_beast': 10}
DEFAULT_HIT_DIE = 8

# PF1e Animal Companion rules: "Animal companions with an Intelligence of 1 or 2 can have ranks in
# any of the following skills". Above that they may buy any skill, which is the `int >= 3` branch in
# `_eligible_skills`. Ordered by what an animal actually wants, so the spend is sensible rather than
# uniform noise -- Perception first is the one allocation choice in here, and it is deliberate.
ANIMAL_SKILLS = ('perception', 'stealth', 'survival', 'acrobatics', 'climb', 'swim', 'fly',
                 'escape artist', 'intimidate')
# Skills gated on actually having that movement mode -- a wolf has no business with ranks in Fly.
MOVEMENT_SKILLS = {'fly': 'fly', 'swim': 'swim', 'climb': 'climb'}

# "bite (1d6)", "2 claws (1d4 plus grab)*", "bite (2d6/3)". The count is optional, the parenthetical
# usually holds the damage, and anything after " plus " is a rider. The inner group is greedy and
# `.`-matches newlines so the dire rat's bracketed disease block survives intact; the trailing `\*?`
# is for the two routines that footnote an attack.
ATTACK_RE = re.compile(r'^\s*(?:(\d+)\s+)?([^()]+?)\s*\((.*)\)\s*\*?\s*$', re.DOTALL)
# Four species write the routine WITHOUT parentheses -- `bite 1d8`, `2 claws 1d6`.
BARE_ATTACK_RE = re.compile(r'^\s*(?:(\d+)\s+)?([a-z][a-z ]*?)\s+(\d*d\d+.*?)\s*\*?\s*$')
# Dice off the front, everything after into notes: `1d2 nonlethal` is 1d2 with a qualifier, while
# `ranged touch attack` and `1d6 + 1-1/2 str` are prose and must NOT be handed a Str bonus and a die
# they do not have. The trailing group requires a LETTER, which is what makes the second one fail.
DAMAGE_HEAD_RE = re.compile(r'^(\d*d\d+(?:\s*[+-]\s*\d+)?|\d+)(?:\s+([a-z].*))?$')
# `bite (2d6/3)` -- the scrape's crit multiplier. Anchored, because a loose `'/' in damage` also
# fires on `bite (1d6 + 1-1/2 str)` and eats the tail of a perfectly good damage expression.
CRIT_RE = re.compile(r'^(\d*d\d+)\s*/\s*(\d+)$')
# The axe beak spells out the 1.5x-Str rule inside its damage. We compute that ourselves (see
# `_parse_attacks`), so strip the prose rather than let it disqualify the die.
STR_PROSE_RE = re.compile(r'\s*[+-]\s*(?:1\s*-\s*1/2|1½|1\.5)?\s*str\b\.?', re.IGNORECASE)
# "+4 stealth", "bluff +4, stealth +4" -- both spellings appear in the data.
RACIAL_SKILL_RE = re.compile(r'([+-]\d+)\s*([a-z ]+)|([a-z ]+?)\s*([+-]\d+)')

ADV_RE = re.compile(r'^(\d+)(?:st|nd|rd|th)-level advancement$')
START_RE = re.compile(r'^starting statistics$')


def _mod(score):
    """PF1e ability modifier. `None` is a real value -- a mindless creature has no Int score."""
    if score is None:
        return None
    return floor((int(score) - 10) / 2)


def _natural_armor(value):
    """The +N out of a "+N natural armor" string, or 0."""
    if not isinstance(value, str):
        return 0
    match = re.match(r'^\s*([+-]?\d+)\s*natural armor\s*$', value.strip())
    return int(match.group(1)) if match else 0


def _signed(value):
    """A signed advancement delta as an int, or None when the slot is empty/mindless."""
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------------------------
# The merge
# ---------------------------------------------------------------------------------------------

def merge_advancement(species_stats, effective_level):
    """Fold the species' advancement block into its starting statistics.

    Returns `(merged_block, notes)`. Per the spec: `size`/`attack`/`speed` REPLACE, `ac` and the
    ability scores ADD, and everything else APPENDS -- including keys no species has invented yet,
    which is why the append branch is the default rather than a list.

    A species carries at most one advancement block and it fires at or above its own trigger level,
    so this is a single fold, not a ladder.
    """
    notes = []
    if not isinstance(species_stats, dict):
        return {}, notes

    start = next((v for k, v in species_stats.items()
                  if START_RE.match(str(k)) and isinstance(v, dict)), None)
    if start is None:
        return {}, ['species carries no "starting statistics" block']

    merged = {k: v for k, v in start.items()}
    merged['ability scores'] = dict(start.get('ability scores') or {})

    for key, block in species_stats.items():
        match = ADV_RE.match(str(key))
        if not match or not isinstance(block, dict):
            continue
        trigger = int(match.group(1))
        if effective_level < trigger:
            notes.append(f'{key} not reached (effective level {effective_level})')
            continue
        _fold(merged, block)
        notes.append(f'{key} applied')

    # One-off abilities parked at species level, beside the blocks rather than inside one. The
    # validator calls these out; they are still the creature's, so they append here too.
    for key, value in species_stats.items():
        if ADV_RE.match(str(key)) or START_RE.match(str(key)) or key in NEVER_MERGE:
            continue
        merged[key] = value

    return merged, notes


def _fold(merged, block):
    for field, value in block.items():
        if field == 'ability scores':
            for stat, delta in (value or {}).items():
                step = _signed(delta)
                if step is None or merged['ability scores'].get(stat) is None:
                    continue            # mindless stays mindless; an unparseable delta is skipped
                merged['ability scores'][stat] = int(merged['ability scores'][stat]) + step
        elif field in ADD_FIELDS:
            total = _natural_armor(merged.get(field)) + _natural_armor(value)
            merged[field] = f'{total:+d} natural armor'
        elif field in REPLACE_FIELDS:
            merged[field] = value
        else:
            existing = merged.get(field)
            if existing and str(existing).strip() and str(existing) != str(value):
                merged[field] = f'{existing}, {value}'
            else:
                merged[field] = value


# ---------------------------------------------------------------------------------------------
# The stat block
# ---------------------------------------------------------------------------------------------

def _abilities(merged, chassis):
    """Merged scores plus the chassis row's `str/dex bonus`, which PF1e adds to BOTH."""
    scores = {}
    bonus = int((chassis or {}).get('str/dex bonus') or 0)
    for stat in STATS:
        raw = (merged.get('ability scores') or {}).get(stat)
        if raw is None:
            scores[stat] = None
            continue
        value = int(raw)
        if stat in ('str', 'dex'):
            value += bonus
        scores[stat] = value
    return scores


def _rng(entry, salt=''):
    """A generator OF THIS CREATURE'S OWN, never the module-level `random`.

    Skill allocation, feat picks and flaw rolls are all drawn here, and drawing them from the global
    stream would shift every roll made after this point in the pipeline -- so a companion's feats
    would churn that character's items and backstory too, and every future diff would carry the
    noise. Seeded off the identity the resolver already rolled (species, name, sex, level, grantor),
    so a replayed generation reproduces exactly and two wolves of the same level still differ.

    `salt` gives an independent stream to each consumer. Without it, adding one feat pick would
    walk the skill allocation off its old values for reasons that have nothing to do with skills.
    """
    material = '|'.join(str(entry.get(field)) for field in
                        ('species', 'name', 'sex', 'effective_level', 'grantor', 'type'))
    if salt:
        material = f'{material}|{salt}'
    return random.Random(zlib.crc32(material.encode('utf-8')))


def _hit_points(character, hd, die, con_mod, rng):
    """House rule: a maximised die at every hit die, matching the PC and the pf1 world config."""
    if homebrew_enabled(character):
        rolled = hd * die
    else:
        rolled = sum(rng.randint(1, die) for _ in range(hd))
    return max(1, rolled + con_mod * hd)


# ---------------------------------------------------------------------------------------------
# The modifier fold (spec section 8, D14)
# ---------------------------------------------------------------------------------------------
#
# A companion's feats and flaws ALWAYS apply, so their numbers belong in this stat block -- D2 makes
# it the only source the standalone web sheet has. The Foundry module therefore attaches feat and
# flaw items with `system.changes` STRIPPED (`createCompanions.js`), so pf1 cannot apply the same
# bonus a second time. Buffs are the other half of that contract: they stay situational, keep their
# changes and ship INACTIVE, so they can never double-count and are never folded here.
#
# Which pf1 change target lands where. A target absent from this map is not silently dropped -- it
# is reported on `stats.unapplied`, the same holdback discipline D12 set for `progression_override`.
MODIFIER_TARGETS = {
    'mhp': 'hp',
    'ac': 'ac',
    'nac': 'natural_armor',
    'fort': 'saves.fort',
    'ref': 'saves.ref',
    'will': 'saves.will',
    'init': 'initiative',
    'cmb': 'cmb',
    'cmd': 'cmd',
    'attack': 'attacks',
}
# `skill.<pf1 id>` is handled by prefix rather than by key, against data.SKILL_IDS.
SKILL_TARGET_PREFIX = 'skill.'

# The expression language `companion_feat_changes.json` / the flaw files may use in a `formula`.
# Deliberately tiny: integers, ability-modifier tokens, @hd, + and -, and max(a, b). Anything richer
# is prose and belongs in contextNotes -- which is why this is a hand-written reader and not `eval`.
FORMULA_TOKENS = ('@str', '@dex', '@con', '@int', '@wis', '@cha', '@hd')
_MAX_RE = re.compile(r'^\s*max\s*\(\s*(.+?)\s*,\s*(.+?)\s*\)\s*$', re.IGNORECASE)
_TERM_RE = re.compile(r'([+-]?)\s*(@[a-z]+|\d+)')


class FormulaError(ValueError):
    """A formula the mini-language cannot read. Raised so the validator can name the offender."""


def eval_formula(formula, context):
    """Resolve a `changes[].formula` to an int. `context` supplies the tokens (mods plus `hd`).

    Raises `FormulaError` rather than guessing, because a silently-zero bonus is the failure mode
    this whole fold exists to prevent.
    """
    if isinstance(formula, (int, float)):
        return int(formula)
    text = str(formula or '').strip()
    if not text:
        raise FormulaError('empty formula')

    match = _MAX_RE.match(text)
    if match:
        return max(eval_formula(match.group(1), context), eval_formula(match.group(2), context))

    total, consumed = 0, 0
    for sign, term in _TERM_RE.findall(text):
        if term.startswith('@'):
            if term not in FORMULA_TOKENS:
                raise FormulaError(f'unknown token {term!r} in {text!r}')
            value = int(context.get(term[1:]) or 0)
        else:
            value = int(term)
        total += -value if sign == '-' else value
        consumed += 1
    if not consumed:
        raise FormulaError(f'nothing to read in {text!r}')
    # Guard against a formula the term scan quietly skipped part of (`2 * @hd`, `floor(x/2)`).
    leftovers = _TERM_RE.sub('', text).replace(' ', '')
    if leftovers:
        raise FormulaError(f'unreadable remainder {leftovers!r} in {text!r}')
    return total


def _skill_names_by_id():
    return {pf1_id: name for name, pf1_id in data.SKILL_IDS.items()}


def _apply_one(stats, target, value, bonus_type, skill_names, modes):
    """Add `value` to whatever `target` names. Returns None on success, else why it was refused."""
    if target.startswith(SKILL_TARGET_PREFIX):
        name = skill_names.get(target[len(SKILL_TARGET_PREFIX):])
        if name is None:
            return f'change target {target!r} is not a pf1 skill id'
        # A feat bonus applies whether or not the creature spent ranks here, so an unranked skill is
        # created rather than skipped -- Acrobatic gives +2 Acrobatics to a wolf with no ranks in it.
        # The one exception is a movement-gated skill the body has no speed for: `_eligible_skills`
        # already refuses to sell a wolf ranks in Fly, and inventing the row here would put it back.
        if name in MOVEMENT_SKILLS and name not in modes and name not in stats['skills']:
            return f'{value:+d} {name} not totalled in -- the body has no {name} speed'
        slot = stats['skills'].setdefault(name, {'ranks': 0, 'total': 0})
        slot['total'] += value
        return None

    field = MODIFIER_TARGETS.get(target)
    if field is None:
        return f'no stat-block field for change target {target!r}'
    if field == 'attacks':
        for attack in stats.get('attacks') or []:
            if attack.get('atk') is not None:
                attack['atk'] += value
        return None
    if field == 'natural_armor':
        # Natural armour is in AC and flat-footed AC; touch AC is what ignores it.
        stats['natural_armor'] += value
        stats['ac'] += value
        stats['flat_footed_ac'] += value
        return None
    if field == 'ac':
        stats['ac'] += value
        # A dodge bonus counts against touch attacks and is exactly what being flat-footed loses.
        # Anything else here is an untyped/deflection-style bonus, which applies to all three.
        stats['touch_ac'] += value
        if str(bonus_type or '').lower() != 'dodge':
            stats['flat_footed_ac'] += value
        return None
    if field.startswith('saves.'):
        stats['saves'][field.split('.', 1)[1]] += value
        return None
    stats[field] = stats.get(field, 0) + value
    return None


def apply_modifiers(stats, sources, mods, hd):
    """Fold every feat / flaw effect into `stats`, in place, and record what happened.

    `sources` is [(label, {changes, contextNotes, unapplied})] -- feats from
    `companion_feat_changes.json`, flaws from the creature's own `flaw_effects`. Writes:

      `stats.applied_changes`  one record per change that landed: source, target, value.
      `stats.context_notes`    the situational text, which is real but not a number.
      `stats.unapplied`        every effect this block cannot express, named rather than dropped.

    The provenance matters as much as the arithmetic: `stats` is FINAL for the web sheet, so without
    `applied_changes` there is no way to explain why a wolf's HP is 3 higher than its chassis says.
    """
    context = {stat: (mods.get(stat) or 0) for stat in STATS}
    context['hd'] = hd
    skill_names = _skill_names_by_id()
    speed = str(stats.get('speed') or '').lower()
    modes = {name for name, word in MOVEMENT_SKILLS.items() if word in speed}

    applied, notes, unapplied = [], [], list(stats.get('unapplied') or [])
    for label, effect in sources:
        effect = effect or {}
        for change in effect.get('changes') or []:
            target = str(change.get('target') or '')
            try:
                value = eval_formula(change.get('formula'), context)
            except FormulaError as error:
                unapplied.append(f'{label}: {error}')
                continue
            if not value:
                continue
            refused = _apply_one(stats, target, value, change.get('type'), skill_names, modes)
            if refused:
                unapplied.append(f'{label}: {refused}')
            else:
                applied.append({'source': label, 'target': target, 'value': value})
        for note in effect.get('contextNotes') or []:
            text = note.get('text') if isinstance(note, dict) else note
            if text:
                notes.append({'source': label, 'target': (note or {}).get('target')
                              if isinstance(note, dict) else None, 'text': text})
        unapplied.extend(f'{label}: {item}' if not str(item).startswith(label)
                         else str(item) for item in effect.get('unapplied') or [])

    stats['applied_changes'] = applied
    stats['context_notes'] = notes
    if unapplied:
        stats['unapplied'] = unapplied
    return stats


def _split_top_level(text, separator):
    """Split on `separator`, but only OUTSIDE parentheses and brackets.

    A plain `text.split(',')` is wrong for eight species: `mokele-mbembe` reads
    `"bite (1d8), tail slap (1d8, reach 10 ft. )"` and `dire rat` parks a whole disease block inside
    one parenthetical, commas and all. Splitting naively cuts those in half and both fragments then
    fail to parse.
    """
    parts, depth, buf, step = [], 0, '', len(separator)
    index = 0
    while index < len(text):
        char = text[index]
        if char in '([':
            depth += 1
        elif char in ')]':
            depth = max(0, depth - 1)
        if depth == 0 and text[index:index + step] == separator:
            parts.append(buf)
            buf = ''
            index += step
            continue
        buf += char
        index += 1
    parts.append(buf)
    return [p for p in parts if p.strip()]


def _routine_chunks(routine):
    """[(chunk, is_alternative)] -- one per attack, flagging the far side of an `X or Y`.

    `"bite (1d4) or spit (ranged touch attack, ...)"` is ONE natural attack with an alternative, not
    two. The distinction matters because PF1e's 1.5x-Str rule counts natural attacks.
    """
    chunks = []
    for comma_part in _split_top_level(str(routine or ''), ','):
        for index, alternative in enumerate(_split_top_level(comma_part, ' or ')):
            chunks.append((alternative, index > 0))
    return chunks


def _parse_attacks(routine, bab, str_mod, size_ac, single_attack_str):
    """The `attack` prose as structured lines.

    Every natural attack in a companion's printed routine is PRIMARY, so each is at full BAB; the
    -5 secondary penalty never applies to what is written here. PF1e's one-attack rule does: a
    creature with exactly one natural attack adds 1.5x Str to damage.
    """
    lines = []
    if not isinstance(routine, str) or not routine.strip():
        return lines
    for chunk, is_alternative in _routine_chunks(routine):
        match = ATTACK_RE.match(chunk) or BARE_ATTACK_RE.match(chunk)
        if not match:
            name = chunk.strip()
            if name:
                lines.append({'name': name, 'count': 1, 'atk': None, 'damage': None, 'notes': None,
                              'crit_multiplier': None, 'alternative': is_alternative})
            continue
        count = int(match.group(1) or 1)
        name = match.group(2).strip()
        # The parenthetical is `<damage>[ plus <rider>][, <more prose>]` -- `tail slap
        # (1d8, reach 10 ft. )` keeps its damage only if the trailing prose is split off first.
        # Brackets protect the dire rat's disease block, whose semicolons and commas are all one
        # rider.
        segments = _split_top_level(match.group(3).strip(), ',')
        trailing = ', '.join(s.strip() for s in segments[1:])
        damage, _, rider = (segments[0] if segments else '').partition(' plus ')
        damage = damage.strip()
        damage = STR_PROSE_RE.sub('', damage).strip()
        crit = None
        crit_match = CRIT_RE.match(damage)
        if crit_match:
            damage, crit = crit_match.group(1), crit_match.group(2)
        head = DAMAGE_HEAD_RE.match(damage)
        if head:
            damage, qualifier = head.group(1).strip(), (head.group(2) or '').strip()
            rider = ', '.join(x for x in (qualifier, rider.strip()) if x)
        else:
            # The parenthetical was prose, not dice -- `spit (ranged touch attack, target is
            # sickened ...)`. Keep it as a note rather than inventing a damage die with a Str bonus.
            rider = f'{damage} {rider}'.strip() if rider else damage
            damage = ''
        # PF1e rounds the 1.5x DOWN, and applies a Str PENALTY at 1x -- so this cannot be
        # `round(str_mod * 1.5)`, which would turn a +5 into +8 (banker's rounding) instead of +7.
        bonus = str_mod + str_mod // 2 if (single_attack_str and str_mod > 0) else str_mod
        lines.append({
            'name': name,
            'count': count,
            'atk': bab + str_mod + size_ac,
            'damage': f'{damage}{bonus:+d}' if damage and bonus else damage or None,
            'notes': ', '.join(x for x in (rider.strip(), trailing) if x) or None,
            'crit_multiplier': crit or None,
            'alternative': is_alternative,
        })
    return lines


def _attack_count(routine):
    """Natural attacks in the routine. An `X or Y` alternative is not a second attack."""
    total = 0
    for chunk, is_alternative in _routine_chunks(routine):
        if is_alternative:
            continue
        match = ATTACK_RE.match(chunk)
        total += int(match.group(1) or 1) if match else 0
    return total


def _racial_skill_mods(merged):
    """`+4 stealth` / `bluff +4, stealth +4` off whichever key the scrape used."""
    mods = {}
    for key in ('racial skill modifiers', 'racial skill bonus'):
        text = merged.get(key)
        if not isinstance(text, str):
            continue
        for chunk in text.split(','):
            chunk = chunk.strip().lower()
            match = RACIAL_SKILL_RE.match(chunk)
            if not match:
                continue
            value = match.group(1) or match.group(4)
            name = (match.group(2) or match.group(3) or '').strip()
            if name in data.SKILL_ABILITY and value:
                mods[name] = mods.get(name, 0) + int(value)
    return mods


def _eligible_skills(merged, int_score):
    """The RAW animal list, minus movement skills the creature has no speed for."""
    speed = str(merged.get('speed') or '').lower()
    modes = {name for name, word in MOVEMENT_SKILLS.items() if word in speed}
    eligible = [s for s in ANIMAL_SKILLS if s not in MOVEMENT_SKILLS or s in modes]
    if int_score is not None and int_score >= 3:
        # PF1e: at Int 3+ it may buy any skill. Keep the animal list at the front of the queue --
        # ranks still go where an animal wants them, the rest of the list only widens the choice.
        # Only the griffon reaches this branch today. `craft`/`perform`/`profession` are excluded
        # because they are umbrella skills: a rank in one is meaningless without a chosen speciality,
        # and nothing here can choose one.
        eligible += [s for s in data.skills
                     if s not in eligible and s not in ('craft', 'perform', 'profession')]
    return eligible


def _skills(merged, chassis, abilities, hd, size_stealth, rng):
    """Spend the chassis row's skill total, then total each rank into a modifier.

    Cap is HD, which is RAW. The house 3x-per-level cap keys off a CHARACTER level a companion does
    not have, and the house rank floor keys off a class it does not have -- see the module docstring.
    """
    budget = int((chassis or {}).get('skills') or 0)
    if abilities.get('int') is None:
        # PF1e: a mindless creature (no Int score at all) cannot have skill ranks. 24 species are --
        # the vermin and most of the plants. The chassis row still offers a rank total, because that
        # table was written for animals; spending it would put ranks on a creature the rules say
        # cannot hold them. Racial bonuses below are a property of the body and survive.
        budget = 0
    racial = _racial_skill_mods(merged)
    eligible = _eligible_skills(merged, abilities.get('int'))
    ranks = {}
    if eligible and budget > 0:
        # Perception first (every animal wants it), then a shuffled round robin over the rest, so
        # two wolves of the same level do not come out identical.
        head, tail = eligible[:1], eligible[1:]
        rng.shuffle(tail)
        queue = head + tail
        index = 0
        while budget > 0 and any(ranks.get(s, 0) < hd for s in queue):
            skill = queue[index % len(queue)]
            index += 1
            if ranks.get(skill, 0) >= hd:
                continue
            ranks[skill] = ranks.get(skill, 0) + 1
            budget -= 1

    out = {}
    for skill in sorted(set(list(ranks) + list(racial))):
        rank = ranks.get(skill, 0)
        ability = data.SKILL_ABILITY.get(skill)
        mod = _mod(abilities.get(ability)) or 0
        total = rank + mod + racial.get(skill, 0)
        if rank:
            total += 3                       # trained in one of its own class skills
        if skill == 'stealth':
            total += size_stealth
        out[skill] = {'ranks': rank, 'total': total}
    return out


def _size_change(start_size, final_size):
    """What growing contributed, as a record. The values are ALREADY inside the stat block."""
    if not start_size or not final_size or start_size == final_size:
        return None
    was = SIZE_GEOMETRY.get(start_size)
    now = SIZE_GEOMETRY.get(final_size)
    if was is None or now is None:
        return None
    return {
        'from': start_size,
        'to': final_size,
        'ac': now['ac'] - was['ac'],
        'attack': now['ac'] - was['ac'],
        'cmb_cmd': now['special'] - was['special'],
        'stealth': now['stealth'] - was['stealth'],
        'space': now['space'],
        'note': ('already applied in this stat block; the published ability-score and natural-armour '
                 'deltas carry the rest of the size change, so do not re-apply either half'),
    }


def companion_stats(character, entry):
    """The finished `stats` block for one bonded creature. `None` when there is nothing to stat."""
    chassis = entry.get('chassis') or {}
    if not entry.get('species') or not chassis:
        return None

    merged, notes = merge_advancement(entry.get('species_stats'), entry.get('effective_level') or 0)
    if not merged:
        return None
    rng = _rng(entry)

    abilities = _abilities(merged, chassis)
    mods = {stat: _mod(score) for stat, score in abilities.items()}
    size = str(merged.get('size') or 'medium').strip().lower()
    geometry = SIZE_GEOMETRY.get(size, SIZE_GEOMETRY['medium'])

    hd = int(chassis.get('hd') or 1)
    die = TIER_HIT_DIE.get(entry.get('kind'), DEFAULT_HIT_DIE)
    bab = int(chassis.get('bab') or 0)
    natural = _natural_armor(merged.get('ac')) + int(chassis.get('natural armor bonus') or 0)

    dex_mod = mods.get('dex') or 0
    str_mod = mods.get('str') or 0
    con_mod = mods.get('con') or 0

    routine = merged.get('attack')
    stats = {
        'size': size,
        'space': geometry['space'],
        'hd': hd,
        'hit_die': f'd{die}',
        'hp': _hit_points(character, hd, die, con_mod, rng),
        'abilities': abilities,
        'ability_modifiers': mods,
        'ac': 10 + geometry['ac'] + dex_mod + natural,
        'touch_ac': 10 + geometry['ac'] + dex_mod,
        'flat_footed_ac': 10 + geometry['ac'] + natural,
        'natural_armor': natural,
        'saves': {
            'fort': int(chassis.get('fort') or 0) + con_mod,
            'ref': int(chassis.get('ref') or 0) + dex_mod,
            'will': int(chassis.get('will') or 0) + (mods.get('wis') or 0),
        },
        'bab': bab,
        # Initiative is Dex alone for a creature with no class features that touch it. It exists as
        # its own field because Improved Initiative is in the companion feat pool and `init` has to
        # have somewhere to land.
        'initiative': dex_mod,
        'cmb': bab + str_mod + geometry['special'],
        'cmd': 10 + bab + str_mod + dex_mod + geometry['special'],
        'speed': merged.get('speed'),
        'attacks': _parse_attacks(routine, bab, str_mod, geometry['ac'],
                                  _attack_count(routine) == 1),
        'skills': _skills(merged, chassis, abilities, hd, geometry['stealth'], rng),
        'special_qualities': merged.get('special qualities'),
        'special_attacks': merged.get('special attacks'),
        'bonus_tricks': int(chassis.get('bonus tricks') or 0),
        'special': chassis.get('special'),
        'size_change': _size_change(_starting_size(entry.get('species_stats')), size),
        'other': _leftovers(merged),
        'merge_notes': notes,
    }

    if entry.get('progression_override'):
        # The archetype's progression change is PROSE (`why` / `confidence`), not a structured veto,
        # and the scope boundary in SESSION_PLAN §3 forbids building a classifier for it. Say so on
        # the entry rather than let the stat block imply it was honoured.
        stats['unapplied'] = ['progression_override: ' +
                              str(entry['progression_override'].get('why')
                                  or entry['progression_override'].get('source') or 'see archetype')]

    # D14: the feats and flaws the resolver rolled are folded in LAST, on top of the chassis numbers,
    # so `applied_changes` reads as a diff against a stat block that is otherwise pure chassis.
    apply_modifiers(stats, modifier_sources(entry), mods, hd)
    return stats


_FEAT_CHANGES_CACHE = None


def feat_change_data():
    """`companion_feat_changes.json`, cached. Separate from `feat_changes.json` on purpose -- see
    that file's `_readme`: the pf1 compendium already automates 12 of these feats, and a PC keeps its
    compendium item's changes, so sharing one file would double-apply on every PC sheet."""
    global _FEAT_CHANGES_CACHE
    if _FEAT_CHANGES_CACHE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', '..', 'json', 'feats', 'companion_feat_changes.json')
        try:
            with open(path, encoding='utf-8') as handle:
                loaded = json.load(handle)
        except (OSError, ValueError):
            loaded = {}
        _FEAT_CHANGES_CACHE = {key: value for key, value in loaded.items()
                               if not str(key).startswith('_')}
    return _FEAT_CHANGES_CACHE


def modifier_sources(entry):
    """[(label, effect)] for every feat and flaw on the entry, in the order they are displayed.

    Feat-tax children count exactly like the feats that bought them -- they are feats the creature
    owns -- so they contribute their own changes rather than riding on the primary's.
    """
    changes = feat_change_data()
    sources = []
    for name in list(entry.get('feats') or []) + list(entry.get('flaw_feats') or []):
        effect = changes.get(name)
        if effect:
            sources.append((name, effect))
    for primary, children in (entry.get('feat_tax_dict') or {}).items():
        for child in children or []:
            effect = changes.get(child)
            if effect:
                sources.append((f'{child} (via {primary})', effect))
    for name, effect in (entry.get('flaw_effects') or {}).items():
        tier = str((effect or {}).get('tier') or 'minor').title()
        sources.append((f'({tier} flaw) {name}', effect))
    return sources


# Merged keys that a named field above already carries. Everything else survives into `stats.other`.
CONSUMED = ('size', 'speed', 'ac', 'attack', 'ability scores', 'special qualities',
            'special attacks', 'source', 'description')


def _leftovers(merged):
    """The merged keys no named stat field carries -- `climb`, `fly`, `bonus feat`, `cmd trip`,
    `sudden charge (ex)`, and whatever a future species invents.

    The spec's Export section called for an advancement-MERGED `species_stats` on the entry. That key
    cannot move: it is one of the five the `animal_companion` alias is frozen at (D9), and swapping
    its content from raw to merged would silently change what the sheet repo's #15 consumer renders.
    So `species_stats` stays raw and the merge's output lands in `stats` -- and this field is what
    makes that lossless, because a one-off ability nobody enumerated is exactly what would otherwise
    vanish between the two.
    """
    return {key: value for key, value in merged.items()
            if key not in CONSUMED and value not in (None, '', {}, [])}


def _starting_size(species_stats):
    if not isinstance(species_stats, dict):
        return None
    start = next((v for k, v in species_stats.items()
                  if START_RE.match(str(k)) and isinstance(v, dict)), None)
    if not start:
        return None
    return str(start.get('size') or '').strip().lower() or None


def stat_bonded_creatures(character):
    """Write `stats` onto every bonded creature the resolver produced.

    Runs after `animal_feats`, so a creature's feats are on the entry before its numbers are. An
    ABSENCE entry gets `stats: None` -- it has no creature, and D9 already established that a
    uniform key set with nulls ships a ghost a renderer will draw.
    """
    for entry in getattr(character, 'bonded_creatures', None) or []:
        if entry.get('type') == 'familiar' and entry.get('species'):
            # A familiar's numbers key off the MASTER (half HP, master BAB/saves/ranks), none of
            # which are final this early in the pipeline -- familiars.stat_familiars is the late
            # pass that fills these in after phase_luck_resolution. Absence entries still fall
            # through and get stats: None like everyone else's.
            continue
        entry['stats'] = companion_stats(character, entry)
    return character.bonded_creatures if hasattr(character, 'bonded_creatures') else []
