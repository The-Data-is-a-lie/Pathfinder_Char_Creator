"""The power metric's DATA must resolve against the corpus and the code (map: optimal-builder, ticket 03).

    C:/Python310/python.exe Backend/scripts/gates/validate_power_metric.py

WHY THIS GATE EXISTS
--------------------
`power_adders.json` is a curated allowlist keyed by feat NAME, and a curated name that matches
nothing is this stack's single most repeated bug: orphaned conditionals from a casing mismatch, the
case-insensitive spell drop, and 27 shifter aspects made silently unpickable by a pool that was
copied instead of moved. Here the failure is quieter still -- "Weapon Specialisation" would simply
contribute zero to every character's damage, forever, and the metric would just be wrong. Nothing
crashes, no test goes red, and the baseline everyone reasons from is quietly understated.

The same applies to the vocabularies. An entry whose `model` is misspelled is skipped by the
scorer's dispatch and contributes nothing. So this gate checks the DATA against the CODE's
`IMPLEMENTED_*` frozensets -- two different artifacts, which is what makes it a real witness.

THE CONFIG/BEHAVIOUR SPLIT
--------------------------
This is the CONFIG layer: it reads files and asserts they cohere, and generates no characters. Its
partner is the BEHAVIOUR layer, `check_power_metric` in scripts/tests/test_house_invariants.py,
which scores generated characters across the whole roster and asserts no axis is silently zero for
a whole class. The golden fixtures are read here because they are files on disk, not generations --
scoring all seven costs nothing and catches a scorer that has stopped producing a shape at all.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import JSON_DIR, REPO, Report                                        # noqa: E402
import power_metric as pm                                                          # noqa: E402

REPORT = Report('validate_power_metric')

GOLDEN = REPO / 'Backend' / 'scripts' / 'golden'
FEATS_CSV = REPO / 'data' / 'feats.csv'
SPELLS_CSV = REPO / 'data' / 'spells.csv'
SPHERES = JSON_DIR / 'class_data' / 'spheres' / 'spheres_of_power.json'

# The buff-effect targets the scorer folds; 'attack'/'damage' go to the real axes, 'ac'/'saves'
# to the buffed diagnostics only (derive.js parity).
BUFF_TARGETS = {'attack', 'damage', 'ac', 'saves'}
BUFF_TIERS = {'persistent', 'combat'}

# Every axis profile_for must emit. A quietly dropped axis is a silently narrower metric.
REQUIRED_AXES = ('to_hit', 'dpr_raw', 'dpr_expected', 'burst_raw', 'burst_expected', 'dc',
                 'caster_tier', 'ac', 'ac_combat', 'ac_touch', 'ac_flat', 'cmd', 'hp', 'fort',
                 'ref', 'will', 'dr', 'skill_breadth')

# The axes profile_for benchmarks against a CR column -- exactly the set _target_multipliers must
# cover. Derived by hand rather than from the profile because the point is to catch the two
# artifacts (code and data) drifting apart.
BENCHMARKED_AXES = ('to_hit', 'dpr_raw', 'burst_raw', 'dc', 'ac', 'ac_combat', 'hp', 'fort',
                    'ref', 'will')

# The generator's level band. cr_for_level must resolve a published-or-extrapolated row for each.
LEVEL_BAND = range(1, 41)


def feat_names():
    """Every feat name in data/feats.csv, as the corpus spells it."""
    import csv
    with FEATS_CSV.open(encoding='utf-8', errors='replace', newline='') as handle:
        return {row['name'].strip() for row in csv.DictReader(handle, delimiter='|')
                if row.get('name')}


def check_feat_allowlist(table):
    """Every `feats` key exists in the corpus, with its model and condition implemented."""
    corpus = feat_names()
    lowered = {name.lower(): name for name in corpus}
    for name, spec in table['feats'].items():
        if name.startswith('_'):
            continue
        if not REPORT.check(name in corpus,
                            f"power_adders.feats: {name!r} is in no data/feats.csv row, so it "
                            f"contributes zero to every character forever"
                            + (f" -- did you mean {lowered[name.lower()]!r}?"
                               if name.lower() in lowered else '')):
            continue
        model = spec.get('model')
        REPORT.check(model in pm.IMPLEMENTED_MODELS,
                     f"power_adders.feats[{name!r}].model={model!r} is not implemented by "
                     f"power_metric (known: {sorted(pm.IMPLEMENTED_MODELS)}) -- it would be "
                     f"skipped silently")
        condition = spec.get('condition')
        REPORT.check(condition in pm.IMPLEMENTED_CONDITIONS,
                     f"power_adders.feats[{name!r}].condition={condition!r} is not one the scorer "
                     f"understands (known: {sorted(pm.IMPLEMENTED_CONDITIONS)})")


def spell_names():
    """Every spell name in data/spells.csv, lowercased -- the corpus the buff table must hit."""
    import csv
    with SPELLS_CSV.open(encoding='utf-8', errors='replace', newline='') as handle:
        return {str(row.get('name') or '').strip().lower()
                for row in csv.DictReader(handle, delimiter='|')}


def check_spell_buffs(table):
    """Every curated buff resolves in the spell corpus with an implemented, well-formed model.

    The same silent-nothing rule as the feat allowlist: a misspelled spell name would simply
    never match a castable list, and the Gorum cleric would quietly stop being sweaty.
    """
    corpus = spell_names()
    block = {k: v for k, v in (table.get('spell_buffs') or {}).items() if not k.startswith('_')}
    if not REPORT.check(block, 'power_adders.spell_buffs is missing or empty -- the buffed round '
                               'would quietly become the unbuffed one'):
        return
    for name, spec in block.items():
        REPORT.check(name.strip().lower() in corpus,
                     f'spell_buffs: {name!r} is in no data/spells.csv row -- it can never match '
                     f'a castable list and contributes nothing forever')
        REPORT.check(spec.get('tier') in BUFF_TIERS,
                     f'spell_buffs[{name!r}].tier={spec.get("tier")!r} is not one of '
                     f'{sorted(BUFF_TIERS)} -- the scorer would drop the whole row silently')
        effects = spec.get('effects')
        if not REPORT.check(isinstance(effects, list) and effects,
                            f'spell_buffs[{name!r}] has no effects list'):
            continue
        for effect in effects:
            model = effect.get('model')
            REPORT.check(model in pm.IMPLEMENTED_BUFF_MODELS,
                         f'spell_buffs[{name!r}] effect model {model!r} is not implemented '
                         f'(known: {sorted(pm.IMPLEMENTED_BUFF_MODELS)})')
            for target in effect.get('targets') or []:
                REPORT.check(target in BUFF_TARGETS,
                             f'spell_buffs[{name!r}] targets {target!r}, which the scorer does '
                             f'not fold (known: {sorted(BUFF_TARGETS)})')
            if model == 'stat_bonus':
                REPORT.check(str(effect.get('stat') or '').lower() in ('str', 'dex'),
                             f'spell_buffs[{name!r}] stat_bonus stat {effect.get("stat")!r} -- '
                             f'only str/dex shift the attack routine')


def check_defense_tables(table):
    """The wall-pass tables resolve (ruling 2026-08-12): posture keys present, curated stance
    names hit real Martial_Disciplines entries, ac_class classes exist and its model is known."""
    posture = table.get('posture') or {}
    for key in ('combat_expertise', 'fighting_defensively',
                'two_weapon_defense', 'cautious_warrior_trait'):
        REPORT.check(key in posture,
                     f'power_adders.posture is missing {key!r} -- the defensive posture would '
                     f'silently contribute nothing to ac_combat')
    for key in ('two_weapon_defense', 'cautious_warrior_trait'):
        REPORT.check(_num((posture.get(key) or {}).get('ac_fighting_defensively')),
                     f'power_adders.posture[{key!r}] has no ac_fighting_defensively value -- '
                     f'the house row would fold nothing')
    # sphere_defense rows must name a real Spheres of Might talent (any sphere), or the wall's
    # talent picker would prefer -- and the scorer would wait on -- a name that can never match.
    might = json.loads((JSON_DIR / 'class_data' / 'spheres'
                        / 'spheres_of_might_enriched.json').read_text(encoding='utf-8'))
    might_talents = {str(t).lower() for sphere in might.values() for t in sphere}
    for name, row in (table.get('sphere_defense') or {}).items():
        if name.startswith('_'):
            continue
        REPORT.check(str(name).lower() in might_talents,
                     f'sphere_defense: {name!r} resolves to no spheres_of_might_enriched.json '
                     f'talent -- a curated row that can never match a held one')
        REPORT.check(_num(row.get('ac')) or _num(row.get('per_bab')),
                     f'sphere_defense[{name!r}] carries neither ac nor per_bab')
    stances = pm.stance_texts()
    for name, row in (table.get('stance_ac') or {}).items():
        if name.startswith('_'):
            continue
        REPORT.check(str(name).strip().lower() in stances,
                     f'stance_ac: {name!r} resolves to no Martial_Disciplines.json entry -- a '
                     f'curated stance that can never match a chosen one')
        REPORT.check(_num(row.get('base')) or _num(row.get('per_hd')),
                     f'stance_ac[{name!r}] carries neither base nor per_hd')
    roster = class_roster()
    for name, spec in (table.get('ac_class') or {}).items():
        if name.startswith('_'):
            continue
        REPORT.check(spec.get('model') == 'stat_to_ac',
                     f'ac_class[{name!r}].model={spec.get("model")!r} is not stat_to_ac -- the '
                     f'scorer would skip it silently')
        for cls in spec.get('classes') or {}:
            REPORT.check(cls in roster,
                         f'ac_class[{name!r}] names class {cls!r}, not a class_data.json key')
    ws = (table.get('wild_shape') or {}).get('druid') or {}
    REPORT.check(bool(ws.get('bands')),
                 'power_adders.wild_shape.druid has no bands -- the wildshape wall would score '
                 'bare-skinned')


def _num(value):
    return isinstance(value, (int, float)) and value > 0


def check_rules(table):
    """The structural rules name real subsystem data."""
    spheres = json.loads(SPHERES.read_text(encoding='utf-8'))
    for name, spec in table['rules'].items():
        if name.startswith('_'):
            continue
        REPORT.check(spec.get('model') in pm.IMPLEMENTED_RULE_MODELS,
                     f"power_adders.rules[{name!r}].model={spec.get('model')!r} is not implemented "
                     f"(known: {sorted(pm.IMPLEMENTED_RULE_MODELS)})")
        sphere = spec.get('requires_sphere')
        if sphere is not None:
            REPORT.check(sphere in spheres,
                         f"power_adders.rules[{name!r}] requires sphere {sphere!r}, which is not a "
                         f"key in spheres_of_power.json")


def check_assumptions(table):
    """Every assumption the scorer reads must be present -- a missing one defaults silently."""
    assumptions = table['_assumptions']
    for key in ('within_30_ft', 'power_attack_active', 'flanking', 'round', 'nova_round',
                'nova_flanking'):
        REPORT.check(key in assumptions,
                     f"power_adders._assumptions is missing {key!r}; the scorer reads it and would "
                     f"fall back to a default nobody wrote down")
    REPORT.check(isinstance(table.get('_blind'), dict) and table['_blind'],
                 "power_adders._blind is empty -- every profile carries it, and a metric that does "
                 "not say what it cannot see is worse than one that does")


def class_roster():
    """Every class name class_data.json knows, exactly as it spells them."""
    raw = json.loads((JSON_DIR / 'class_data.json').read_text(encoding='utf-8'))
    return set(raw)


def check_class_keyed_tables(table):
    """The nova and dr tables resolve: implemented models, real class names, sane parameters.

    Same failure mode as the feat allowlist -- 'barbarian (unchained)' misspelled 'Barbarian
    (Unchained)' would contribute zero to every unchained barbarian forever, silently.
    """
    roster = class_roster()
    for section, models in (('nova', pm.IMPLEMENTED_NOVA_MODELS),
                            ('dr', pm.IMPLEMENTED_DR_MODELS)):
        block = table.get(section)
        if not REPORT.check(isinstance(block, dict) and any(not k.startswith('_') for k in block),
                            f"power_adders.{section} is missing or empty -- the "
                            f"{'burst_raw' if section == 'nova' else 'dr'} axis would quietly "
                            f"score every character at its weapon-only floor"):
            continue
        for name, spec in block.items():
            if name.startswith('_'):
                continue
            REPORT.check(spec.get('model') in models,
                         f"power_adders.{section}[{name!r}].model={spec.get('model')!r} is not "
                         f"implemented (known: {sorted(models)}) -- it would be skipped silently")
            classes = spec.get('classes')
            if not REPORT.check(isinstance(classes, dict) and classes,
                                f"power_adders.{section}[{name!r}] has no classes dict -- it can "
                                f"never fire"):
                continue
            for cls, params in classes.items():
                REPORT.check(cls in roster,
                             f"power_adders.{section}[{name!r}] names class {cls!r}, which is not "
                             f"a class_data.json key -- it contributes zero forever")
                scale = (params or {}).get('scale')
                if scale is not None:
                    REPORT.check(
                        all(str(k).isdigit() and isinstance(v, int) for k, v in scale.items()),
                        f"power_adders.{section}[{name!r}].classes[{cls!r}].scale must map "
                        f"numeric-string levels to integer bonuses, got {scale!r}")


def check_target_multipliers():
    """The bar-raising lever covers exactly the benchmarked axes, numerically.

    profile_for multiplies every benchmark denominator by _target_multipliers[axis], defaulting a
    missing axis to 1.0 -- so a misspelled axis would silently keep the OLD bar while everyone
    believed the new one was in force. That is the exact failure mode this whole gate file exists
    for, pointed at the newest tunable.
    """
    raw = json.loads((JSON_DIR / 'cr_benchmarks.json').read_text(encoding='utf-8'))
    block = raw.get('_target_multipliers')
    if not REPORT.check(isinstance(block, dict) and block,
                        "cr_benchmarks.json has no _target_multipliers block -- profile_for would "
                        "default every axis to 1.0 and the bar could never be raised from data"):
        return
    axes = {key for key in block if not key.startswith('_')}
    missing = sorted(set(BENCHMARKED_AXES) - axes)
    extra = sorted(axes - set(BENCHMARKED_AXES))
    REPORT.check(not missing,
                 f"_target_multipliers is missing {missing} -- those axes would silently stay at "
                 f"bar 1.0 no matter what anyone believes was configured")
    REPORT.check(not extra,
                 f"_target_multipliers names {extra}, which profile_for never benchmarks -- a "
                 f"misspelled axis raising nothing")
    for axis in sorted(axes & set(BENCHMARKED_AXES)):
        value = block[axis]
        REPORT.check(isinstance(value, (int, float)) and value > 0,
                     f"_target_multipliers[{axis!r}] = {value!r} is not a positive number")


def check_benchmarks():
    """The CR table covers the whole band, is monotonic, and flags what was extrapolated."""
    rows = pm.benchmarks()
    published = [row for row in rows.values() if not row['extrapolated']]
    REPORT.check(len(published) == 31,
                 f"cr_benchmarks: expected 31 published rows (CR 1/2-30), found {len(published)}")

    for level in LEVEL_BAND:
        cr = pm.cr_for_level(level)
        REPORT.check(cr in rows,
                     f"cr_benchmarks: level {level} maps to CR {cr}, which has no row -- the band "
                     f"runs 1-40 and every level must resolve")

    ordered = [rows[cr] for cr in sorted(rows)]
    for field in ('hp', 'ac', 'attack_high', 'damage_high', 'save_good', 'dc_primary'):
        for previous, current in zip(ordered, ordered[1:]):
            if not REPORT.check(
                    current[field] >= previous[field],
                    f"cr_benchmarks: {field} goes DOWN from CR {previous['cr_label']} to "
                    f"CR {current['cr_label']} ({previous[field]} -> {current[field]}) -- a "
                    f"transcription error, since the published table is monotonic"):
                break

    for row in ordered:
        if row['cr'] > 30:
            REPORT.check(row['extrapolated'] is True,
                         f"cr_benchmarks: CR {row['cr_label']} is past the published table but is "
                         f"not flagged extrapolated")
        else:
            REPORT.check(row['extrapolated'] is False,
                         f"cr_benchmarks: CR {row['cr_label']} is published but is flagged "
                         f"extrapolated")


def check_golden_profiles():
    """The scorer still produces a full profile for each golden fixture.

    Files, not generations -- so this stays a config check. It catches a scorer that has stopped
    emitting an axis, and a payload-shape change that has quietly broken the fold.
    """
    fixtures = sorted(GOLDEN.glob('*.json'))
    if not REPORT.check(fixtures, f"no golden fixtures under {GOLDEN} to score"):
        return 0
    for path in fixtures:
        payload = json.loads(path.read_text(encoding='utf-8'))
        try:
            profile = pm.profile_for(payload)
        except Exception as exc:                                    # noqa: BLE001
            REPORT.error(f"power_metric.profile_for raised on golden {path.name}: {exc!r}")
            continue
        missing = [axis for axis in REQUIRED_AXES if axis not in profile['axes']]
        REPORT.check(not missing,
                     f"golden {path.name}: profile is missing axes {missing}")
        for axis in ('ac', 'hp', 'to_hit'):
            entry = profile['axes'].get(axis) or {}
            REPORT.check(entry.get('raw') not in (None, 0),
                         f"golden {path.name}: axis {axis!r} scored {entry.get('raw')!r} -- every "
                         f"character has some AC, hit points and attack bonus, so a zero here is "
                         f"the fold silently failing rather than a weak character")
        burst = (profile['axes'].get('burst_raw') or {}).get('raw') or 0
        sustained = (profile['axes'].get('dpr_raw') or {}).get('raw') or 0
        REPORT.check(burst >= sustained,
                     f"golden {path.name}: burst_raw {burst} < dpr_raw {sustained} -- the nova "
                     f"round is the sustained round plus adders, so it can never be lower")
        combat_ac = (profile['axes'].get('ac_combat') or {}).get('raw') or 0
        sheet_ac = (profile['axes'].get('ac') or {}).get('raw') or 0
        REPORT.check(combat_ac >= sheet_ac,
                     f"golden {path.name}: ac_combat {combat_ac} < ac {sheet_ac} -- the "
                     f"fight-state AC is the sheet AC plus defensive folds, never lower")
        REPORT.check(profile['diagnostics']['weapon_known'],
                     f"golden {path.name}: weapon "
                     f"{profile['diagnostics']['weapon_name']!r} does not resolve in "
                     f"weapons_data.json, so its damage dice score as zero")
    return len(fixtures)


def check_mythic_table(table):
    """The mythic chassis bucket resolves: implemented models, and the deferral is on record.

    Same silent-nothing contract as every other bucket -- plus one honesty check: deferring the
    597 path abilities is a ruling, and a ruling that falls out of _blind stops being visible on
    every profile, which is how a knowing understatement becomes an unknowing one."""
    block = table.get('mythic')
    if not REPORT.check(isinstance(block, dict) and block,
                        "power_adders.mythic is missing -- the surge EV shift and the "
                        "diagnostics block would quietly stop firing"):
        return
    for name, spec in block.items():
        if name.startswith('_') or not isinstance(spec, dict) or 'model' not in spec:
            continue
        REPORT.check(spec['model'] in pm.IMPLEMENTED_MYTHIC_MODELS,
                     f"power_adders.mythic[{name!r}].model={spec['model']!r} is not implemented "
                     f"(known: {sorted(pm.IMPLEMENTED_MYTHIC_MODELS)}) -- it would be skipped "
                     f"silently")
    REPORT.check(bool((table.get('_blind') or {}).get('mythic')),
                 "power_adders._blind.mythic is empty -- the path-ability deferral must stay "
                 "printed on every profile")


def main():
    table = pm.adders()
    check_feat_allowlist(table)
    check_rules(table)
    check_spell_buffs(table)
    check_defense_tables(table)
    check_assumptions(table)
    check_class_keyed_tables(table)
    check_mythic_table(table)
    check_benchmarks()
    check_target_multipliers()
    fixtures = check_golden_profiles()
    adders = sum(1 for k in table['feats'] if not k.startswith('_'))
    rules = sum(1 for k in table['rules'] if not k.startswith('_'))
    nova = sum(1 for k in table.get('nova', {}) if not k.startswith('_'))
    dr = sum(1 for k in table.get('dr', {}) if not k.startswith('_'))
    buffs = sum(1 for k in table.get('spell_buffs', {}) if not k.startswith('_'))
    return REPORT.finish(f'{adders} feat adders, {rules} structural rules, {nova} nova rules, '
                         f'{dr} dr rules, {buffs} spell buffs, {len(pm.benchmarks())} CR rows, '
                         f'{fixtures} goldens scored')


if __name__ == '__main__':
    sys.exit(main())
