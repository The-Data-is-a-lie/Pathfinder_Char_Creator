"""Regression checks for the pipeline phase contracts (run directly; this repo has no pytest
harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    .venv/Scripts/python.exe Backend/scripts/tests/test_pipeline_phases.py

The point of utils/class_func/pipeline.py is that an ordering mistake RAISES instead of silently
producing a worse character. A guard that never fires is worth nothing, so these tests deliberately
violate each contract and assert the error, then assert the correct order is accepted.

The four ordering hazards these protect (each was previously only a comment in main_test.py):
  * stats must run after randomize_level -- inherents and level-up bumps scale off total level
  * profession_chooser must run before skills_selector -- the Always Improving gate reads
    character.profession_feats
  * the class-features bucket must be finished before the bonus-spell lookups read it
  * a phase that stops setting what it declares is caught at its own boundary
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report  # noqa: E402

from utils.class_func.pipeline import (  # noqa: E402
    PhaseOrderError, PhaseRecord, phase, seal, is_sealed, require_sealed)

REPORT = Report('test_pipeline_phases')


def check(label, condition):
    if condition:
        print(f'  ok    {label}')
    else:
        print(f'  FAIL  {label}')
    REPORT.check(condition, label)


def raises(label, func, *args, **kwargs):
    """Assert func raises PhaseOrderError, and that the message names the missing thing."""
    try:
        func(*args, **kwargs)
    except PhaseOrderError as exc:
        print(f'  ok    {label}  -> {exc}')
        return str(exc)
    except Exception as exc:                                   # noqa: BLE001 - report the wrong type
        check(f'{label} (raised {type(exc).__name__}, expected PhaseOrderError)', False)
        return ''
    check(f'{label} (did not raise)', False)
    return ''


class Stub:
    """Minimal stand-in: the contract only looks at attribute presence."""


# --------------------------------------------------------------------------------------------- #

def test_requires_missing_raises():
    @phase(requires=['level'], provides=[])
    def needs_level(character):
        return 'ran'

    msg = raises('a phase missing its requirement raises', needs_level, Stub())
    check('the error names the phase', 'needs_level' in msg)
    check('the error names the missing attribute', 'level' in msg)

    ok = Stub()
    ok.level = 12
    check('the same phase runs once the requirement is set', needs_level(ok) == 'ran')


def test_falsy_requirement_counts_as_set():
    """A level of 0 or an empty list is SET. The check is 'has this phase run', not 'is it truthy' --
    testing truthiness would make a legitimately-empty value look like a missing one."""
    @phase(requires=['classes', 'bab_total'], provides=[])
    def needs_both(character):
        return 'ran'

    stub = Stub()
    stub.classes = []
    stub.bab_total = 0
    check('falsy-but-set attributes satisfy requires', needs_both(stub) == 'ran')


def test_provides_is_checked_on_exit():
    @phase(requires=[], provides=['skill_rank_budget'])
    def forgets_to_set(character):
        return 'ran'

    msg = raises('a phase that does not set what it provides raises', forgets_to_set, Stub())
    check('the exit error names the attribute', 'skill_rank_budget' in msg)

    @phase(requires=[], provides=['skill_rank_budget'])
    def sets_it(character):
        character.skill_rank_budget = 264
        return 'ran'

    check('a phase that sets what it provides passes', sets_it(Stub()) == 'ran')


def test_sealing():
    stub = Stub()
    check('a bucket starts unsealed', not is_sealed(stub, 'class features'))
    raises('reading an unsealed bucket raises', require_sealed, stub, 'class features', 'a reader')
    seal(stub, 'class features')
    check('the bucket reads as sealed after seal()', is_sealed(stub, 'class features'))
    require_sealed(stub, 'class features', 'a reader')          # must not raise
    check('reading a sealed bucket is allowed', True)
    check('sealing one bucket does not seal another', not is_sealed(stub, 'spellbooks'))


def test_real_phases_declare_their_hazards():
    """The two extracted phases must actually carry the contracts, not just be plain functions --
    otherwise the guard silently disappears the next time someone edits main_test."""
    import main_test

    stats_phase = main_test.phase_roll_and_assign_stats
    check('stats phase requires level (inherents scale off total level)',
          'level' in getattr(stats_phase, 'requires', ()))
    check('stats phase requires chosen_race (racial stat table)',
          'chosen_race' in getattr(stats_phase, 'requires', ()))

    prof_phase = main_test.phase_professions_and_skills
    check('professions phase provides profession_feats (the Always Improving gate)',
          'profession_feats' in getattr(prof_phase, 'provides', ()))
    check('professions phase provides skill_rank_budget',
          'skill_rank_budget' in getattr(prof_phase, 'provides', ()))

    # The real hazard: running the stats phase before randomize_level has set `level`.
    raises('the real stats phase raises when run before level exists',
           stats_phase, Stub(), '4', '6', 'Y')

    # phase_bootstrap_identity is the FIRST phase, so it has nothing to require -- there is no
    # earlier phase whose output could be absent. Its guard is entirely on the way out: it declares
    # eight attributes, several of which are set invisibly inside a callee (`region` inside
    # region_chooser, `c_class` inside chooseClass via select_classes) rather than returned. Those
    # are exactly the writes that go missing without anyone noticing, so `provides` is the contract
    # that matters here and an empty `requires` is the correct declaration, not a stub.
    boot = main_test.phase_bootstrap_identity
    check('bootstrap phase requires nothing (it is first; nothing crosses in)',
          getattr(boot, 'requires', None) == ())
    for name in ('chosen_race', '_class_picks', 'region', 'f_name'):
        check(f'bootstrap phase provides {name}',
              name in getattr(boot, 'provides', ()))
    # The next phase's requires must be satisfiable by what this one provides, or the chain is
    # broken at its first link.
    check('bootstrap provides chosen_race, which the stats phase requires',
          'chosen_race' in getattr(boot, 'provides', ())
          and 'chosen_race' in getattr(stats_phase, 'requires', ()))


def test_alignment_and_level_phase():
    """phase_alignment_and_level -- the block between identity and stats.

    Its hazards are not the obvious ones. Nothing here would CRASH out of order; each failure is a
    quietly different NPC, which is why the contract has to carry them:

      * `region` -- randomize_deity reads it through a `getattr(self, "region", None)` default, so
        running before region_chooser costs the homeland faith bias silently, with no exception.
      * `chosen_race` -- randomize_body_feature indexes the race's age/height/weight dice.
      * `level`/`classes` -- this phase is where randomize_level runs, so it is the link that lets
        the stats phase's `requires=['level', 'classes']` ever be satisfied.
    """
    import main_test

    align_phase = main_test.phase_alignment_and_level
    boot = main_test.phase_bootstrap_identity
    stats_phase = main_test.phase_roll_and_assign_stats

    for name in ('region', 'chosen_race', '_class_picks'):
        check(f'alignment/level phase requires {name}',
              name in getattr(align_phase, 'requires', ()))
    check('every requirement is something bootstrap provides (the chain holds)',
          set(align_phase.requires) <= set(boot.provides))
    check('it provides level and classes, which the stats phase requires',
          set(stats_phase.requires) - {'chosen_race'} <= set(align_phase.provides))

    # The two strings that are NOT interchangeable: choose_alignment stores the lowercased form
    # (the deity table is keyed that way) and the payload exports the title-cased one. Both must be
    # declared, or a later reader silently picks up the wrong casing.
    for name in ('alignment', 'alignment_display'):
        check(f'alignment/level phase provides {name}', name in align_phase.provides)

    # The chosen deity is `deity_choice`, never `deity` -- `character.deity` is the deity data TABLE
    # keyed by alignment, and overwriting it with one deity breaks domain selection.
    check('it provides deity_choice, not deity',
          'deity_choice' in align_phase.provides and 'deity' not in align_phase.provides)

    # The real hazard, run for real: no region, no race, no class picks.
    raises('the real alignment/level phase raises when run before bootstrap',
           align_phase, Stub(), 'LG', 'random', 1, 5)

    # ...and it still raises when only SOME of the identity is in place, which is the ordering
    # mistake that would actually happen -- a block moved above one call rather than above all three.
    partial = Stub()
    partial.region = 'Tal-Falko'
    partial.chosen_race = 'Human'
    msg = raises('it still raises when only part of the identity is set',
                 align_phase, partial, 'LG', 'random', 1, 5)
    check('the error names _class_picks and nothing already set', '_class_picks' in msg
          and 'chosen_race' not in msg)


def test_hp_and_spellbooks_phase():
    """phase_hp_and_spellbooks -- HP, then one spellbook per class.

    Its hazard is the quietest one in the pipeline so far: total_hp_calc reads the FINAL Con score
    through final_ability_mod, so running it before the stats phase does not raise, it just gives
    every character the hit points of a Con-10 one. `requires=['stats']` is what turns that into an
    error at the boundary instead of a wrong number on a Foundry sheet weeks later.
    """
    import main_test

    hp_phase = main_test.phase_hp_and_spellbooks
    stats_phase = main_test.phase_roll_and_assign_stats
    align_phase = main_test.phase_alignment_and_level

    check('hp phase requires stats (Total_HP uses the FINAL Con score)',
          'stats' in getattr(hp_phase, 'requires', ()))
    for name in ('level', 'classes'):
        check(f'hp phase requires {name}', name in hp_phase.requires)
    check('every requirement comes from an earlier phase (the chain holds)',
          set(hp_phase.requires) <= set(align_phase.provides) | set(stats_phase.provides) | {'stats'})

    # The three names that used to leave this block as locals are now declared outputs. If any of
    # them stops being set, `provides` fails here rather than at the export dict 1,300 lines later.
    for name in ('total_hp_rolls', 'spells_per_day_list', 'spells_known_list'):
        check(f'hp phase provides {name} (was a local crossing out)', name in hp_phase.provides)
    check('hp phase provides Total_HP and spellbooks',
          {'Total_HP', 'spellbooks'} <= set(hp_phase.provides))

    raises('the real hp phase raises when run before stats exist', hp_phase, Stub())

    partial = Stub()
    partial.level = 5
    partial.classes = [{'name': 'wizard', 'level': 5}]
    msg = raises('it still raises when only the level half is in place', hp_phase, partial)
    check('the error names stats and nothing already set',
          'stats' in msg and 'classes' not in msg)


def test_class_options_phase():
    """phase_class_options -- the block the ticket expected to need twenty-plus `requires`.

    It needs four, and the reason is the rule rather than luck: the block reads a great deal, but
    nearly all of it is state the block itself produced a few lines earlier. What actually crosses
    in is the prerequisite-seeding state (the ability scores, BAB and caster level that every talent
    pool is filtered against) and one write-after-write.
    """
    import main_test

    opts = main_test.phase_class_options
    hp_phase = main_test.phase_hp_and_spellbooks

    check('class-options phase keeps requires small (ticket 05: 2-4 names)',
          2 <= len(opts.requires) <= 4)
    for name in ('stats', 'bab_total', 'casting_level_num'):
        check(f'class-options requires {name} (talent prereq seeding)', name in opts.requires)

    # The one true write-after-write in the pipeline: favored_class_calculator does
    # `character.Total_HP += character.level`. If the HP phase were allowed to run afterwards it
    # would OVERWRITE the favoured-class bonus rather than fail -- so the ordering has to be a
    # contract, and this is the assertion that says so.
    check('class-options requires Total_HP (favoured class ADDS to it)',
          'Total_HP' in opts.requires)
    check('...and the HP phase is the thing that provides it, so the order is forced',
          'Total_HP' in hp_phase.provides)

    # The eight names that used to cross out as locals.
    for name in ('skill_rank_level', 'chosen_school', 'chosen_opposing_school', 'archetype_info',
                 'archetypes_per_class', 'bloodline_sorc', 'bloodline_rager',
                 'animal_companion_feats'):
        check(f'class-options provides {name} (was a local crossing out)', name in opts.provides)

    raises('the real class-options phase raises when run before the stats exist', opts, Stub())

    # The ordering mistake that would actually happen: this block moved above the HP phase. Every
    # prerequisite-seeding name is present, so only the write-after-write is missing.
    seeded = Stub()
    seeded.stats = {'str': 10}
    seeded.bab_total = 3
    seeded.casting_level_num = 0
    msg = raises('it raises when moved above the HP phase', opts, seeded)
    check('the error names Total_HP alone', 'Total_HP' in msg and 'stats' not in msg)


def test_returns_is_checked_on_exit():
    """`returns` is the third contract: outputs that are NOT character state ride a PhaseRecord,
    and an over-declared field has to fail on the way out exactly as `provides` does -- otherwise
    the record's whole advantage over a tuple (a typo raises here, not in the payload) is lost."""
    @phase(requires=[], provides=[], returns=['weapon_name'])
    def forgets_a_field(character):
        return PhaseRecord(armor_ac=3)

    msg = raises('a phase whose record lacks a declared field raises', forgets_a_field, Stub())
    check('the record error names the field', 'weapon_name' in msg)
    check('the record error names the phase', 'forgets_a_field' in msg)

    @phase(requires=[], provides=[], returns=['weapon_name'])
    def carries_it(character):
        return PhaseRecord(weapon_name='Longsword')

    check('a phase whose record carries the field passes',
          carries_it(Stub()).weapon_name == 'Longsword')

    # The failure mode a plain dict would NOT catch: reading a field nobody set. On a record this
    # is an AttributeError at the reader; in a dict it is a KeyError at best and a silent None at
    # worst, arriving in the payload as a key the two consuming repos read positionally.
    rec = PhaseRecord(weapon_name='Longsword')
    try:
        rec.weapon_nmae                                          # noqa: B018 - deliberate typo
        check('a mistyped record field raises at the reader', False)
    except AttributeError:
        check('a mistyped record field raises at the reader', True)


