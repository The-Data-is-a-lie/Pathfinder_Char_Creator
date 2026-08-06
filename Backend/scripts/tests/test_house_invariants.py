"""House-rule invariant sweep: every generatable class x level ladder x seeds (run directly; this
repo has no pytest harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    C:\\Python310\\python.exe Backend/scripts/tests/test_house_invariants.py
    C:\\Python310\\python.exe Backend/scripts/tests/test_house_invariants.py --classes fighter,wizard
    C:\\Python310\\python.exe Backend/scripts/tests/test_house_invariants.py --levels 1,20 --seeds 1

Asserts the house-rule FORMULAS (oks/pathfinder/house-rules/), not pinned sheets -- the golden
payload test owns exact-output regression. Per generated character (homebrew flag on, the
generator's default):

  * feats   -- normal == max(0, ceil(L/2) + 2 creation - profession-feat slots);
               story == 1 + L//5; flavor == 1; flaw feats diminish: min(flaws//2 + 1, 3), 0 at 0
               (first 2 flaws grant 1 each, the 4th grants the 3rd; behind misc_homebrew_rules,
               the generator's default)
  * skills  -- sum(skill_ranks) == skill_rank_budget;
               budget == sum(max(1, points(2->4 floor) + best final mental mod) * class level)
                         + background 2L + favored-class {0, L};
               no skill above the 3-ranks-per-level cap; only renderable skills
  * HP      -- sheet_health == sum(max hit die x level) (full-HP house rule);
               Total_HP adds the FINAL Con mod x L, plus favored-class {0, L}
  * homebrew feats -- every placed Metzofitz-only feat carries rules text in
               homebrew_feat_desc_dict (else the Foundry module renders an empty row), and across
               a full sweep at least one Metzofitz pick appears at all
  * sanity  -- generation raises no exception

A failure prints the class/level/seed cell plus the replayable generation seed.
"""
import argparse
import io
import json
import sys
import traceback
from contextlib import redirect_stdout
from math import ceil, floor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import BACKEND, Report, choice_schedule, schedule_levels  # noqa: E402

# The pick schedule, read from disk rather than through the generator's resolver.
SCHEDULE = choice_schedule()

from utils import data  # noqa: E402
from utils.class_func import backstory as _bs  # noqa: E402

# Sever Ollama like test_golden_payload.py: build_archetype reaches for it to break scoring ties.
_bs._try_ollama = lambda *a, **k: ''

import main_test  # noqa: E402

LEVELS = [1, 5, 10, 15, 20]
SEEDS = [1101, 2202, 3303]

with open(BACKEND / 'json' / 'class_data.json', encoding='utf-8') as f:
    CLASS_DATA = json.load(f)

REPORT = Report('test_house_invariants')
METZ_PICKS = [0]
# Bonded-creature branch coverage (#35). Counted rather than assumed, because the #30 stack review's
# "both=0, neither=0 over 400 generations" was measured by a sample that could not reach the path it
# claimed to clear.
BOND = {'granted': 0, 'absent': 0, 'both': 0, 'neither': 0, 'druid_flip': 0,
        'feats': 0, 'tax': 0, 'flaws': 0, 'applied': 0}

# The feat economy's own data, imported rather than restated -- the pool and the tax allowlist are
# curated files and this test must fail when a creature strays outside them, not when a copy here
# falls behind them. `TYPE_NOUNS` is the label vocabulary; only the chassis-driven types have feats.
from utils.class_func.companion_feats import CHASSIS_TYPES as _CHASSIS_TYPES, TYPE_NOUNS as _NOUNS
COMPANION_FEAT_TYPES = {kind: _NOUNS[kind] for kind in _CHASSIS_TYPES}
with open(BACKEND / 'json' / 'animal_companion.json', encoding='utf-8') as _fh:
    _CHASSIS = json.load(_fh)
COMPANION_POOL = _CHASSIS.get('feats') or []
COMPANION_TAX_CHILDREN = _CHASSIS.get('tax_children') or []

# Metzofitz-only pool names: what metzofitz_feat_frame offers minus every AoN name (collisions
# resolve to AoN, so only names absent from feats.csv prove a homebrew pick happened).
from utils.class_func import feats as _feats
_METZ_ONLY = ({str(n).lower() for n in _feats.metzofitz_feat_frame()['name']}
              - {str(n).lower() for n in _feats.grab_and_clean_feats('data/feats.csv')['name']})

# Psionics. The twelve are ordinary class_data entries, so the sweep above already rolls every one
# of them at every level -- these sets only say which of the three manifesting shapes each belongs
# to (see utils/class_func/psionics.py). Sourced from data.py so a class moving between shapes is a
# one-place edit.
_PSIONIC = {x.lower() for x in getattr(data, 'psionic_class', [])}
_PP_ONLY = {x.lower() for x in getattr(data, 'psionic_pp_only_classes', [])}   # aegis: PP, no powers
# The soulknife manifests nothing at all: no stat, no power points, no powers. It still gets a
# payload entry, because a class silently absent from `manifesters` is indistinguishable from a bug.
_NO_MANIFESTING = {'soulknife'}

