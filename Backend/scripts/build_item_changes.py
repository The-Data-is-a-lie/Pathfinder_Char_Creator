"""Build Backend/json/items/item_changes.json from items_best.json descriptions.

Scans every slot item's description prose for bonuses. Clean, unconditional
numeric bonuses ("+2 competence bonus on Intimidate checks") become pf1
change dicts; bonus sentences that are conditional or unparseable become
contextNotes so the sheet still surfaces them. Sentences with no bonus but
a mechanical effect (activated abilities, uses/day, saves, granted spells)
become one summarizing contextNote per item, with dice/DCs/durations wrapped
as [[ ]] inline rolls per the house conditional style. Hand-tuned corrections
in item_changes_overrides.json are merged on top (full replacement per item).

Run:  python Backend/scripts/build_item_changes.py [--report]
      --report prints unparsed bonus sentences and low-confidence auto notes
      instead of writing the file.
"""
import json, os, re, sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS_PATH = os.path.join(BACKEND, 'json', 'items_best.json')
OUT_DIR = os.path.join(BACKEND, 'json', 'items')
OUT_PATH = os.path.join(OUT_DIR, 'item_changes.json')
OVERRIDES_PATH = os.path.join(OUT_DIR, 'item_changes_overrides.json')

BONUS_TYPES = {
    'competence': 'competence', 'enhancement': 'enh', 'resistance': 'resist',
    'deflection': 'deflection', 'insight': 'insight', 'luck': 'luck',
    'morale': 'morale', 'sacred': 'sacred', 'profane': 'profane',
    'dodge': 'dodge', 'circumstance': 'circumstance', 'alchemical': 'alchemical',
    'natural armor': 'enh', 'natural': 'enh', 'untyped': 'untyped',
    # armor/shield bonuses are pf1 'base' type on their own AC layer (aac/sac)
    'armor': 'base', 'shield': 'base',
}
TYPE_RE = '|'.join(sorted(BONUS_TYPES, key=len, reverse=True))

SKILLS = {
    'acrobatics': 'acr', 'appraise': 'apr', 'artistry': 'art', 'bluff': 'blf',
    'climb': 'clm', 'craft': 'crf', 'diplomacy': 'dip', 'disable device': 'dev',
    'disguise': 'dis', 'escape artist': 'esc', 'fly': 'fly', 'handle animal': 'han',
    'heal': 'hea', 'intimidate': 'int', 'linguistics': 'lin', 'lore': 'lor',
    'perception': 'per', 'perform': 'prf', 'profession': 'pro', 'ride': 'rid',
    'sense motive': 'sen', 'sleight of hand': 'slt', 'spellcraft': 'spl',
    # common typos in the scraped source data
    'sleight of hands': 'slt', 'slight of hand': 'slt',
    'stealth': 'ste', 'survival': 'sur', 'swim': 'swm', 'use magic device': 'umd',
    'knowledge (arcana)': 'kar', 'knowledge (dungeoneering)': 'kdu',
    'knowledge (engineering)': 'ken', 'knowledge (geography)': 'kge',
    'knowledge (history)': 'khi', 'knowledge (local)': 'klo',
    'knowledge (nature)': 'kna', 'knowledge (nobility)': 'kno',
    'knowledge (planes)': 'kpl', 'knowledge (religion)': 'kre',
}
ABILITIES = {'strength': 'str', 'dexterity': 'dex', 'constitution': 'con',
             'intelligence': 'int', 'wisdom': 'wis', 'charisma': 'cha'}

# ordered: first match wins for non-skill targets found inside a bonus phrase
PHRASE_TARGETS = [
    (r'natural armor', 'nac'),
    (r'armor class|\bac\b', 'ac'),
    (r'fortitude sav', 'fort'),
    (r'reflex sav', 'ref'),
    (r'will sav', 'will'),
    (r'saving throws|\bsaves\b', 'allSavingThrows'),
    (r'initiative', 'init'),
    (r'combat maneuver defense|\bcmd\b', 'cmd'),
    (r'combat maneuver checks?|combat maneuvers|grapple checks?|\bcmb\b', 'cmb'),
    (r'attack rolls', 'attack'),
    (r'damage rolls', 'damage'),
]

