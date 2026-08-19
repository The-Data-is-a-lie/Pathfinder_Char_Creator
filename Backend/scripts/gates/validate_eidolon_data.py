"""Gate the eidolon data trio -- eidolon_table.json + eidolon_base_forms.json + eidolon_evolutions.json.

    C:\\Python310\\python.exe Backend/scripts/gates/validate_eidolon_data.py

Spec section 8, "Eidolon (v1.1)". These three files are the whole rulebook the EP spender reads: the
table says how many points a summoner has and how many attacks the creature may end up with, the
base forms say what it starts as, and the evolutions say what may be bought and what it costs. None
of that is in code, by design -- which means every failure mode here is a data failure, and every
one of them is quiet:

- a **cost that drifts** does not raise; the spender just buys more or less than RAW allows, and the
  only symptom is a creature that feels wrong at the table;
- a **prereq token that resolves to nothing** silently becomes "no prerequisite", so the greedy
  spender happily buys Rider Bond on an eidolon with no mount;
- a **base form whose `pf_content` name misses** is the D3 silent-drop again -- the module clones
  nothing and the creature degrades, having passed every backend check;
- an **evolution excluded for being third-party** that loses its `exclude` key rejoins the random
  pool without anything saying so.

What this asserts:
- the published census: 81 curated evolutions with the cost histogram 32/28/11/10, and the two 3PP
  rows kept in the file but out of the pool. The numbers are stated here rather than counted from
  the file, because a gate that derives its expectation from the thing it is gating confirms nothing;
- every prereq token resolves -- evolution names (including the qualified `limbs (arms)` form),
  base forms, sizes `companion_stats.SIZE_GEOMETRY` knows, and summoner levels inside 1..20;
- every `repeat` cap parses in the tiny `level` language and is at least 1 at 1st -- a cap that
  reads 0 is a pick nobody can ever take. It is deliberately NOT also asserted to be non-decreasing:
  the grammar below only admits `N` and `N + level // M`, which cannot shrink, so such a check would
  pass vacuously and read as coverage it does not have;
- every `changes` block moves a probe stat block through `companion_stats.apply_modifiers` itself,
  so a target the fold cannot place fails here rather than vanishing into `stats.unapplied`;
- the table's Evolution Pool and Max Attacks columns match ticket 07's verified reading exactly, and
  the derived columns (BAB, saves, skills, feats) still follow their formulas off HD;
- each base form parses through `companion_stats`' own parsers, names exactly two good saves, spends
  its free evolutions on evolutions that exist, and maps 1:1 onto `pf-eidolon-forms` -- with the
  Aberrant pair, which these rules do not contain, asserted as the ONLY unmapped entries.

The `pf-eidolon-evolutions` compendium cross-check the build plan named is SKIPPED, not silently
dropped: no dump of that pack exists in this repo (`pf_content_companions.json` carries actors --
forms, companions, familiars -- not evolution items), and v1 is backend-only, so evolutions ride the
entry as named features rather than as pack items. It becomes a real check when the renderer ticket
lands one.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _harness import JSON_DIR, Report, read_json                        # noqa: E402

from utils.class_func.companion_stats import (                          # noqa: E402
    STATS, SIZE_GEOMETRY, SKILL_TARGET_PREFIX, MODIFIER_TARGETS, FormulaError,
    _natural_armor, _parse_attacks, apply_modifiers, eval_formula,
)

TABLE = JSON_DIR / 'eidolon_table.json'
FORMS = JSON_DIR / 'eidolon_base_forms.json'
EVOLUTIONS = JSON_DIR / 'eidolon_evolutions.json'
PF_CONTENT = JSON_DIR / 'pf_content_companions.json'

# --- external rules, stated here because the data cannot be its own authority -------------------
#
# The Eidolon Base Statistics table, levels 1..20, as verified in companions ticket 07. Hit Dice
# drives four more columns, so it is the only other one written out; the rest are formulas below.
EVOLUTION_POOL = (3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 25, 26)
MAX_ATTACKS = (3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 7, 7)
HIT_DICE = (1, 2, 3, 3, 4, 5, 6, 6, 7, 8, 9, 9, 10, 11, 12, 12, 13, 14, 15, 15)
ARMOR_BONUS = (0, 2, 2, 2, 4, 4, 6, 6, 6, 8, 8, 10, 10, 10, 12, 12, 14, 14, 14, 16)
STR_DEX_BONUS = (0, 1, 1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 5, 6, 6, 7, 7, 7, 8)

# The six chained base forms. The pack also ships an Aberrant Baseform; these rules do not contain
# it, and the base-form file says so -- so it is asserted as unmapped rather than left to chance.
RAW_FORMS = {'aquatic', 'avian', 'biped', 'quadruped', 'serpentine', 'tauric'}
UNMAPPED_PACK_FORMS = {'Aberrant Baseform', 'Aberrant Baseform (Small)'}

# The curated census. A curation pass that legitimately adds an evolution edits these two lines and
# says why in the changelog; anything else moving them is drift.
EXPECTED_TOTAL = 81
EXPECTED_COSTS = {1: 32, 2: 28, 3: 11, 4: 10}
EXPECTED_EXCLUDED = 2

PREREQ_KEYS = {'min_summoner_level', 'evolutions', 'forms', 'size', 'alignment', 'any_attack',
               'min_ability'}

# Prerequisites the scrape could not see, because the published text states them in the tail of the
# benefit prose rather than in a heading. Swept 2026-08-17: every "must possess the X evolution"
# sentence, matched against what the entry actually declares. The gate keeps the sweep rather than
# the answer -- a re-scrape that reworded a benefit would otherwise drop a gate silently.
PROSE_PREREQ_RE = re.compile(r'must (?:possess|have)(?: the)? ([a-z][a-z \-]*?) evolution',
                             re.IGNORECASE)
EVOLUTION_TYPES = {'ex', 'su', 'sp', 'ex or su'}
CHOICE_KINDS = {'ability', 'energy', 'limbs', 'skill'}
ATTACK_KINDS = {'primary', 'secondary'}
PRINTED_SIZES = {'medium', 'large', 'huge'}
DIE_RE = re.compile(r'^\d+d\d+$')
SAVES = ('fort', 'ref', 'will')
SAVE_GRADES = {'good', 'poor'}
STAT_KEYS = {'size', 'speed', 'ac', 'attack', 'ability scores', 'special qualities',
             'special attacks'}

# `repeat.max_formula` is its own tiny language -- a constant, optionally plus one per N summoner
# levels. Read by hand rather than `eval` for the same reason `companion_stats.eval_formula` is:
# a formula nobody can read must fail loudly, not resolve to something plausible.
REPEAT_RE = re.compile(r'^\s*(\d+)\s*(?:\+\s*level\s*//\s*([1-9]\d*)\s*)?$')

# A qualified prereq/free-evolution token: `limbs (arms)`, `reach (bite)`.
QUALIFIED_RE = re.compile(r'^(.*?)\s*\((.*)\)$')

PROBE_SPREAD = {'str': 3, 'dex': 2, 'con': 2, 'int': -4, 'wis': 1, 'cha': -3}
PROBE_HD = 6

REPORT = Report('validate_eidolon_data')


def probe_stats():
    """A stat block with every field the fold can touch, so a no-op change is detectable."""
    return {
        'hp': 30, 'ac': 16, 'touch_ac': 12, 'flat_footed_ac': 14, 'natural_armor': 4,
        'saves': {'fort': 7, 'ref': 7, 'will': 2}, 'initiative': 2, 'cmb': 7, 'cmd': 19,
        'speed': '50 ft. , fly 60 ft. (good), swim 30 ft. , climb 20 ft. ',
        'attacks': [{'atk': 7}], 'skills': {'acrobatics': {'ranks': 6, 'total': 10}},
    }


def eval_repeat(formula, level):
    """`1` / `1 + level // 5` -> an int cap at `level`. Returns None for "unlimited" (EP is the cap).

    Raises ValueError on anything else, which is the point: the spender will read these at every
    level of every generation, and a cap it cannot parse must not become an unlimited one.
    """
    if formula is None:
        return None
    match = REPEAT_RE.match(str(formula))
    if not match:
        raise ValueError(f'{formula!r} is not `N` or `N + level // M`')
    base, per = match.group(1), match.group(2)
    return int(base) + (level // int(per) if per else 0)


def resolve_token(token, pool):
    """Resolve `bite` / `limbs (arms)` / `reach (bite)` against the evolution pool.

    Returns an error string, or None when the token resolves. The qualifier is legal when the base
    evolution offers it as a choice (`limbs (arms)`) or when it names another evolution the
    qualifier attaches to (`reach (bite)`); anything else is a token nothing will ever match.
    """
    name, qualifier = token, None
    match = QUALIFIED_RE.match(token)
    if match:
        name, qualifier = match.group(1).strip(), match.group(2).strip()
    if name not in pool:
        return f'{token!r} names no evolution ({name!r} is not a key)'
    if qualifier is None:
        return None
    options = ((pool[name].get('choice') or {}).get('options')) or []
    if qualifier in options or qualifier in pool:
        return None
    return (f'{token!r}: qualifier {qualifier!r} is neither one of {name!r}\'s choices '
            f'({options or "none"}) nor an evolution name')


def check_evolution(key, entry, pool):
    where = f'evolutions/{key}'
    REPORT.check(str(entry.get('name', '')).lower() == key,
                 f'{where}: name {entry.get("name")!r} does not match its key')
    REPORT.check(isinstance(entry.get('benefit'), str) and entry['benefit'].strip(),
                 f'{where}: empty benefit -- the entry rides the sheet as rules text')
    REPORT.check(isinstance(entry.get('source'), str) and entry['source'].strip(),
                 f'{where}: no source')
    REPORT.check(entry.get('type') in EVOLUTION_TYPES,
                 f'{where}: type {entry.get("type")!r} not in {sorted(EVOLUTION_TYPES)}')

    cost = entry.get('cost')
    REPORT.check(isinstance(cost, int) and 1 <= cost <= 4,
                 f'{where}: cost {cost!r} is not an int in 1..4')

    # -- prerequisites: every token has to resolve, or the legality filter is a no-op
    prereqs = entry.get('prereqs')
    if REPORT.check(isinstance(prereqs, dict) and set(prereqs) == PREREQ_KEYS,
                    f'{where}: prereq keys {sorted(prereqs or [])}, expected {sorted(PREREQ_KEYS)}'):
        level = prereqs['min_summoner_level']
        REPORT.check(level is None or (isinstance(level, int) and 1 <= level <= 20),
                     f'{where}: min_summoner_level {level!r} is not None or an int in 1..20')
        for token in prereqs['evolutions'] or []:
            problem = resolve_token(token, pool)
            REPORT.check(not problem, f'{where}: prereq {problem}')
        forms = prereqs['forms']
        if forms is not None:
            REPORT.check(forms and set(forms) <= RAW_FORMS,
                         f'{where}: forms {forms!r} is empty or names a form that does not exist')
        size = prereqs['size']
        REPORT.check(size is None or size in SIZE_GEOMETRY,
                     f'{where}: prereq size {size!r} is not in SIZE_GEOMETRY')
        REPORT.check(isinstance(prereqs['any_attack'], bool),
                     f'{where}: any_attack {prereqs["any_attack"]!r} is not a bool')
        minimums = prereqs['min_ability']
        REPORT.check(minimums is None or (set(minimums) <= set(STATS)
                                          and all(isinstance(v, int) for v in minimums.values())),
                     f'{where}: min_ability {minimums!r} is not None or a map of the six to ints')

        # The prose is the authority the scrape read; if it names a prerequisite the entry does not
        # declare, the legality filter is not enforcing a rule the rulebook prints.
        declared = {token.split(' (')[0] for token in prereqs['evolutions'] or []}
        for phrase in PROSE_PREREQ_RE.findall(entry.get('benefit') or ''):
            required = phrase.strip().lower().split(' (')[0]
            if required in pool:
                REPORT.check(required in declared,
                             f'{where}: the benefit says it requires the {required!r} evolution, '
                             f'but prereqs.evolutions declares {sorted(declared) or "nothing"} -- '
                             f'the spender would never check it')

    # -- repeat caps: parseable, never shrinking, and at least one pick at 1st
    repeat = entry.get('repeat')
    if REPORT.check(isinstance(repeat, dict) and set(repeat) <= {'max_formula',
                                                                 'per_choice_max_formula'},
                    f'{where}: repeat {repeat!r} carries unknown keys'):
        for field, formula in repeat.items():
            try:
                first = eval_repeat(formula, 1)
            except ValueError as error:
                REPORT.error(f'{where}: {field} {error}')
                continue
            REPORT.check(first is None or first >= 1,
                         f'{where}: {field} caps at {first} at 1st -- a pick nobody can take')
        REPORT.check('per_choice_max_formula' not in repeat or entry.get('choice'),
                     f'{where}: per_choice_max_formula without a choice to count per')

    # -- attacks and size, the two things a pick can spend out of a table column
    attacks = entry.get('grants_attack')
    REPORT.check(isinstance(attacks, int) and 0 <= attacks <= MAX_ATTACKS[0],
                 f'{where}: grants_attack {attacks!r} is not an int in 0..{MAX_ATTACKS[0]} -- a '
                 f'single pick must fit inside the tightest Max Attacks row')
    size = entry.get('grants_size')
    REPORT.check(size is None or size in SIZE_GEOMETRY,
                 f'{where}: grants_size {size!r} is not in SIZE_GEOMETRY')

    # The attack block is PARSED from the prose by the curator, so this is where a reworded benefit
    # surfaces: an attack-granting evolution with no block would put a nameless, damage-less attack
    # on the stat block, and a count that disagreed with `grants_attack` would spend Max Attacks on
    # one number and print the other.
    attack = entry.get('attack')
    if attacks:
        if REPORT.check(isinstance(attack, dict),
                        f'{where}: grants {attacks} attack(s) but has no parsed attack block -- '
                        f'the damage/primary line in its benefit no longer matches'):
            REPORT.check(attack.get('count') == attacks,
                         f'{where}: attack.count {attack.get("count")!r} disagrees with '
                         f'grants_attack {attacks}')
            REPORT.check(attack.get('kind') in ATTACK_KINDS,
                         f'{where}: attack.kind {attack.get("kind")!r} not in '
                         f'{sorted(ATTACK_KINDS)}')
            damage = attack.get('damage') or {}
            REPORT.check(set(damage) == PRINTED_SIZES,
                         f'{where}: attack.damage covers {sorted(damage)}, expected the three '
                         f'printed sizes {sorted(PRINTED_SIZES)} (Small is a step-down marker, '
                         f'not a printed die -- spec section 16, D11)')
            for printed, die in damage.items():
                REPORT.check(DIE_RE.match(str(die)),
                             f'{where}: attack.damage[{printed}] {die!r} is not a die expression')
    else:
        REPORT.check(attack is None,
                     f'{where}: has an attack block but grants_attack is 0 -- it would print an '
                     f'attack nothing counted against Max Attacks')

    choice = entry.get('choice')
    if choice is not None:
        REPORT.check(choice.get('kind') in CHOICE_KINDS,
                     f'{where}: choice kind {choice.get("kind")!r} not in {sorted(CHOICE_KINDS)}')
        options = choice.get('options')
        REPORT.check(options is None or (isinstance(options, list) and options),
                     f'{where}: choice options {options!r} is present but empty')

    scores = entry.get('ability_scores')
    if scores is not None:
        REPORT.check(set(scores) <= set(STATS) and all(isinstance(v, int) for v in scores.values()),
                     f'{where}: ability_scores {scores!r} is not a subset of the six, all ints')

    holdback = entry.get('numeric_holdback')
    REPORT.check(holdback is None or (isinstance(holdback, str) and holdback.strip()),
                 f'{where}: numeric_holdback is present but empty -- name the number or drop the key')

    # -- the fold: a declared change must land somewhere apply_modifiers can place it
    for change in entry.get('changes') or []:
        target = str(change.get('target') or '')
        REPORT.check(target in MODIFIER_TARGETS or target.startswith(SKILL_TARGET_PREFIX),
                     f'{where}: change target {target!r} is not one apply_modifiers can place')
        try:
            eval_formula(change.get('formula'), dict(PROBE_SPREAD, hd=PROBE_HD))
        except FormulaError as error:
            REPORT.error(f'{where}: {error}')
    if entry.get('changes'):
        before, after = probe_stats(), probe_stats()
        apply_modifiers(after, [(key, entry)], PROBE_SPREAD, PROBE_HD)
        after.pop('applied_changes', None), after.pop('context_notes', None)
        REPORT.check(after != before,
                     f'{where}: declares {len(entry["changes"])} change(s) but moved nothing on the '
                     f'probe block -- the fold would drop it silently')


def check_evolutions(payload):
    REPORT.check(set(payload) == {'meta', 'evolutions'},
                 f'eidolon_evolutions.json: top-level keys {sorted(payload)}, expected meta + '
                 f'evolutions')
    pool = payload.get('evolutions') or {}

    REPORT.check(len(pool) == EXPECTED_TOTAL,
                 f'evolutions: {len(pool)} entries, expected the curated {EXPECTED_TOTAL}')
    histogram = {}
    for entry in pool.values():
        histogram[entry.get('cost')] = histogram.get(entry.get('cost'), 0) + 1
    REPORT.check(histogram == EXPECTED_COSTS,
                 f'evolutions: cost histogram {dict(sorted(histogram.items(), key=str))}, expected '
                 f'{EXPECTED_COSTS}')

    excluded = {name for name, entry in pool.items() if entry.get('exclude')}
    REPORT.check(len(excluded) == EXPECTED_EXCLUDED,
                 f'evolutions: {len(excluded)} entries held out of the pool ({sorted(excluded)}), '
                 f'expected {EXPECTED_EXCLUDED}')
    for name in excluded:
        REPORT.check(str(pool[name]['exclude']).strip(),
                     f'evolutions/{name}: excluded from the pool with an empty reason')
    for name, entry in pool.items():
        REPORT.check(not entry.get('third_party') or entry.get('exclude'),
                     f'evolutions/{name}: third_party but NOT excluded -- 3PP content would join '
                     f'the random pool with nothing saying so')
        check_evolution(name, entry, pool)
    return pool


def check_table(payload):
    REPORT.check(set(payload) == {'meta', 'levels'},
                 f'eidolon_table.json: top-level keys {sorted(payload)}, expected meta + levels')
    rows = payload.get('levels') or {}
    if not REPORT.check(set(rows) == {str(n) for n in range(1, 21)},
                        f'table: levels are {sorted(rows)}, expected exactly "1".."20"'):
        return rows

    for level in range(1, 21):
        row, where = rows[str(level)], f'table/{level}'
        index = level - 1
        REPORT.check(row.get('evolution_pool') == EVOLUTION_POOL[index],
                     f'{where}: evolution_pool {row.get("evolution_pool")!r}, ticket 07 verified '
                     f'{EVOLUTION_POOL[index]}')
        REPORT.check(row.get('max_attacks') == MAX_ATTACKS[index],
                     f'{where}: max_attacks {row.get("max_attacks")!r}, ticket 07 verified '
                     f'{MAX_ATTACKS[index]}')
        hd = row.get('hd')
        if not REPORT.check(hd == HIT_DICE[index],
                            f'{where}: hd {hd!r}, RAW says {HIT_DICE[index]}'):
            continue
        # The four derived columns. Stated as formulas so a hand-edited row cannot drift one cell.
        REPORT.check(row.get('bab') == hd, f'{where}: bab {row.get("bab")!r}, expected hd ({hd})')
        REPORT.check(row.get('good_save') == 2 + hd // 2,
                     f'{where}: good_save {row.get("good_save")!r}, expected {2 + hd // 2}')
        REPORT.check(row.get('poor_save') == hd // 3,
                     f'{where}: poor_save {row.get("poor_save")!r}, expected {hd // 3}')
        REPORT.check(row.get('skills') == 4 * hd,
                     f'{where}: skills {row.get("skills")!r}, expected 4 per HD ({4 * hd})')
        REPORT.check(row.get('feats') == 1 + (hd - 1) // 2,
                     f'{where}: feats {row.get("feats")!r}, expected {1 + (hd - 1) // 2}')
        REPORT.check(row.get('armor_bonus') == ARMOR_BONUS[index],
                     f'{where}: armor_bonus {row.get("armor_bonus")!r}, RAW says '
                     f'{ARMOR_BONUS[index]}')
        REPORT.check(row.get('str_dex_bonus') == STR_DEX_BONUS[index],
                     f'{where}: str_dex_bonus {row.get("str_dex_bonus")!r}, RAW says '
                     f'{STR_DEX_BONUS[index]}')

    named = [special for row in rows.values() for special in row.get('special') or []]
    repeated = {name for name in named if named.count(name) > 1}
    REPORT.check(repeated <= {'ability score increase'},
                 f'table: {sorted(repeated)} is granted at more than one level -- only the ability '
                 f'score increase repeats')
    return rows


def check_form(name, form, pool):
    where = f'forms/{name}'
    stats = form.get('starting statistics') or {}
    REPORT.check(set(stats) <= STAT_KEYS,
                 f'{where}: unknown stat keys {sorted(set(stats) - STAT_KEYS)}')

    size = str(stats.get('size') or '').strip().lower()
    REPORT.check(size in SIZE_GEOMETRY, f'{where}: size {size!r} not in SIZE_GEOMETRY')
    REPORT.check(form.get('default_size') == size,
                 f'{where}: default_size {form.get("default_size")!r} disagrees with the block\'s '
                 f'own size {size!r}')
    REPORT.check(isinstance(stats.get('speed'), str) and stats['speed'].strip(),
                 f'{where}: speed is missing or empty')
    REPORT.check(_natural_armor(stats.get('ac')) >= 0,
                 f'{where}: ac {stats.get("ac")!r} did not parse as a natural armor line')
    REPORT.check(_parse_attacks(stats.get('attack'), 0, 0, 0, True),
                 f'{where}: attack {stats.get("attack")!r} produced no parsed attacks')

    scores = stats.get('ability scores') or {}
    REPORT.check(set(scores) == set(STATS),
                 f'{where}: ability scores carry {sorted(scores)}, expected all six')
    for stat, score in scores.items():
        REPORT.check(isinstance(score, int) and 1 <= score <= 30,
                     f'{where}: {stat} = {score!r} is not an int in 1..30')

    saves = form.get('saves') or {}
    if REPORT.check(set(saves) == set(SAVES) and set(saves.values()) <= SAVE_GRADES,
                    f'{where}: saves {saves!r}, expected fort/ref/will each good or poor'):
        good = [key for key, grade in saves.items() if grade == 'good']
        REPORT.check(len(good) == 2,
                     f'{where}: {len(good)} good saves ({sorted(good)}) -- every base form has two')

    free = form.get('free evolutions') or {}
    REPORT.check(free, f'{where}: no free evolutions')
    for token, count in free.items():
        problem = resolve_token(token, pool)
        REPORT.check(not problem, f'{where}: free evolution {problem}')
        REPORT.check(isinstance(count, int) and count >= 1,
                     f'{where}: free evolution {token!r} has count {count!r} -- the value is how '
                     f'many times it is granted, not its cost')


def check_forms(payload, pool, pack_forms):
    REPORT.check(set(payload) == {'meta', 'small_package', 'forms'},
                 f'eidolon_base_forms.json: top-level keys {sorted(payload)}, expected meta + '
                 f'small_package + forms')
    forms = payload.get('forms') or {}
    REPORT.check(set(forms) == RAW_FORMS,
                 f'forms: {sorted(forms)}, expected the six chained base forms (difference: '
                 f'{sorted(set(forms) ^ RAW_FORMS)})')

    package = payload.get('small_package') or {}
    REPORT.check((package.get('ability_scores') or {}) == {'str': -4, 'dex': 2, 'con': -2},
                 f'small_package: ability_scores {package.get("ability_scores")!r}, RAW says '
                 f'-4 Str / +2 Dex / -2 Con')

    mapped = set()
    for name, form in forms.items():
        check_form(name, form or {}, pool)
        for key in ('pf_content', 'pf_content_small'):
            actor = (form or {}).get(key)
            if REPORT.check(actor in pack_forms,
                            f'forms/{name}: {key} {actor!r} is not one of the pf-eidolon-forms '
                            f'actors -- the module would clone nothing and degrade (D3)'):
                mapped.add(actor)

    REPORT.check(set(pack_forms) - mapped == UNMAPPED_PACK_FORMS,
                 f'forms: the pack actors nothing maps to are {sorted(set(pack_forms) - mapped)}, '
                 f'expected only {sorted(UNMAPPED_PACK_FORMS)} -- a form that silently stopped '
                 f'being mapped looks exactly like this')
    return forms


def main():
    pool = check_evolutions(read_json(EVOLUTIONS))
    rows = check_table(read_json(TABLE))
    pack_forms = read_json(PF_CONTENT).get('pf-eidolon-forms') or []
    forms = check_forms(read_json(FORMS), pool, pack_forms)

    REPORT.skip('pf-eidolon-evolutions pack cross-check: no dump of that pack exists in this repo '
                '(pf_content_companions.json carries actors, not evolution items), and v1 is '
                'backend-only -- evolutions ride the entry as named features. It becomes a real '
                'check when the renderer ticket lands a dump.')
    return REPORT.finish(f'{len(pool)} evolutions, {len(rows)} table rows and {len(forms)} base '
                         f'forms validated')


if __name__ == '__main__':
    sys.exit(main())