def test_gear_and_equipment_phase():
    """phase_gear_and_equipment -- the first phase whose outputs are mostly NOT character state.

    Its ordering hazard is the one the file already got wrong once and fixed by moving a call:
    item_chooser used to drain the purse before plan_enhancements reserved its share, so no
    character could afford an enhancement tier and enhancement_effects_dict was empty for every
    realistically funded NPC. That is now an ordering rule INSIDE the phase; what the contract
    guards is the purse existing at all, and the armour type the selection is limited against.

    It is also the phase that proves the record: eleven values cross out of it and every one is read
    only by the export, so none of them belongs on the character.
    """
    import main_test

    gear = main_test.phase_gear_and_equipment

    check('gear phase keeps requires small (ticket 05: 2-4 names)',
          2 <= len(gear.requires) <= 4)
    check('gear phase requires gold (every spender below draws the purse down)',
          'gold' in gear.requires)
    check('gear phase requires armor_type (list_selection limits on it)',
          'armor_type' in gear.requires)

    # What IS character state: the chosen kit, which later phases and the buff pass read.
    for name in ('armor_dict', 'weapon_dict', 'shield_dict', 'shield_flag', 'mind_blade'):
        check(f'gear phase provides {name} (real character state)', name in gear.provides)

    # What is NOT: eleven export-only outputs. On the character these would be eleven more
    # attributes on an object that already carries ~200.
    for name in ('weapon_name', 'equipment_list', 'equip_descrip', 'armor_ac', 'shield_ac',
                 'weapon_enhancement_chosen_list', 'armor_enhancement_chosen_list',
                 'shield_enhancement_chosen_list'):
        check(f'gear phase returns {name} on its record', name in gear.returns)
    check('nothing is declared both on the character and on the record',
          not (set(gear.provides) & set(gear.returns)))

    raises('the real gear phase raises when run before the purse is filled', gear, Stub())

    # The ordering mistake that would actually happen: the block moved above assign_gold, which
    # sits two lines from armor_chooser. Everything else is in place, so only `gold` is missing.
    armed = Stub()
    armed.armor_type = 'L'
    msg = raises('it raises when moved above assign_gold', gear, armed)
    check('the error names gold alone', 'gold' in msg and 'armor_type' not in msg)