# a bonus sentence with any of these is situational -> context note, not a change
CONDITIONAL_RE = re.compile(
    r'\b(when|whenever|while|if|against|versus|vs\.|once per|per day|1/day|'
    r'made to|made as|made while|to confirm|during|only|except|to avoid|'
    r'to resist|to escape|related to|allies|adjacent|within|opposed|'
    r'underwater|in dim light|in darkness|at night|first|'
    r'for example|for instance|e\.g\.)\b', re.I)

# crafting/comparison rules text, not a bonus the wearer gains
NOISE_RE = re.compile(r'(need(s)?\s+to\s+have|must\s+have)\s+a\s+\+\d+\s+enhancement bonus', re.I)

# phrase captures exclude '+' so a later bonus in the same sentence can never
# leak into an earlier phrase ("+3 ... saving throws, +4 armor bonus to ac")
BONUS_RE = re.compile(
    rf'\+(\d+)\s+(?:({TYPE_RE})\s+)?bonus\s+(?:on|to|upon|for)\s+([^.;+]{{1,120}})', re.I)
# reversed order: "an enhancement bonus to strength of +4" / "to his natural armor from +1 to +5"
BONUS_REV_RE = re.compile(
    rf'(?:({TYPE_RE})\s+)bonus\s+(?:on|to)\s+([^.;+]{{1,80}}?)\s+(?:of|from)\s+\+(\d+)', re.I)
# "a deflection bonus of +1 to +5 to AC" — bonus of +N (tier list) to <target>
BONUS_OF_RE = re.compile(
    rf'(?:({TYPE_RE})\s+)?bonus\s+of\s+\+(\d+)(?:\s*(?:,|to|or|/|–|—|-)\s*(?:or\s+)?\+\d+)*'
    rf'\s+(?:on|to|upon)\s+([^.;+]{{1,120}})', re.I)

# "when fastened about the waist, ..." is how the item is worn, not a situational condition
WEAR_CLAUSE_RE = re.compile(
    r'^\s*(?:when|while|once)\s+(?:fastened|worn|donned|wrapped|placed|strapped|attuned|slipped)'
    r'[^,]*,\s*', re.I)

# a sentence with any of these is a mechanical effect worth a context note
MECHANICAL_RE = re.compile(
    r'\bas an? (?:standard|swift|move|full[- ]round|free|immediate) action\b'
    r'|\bonce per (?:day|week|month|round)\b|\b\d+\s*(?:times? )?(?:/|per )\s*(?:day|week)\b'
    r'|\bat will\b|\bcommand word\b|\bon command\b|\bcharges?\b'
    r'|\bfunctions? (?:as|like)\b|\bas (?:if|though) (?:using|casting|under|affected)\b'
    r'|\bcan cast\b|\bcan use\b|\bcaster level\b|\bspell-like\b'
    r'|\bDC\s*\d+\b|\bmust succeed\b|\bsaving throw\b|\bsave\b'
    r'|\bimmun(?:e|ity)\b|\bresistance\b|\bdamage reduction\b|\bfast healing\b'
    r'|\breroll\b|\bconcealment\b|\bdarkvision\b|\blow-light vision\b|\bsee invisib'
    r'|\btemporary hit points\b|\bis treated as\b|\balways treated\b|\bignores?\b'
    r'|\bbreathe\b|\b(?:fly|climb|swim|burrow) speed\b', re.I)

# numerals that are bookkeeping, not mechanics — stripped before the numeral test
NUM_NOISE_RE = re.compile(r'(?:[\d,]+\s*gp\b|\d+\s*lbs?\.?|\bpg\.\s*\d+)', re.I)

NOTE_CAP = 600  # soft cap for an auto effect note; truncate at a sentence boundary

# inline-roll wrapping, whitelist only: dice, DC N, +N bonuses, durations,
# uses/day, and range/radius distances. One pass so insertions never nest.
ROLL_RE = re.compile(
    r'(?P<dice>\b\d+d\d+(?:\s*[+-]\s*\d+)?\b)'
    r'|(?P<dc>\bDC\s*)(?P<dcnum>\d+)\b'
    r'|(?P<plus>\+)(?P<plusnum>\d+)\b'
    r'|\b(?P<durnum>\d+)(?P<durunit>\s*(?:round|minute|hour)s?\b)'
    r'|\b(?P<usesnum>\d+)(?P<usesunit>\s*(?:times? )?(?:/|per )\s*(?:day|week)\b)'
    r'|\b(?P<feetnum>\d+)(?P<feetunit>[- ]?(?:foot|feet|ft\.?)\b)', re.I)


