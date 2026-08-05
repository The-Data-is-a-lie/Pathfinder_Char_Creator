"""Standalone regression checks for the deterministic build-archetype scorer (run directly; this
repo has no pytest harness -- mirrors the CLI-smoke-test convention of Backend/main_test.py).

    C:\\Python310\\python.exe Backend/scripts/test_build_archetype.py

Covers: the 37-fixture classification matrix (incl. the flagship wizard-with-backup-crossbow
regression; every non-Generalist archetype of the generalized v3 roster has a proving fixture),
determinism, use_api parity when Ollama is unreachable, the never-raises guarantee on garbage
input, and mechanical sanity of Backend/json/build_archetypes.json against the engine's signal
vocabulary. Run `... test_build_archetype.py explain <fixture>` to dump a fixture's top-5
scores and live signals while tuning roster weights.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _harness import JSON_DIR, Report, read_json  # noqa: E402

from utils.class_func import backstory as _bs  # noqa: E402
from utils.class_func import build_archetype as ba  # noqa: E402

# The scorer must be identical with or without a reachable model: sever Ollama outright so
# use_api=True exercises the "unreachable" path deterministically.
_bs._try_ollama = lambda *a, **k: ''

REPORT = Report('test_build_archetype')

FEAT_BUCKETS = read_json(JSON_DIR / 'feat_buckets.json')


def mk(**kw):
    """A complete _build-shaped dict (see main_test.py) with fighter-ish defaults."""
    build = {
        'classes': ['fighter 8'], 'class_names': ['fighter'],
        'class_entries': [{'name': 'fighter', 'level': 8}], 'total_level': 8,
        'primary_class': 'fighter', 'bab_tier': 'H', 'main_stat': 'str',
        'stats': '16/12/14/10/10/10',
        'stat_dict': {'str': 16, 'dex': 12, 'con': 14, 'int': 10, 'wis': 10, 'cha': 10},
        'weapon': 'Longsword', 'weapon_category': 'One-Handed Melee', 'weapon_groups': 'Heavy Blades',
        'weapon_special': '', 'weapon_critical': '19-20/x2',
        'armor': 'Breastplate', 'armor_type': 'M', 'shield': '', 'shield_flag': False,
        'feats': [], 'feat_buckets': FEAT_BUCKETS, 'class_feature_names': [],
        'disciplines': [], 'stances': [], 'maneuvers': [], 'initiator_level': 0,
        'spheres': [], 'sphere_mana_pool': 0,
        'casting': [], 'spells': [], 'spell_levels': [],
        'companion': False,
    }
    build.update(kw)
    return build


FIXTURES = {
    'wizard_backup_crossbow': mk(
        classes=['wizard 15'], class_names=['wizard'],
        class_entries=[{'name': 'wizard', 'level': 15}], total_level=15, primary_class='wizard',
        bab_tier='L', main_stat='int',
        stat_dict={'str': 8, 'dex': 14, 'con': 12, 'int': 22, 'wis': 12, 'cha': 10},
        weapon='Heavy crossbow', weapon_category='Ranged', weapon_groups='Crossbows',
        weapon_critical='19-20/x2', armor='', armor_type=None,
        spell_levels=[8], casting=['wizard (spells up to level 8)'],
        spells=['Wall of Force', 'Dimensional Lock', 'Maze', 'Mind Blank', 'Black Tentacles']),
    'dex_rogue_leather_rapier': mk(
        classes=['rogue 10'], class_names=['rogue'],
        class_entries=[{'name': 'rogue', 'level': 10}], total_level=10, primary_class='rogue',
        bab_tier='M', main_stat='dex',
        stat_dict={'str': 10, 'dex': 20, 'con': 12, 'int': 14, 'wis': 10, 'cha': 12},
        weapon='Rapier', weapon_category='One-Handed Melee', weapon_groups='Light Blades',
        weapon_critical='18-20/x2', armor='Leather', armor_type='L',
        feats=['Weapon Finesse', 'Improved Feint', 'Two-Weapon Fighting'],
        class_feature_names=['Sneak Attack', 'Evasion', 'Uncanny Dodge']),
    'zen_archer_monk': mk(
        classes=['monk 8'], class_names=['monk'],
        class_entries=[{'name': 'monk', 'level': 8}], total_level=8, primary_class='monk',
        bab_tier='M', main_stat='wis',
        stat_dict={'str': 12, 'dex': 16, 'con': 12, 'int': 10, 'wis': 18, 'cha': 8},
        weapon='Composite longbow', weapon_category='Ranged', weapon_groups='Bows',
        weapon_critical='x3', armor='', armor_type=None,
        feats=['Point-Blank Shot', 'Precise Shot', 'Rapid Shot', 'Weapon Focus (longbow)']),
    'magus_gish': mk(
        classes=['magus 12'], class_names=['magus'],
        class_entries=[{'name': 'magus', 'level': 12}], total_level=12, primary_class='magus',
        bab_tier='M', main_stat='int',
        stat_dict={'str': 16, 'dex': 14, 'con': 14, 'int': 18, 'wis': 10, 'cha': 8},
        weapon='Scimitar', weapon_category='One-Handed Melee', weapon_groups='Heavy Blades',
        weapon_critical='18-20/x2', armor='Chain shirt', armor_type='L',
        spell_levels=[4], casting=['magus (spells up to level 4)'],
        spells=['Shocking Grasp', 'Frigid Touch', 'Haste', 'Displacement'],
        feats=['Weapon Focus (scimitar)', 'Improved Critical (scimitar)']),
    'reach_cleric_polearm': mk(
        classes=['cleric 9'], class_names=['cleric'],
        class_entries=[{'name': 'cleric', 'level': 9}], total_level=9, primary_class='cleric',
        bab_tier='M', main_stat='wis',
        stat_dict={'str': 16, 'dex': 10, 'con': 14, 'int': 10, 'wis': 18, 'cha': 12},
        weapon='Glaive', weapon_category='Two-Handed Melee', weapon_groups='Polearms',
        weapon_special='reach', weapon_critical='x3', armor='Full plate', armor_type='H',
        spell_levels=[5], casting=['cleric (spells up to level 5)'],
        spells=['Righteous Might', 'Divine Favor', 'Bless', 'Hold Person'],
        feats=['Combat Reflexes', 'Stand Still', 'Power Attack']),
    'summoner_eidolon': mk(
        classes=['summoner 10'], class_names=['summoner'],
        class_entries=[{'name': 'summoner', 'level': 10}], total_level=10, primary_class='summoner',
        bab_tier='L', main_stat='cha',
        stat_dict={'str': 8, 'dex': 14, 'con': 14, 'int': 12, 'wis': 10, 'cha': 20},
        weapon='Dagger', weapon_category='Light Melee', weapon_groups='Light Blades',
        armor='Leather', armor_type='L',
        spell_levels=[4], casting=['summoner (spells up to level 4)'],
        spells=['Summon Monster V', 'Haste', 'Evolution Surge'],
        feats=['Augment Summoning', 'Spell Focus (conjuration)']),
    'pow_warder_tank': mk(
        classes=['fighter 6', 'warder 6'], class_names=['fighter', 'warder'],
        class_entries=[{'name': 'fighter', 'level': 6}, {'name': 'warder', 'level': 6}],
        total_level=12, primary_class='fighter', bab_tier='H', main_stat='str',
        stat_dict={'str': 18, 'dex': 10, 'con': 16, 'int': 13, 'wis': 10, 'cha': 8},
        weapon='Longsword', armor='Full plate', armor_type='H', shield='Heavy steel shield',
        shield_flag=True, disciplines=['Iron Tortoise', 'Golden Lion'], initiator_level=9,
        feats=['Combat Reflexes', 'Shield Focus', 'Toughness']),
    'sphere_blaster': mk(
        classes=['incanter 10'], class_names=['incanter'],
        class_entries=[{'name': 'incanter', 'level': 10}], total_level=10,
        primary_class='incanter', bab_tier='L', main_stat='int',
        stat_dict={'str': 8, 'dex': 14, 'con': 12, 'int': 20, 'wis': 12, 'cha': 10},
        weapon='', weapon_category='', weapon_groups='', weapon_critical='',
        armor='', armor_type=None,
        spheres=['destruction', 'war', 'protection'], sphere_mana_pool=12),
    'switch_hitter_ranger': mk(
        classes=['ranger 12'], class_names=['ranger'],
        class_entries=[{'name': 'ranger', 'level': 12}], total_level=12, primary_class='ranger',
        bab_tier='H', main_stat='str',
        stat_dict={'str': 18, 'dex': 16, 'con': 14, 'int': 10, 'wis': 12, 'cha': 8},
        weapon='Composite longbow', weapon_category='Ranged', weapon_groups='Bows',
        weapon_critical='x3', armor='Chain shirt', armor_type='L',
        feats=['Point-Blank Shot', 'Rapid Shot', 'Manyshot', 'Power Attack', 'Cleave',
               'Quick Draw']),
    'beastmaster_druid': mk(
        classes=['druid 11'], class_names=['druid'],
        class_entries=[{'name': 'druid', 'level': 11}], total_level=11, primary_class='druid',
        bab_tier='M', main_stat='wis',
        stat_dict={'str': 14, 'dex': 12, 'con': 14, 'int': 10, 'wis': 19, 'cha': 10},
        weapon='Scimitar', weapon_category='One-Handed Melee', weapon_groups='Heavy Blades',
        weapon_critical='18-20/x2', armor='Hide', armor_type='M', companion=True,
        spell_levels=[6], casting=['druid (spells up to level 6)'],
        spells=["Summon Nature's Ally VI", 'Barkskin', 'Cure Serious Wounds'],
        feats=['Boon Companion', 'Power Attack']),
    'sword_and_board_fighter': mk(
        weapon='Longsword', armor='Full plate', armor_type='H',
        shield='Heavy steel shield', shield_flag=True,
        feats=['Weapon Focus (longsword)', 'Power Attack']),
    'barbarian_two_hander': mk(
        classes=['barbarian 12'], class_names=['barbarian'],
        class_entries=[{'name': 'barbarian', 'level': 12}], total_level=12,
        primary_class='barbarian', bab_tier='H', main_stat='str',
        stat_dict={'str': 20, 'dex': 12, 'con': 18, 'int': 8, 'wis': 10, 'cha': 8},
        weapon='Greataxe', weapon_category='Two-Handed Melee', weapon_groups='Axes',
        weapon_critical='x3', armor='Breastplate', armor_type='M',
        feats=['Power Attack', 'Cleave', 'Raging Vitality'],
        class_feature_names=['Rage', 'Rage Power', 'Damage Reduction']),
    'gunslinger_musket': mk(
        classes=['gunslinger 9'], class_names=['gunslinger'],
        class_entries=[{'name': 'gunslinger', 'level': 9}], total_level=9,
        primary_class='gunslinger', bab_tier='H', main_stat='dex',
        stat_dict={'str': 10, 'dex': 20, 'con': 12, 'int': 10, 'wis': 14, 'cha': 8},
        weapon='Musket', weapon_category='Ranged', weapon_groups='Firearms',
        weapon_critical='x4', armor='Leather', armor_type='L',
        feats=['Rapid Reload', 'Deadly Aim', 'Point-Blank Shot']),
    'mounted_cavalier': mk(
        classes=['cavalier 10'], class_names=['cavalier'],
        class_entries=[{'name': 'cavalier', 'level': 10}], total_level=10,
        primary_class='cavalier', bab_tier='H', main_stat='str',
        stat_dict={'str': 18, 'dex': 12, 'con': 14, 'int': 10, 'wis': 10, 'cha': 14},
        weapon='Lance', weapon_category='Two-Handed Melee', weapon_groups='Polearms',
        weapon_special='reach', weapon_critical='x3', armor='Full plate', armor_type='H',
        shield='Heavy steel shield', shield_flag=True,
        feats=['Mounted Combat', 'Ride-By Attack', 'Spirited Charge', 'Power Attack']),
    'bard_support': mk(
        classes=['bard 11'], class_names=['bard'],
        class_entries=[{'name': 'bard', 'level': 11}], total_level=11, primary_class='bard',
        bab_tier='M', main_stat='cha',
        stat_dict={'str': 10, 'dex': 14, 'con': 12, 'int': 14, 'wis': 10, 'cha': 18},
        weapon='Rapier', weapon_category='One-Handed Melee', weapon_groups='Light Blades',
        weapon_critical='18-20/x2', armor='Chain shirt', armor_type='L',
        spell_levels=[4], casting=['bard (spells up to level 4)'],
        spells=['Haste', 'Good Hope', 'Heroism', 'Glitterdust'],
        feats=['Lingering Performance', 'Flagbearer']),
    'witch_debuffer': mk(
        classes=['witch 12'], class_names=['witch'],
        class_entries=[{'name': 'witch', 'level': 12}], total_level=12, primary_class='witch',
        bab_tier='L', main_stat='int',
        stat_dict={'str': 8, 'dex': 14, 'con': 12, 'int': 20, 'wis': 13, 'cha': 10},
        weapon='Dagger', weapon_category='Light Melee', weapon_groups='Light Blades',
        armor='', armor_type=None,
        spell_levels=[6], casting=['witch (spells up to level 6)'],
        spells=['Hold Monster', 'Bestow Curse', 'Confusion', 'Sleep'],
        class_feature_names=['Hex', 'Major Hex', 'Evil Eye']),
    'kineticist_blaster': mk(
        classes=['kineticist 10'], class_names=['kineticist'],
        class_entries=[{'name': 'kineticist', 'level': 10}], total_level=10,
        primary_class='kineticist', bab_tier='M', main_stat='con',
        stat_dict={'str': 10, 'dex': 16, 'con': 20, 'int': 10, 'wis': 12, 'cha': 8},
        weapon='', weapon_category='', weapon_groups='', weapon_critical='',
        armor='Leather', armor_type='L',
        class_feature_names=['Kinetic Blast', 'Infusion', 'Burn']),
    'oracle_healer': mk(
        classes=['oracle 13'], class_names=['oracle'],
        class_entries=[{'name': 'oracle', 'level': 13}], total_level=13, primary_class='oracle',
        bab_tier='M', main_stat='cha',
        stat_dict={'str': 10, 'dex': 10, 'con': 14, 'int': 10, 'wis': 14, 'cha': 20},
        weapon='Morningstar', weapon_category='One-Handed Melee', weapon_groups='Hammers',
        armor='Breastplate', armor_type='M',
        spell_levels=[6], casting=['oracle (spells up to level 6)'],
        spells=['Heal', 'Breath of Life', 'Cure Critical Wounds', 'Restoration'],
        feats=['Selective Channeling', 'Extra Channel']),
    'stalker_ambusher': mk(
        classes=['stalker 9'], class_names=['stalker'],
        class_entries=[{'name': 'stalker', 'level': 9}], total_level=9, primary_class='stalker',
        bab_tier='M', main_stat='dex',
        stat_dict={'str': 12, 'dex': 18, 'con': 12, 'int': 10, 'wis': 16, 'cha': 8},
        weapon='Kukri', weapon_category='Light Melee', weapon_groups='Light Blades',
        weapon_critical='18-20/x2', armor='Leather', armor_type='L',
        disciplines=['Veiled Moon', 'Steel Serpent'], initiator_level=9,
        feats=['Two-Weapon Fighting', 'Weapon Finesse']),
    'warrior_mook': mk(
        classes=['warrior 2'], class_names=['warrior'],
        class_entries=[{'name': 'warrior', 'level': 2}], total_level=2, primary_class='warrior',
        bab_tier='H', main_stat='str',
        stat_dict={'str': 15, 'dex': 11, 'con': 12, 'int': 9, 'wis': 10, 'cha': 8},
        weapon='Spear', weapon_category='Two-Handed Melee', weapon_groups='Spears',
        weapon_special='brace', weapon_critical='x3', armor='Leather', armor_type='L'),
    # --- v3 additions: every non-Generalist archetype gets a proving fixture ---
    'warpriest_self_buffer': mk(
        classes=['warpriest 9'], class_names=['warpriest'],
        class_entries=[{'name': 'warpriest', 'level': 9}], total_level=9,
        primary_class='warpriest', bab_tier='M', main_stat='wis',
        stat_dict={'str': 16, 'dex': 10, 'con': 14, 'int': 10, 'wis': 17, 'cha': 12},
        weapon='Warhammer', weapon_category='One-Handed Melee', weapon_groups='Hammers',
        weapon_critical='x3', armor='Scale mail', armor_type='M',
        spell_levels=[3], casting=['warpriest (spells up to level 3)'],
        spells=['Divine Favor', 'Divine Power', 'Magic Vestment', 'Bless'],
        feats=['Power Attack', 'Weapon Focus (warhammer)']),
    'warlord_team_buffer': mk(
        classes=['warlord 8'], class_names=['warlord'],
        class_entries=[{'name': 'warlord', 'level': 8}], total_level=8, primary_class='warlord',
        bab_tier='H', main_stat='cha',
        stat_dict={'str': 16, 'dex': 12, 'con': 14, 'int': 10, 'wis': 8, 'cha': 16},
        weapon='Longsword', armor='Breastplate', armor_type='M',
        disciplines=['Golden Lion', 'Scarlet Throne'], initiator_level=8,
        feats=['Power Attack', 'Combat Reflexes']),
    'reach_fighter_keepaway': mk(
        classes=['fighter 10'], class_names=['fighter'],
        class_entries=[{'name': 'fighter', 'level': 10}], total_level=10, primary_class='fighter',
        bab_tier='H', main_stat='str',
        stat_dict={'str': 18, 'dex': 14, 'con': 14, 'int': 12, 'wis': 10, 'cha': 8},
        weapon='Guisarme', weapon_category='Two-Handed Melee', weapon_groups='Polearms',
        weapon_special='reach', weapon_critical='x3', armor='Breastplate', armor_type='M',
        feats=['Combat Reflexes', 'Improved Trip', 'Greater Trip', 'Stand Still',
               'Power Attack']),
    'unarmed_grappler': mk(
        classes=['fighter 9'], class_names=['fighter'],
        class_entries=[{'name': 'fighter', 'level': 9}], total_level=9, primary_class='fighter',
        bab_tier='H', main_stat='str',
        stat_dict={'str': 18, 'dex': 12, 'con': 16, 'int': 10, 'wis': 12, 'cha': 8},
        weapon='Unarmed strike', weapon_category='Light Melee', weapon_groups='Monk|Natural',
        weapon_critical='x2', armor='Chain shirt', armor_type='L',
        feats=['Improved Grapple', 'Greater Grapple', 'Rapid Grappler',
               'Improved Unarmed Strike', 'Stunning Pin']),
    'charger_barbarian': mk(
        classes=['barbarian 10'], class_names=['barbarian'],
        class_entries=[{'name': 'barbarian', 'level': 10}], total_level=10,
        primary_class='barbarian', bab_tier='H', main_stat='str',
        stat_dict={'str': 20, 'dex': 14, 'con': 16, 'int': 8, 'wis': 10, 'cha': 8},
        weapon='Greatsword', weapon_category='Two-Handed Melee', weapon_groups='Heavy Blades',
        weapon_critical='19-20/x2', armor='Studded leather', armor_type='L',
        feats=['Power Attack', 'Dodge', 'Raging Vitality'],
        class_feature_names=['Rage', 'Fast Movement', 'Rage Power']),
    'mounted_horse_archer': mk(
        classes=['ranger 9'], class_names=['ranger'],
        class_entries=[{'name': 'ranger', 'level': 9}], total_level=9, primary_class='ranger',
        bab_tier='H', main_stat='dex',
        stat_dict={'str': 12, 'dex': 18, 'con': 13, 'int': 10, 'wis': 14, 'cha': 8},
        weapon='Composite shortbow', weapon_category='Ranged', weapon_groups='Bows',
        weapon_critical='x3', armor='Studded leather', armor_type='L', companion=True,
        feats=['Mounted Combat', 'Mounted Archery', 'Point-Blank Shot', 'Rapid Shot']),
    'alchemist_bomber': mk(
        classes=['alchemist 9'], class_names=['alchemist'],
        class_entries=[{'name': 'alchemist', 'level': 9}], total_level=9,
        primary_class='alchemist', bab_tier='M', main_stat='int',
        stat_dict={'str': 10, 'dex': 16, 'con': 12, 'int': 18, 'wis': 12, 'cha': 8},
        weapon='Light crossbow', weapon_category='Ranged', weapon_groups='Crossbows',
        weapon_critical='19-20/x2', armor='Leather', armor_type='L',
        spell_levels=[3], casting=['alchemist (extracts up to level 3)'],
        spells=['Shield', 'Cure Light Wounds', 'Haste'],
        feats=['Point-Blank Shot', 'Precise Shot', 'Rapid Shot', 'Throw Anything']),
    'sorcerer_blaster': mk(
        classes=['sorcerer 8'], class_names=['sorcerer'],
        class_entries=[{'name': 'sorcerer', 'level': 8}], total_level=8, primary_class='sorcerer',
        bab_tier='L', main_stat='cha',
        stat_dict={'str': 8, 'dex': 14, 'con': 14, 'int': 12, 'wis': 10, 'cha': 18},
        weapon='Dagger', weapon_category='Light Melee', weapon_groups='Light Blades',
        armor='', armor_type=None,
        spell_levels=[4], casting=['sorcerer (spells up to level 4)'],
        spells=['Fireball', 'Scorching Ray', 'Lightning Bolt', 'Haste'],
        feats=['Spell Focus (evocation)', 'Empower Spell', 'Spell Penetration']),
    'druid_shapeshifter': mk(
        classes=['druid 10'], class_names=['druid'],
        class_entries=[{'name': 'druid', 'level': 10}], total_level=10, primary_class='druid',
        bab_tier='M', main_stat='wis',
        stat_dict={'str': 14, 'dex': 12, 'con': 14, 'int': 10, 'wis': 18, 'cha': 10},
        weapon='', weapon_category='', weapon_groups='', weapon_critical='',
        armor='Hide', armor_type='M',
        spell_levels=[5], casting=['druid (spells up to level 5)'],
        spells=['Barkskin', 'Strong Jaw', "Summon Nature's Ally IV"],
        class_feature_names=['Wild Shape', 'Wild Empathy']),
    'adept_hedge_mage': mk(
        classes=['adept 5'], class_names=['adept'],
        class_entries=[{'name': 'adept', 'level': 5}], total_level=5, primary_class='adept',
        bab_tier='L', main_stat='wis',
        stat_dict={'str': 10, 'dex': 11, 'con': 12, 'int': 12, 'wis': 14, 'cha': 10},
        weapon='Dagger', weapon_category='Light Melee', weapon_groups='Light Blades',
        armor='', armor_type=None,
        spell_levels=[2], casting=['adept (spells up to level 2)'],
        spells=['Cure Light Wounds', 'Sleep', 'Burning Hands']),
    'archer_fighter': mk(
        classes=['fighter 9'], class_names=['fighter'],
        class_entries=[{'name': 'fighter', 'level': 9}], total_level=9, primary_class='fighter',
        bab_tier='H', main_stat='dex',
        stat_dict={'str': 14, 'dex': 18, 'con': 14, 'int': 10, 'wis': 12, 'cha': 8},
        weapon='Composite longbow', weapon_category='Ranged', weapon_groups='Bows',
        weapon_critical='x3', armor='Studded leather', armor_type='L',
        feats=['Point-Blank Shot', 'Precise Shot', 'Rapid Shot', 'Manyshot', 'Deadly Aim']),
    'dual_wield_ranger': mk(
        classes=['ranger 10'], class_names=['ranger'],
        class_entries=[{'name': 'ranger', 'level': 10}], total_level=10, primary_class='ranger',
        bab_tier='H', main_stat='str',
        stat_dict={'str': 16, 'dex': 15, 'con': 14, 'int': 10, 'wis': 12, 'cha': 8},
        weapon='Kukri', weapon_category='Light Melee', weapon_groups='Light Blades',
        weapon_critical='18-20/x2', armor='Chain shirt', armor_type='L',
        feats=['Two-Weapon Fighting', 'Improved Two-Weapon Fighting', 'Double Slice',
               'Power Attack']),
    'flurry_monk': mk(
        classes=['monk 9'], class_names=['monk'],
        class_entries=[{'name': 'monk', 'level': 9}], total_level=9, primary_class='monk',
        bab_tier='M', main_stat='wis',
        stat_dict={'str': 16, 'dex': 14, 'con': 13, 'int': 10, 'wis': 16, 'cha': 8},
        weapon='Unarmed strike', weapon_category='Light Melee', weapon_groups='Monk|Natural',
        weapon_critical='x2', armor='', armor_type=None,
        feats=['Improved Unarmed Strike', 'Stunning Fist', 'Power Attack', 'Dodge']),
    'hp_tank_barbarian': mk(
        classes=['barbarian 11'], class_names=['barbarian'],
        class_entries=[{'name': 'barbarian', 'level': 11}], total_level=11,
        primary_class='barbarian', bab_tier='H', main_stat='str',
        stat_dict={'str': 16, 'dex': 12, 'con': 20, 'int': 8, 'wis': 10, 'cha': 8},
        weapon='Warhammer', weapon_category='One-Handed Melee', weapon_groups='Hammers',
        weapon_critical='x3', armor='Breastplate', armor_type='M',
        shield='Heavy steel shield', shield_flag=True,
        feats=['Toughness', 'Endurance', 'Raging Vitality', 'Power Attack'],
        class_feature_names=['Rage', 'Damage Reduction']),
    'guard_man_at_arms': mk(
        classes=['warrior 3'], class_names=['warrior'],
        class_entries=[{'name': 'warrior', 'level': 3}], total_level=3, primary_class='warrior',
        bab_tier='H', main_stat='str',
        stat_dict={'str': 15, 'dex': 11, 'con': 12, 'int': 9, 'wis': 10, 'cha': 8},
        weapon='Longsword', weapon_category='One-Handed Melee', weapon_groups='Heavy Blades',
        weapon_critical='19-20/x2', armor='Chain shirt', armor_type='L'),
    'conjurer_summoner': mk(
        classes=['wizard 14'], class_names=['wizard'],
        class_entries=[{'name': 'wizard', 'level': 14}], total_level=14, primary_class='wizard',
        bab_tier='L', main_stat='int',
        stat_dict={'str': 8, 'dex': 14, 'con': 12, 'int': 20, 'wis': 12, 'cha': 10},
        weapon='Dagger', weapon_category='Light Melee', weapon_groups='Light Blades',
        armor='', armor_type=None,
        spell_levels=[7], casting=['wizard (spells up to level 7)'],
        spells=['Summon Monster VII', 'Summon Monster VI', 'Summon Monster V', 'Haste'],
        feats=['Augment Summoning', 'Spell Focus (conjuration)', 'Superior Summoning']),
    'harrier_duelist': mk(
        classes=['fighter 8'], class_names=['fighter'],
        class_entries=[{'name': 'fighter', 'level': 8}], total_level=8, primary_class='fighter',
        bab_tier='H', main_stat='dex',
        stat_dict={'str': 12, 'dex': 18, 'con': 13, 'int': 10, 'wis': 12, 'cha': 10},
        weapon='Rapier', weapon_category='One-Handed Melee', weapon_groups='Light Blades',
        weapon_critical='18-20/x2', armor='Leather', armor_type='L',
        feats=['Weapon Finesse', 'Dodge', 'Mobility', 'Spring Attack', 'Wind Stance']),
}

# Roster-independent guards: substrings that must NOT appear in the winning label (lowercased).
# The flagship regression: a full caster's backup ranged weapon must never read as a shooter.
FORBID = {
    'wizard_backup_crossbow': ('archer', 'sniper', 'sharpshooter', 'gunslinger', 'shooter'),
    'witch_debuffer': ('archer', 'sniper', 'duelist', 'brawler'),
    'oracle_healer': ('bruiser', 'archer', 'duelist'),
    'summoner_eidolon': ('archer', 'duelist', 'skirmisher'),
    'zen_archer_monk': ('brawler', 'grappler', 'wrestl'),
    'beastmaster_druid': ('shapeshift', 'wildshap'),
    'dex_rogue_leather_rapier': ('archer', 'tank'),
    'warlord_team_buffer': ('man-at-arms', 'generalist'),
    'alchemist_bomber': ('archer', 'hedge'),
    'charger_barbarian': ('man-at-arms',),
    'guard_man_at_arms': ('tank', 'bruiser'),
}

# EXPECTED winning labels per fixture -- FINALIZED against the generalized v3 roster
# (Backend/json/build_archetypes.json). A tuple means "any of these is a pass".
EXPECT = {
    'wizard_backup_crossbow': 'Magic Battlefield Controller',
    'dex_rogue_leather_rapier': 'Trickster',
    'zen_archer_monk': 'Zen Archer',
    'magus_gish': 'Spellblade',
    'reach_cleric_polearm': 'Area Denier',
    'summoner_eidolon': 'Eidolon Master',
    'pow_warder_tank': 'AC Tank',
    'sphere_blaster': 'Blaster',
    'switch_hitter_ranger': 'Switch Hitter',
    'beastmaster_druid': 'Beastmaster',
    'sword_and_board_fighter': ('AC Tank', 'Man-at-Arms'),
    'barbarian_two_hander': 'Bruiser',
    'gunslinger_musket': 'Sharpshooter',
    'mounted_cavalier': 'Mounted Lancer',
    'bard_support': 'Team Buffer',
    'witch_debuffer': 'Debuffer',
    'kineticist_blaster': 'Kinetic Blaster',
    'oracle_healer': 'Healer',
    'stalker_ambusher': 'Trickster',
    'warrior_mook': ('Bruiser', 'Man-at-Arms'),
    'warpriest_self_buffer': 'Self Buffer',
    'warlord_team_buffer': 'Team Buffer',
    'reach_fighter_keepaway': 'Keep Away Fighter',
    'unarmed_grappler': 'Martial Battlefield Controller',
    'charger_barbarian': 'Charger',
    'mounted_horse_archer': 'Mounted Archer',
    'alchemist_bomber': 'Mad Bomber',
    'sorcerer_blaster': 'Blaster',
    'druid_shapeshifter': 'Shapeshifter',
    'adept_hedge_mage': 'Hedge Mage',
    'archer_fighter': 'Archer',
    'dual_wield_ranger': 'Dual Wielder',
    'flurry_monk': 'Brawler',
    'hp_tank_barbarian': 'HP Tank',
    'guard_man_at_arms': 'Man-at-Arms',
    'conjurer_summoner': 'Summoner',
    'harrier_duelist': 'Harrier',
}


def _classify(build):
    return ba.choose_build_archetype(build, use_api=False)


def test_fixture_matrix():
    for name, build in FIXTURES.items():
        res = _classify(build)
        # Guard: an empty label is nonsensical to keep classifying against -- skip straight to the
        # next fixture rather than let `.lower()` and the FORBID/EXPECT checks below run on it.
        if not REPORT.check(res.label, f'{name}: empty label'):
            continue
        label_l = res.label.lower()
        for bad in FORBID.get(name, ()):
            REPORT.check(bad not in label_l,
                         f'{name}: won forbidden label {res.label!r} (contenders {res.contenders})')
        if name in EXPECT:
            want = EXPECT[name] if isinstance(EXPECT[name], tuple) else (EXPECT[name],)
            REPORT.check(res.label in want,
                         f'{name}: got {res.label!r}, want one of {want} (contenders {res.contenders})')
        REPORT.check('generalist' != label_l or name == 'garbage',
                     f'{name}: fell through to Generalist (contenders {res.contenders})')


def test_determinism_and_api_parity():
    for name, build in FIXTURES.items():
        a, b = _classify(build), _classify(build)
        REPORT.check(a == b, f'{name}: non-deterministic')
        c = ba.choose_build_archetype(build, use_api=True)   # Ollama severed above -> must match
        REPORT.check(a.label == c.label, f'{name}: use_api changed the answer with no model reachable')


def test_never_raises():
    horrors = [{}, {'feats': None, 'classes': None}, {'stat_dict': 'not a dict'},
               {'spell_levels': ['x', None]}, {'class_entries': [{}]},
               {'weapon': 42, 'feat_buckets': []}, {'spheres': 123}]
    for h in horrors:
        res = ba.choose_build_archetype(h, use_api=True)
        REPORT.check(res.label, f'garbage {h!r}: empty label')


def test_roster_mechanics():
    roster = ba._load_roster()
    entries = roster['archetypes']
    REPORT.check(25 <= len(entries) <= 40, f'roster size {len(entries)} outside 25-40')
    vocab = set(ba._signals(mk(spheres=['destruction'], disciplines=['Iron Tortoise'],
                               spell_levels=[4], initiator_level=4, companion=True)))
    ranks, catch_alls = [], []
    for label, e in entries.items():
        used = set(e.get('signals', {})) | {g['signal'] for k in
                                            ('requires_any', 'requires_all', 'vetoes')
                                            for g in (e.get(k) or [])}
        unknown = used - vocab
        REPORT.check(not unknown, f'{label}: unknown signals {sorted(unknown)}')
        REPORT.check(e.get('tactics'), f'{label}: missing tactics')
        REPORT.check(e.get('family') in roster['families'], f'{label}: bad family')
        REPORT.check(e.get('tactical_pattern') in roster['tactical_patterns'], f'{label}: bad pattern')
        ranks.append(e.get('tie_break_rank'))
        if not (e.get('requires_any') or e.get('requires_all')):
            catch_alls.append(label)
    REPORT.check(len(ranks) == len(set(ranks)), 'tie_break_rank values not unique')
    REPORT.check(len(catch_alls) == 1, f'expected exactly one catch-all, got {catch_alls}')


def main():
    if len(sys.argv) > 2 and sys.argv[1] == 'explain':
        top, sig = ba.explain_build_archetype(FIXTURES[sys.argv[2]])
        print('signals:', json.dumps(sig, indent=1))
        for label, score, parts in top:
            print(f'{score:6.3f}  {label}  {parts}')
        return 0
    for fn in (test_roster_mechanics, test_fixture_matrix,
               test_determinism_and_api_parity, test_never_raises):
        fn()
        print(f'{fn.__name__}: done')
    print('--- classification matrix ---')
    for name, build in FIXTURES.items():
        res = _classify(build)
        print(f'{name:28s} -> {res.label:24s} [{res.family} / {res.pattern}] '
              f'{res.confidence} gap={res.gap}')
    return REPORT.finish(f'{REPORT.checks} checks', max_errors=25)


if __name__ == '__main__':
    sys.exit(main())