def test_appearance_and_traits_phase():
    """phase_appearance_and_traits -- seven flavour rolls, none of them character state.

    Its hazard is invisible by construction: language_chooser is HANDED the skill ranks, so running
    this before the skills are spent does not raise, it just picks languages against an empty rank
    sheet. `skill_rank_budget` is the only attribute that can express that ordering, because the
    ranks themselves never reach the character -- which is exactly why the contract has to name it.
    """
    import main_test

    look = main_test.phase_appearance_and_traits
    prof = main_test.phase_professions_and_skills

    check('appearance phase requires skill_rank_budget (languages are chosen against the ranks)',
          'skill_rank_budget' in look.requires)
    check('...and the professions phase is what provides it, so the order is forced',
          'skill_rank_budget' in prof.provides)
    check('appearance phase requires chosen_race (appearance tables are keyed by race)',
          'chosen_race' in look.requires)

    # Every output is export-only, so the phase should put NOTHING on the character.
    check('appearance phase provides no character state (all seven outputs are export-only)',
          look.provides == ())
    for name in ('selected_traits', 'hero_points', 'hair_color', 'appearance', 'language_text'):
        check(f'appearance phase returns {name} on its record', name in look.returns)

    raises('the real appearance phase raises when run before the skills are spent',
           look, Stub(), {})

    raced = Stub()
    raced.chosen_race = 'Human'
    msg = raises('it raises when moved above the professions phase', look, raced, {})
    check('the error names skill_rank_budget alone',
          'skill_rank_budget' in msg and 'chosen_race' not in msg)