def _wrap(m):
    if m.group('dice'):
        return f"[[{m.group('dice')}]]"
    if m.group('dc'):
        return f"{m.group('dc')}[[{m.group('dcnum')}]]"
    if m.group('plus'):
        return f"+[[{m.group('plusnum')}]]"
    if m.group('durnum'):
        return f"[[{m.group('durnum')}]]{m.group('durunit')}"
    if m.group('usesnum'):
        return f"[[{m.group('usesnum')}]]{m.group('usesunit')}"
    return f"[[{m.group('feetnum')}]]{m.group('feetunit')}"


def wrap_rolls(text):
    """Wrap rollable/mechanical numbers in [[ ]] per the house note style."""
    return ROLL_RE.sub(_wrap, text)


def is_mechanical(sentence):
    """A no-bonus sentence still worth a note: effect keywords or a real numeral."""
    if MECHANICAL_RE.search(sentence):
        return True
    return bool(re.search(r'\d', NUM_NOISE_RE.sub('', sentence)))


def change(formula, target, bonus_type):
    return {'formula': str(formula), 'target': target,
            'type': bonus_type, 'operator': 'add', 'priority': 0}


def phrase_targets(phrase):
    """All pf1 change targets named inside a bonus phrase."""
    p = phrase.lower()
    targets = []
    for name, sid in SKILLS.items():
        if re.search(rf'(?<!\w){re.escape(name)}(?!\w)', p):
            targets.append(f'skill.{sid}')
    # avoid double-matching e.g. "craft" inside "knowledge (arcana)" lists is fine;
    # but skip bare 'craft'/'perform'/'profession' if a parenthesised form matched
    for pattern, target in PHRASE_TARGETS:
        if re.search(pattern, p):
            targets.append(target)
            break
    if not targets:
        m = re.search(r'\b(strength|dexterity|constitution|intelligence|wisdom|charisma)'
                      r'(-based)?\s+(?:skill\s+)?checks\b', p)
        if m:
            targets.append(f'{ABILITIES[m.group(1)]}Checks')
        elif re.search(r'\bability checks\b', p):
            targets.append('allChecks')
    if not targets and 'check' not in p:
        m = re.search(r'\b(strength|dexterity|constitution|intelligence|wisdom|charisma)\b'
                      r'(?!\s*[-–]based)', p)
        if m:
            targets.append(ABILITIES[m.group(1)])
    return targets


NOTE_TARGET_FALLBACKS = [
    ('allSavingThrows', r'sav(e|ing)'),
    ('ac', r'armor class|\bac\b'),
    ('attack', r'attack'),
    ('init', r'initiative'),
    ('cmb', r'combat maneuver|\bcmb\b'),
    ('concentration', r'concentration'),
    ('skills', r'checks|skill'),
]

# change targets that are not valid pf1 context-note targets -> nearest note section
NOTE_TARGET_REMAP = {'damage': 'attack', 'nac': 'ac', 'aac': 'ac', 'sac': 'ac',
                     'str': 'strChecks', 'dex': 'dexChecks', 'con': 'conChecks',
                     'int': 'intChecks', 'wis': 'wisChecks', 'cha': 'chaChecks'}


# valid pf1 context-note targets (system config contextNoteTargets), plus
# "skill.<id>" for specific skills — asserted before anything reaches Foundry
PF1_NOTE_TARGETS = {
    'attack', 'critical', 'effect', 'melee', 'meleeWeapon', 'meleeSpell',
    'ranged', 'rangedWeapon', 'rangedSpell', 'cmb',
    'allSavingThrows', 'fort', 'ref', 'will',
    'skills', 'strSkills', 'dexSkills', 'conSkills', 'intSkills', 'wisSkills', 'chaSkills',
    'allChecks', 'strChecks', 'dexChecks', 'conChecks', 'intChecks', 'wisChecks', 'chaChecks',
    'spellEffect', 'concentration', 'cl', 'ac', 'cmd', 'sr', 'init',
    'landSpeed', 'climbSpeed', 'swimSpeed', 'burrowSpeed', 'flySpeed', 'allSpeeds',
}


def valid_note_target(target):
    return target in PF1_NOTE_TARGETS or \
        (target.startswith('skill.') and target[6:] in SKILLS.values())