# Free talents, named talents and the subsystem bucket map are IMPORTED rather than restated: the
# module owns them, and a second copy here would let the gate agree with a drifted generator.
from utils.class_func.psionics import FREE_TALENTS, MANDATED_TALENTS, SUBSYSTEM_BUCKET

# The published class tables, read straight from the data file rather than through psionics.py: the
# point of the check below is to catch the generator disagreeing with the source of truth, which it
# cannot do if both read through the same accessor.
with open(BACKEND / 'json' / 'class_data' / 'psionics' / 'psionic_powers_known.json',
          encoding='utf-8') as f:
    PSIONIC_TABLES = json.load(f)

# Occult Adventures. class -> dataset -> the payload bucket its picks land in; must match the
# generic_class_option_chooser calls in main_test.py and the datasets in
# Backend/scripts/build_occult_class_data.py. validate_occult_data.py owns the DATA (are the pools
# well-formed, do the schedules reach the counts the prose promises); this owns the OUTPUT (did a
# generated character actually receive them).
_OCCULT_BUCKETS = {
    'occultist': {'implements': 'implements', 'focus powers': 'focus_powers'},
    'kineticist': {'elemental focus': 'elemental_focus', 'wild talents': 'wild_talents',
                   'infusions': 'infusions'},
    'medium': {'spirits': 'medium_spirit'},
    'mesmerist': {'mesmerist tricks': 'mesmerist_tricks', 'bold stare': 'bold_stare'},
    'psychic': {'disciplines': 'psychic_discipline',
                'phrenic amplifications': 'phrenic_amplifications'},
    'spiritualist': {'emotional focus': 'emotional_focus'},
}
# The option pools themselves, so a pick can be checked against the list it was supposed to come
# from. Read from the files rather than through the chooser, for the same reason the psionics
# tables above are: a gate that reads through the code it is gating cannot catch that code drifting.
_OCCULT_OPTIONS = {}
for _name in _OCCULT_BUCKETS:
    with open(BACKEND / 'json' / 'class_data' / f'{_name}.json', encoding='utf-8') as f:
        _OCCULT_OPTIONS[_name] = json.load(f)
# Occult branch coverage, same rule as BOND below: every occult check is conditional on an occult
# class being rolled, so a sweep that rolled none would print PASS having asserted nothing.
OCCULT = {'chars': 0, 'picks': 0, 'multi_pick_buckets': 0, 'kineticists': 0, 'casters': 0}


def check(condition, message):
    return REPORT.check(condition, message)


def generatable_classes():
    """Same pool as util._available_class_pool: class_data keys minus occult + pending PoW/psionic."""
    excluded = {x.lower() for x in getattr(data, 'occult_classes', [])}
    excluded |= {x.lower() for x in getattr(data, 'pow_classes_pending_foundry', [])}
    excluded |= {x.lower() for x in getattr(data, 'psionic_classes_pending', [])}
    return [name for name in CLASS_DATA if name not in excluded]


def hit_die(name):
    return int(str(CLASS_DATA[name]['hit die']).replace('.', '').replace('d', ''))


def skill_points(name):
    points = int(CLASS_DATA[name]['skill points at each level'])
    # the 2->4 rank floor: mirrors misc_homebrew_rules='Y', the generator's default
    return 4 if points == 2 else points


def final_score(payload, stat):
    return (payload[stat] + (payload.get('inherents') or {}).get(stat, 0)
            + (payload.get('level_up_stats') or {}).get(stat, 0))


def final_mod(payload, stat):
    return floor((final_score(payload, stat) - 10) / 2)