def test_class_bonus_feats_phase():
    """phase_class_bonus_feats -- the feats a class GRANTS, before any are chosen.

    The hazard here is a silent refund, and it is worth spelling out because it hides itself. The
    bloodline bonus list is drawn from `character.bloodline`; run this before the bloodline is
    resolved and the list comes back EMPTY -- at which point the phase's own refund converts every
    unfilled slot into an ordinary feat, so the character still ends up with the right feat COUNT
    and the wrong feats. A total that still adds up is the hardest kind of bug to notice.
    """
    import main_test

    grants = main_test.phase_class_bonus_feats

    check('class-bonus-feats requires bloodline (the bonus list is the bloodline\'s own)',
          'bloodline' in grants.requires)
    check('class-bonus-feats requires feat_amounts (it REFUNDS into the budget -- ticket 08)',
          'feat_amounts' in grants.requires)
    check('class-bonus-feats requires bab_total (the BAB>=1 free-feat seeding)',
          'bab_total' in grants.requires)
    check('requires stays small (ticket 05: 2-4 names)', 2 <= len(grants.requires) <= 4)

    for name in ('bloodline_feats', 'bloodline_feat_labels', 'ranger_style_feats',
                 'monk_bonus_feats'):
        check(f'class-bonus-feats returns {name} on its record', name in grants.returns)
    check('nothing is declared both on the character and on the record',
          not (set(grants.provides) & set(grants.returns)))

    raises('the real class-bonus-feats phase raises before the bloodline is resolved',
           grants, Stub())

    # The ordering mistake that would actually happen: this block moved above the try/except that
    # resolves character.bloodline, which sits ~30 lines earlier. Everything else is in place.
    armed = Stub()
    armed.bab_total = 6
    armed.feat_amounts = 9
    msg = raises('it raises when moved above the bloodline resolution', grants, armed)
    check('the error names bloodline alone', 'bloodline' in msg and 'bab_total' not in msg)