def note_target(sentence, targets):
    """(target, defaulted) — defaulted means nothing matched and 'skills' is a guess."""
    if targets:
        t = targets[0]
        return NOTE_TARGET_REMAP.get(t, t), False
    s = sentence.lower()
    for target, pattern in NOTE_TARGET_FALLBACKS:
        if re.search(pattern, s):
            return target, False
    return 'skills', True


def clean_sentence(sentence):
    return re.sub(r'\s+', ' ', sentence).strip().capitalize()


def parse_item(name, description):
    """Return ({changes, contextNotes[, unplaced]}, unparsed_sentences, flags)."""
    changes, notes, unparsed, flags = [], [], [], []
    seen_targets = set()
    # tier number in the item's own name ("belt of giant strength +2") wins when
    # the shared prose lists several tiers (+2, +4, or +6)
    name_tier = re.search(r'\+(\d+)$', name.strip())
    description = re.sub(r'\s+', ' ', description or '')
    leftover = []  # (order, sentence) with no bonus match — effect-note candidates
    for si, sentence in enumerate(re.split(r'(?<=[.;])\s+', description)):
        if NOISE_RE.search(sentence):
            continue
        sentence = WEAR_CLAUSE_RE.sub('', sentence)
        matches = list(BONUS_RE.finditer(sentence))
        for m in BONUS_REV_RE.finditer(sentence):
            bonus_type, phrase, num = m.group(1), m.group(2), m.group(3)
            matches.append(_Rev(num, bonus_type, phrase))
        for m in BONUS_OF_RE.finditer(sentence):
            bonus_type, num, phrase = m.group(1), m.group(2), m.group(3)
            matches.append(_Rev(num, bonus_type, phrase))
        if not matches:
            leftover.append((si, sentence))
            continue
        # "Ellipsoid : +1 ... " style option lists grant one pick, never all of them
        conditional = bool(CONDITIONAL_RE.search(sentence)) or \
            bool(re.match(r'\s*[\w\' ]{1,20}\s:', sentence))
        multi_tier = bool(re.search(r'\+\d+\s*(?:,|to|or|/|–|—|-)\s*(?:or\s+)?\+\d+', sentence))
        for m in matches:
            num, bonus_type, phrase = m.group(1), (m.group(2) or 'untyped').lower(), m.group(3)
            if multi_tier and name_tier:
                num = name_tier.group(1)
            targets = phrase_targets(phrase)
            if conditional or not targets or (multi_tier and not name_tier):
                text = clean_sentence(sentence)
                if text and all(n['text'] != text for n in notes):
                    target, defaulted = note_target(sentence, targets)
                    notes.append({'text': text, 'target': target,
                                  '_defaulted': defaulted, '_order': si})
                if not targets and not conditional:
                    unparsed.append(sentence.strip())
                continue
            for target in targets:
                # armor/shield bonuses stack on their own pf1 AC layer
                if bonus_type == 'armor' and target == 'ac':
                    target = 'aac'
                elif bonus_type == 'shield' and target == 'ac':
                    target = 'sac'
                if target in seen_targets:
                    continue
                seen_targets.add(target)
                changes.append(change(num, target, BONUS_TYPES.get(bonus_type, 'untyped')))
    # second pass: one summarizing effect note from the mechanical no-bonus
    # sentences (activated abilities, uses/day, saves, granted effects);
    # pure flavor — no effect keyword, no meaningful numeral — is dropped
    mech = [(si, clean_sentence(s)) for si, s in leftover if is_mechanical(s)]
    mech = [(si, s) for si, s in mech if s]
    if mech:
        kept, length = [], 0
        for si, s in mech:
            if kept and length + len(s) + 1 > NOTE_CAP:
                flags.append(('truncated', s))
                break
            kept.append((si, s))
            length += len(s) + 1
        text = ' '.join(s for _, s in kept)
        target, defaulted = note_target(text, [])
        notes.append({'text': text, 'target': target,
                      '_defaulted': defaulted, '_order': kept[0][0]})
        if re.search(r'\bfunctions? (?:as|like)\b', text, re.I):
            flags.append(('cross-reference', text))
    # rehome defaulted notes: merge onto the item's anchor target when it has
    # one (another placed note, or a change), else split off as `unplaced` so
    # Foundry skips them and the web sheet can still show the text
    placed = [n for n in notes if not n['_defaulted']]
    floating = [n for n in notes if n['_defaulted']]
    unplaced = []
    if floating:
        anchor = min(placed, key=lambda n: n['_order'])['target'] if placed else None
        if anchor is None:
            for c in changes:
                t = NOTE_TARGET_REMAP.get(c['target'], c['target'])
                if valid_note_target(t):
                    anchor = t
                    break
        if anchor is None:
            unplaced = [n['text'] for n in sorted(floating, key=lambda n: n['_order'])]
            notes = placed
        else:
            merged = sorted([n for n in placed if n['target'] == anchor] + floating,
                            key=lambda n: n['_order'])
            notes = [n for n in placed if n['target'] != anchor]
            notes.append({'text': ' '.join(n['text'] for n in merged),
                          'target': anchor, '_order': merged[0]['_order']})
            notes.sort(key=lambda n: n['_order'])
    for n in notes:
        n.pop('_defaulted', None)
        n.pop('_order', None)
        n['text'] = wrap_rolls(n['text'])
    parsed = {'changes': changes, 'contextNotes': notes}
    if unplaced:
        parsed['unplaced'] = unplaced  # plain text (no [[ ]]) — web-sheet only
    return parsed, unparsed, flags