def check_character(cell, payload):
    L = payload['total_level']
    classes = payload['classes']

    # ---- spell slots are numbers ----
    # `spells_per_day_attr` loops `range(0, highest_spell_known + 1)` and indexes the scraped table,
    # so a `highest_spell_known` that runs one spell level past what the class actually gets reads a
    # cell the scrape correctly left blank -- and the tables spell blank as the STRING 'null', not
    # JSON null. That string reached the payload and from there the Foundry sheet and the web sheet.
    # It shipped for every sorcerer, oracle, psychic and arcanist at roughly half of all levels
    # (spontaneous casters gain each spell level one class level later than prepared ones), plus
    # every adept, until caster_formula learned both progressions.
    #
    # Checked HERE rather than by a golden fixture on purpose: the seven goldens contain no
    # spontaneous full caster at a divergent level, so fixing the bug moved none of them. A property
    # asserted over the whole swept roster catches the next class to acquire a bespoke progression;
    # one more fixture would only have covered the one class somebody thought to add.
    for book in (payload.get('spellbooks') or []):
        rows = book.get('spells_per_day_list') or []
        bad = [(i, cell_value) for i, cell_value in enumerate(rows)
               if not isinstance(cell_value, (int, float)) or isinstance(cell_value, bool)]
        check(not bad,
              f"{cell}: {book.get('name')} spells_per_day_list has non-numeric slot(s) {bad[:4]} "
              f"-- a blank table cell leaked in as a value; caster_formula is claiming a spell "
              f"level this class does not reach (row: {rows})")

    # ---- feats ----
    prof_slots = len(payload.get('profession_feats') or [])
    want_normal = max(0, ceil(L / 2) + 2 - prof_slots)
    check(payload['normal_feat_amount'] == want_normal,
          f"{cell}: normal feats {payload['normal_feat_amount']} != ceil({L}/2)+2-{prof_slots} = {want_normal}")
    budget = payload['feat_budget']
    check(budget['story'] == 1 + L // 5,
          f"{cell}: story feats {budget['story']} != 1 + {L}//5 = {1 + L // 5}")
    check(budget['flavor'] == 1, f"{cell}: flavor feats {budget['flavor']} != 1")
    flaws = len(payload['flaw'])
    want_flaw = min(flaws // 2 + 1, 3) if flaws else 0
    check(budget['flaw'] == want_flaw,
          f"{cell}: flaw feats {budget['flaw']} != diminishing({flaws}) = {want_flaw} ({payload['flaw']})")

    # ---- skill ranks ----
    mental = max(final_mod(payload, s) for s in ('int', 'wis', 'cha'))
    base = sum(max(1, skill_points(c['name']) + mental) * c['level'] for c in classes)
    ranks = payload['skill_ranks']
    recorded = payload['skill_rank_budget']
    favored = recorded - base - 2 * L
    check(favored in (0, L),
          f"{cell}: skill budget {recorded} != base {base} + background {2 * L} + favored 0|{L}")
    check(sum(ranks.values()) == recorded,
          f"{cell}: spent {sum(ranks.values())} of skill budget {recorded}")
    over = {s: r for s, r in ranks.items() if r > 3 * L}
    check(not over, f"{cell}: skills above the 3-ranks-per-level cap ({3 * L}): {over}")
    bad = [s for s in ranks if s not in data.skills]
    check(not bad, f"{cell}: ranks on unrenderable skills: {bad}")

    # ---- Metzofitz homebrew feats ----
    placed = []
    for bucket in ('feats', 'story_feats', 'flaw_feats', 'flavor_feats', 'class_feats'):
        placed.extend(str(f) for f in (payload.get(bucket) or []))
    metz = [f for f in placed if f.lower() in _METZ_ONLY]
    METZ_PICKS[0] += len(metz)
    descs = {str(k).lower(): v for k, v in (payload.get('homebrew_feat_desc_dict') or {}).items()}
    undescribed = [f for f in metz if not descs.get(f.lower())]
    check(not undescribed, f"{cell}: Metzofitz feats with no rules text: {undescribed}")

    # ---- psionics ----
    psionic = [c for c in classes if c['name'] in _PSIONIC]
    manifesters = payload.get('manifesters')
    descs = payload.get('powers_desc_dict')
    check(isinstance(manifesters, list) and isinstance(descs, dict),
          f"{cell}: payload is missing the manifesters / powers_desc_dict block")
    if isinstance(manifesters, list) and isinstance(descs, dict):
        # One entry per psionic class and nothing else -- an extra entry means a non-psionic class
        # leaked in, a missing one means a manifester vanished from the sheet.
        check(sorted(m['name'] for m in manifesters) == sorted(c['name'] for c in psionic),
              f"{cell}: manifesters {[m['name'] for m in manifesters]} "
              f"!= psionic classes {[c['name'] for c in psionic]}")
        # Powers only ever come from a manifester, so an empty pool must mean an empty dict.
        if not psionic:
            check(not descs, f"{cell}: powers_desc_dict is populated on a non-psionic character")

        for m in manifesters:
            name = m['name']
            tag = f"{cell}: {name}"
            entry = next((c for c in psionic if c['name'] == name), None)
            if entry is None:
                continue
            table = PSIONIC_TABLES.get(name, {})
            # Manifester level is the class level (no cross-class stacking in psionics), clamped at
            # 20 because the published tables stop there -- the payload exports the clamped value,
            # so it is recomputed here rather than read back from `classes`.
            check(m['level'] == entry['level'],
                  f"{tag}: manifester entry level {m['level']} != class level {entry['level']}")
            check(m['manifester_level'] == min(entry['level'], 20),
                  f"{tag}: manifester level {m['manifester_level']} != min({entry['level']}, 20)")
            row = min(max(m['manifester_level'], 1), 20) - 1

            # ---- subsystem picks: generated, and findable ----
            # The failure this guards is "generated but invisible": the picks land in the class
            # features dict under a bucket name only main_test.py knew, so a renderer showing a
            # class's psionics had no way to reach them. The aegis and soulknife are the proof
            # cases -- their tab has nothing else on it, so a missing pointer reads as an empty tab.
            want_bucket = SUBSYSTEM_BUCKET.get(name, '')
            check(m['subsystem_bucket'] == want_bucket,
                  f"{tag}: subsystem_bucket {m['subsystem_bucket']!r} != {want_bucket!r}")
            if want_bucket:
                picks = (payload.get('class_features') or {}).get(want_bucket) or {}
                # How many picks are DUE at this level. generic_class_option_chooser walks the
                # schedule (`i = len(chosen_set)`), so the count is exactly the entries at or below
                # the class level; the three single-pick classes have no schedule and take one at
                # 1st. Read from class_choice_schedule.json via the harness's own expansion, NOT
                # through generic_func.levels_for -- see _harness.choice_schedule.
                schedule = schedule_levels(SCHEDULE, name, want_bucket, entry['level'])
                want_picks = len(schedule) if schedule is not None else 1
                check(len(picks) == want_picks,
                      f"{tag}: subsystem bucket {want_bucket!r} holds {len(picks)} picks, expected "
                      f"{want_picks} at class level {entry['level']} -- picks that never land "
                      f"appear nowhere on a sheet")

            if name in _NO_MANIFESTING:
                check(not m['manifesting_stat'] and not m['pp_per_day'] and not m['powers_chosen']
                      and not m['caster_type'],
                      f"{tag}: manifests nothing, but carries "
                      f"stat={m['manifesting_stat']!r} pp={m['pp_per_day']} "
                      f"caster_type={m['caster_type']!r} powers={len(m['powers_chosen'])}")
                # The mind blade is the soulknife's ONLY psionic thing, so an absent one leaves the
                # class with nothing to render. It must also be the weapon actually equipped.
                blade = m['mind_blade']
                check(isinstance(blade, dict) and blade.get('name'),
                      f"{tag}: no mind blade on the manifester entry")
                if isinstance(blade, dict):
                    check(blade['name'] == payload.get('weapon_name'),
                          f"{tag}: mind blade {blade['name']!r} != equipped weapon "
                          f"{payload.get('weapon_name')!r}")
                continue

            check(m['manifesting_stat'] in ('str', 'dex', 'con', 'int', 'wis', 'cha'),
                  f"{tag}: manifesting stat {m['manifesting_stat']!r} is not an ability")
            # A key ability of 9 or lower cannot manifest AT ALL -- not badly, at all -- so the
            # whole record legitimately reads zero. Everything below assumes the gate is passed.
            if final_mod(payload, m['manifesting_stat']) < 0:
                # caster_type moves with the points: handing Foundry a progression on a book worth
                # zero points would have the module compute points the rules deny this character.
                check(not m['caster_type'],
                      f"{tag}: cannot manifest, but carries caster_type {m['caster_type']!r}")
                continue

            # Power points = the class table at manifester level, PLUS floor(mod x ML / 2). The
            # formula is restated rather than imported so a change to psionics.py has to be a
            # deliberate change here too -- that is the point of an invariant test.
            base_pp = table.get('pp_per_day', [0] * 20)[row]
            bonus = max(0, floor(final_mod(payload, m['manifesting_stat']) * m['manifester_level'] / 2))
            check(m['pp_per_day'] == base_pp + bonus,
                  f"{tag}: pp {m['pp_per_day']} != table {base_pp} + bonus {bonus}")
            # caster_type is the pf1-psionics progression name the Foundry manifester book needs.
            # Recomputed from the class's own table rather than trusted: a wrong one is invisible
            # in the payload and shows up in Foundry as a plausible but wrong power-point total.
            want_type = next((k for k, v in data.psionic_pp_tables.items()
                              if v == table.get('pp_per_day')), '')
            check(m['caster_type'] == want_type,
                  f"{tag}: caster_type {m['caster_type']!r} != {want_type!r} for its pp table")

            if name in _PP_ONLY:
                check(not m['powers_chosen'],
                      f"{tag}: spends power points on class options, but knows "
                      f"{len(m['powers_chosen'])} power(s)")
                continue

            # The class table is a CEILING. Every power-knowing class also demands a key ability of
            # "at least 10 + the power's level" to learn one, so a middling score caps the class
            # table -- most visibly on the psychic warrior, which manifests off Wis but plays off
            # Str. Without this the gate would pass a psion handed 9th-level powers on Int 14.
            want_max = min(table.get('max_power_level', [0] * 20)[row],
                           final_score(payload, m['manifesting_stat']) - 10)
            check(m['max_power_level'] == want_max,
                  f"{tag}: max power level {m['max_power_level']} != min(table, score-10) = {want_max}")
            # Talents are granted free by class feature and explicitly do NOT count against powers
            # known, so the total on the sheet is the table plus the grant.
            want_talents = FREE_TALENTS.get(name, 0)
            check(m['talents_known'] == want_talents,
                  f"{tag}: {m['talents_known']} talents != class grant {want_talents}")
            want_known = table.get('powers_known', [0] * 20)[row]
            check(len(m['powers_chosen']) == want_known + want_talents,
                  f"{tag}: knows {len(m['powers_chosen'])} powers != table {want_known} "
                  f"+ {want_talents} free talents")
            # Talents live in bucket 0 and nowhere else -- a talent that landed in a leveled bucket
            # would mean it had been bought with a powers-known slot after all.
            check(len(m['powers_by_level'][0]) == want_talents if m['powers_by_level'] else True,
                  f"{tag}: bucket 0 holds {len(m['powers_by_level'][0]) if m['powers_by_level'] else 0} "
                  f"names, expected exactly the {want_talents} free talents")
            for named in MANDATED_TALENTS.get(name, []):
                check(named in m['powers_chosen'],
                      f"{tag}: class grants {named!r} by name, but it is not among its powers")
            # powers_known_list is how the sheet groups the same powers by level, so the two views
            # of one fact must agree.
            check(sum(m['powers_known_list']) == len(m['powers_chosen']),
                  f"{tag}: powers_known_list sums to {sum(m['powers_known_list'])} "
                  f"but {len(m['powers_chosen'])} powers were chosen")
            check(len(set(m['powers_chosen'])) == len(m['powers_chosen']),
                  f"{tag}: duplicate powers in powers_chosen")
            # powers_by_level is the only record of WHICH power sits at which level -- the
            # description entry keys its levels by power list ("psion/wilder"), not by class, so a
            # renderer cannot recover it. Both renderers group by these buckets.
            buckets = m['powers_by_level']
            check(len(buckets) == want_max + 1,
                  f"{tag}: powers_by_level has {len(buckets)} buckets, expected {want_max + 1} "
                  f"(levels 0..{want_max})")
            check(sorted(p for b in buckets for p in b) == sorted(m['powers_chosen']),
                  f"{tag}: powers_by_level does not reconcile with powers_chosen")
            check([len(b) for b in buckets] == m['powers_known_list'],
                  f"{tag}: powers_known_list {m['powers_known_list']} != bucket sizes "
                  f"{[len(b) for b in buckets]}")
            # Same failure the Metzofitz-feat check guards: a name with no rules text renders as an
            # empty row in Foundry and as nothing at all on the web sheet.
            missing = [p for p in m['powers_chosen'] if not descs.get(p)]
            check(not missing, f"{tag}: powers with no rules text: {missing[:5]}")
            if name == 'psion':
                # The discipline decides the psion's whole power list, so it cannot be blank.
                check(m['discipline'], f"{tag}: no discipline chosen")

    # ---- Occult Adventures ----
    features = payload.get('class features') or {}
    for entry in classes:
        name = entry['name']
        if name not in _OCCULT_BUCKETS:
            continue
        OCCULT['chars'] += 1
        level = entry['level']
        for dataset, bucket in _OCCULT_BUCKETS[name].items():
            tag = f"{cell}: {name}/{dataset}"
            pool = _OCCULT_OPTIONS[name][dataset]
            chosen = features.get(bucket) or {}
            # How many picks the schedule grants by this class level. A subsystem with no schedule
            # is a single pick taken at 1st -- the marksman/vitalist shape psionics already uses.
            schedule = schedule_levels(SCHEDULE, name, bucket, level)
            want = len(schedule) if schedule is not None else 1
            check(len(chosen) == want,
                  f"{tag}: {len(chosen)} pick(s) at class level {level}, expected {want}")
            OCCULT['picks'] += len(chosen)
            if schedule is not None and want > 1:
                OCCULT['multi_pick_buckets'] += 1
            # A pick that is not in the pool means the bucket was written by something else --
            # exactly the collision that would silently merge two classes' choices into one bucket.
            strays = [p for p in chosen if p not in pool]
            check(not strays, f"{tag}: picks that are not options: {strays[:5]}")
            # Same failure the psionics and Metzofitz checks guard: a name with no rules text is an
            # empty row in Foundry and nothing at all on the web sheet.
            blank = [p for p, text in chosen.items() if not str(text).strip()]
            check(not blank, f"{tag}: picks with no rules text: {blank[:5]}")

        if name == 'kineticist':
            # Burn is Constitution-priced and deliberately unmodelled (section 10), but the class
            # must never acquire a spellbook on the way past -- that is what a stray base_classes
            # or caster_mod entry would look like from out here.
            OCCULT['kineticists'] += 1
            books = [b for b in (payload.get('spellbooks') or []) if b.get('name') == 'kineticist']
            check(not books,
                  f"{cell}: kineticist has a spellbook; it is a non-caster in every table")
        else:
            OCCULT['casters'] += 1
            books = [b for b in (payload.get('spellbooks') or []) if b.get('name') == name]
            check(len(books) == 1,
                  f"{cell}: {name} casts psychic magic but has {len(books)} spellbook(s)")

    # ---- OGL section 10 ----
    # Serving extracted mechanics is Distribution, so every payload must point at the licence.
    check(payload.get('license_url'), f"{cell}: payload carries no license_url")

    # ---- HP ----
    max_hd = sum(hit_die(c['name']) * c['level'] for c in classes)
    check(payload['sheet_health'] == max_hd,
          f"{cell}: sheet_health {payload['sheet_health']} != full-HP hit dice {max_hd}")
    want_hp = max_hd + final_mod(payload, 'con') * L
    check(payload['Total_HP'] - want_hp in (0, L),
          f"{cell}: Total_HP {payload['Total_HP']} != {want_hp} (+favored 0|{L})")

    check_bonded_creatures(cell, payload)


def check_companion_feats(tag, entry, stats):
    """Spec section 8, D14/D15/D16 -- the feat economy and the modifier fold.

    `validate_companion_feats.py` gates the DATA (every pool name real, every declared effect
    landing on a probe block). What needs a whole generated creature is the wiring: that the labels
    line up with the feats they name, that no feat arrives that this body could not take, and that
    the fold left an audit trail instead of quietly moving a number.
    """
    if entry.get('type') not in COMPANION_FEAT_TYPES:
        return                       # familiars use the master's feats; eidolons are evolutions
    feats = entry.get('feats')
    labels = entry.get('feat_labels')
    check(isinstance(feats, list) and isinstance(labels, list),
          f"{tag}: feats/feat_labels are {type(feats).__name__}/{type(labels).__name__}, not lists")
    if not (isinstance(feats, list) and isinstance(labels, list)):
        return
    BOND['feats'] += len(feats)

    # A label list out of step with its feat list is the defect that renames every feat on the
    # sheet by one position -- silently, and only visibly wrong to someone who knows the chassis.
    check(len(labels) == len(feats),
          f"{tag}: {len(feats)} feats but {len(labels)} labels")
    noun = COMPANION_FEAT_TYPES[entry['type']]
    for label in labels:
        check(str(label).startswith(f'{noun} '),
              f"{tag}: label {label!r} does not read '{noun} <grant level>'")

    pool = set(COMPANION_POOL)
    strays = [f for f in feats + list(entry.get('flaw_feats') or []) if f not in pool]
    check(not strays, f"{tag}: feats that are not in the bonded-creature pool: {strays[:5]}")

    allowed = set(COMPANION_TAX_CHILDREN)
    for primary, children in (entry.get('feat_tax_dict') or {}).items():
        BOND['tax'] += len(children or [])
        outside = [c for c in children or [] if c not in allowed]
        check(not outside,
              f"{tag}: feat tax granted {outside[:5]} via {primary!r}, which is not on the "
              "tax_children allowlist -- that is how a wolf ends up with Drunken Brawler")

    # D16: flaws buy feats on the diminishing house ladder, exactly as they do for a PC.
    flaws = entry.get('flaws')
    check(isinstance(flaws, list), f"{tag}: flaws is {type(flaws).__name__}, not a list")
    if isinstance(flaws, list):
        BOND['flaws'] += len(flaws)
        check(len(flaws) <= 4, f"{tag}: {len(flaws)} flaws; the d100 ladder tops out at 4")
        check(sorted(entry.get('flaw_effects') or {}) == sorted(flaws),
              f"{tag}: flaw_effects does not reconcile with flaws")
        want = min(len(flaws) // 2 + 1, 3) if flaws else 0
        got = entry.get('flaw_feat_amount')
        check(got in (0, want),
              f"{tag}: {len(flaws)} flaws grant {got} feats, expected {want} (or 0 without the "
              "misc_homebrew flag)")
        check(len(entry.get('flaw_feats') or []) <= (got or 0),
              f"{tag}: {len(entry.get('flaw_feats') or [])} flaw feats but only {got} were bought")

    # D14: the fold leaves provenance. `stats` is FINAL for the web sheet, so an unexplained number
    # is unauditable -- and a source naming a feat the creature does not own is a fold gone wrong.
    applied = stats.get('applied_changes')
    check(isinstance(applied, list), f"{tag}: stats.applied_changes is missing")
    owned = set(feats) | set(entry.get('flaw_feats') or []) | set(entry.get('flaws') or [])
    owned |= {c for children in (entry.get('feat_tax_dict') or {}).values() for c in children or []}
    for record in applied or []:
        BOND['applied'] += 1
        source = str(record.get('source') or '')
        stem = source.split(' (via ')[0].split(') ', 1)[-1]
        check(stem in owned,
              f"{tag}: stats.applied_changes credits {source!r}, which the creature does not own")
    check(isinstance(stats.get('context_notes'), list),
          f"{tag}: stats.context_notes is missing")


def check_bonded_creatures(cell, payload):
    """Map #18, slice K (#35). The stat-block arithmetic is gated species-by-species in
    `validate_companion_stats.py`; what is checkable only HERE is the shape of the emitted list and
    the druid flip, both of which need a whole generated character.

    The flip is the regression test for F's rewire, and it is here because of how the original
    measurement failed: "both=0, neither=0 over 400 generations" was reported by a sample that never
    rolled an archetype and so could not reach the broken path. A sample that cannot reach a defect
    reports zero forever, so this counts BRANCHES REACHED and fails if the sweep never saw one.
    """
    entries = payload.get('bonded_creatures')
    check(isinstance(entries, list),
          f"{cell}: bonded_creatures is {type(entries).__name__}, not a list")
    if not isinstance(entries, list):
        return

    for entry in entries:
        tag = f"{cell}: {entry.get('grantor')}/{entry.get('type')}"
        check(entry.get('type') in ('companion', 'mount', 'familiar', 'eidolon'),
              f"{tag}: type {entry.get('type')!r} is not a bonded-creature type")

        if not entry.get('species'):
            BOND['absent'] += 1
            # D9: an absence entry is the record of WHY there is no creature, so it must carry one.
            check(entry.get('outcome') and entry['outcome'] != 'granted',
                  f"{tag}: no species but outcome is {entry.get('outcome')!r}")
            check(entry.get('stats') is None,
                  f"{tag}: absence entry carries a stats block")
            continue

        BOND['granted'] += 1
        check(entry.get('effective_level', 0) >= 1,
              f"{tag}: granted at effective level {entry.get('effective_level')!r}")
        stats = entry.get('stats')
        check(isinstance(stats, dict), f"{tag}: species {entry['species']!r} has no stats block")
        if not isinstance(stats, dict):
            continue

        # #31/D2: the backend is the SOLE source of these numbers, so a missing one is not something
        # a renderer can fill in -- the standalone web sheet has no game system to fall back on.
        for field in ('hp', 'ac', 'touch_ac', 'flat_footed_ac', 'bab', 'cmb', 'cmd', 'hd', 'size'):
            check(stats.get(field) is not None, f"{tag}: stats.{field} is None")
        check(stats.get('hp', 0) >= 1, f"{tag}: hp {stats.get('hp')}")
        check(stats.get('touch_ac', 0) <= stats.get('ac', 0),
              f"{tag}: touch AC {stats.get('touch_ac')} exceeds full AC {stats.get('ac')}")
        check(stats.get('hd') == (entry.get('chassis') or {}).get('hd'),
              f"{tag}: stats.hd {stats.get('hd')} != chassis hd "
              f"{(entry.get('chassis') or {}).get('hd')} -- the chassis is re-read after stacking, "
              f"so these cannot disagree")
        check(all(v is not None for k, v in (stats.get('abilities') or {}).items() if k != 'int'),
              f"{tag}: a non-Int ability score is None ({stats.get('abilities')})")

        # Ticket 04: `size_change` exists exactly when the advancement grew the creature, and its
        # values are provenance for numbers already totalled in. Present-when-it-should-not-be is
        # the failure that would make a renderer apply the geometry twice.
        start = next((v for k, v in (entry.get('species_stats') or {}).items()
                      if str(k) == 'starting statistics' and isinstance(v, dict)), {})
        grew = str(start.get('size') or '').strip().lower() != str(stats.get('size') or '').lower()
        check(bool(stats.get('size_change')) == grew,
              f"{tag}: size {start.get('size')!r} -> {stats.get('size')!r} but size_change is "
              f"{stats.get('size_change')!r}")

        check_companion_feats(tag, entry, stats)

    # ---- the druid flip (F's rewire) ----
    # Only meaningful on a character whose ONLY domain source is the druid bond; clerics and
    # inquisitors get domains from their own subsystem and would read as a false "both".
    names = {c['name'] for c in payload['classes']}
    if 'druid' not in names or names & {'cleric', 'inquisitor'}:
        return
    druid = [e for e in entries if e.get('grantor') == 'druid']
    if not druid:
        return
    got_creature = any(e.get('species') for e in druid)
    got_domain = bool(payload.get('full_domain'))
    removed = any(e.get('outcome') == 'archetype_removed' for e in druid)

    if got_creature and got_domain:
        BOND['both'] += 1
        check(False, f"{cell}: druid has BOTH a companion and a domain -- the flip is not "
                     f"exclusive (the defect a fresh per-row draw reintroduces without F's rewire)")
    elif not got_creature and not got_domain and not removed:
        BOND['neither'] += 1
        check(False, f"{cell}: druid has NEITHER a companion nor a domain, and no archetype "
                     f"removed the feature")
    BOND['druid_flip'] += 1


def run(classes, levels, seeds):
    total = len(classes) * len(levels) * len(seeds)
    done = 0
    for name in classes:
        for level in levels:
            for seed in seeds:
                cell = f"{name} L{level} seed {seed}"
                done += 1
                try:
                    with redirect_stdout(io.StringIO()):
                        payload = main_test.generate_random_char(
                            class_choice=name, chosen_BAB='high', multi_class='N',
                            userInput_race='random', userInput_region='Tal-Falko',
                            alignment_input='random', userInput_gender='random',
                            high_level=level, low_level=level, gold_num=10000,
                            num_dice='4', num_sides='6', use_backstory_api='N',
                            spheres_flag='N', seed=seed)
                except Exception:
                    tail = traceback.format_exc().strip().splitlines()
                    REPORT.error(f"{cell}: generation raised -- {tail[-1]} "
                                 f"(replay with seed={seed})")
                    continue
                check_character(f"{cell} (gen seed {payload.get('generation_seed')})", payload)
        print(f"  {name}: ok through L{levels[-1]} ({done}/{total})")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--classes', help='comma-separated subset (default: every generatable class)')
    parser.add_argument('--levels', help=f'comma-separated levels (default {LEVELS})')
    parser.add_argument('--seeds', type=int, default=len(SEEDS),
                        help=f'how many of the fixed seeds to run (default {len(SEEDS)})')
    args = parser.parse_args()

    classes = args.classes.split(',') if args.classes else generatable_classes()
    unknown = [c for c in classes if c not in CLASS_DATA]
    if unknown:
        print(f"unknown classes: {unknown}")
        return 2
    levels = [int(x) for x in args.levels.split(',')] if args.levels else LEVELS
    seeds = SEEDS[:max(1, args.seeds)]

    total = len(classes) * len(levels) * len(seeds)
    print(f"sweeping {len(classes)} classes x {levels} x {len(seeds)} seed(s) "
          f"= {total} generations")
    run(classes, levels, seeds)

    # Existence check only on a sweep big enough that zero picks means the wiring broke, not luck.
    if total >= 100:
        check(METZ_PICKS[0] > 0,
              f"no Metzofitz homebrew feat appeared in {total} generations -- pool wiring broken?")
    print(f"  Metzofitz picks across the sweep: {METZ_PICKS[0]}")

    # The companion checks above are all conditional on a creature existing, so a sweep that rolled
    # none would print PASS having asserted nothing. Say so instead.
    if total >= 100:
        check(BOND['granted'] > 0,
              f"no bonded creature was granted in {total} generations -- every companion check "
              f"above was skipped, so this run proves nothing about them")
        check(BOND['druid_flip'] > 0,
              f"the druid flip was never reached in {total} generations")
        # Same guard one level down: the whole feat economy is gated behind a granted creature, so
        # a run that granted creatures but rolled no feats or no flaws asserted nothing about D15.
        check(BOND['feats'] > 0,
              f"{BOND['granted']} bonded creatures were granted in {total} generations but not one "
              f"feat was rolled -- every D15 check above was skipped")
        check(BOND['flaws'] > 0,
              f"{BOND['granted']} bonded creatures were granted but not one flaw was rolled -- "
              f"every D16 flaw check above was skipped")
    print(f"  bonded creatures: {BOND['granted']} granted, {BOND['absent']} absence entries, "
          f"{BOND['druid_flip']} druid flips (both={BOND['both']}, neither={BOND['neither']})")
    print(f"  companion feats: {BOND['feats']} rolled, {BOND['tax']} taxed in, "
          f"{BOND['flaws']} flaws, {BOND['applied']} folded changes")

    # Same guard, same reason: every occult check is conditional on rolling one of the six.
    if total >= 100:
        check(OCCULT['chars'] > 0,
              f"no occult class was rolled in {total} generations -- every occult check above was "
              f"skipped, so this run proves nothing about them")
        check(OCCULT['multi_pick_buckets'] > 0,
              "no occult multi-pick bucket was ever exercised; only single picks were checked")
        check(OCCULT['kineticists'] > 0 and OCCULT['casters'] > 0,
              f"the occult sweep reached {OCCULT['kineticists']} kineticist(s) and "
              f"{OCCULT['casters']} caster(s) -- both sides of the spellbook split must be hit")
    print(f"  occult classes: {OCCULT['chars']} rolled, {OCCULT['picks']} picks, "
          f"{OCCULT['multi_pick_buckets']} multi-pick buckets "
          f"({OCCULT['kineticists']} kineticist, {OCCULT['casters']} caster)")

    return REPORT.finish(f'{REPORT.checks} checks')


if __name__ == '__main__':
    sys.exit(main())