def test_bloodline_resolution_phase():
    """phase_bloodline_resolution -- collapse two optional tables into one name.

    Its `except (NameError, AttributeError)` is NOT the dead kind that was deleted from the school
    reads: bloodline_sorc/bloodline_rager only exist for bloodline classes, so the AttributeError arm
    is live for everyone else. That is exactly why both are declared -- otherwise a reordering falls
    into the handler and reads "N/A" instead of failing.
    """
    import main_test

    bl = main_test.phase_bloodline_resolution
    opts = main_test.phase_class_options
    grants = main_test.phase_class_bonus_feats

    check('bloodline phase provides bloodline', 'bloodline' in bl.provides)
    check('...which phase_class_bonus_feats requires, so the order is forced',
          'bloodline' in grants.requires)
    check('its requirements come from phase_class_options (the chain holds)',
          set(bl.requires) <= set(opts.provides))
    check('it returns nothing on a record (bloodline is character state)', bl.returns == ())

    raises('the real bloodline phase raises before the bloodline tables exist', bl, Stub())


def test_path_of_war_and_spheres_phase():
    """phase_path_of_war_and_spheres -- the block ticket 08 is about.

    Thirty-two values cross out and not one is character state, which is the single strongest
    argument for the record: as attributes they would be 32 more names on an object already carrying
    ~200; as a tuple, 32 positions nobody can read.
    """
    import main_test

    pw = main_test.phase_path_of_war_and_spheres

    check('PoW/Spheres requires profession_feats (the reservation subtracts them)',
          'profession_feats' in pw.requires)
    check('PoW/Spheres requires feat_amounts (it MUTATES the budget -- ticket 08)',
          'feat_amounts' in pw.requires)
    check('requires stays within the rule (2-4 names)', 2 <= len(pw.requires) <= 4)
    check('it returns a large record rather than character attributes', len(pw.returns) >= 30)
    check('nothing is declared in both homes', not (set(pw.provides) & set(pw.returns)))
    for name in ('mt_feats', 'style_feats', 'sphere_feats', 'martial_disciplines', 'manifesters'):
        check(f'PoW/Spheres returns {name} on its record', name in pw.returns)

    raises('the real PoW/Spheres phase raises when run before the professions phase', pw,
           Stub(), 'N', False)