class _Rev:
    """Adapter so reversed-order regex matches expose BONUS_RE's group order."""
    def __init__(self, num, bonus_type, phrase):
        self._groups = {1: num, 2: bonus_type, 3: phrase}

    def group(self, i):
        return self._groups[i]


def main():
    report = '--report' in sys.argv
    with open(ITEMS_PATH, encoding='utf-8') as f:
        slots = json.load(f)

    result, all_unparsed, all_flags = {}, [], []
    total = with_changes = with_notes = 0
    for slot, items in slots.items():
        for name, entry in items.items():
            total += 1
            parsed, unparsed, flags = parse_item(name, entry.get('description', ''))
            all_unparsed += [f'{name}: {s}' for s in unparsed]
            all_flags += [(name, reason, text) for reason, text in flags]
            if parsed['changes'] or parsed['contextNotes'] or parsed.get('unplaced'):
                result[name.lower()] = parsed
                with_changes += bool(parsed['changes'])
                with_notes += bool(parsed['contextNotes'])

    if os.path.exists(OVERRIDES_PATH):
        with open(OVERRIDES_PATH, encoding='utf-8') as f:
            overrides = json.load(f)
        for name, entry in overrides.items():
            result[name.lower()] = entry

    bad_targets = [(name, n['target']) for name, entry in result.items()
                   for n in entry.get('contextNotes', [])
                   if not valid_note_target(n['target'])]
    if bad_targets:
        for name, target in bad_targets:
            print(f'INVALID NOTE TARGET {target!r} on {name}')
        sys.exit(1)

    by_reason = {}
    for name, reason, text in all_flags:
        by_reason.setdefault(reason, []).append((name, text))
    reasons = ', '.join(f'{r}: {len(v)}' for r, v in sorted(by_reason.items()))
    # the four placement branches, counted over the final (override-merged) data
    mech = sum(1 for e in result.values() if e.get('changes'))
    ctx_skill = ctx_other = 0
    for e in result.values():
        for n in e.get('contextNotes', []):
            if n['target'] == 'skills' or n['target'].startswith('skill.'):
                ctx_skill += 1
            else:
                ctx_other += 1
    unplaced_items = [(name, e['unplaced']) for name, e in result.items()
                      if e.get('unplaced')]
    print(f'{total} items scanned ({len(result)} covered): '
          f'Mechanical {mech} items | Context(skill) {ctx_skill} notes | '
          f'Context(Other) {ctx_other} notes | Unplaced {len(unplaced_items)} items')
    print(f'{len(all_unparsed)} unparsed bonus sentences, flags [{reasons}]')
    if report:
        for line in all_unparsed:
            print(' ?', line[:220])
        for reason in ('truncated', 'cross-reference'):
            for name, text in by_reason.get(reason, []):
                print(f' ! [{reason}] {name}: {text[:200]}')
        for name, texts in unplaced_items:
            print(f' ~ [unplaced] {name}: {" | ".join(texts)[:200]}')
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f'wrote {OUT_PATH} ({len(result)} items)')


if __name__ == '__main__':
    main()