def test_class_features_and_bonus_spells_phase():
    """phase_class_features_and_bonus_spells -- the seal, then the reads that depend on it."""
    import main_test

    cf = main_test.phase_class_features_and_bonus_spells

    for name in ('class_features', 'class_feature_levels', 'class_feature_owners',
                 'casting_level_str_foundry'):
        check(f'class-features phase returns {name}', name in cf.returns)
    check('class-features phase puts nothing on the character', cf.provides == ())

    # The conditionally-bound export string: seeded inside the phase so `returns` can check it.
    # Without the seed a non-low/high/mid caster leaves the name unbound and the export dies.
    raises('the real class-features phase raises before the class choices exist', cf, Stub(), 'mid')


def test_feat_phases():
    """The two feat phases, and the boundary between them.

    `character.feats` and the local `feats` are NOT the same list -- `separate_feats_func` splits the
    local five ways while the attribute keeps the merged one. That is the trap that would have
    shipped the wrong feats if the extraction had repointed by name, so the split is asserted here.
    """
    import main_test

    sel = main_test.phase_feat_selection
    tax = main_test.phase_feat_tax_and_swaps

    check('feat selection provides feats on the CHARACTER (choosers read it there)',
          'feats' in sel.provides)
    check('...and does NOT also carry feats on its record (one value, one home)',
          'feats' not in sel.returns)
    check('feat selection requires chooseable (class grants are seeded into it first)',
          'chooseable' in sel.requires)

    check('the feat-tax phase returns the five-way split',
          {'feats', 'story_feats', 'flaw_feats', 'flavor_feats', 'class_feats'} <= set(tax.returns))
    check('the feat-tax phase returns feat_budget', 'feat_budget' in tax.returns)
    check('the feat-tax phase only READS the budget -- every mutation is upstream now',
          'feat_amounts' in tax.requires and 'feat_amounts' not in tax.provides)
    check('nothing is declared in both homes', not (set(tax.provides) & set(tax.returns)))

    raises('the real feat-selection phase raises before the class grants are seeded',
           sel, Stub(), None, {}, 'Y', 0)


def main():
    for test in (test_requires_missing_raises,
                 test_falsy_requirement_counts_as_set,
                 test_provides_is_checked_on_exit,
                 test_returns_is_checked_on_exit,
                 test_sealing,
                 test_real_phases_declare_their_hazards,
                 test_alignment_and_level_phase,
                 test_hp_and_spellbooks_phase,
                 test_class_options_phase,
                 test_gear_and_equipment_phase,
                 test_appearance_and_traits_phase,
                 test_class_bonus_feats_phase,
                 test_bloodline_resolution_phase,
                 test_path_of_war_and_spheres_phase,
                 test_class_features_and_bonus_spells_phase,
                 test_feat_phases):
        print(f'{test.__name__}:')
        test()

    print()
    return REPORT.finish('phase contracts enforced')


if __name__ == '__main__':
    sys.exit(main())
