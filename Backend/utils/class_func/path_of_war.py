"""Path of War (Dreamscarred Press) generation.

Two branches share one selection engine:
  - PoW initiator classes (data.path_of_war_class): SPECIALIZE in randint(2,3) of the class's
    disciplines (select_disciplines parses the class "Maneuvers" entry); counts from
    path_of_war_maneuvers_known.json at class level; initiator level = class level. Initiators
    also take 1..len(specialized) STYLE FEAT CHAINS from the Metzofitz catalogue (base feat
    consumes a normal feat slot like Martial Training; both followers always bundle free).
  - Everyone else may roll "martial paths" (campaign house rule): BAB L -> 0-1 disciplines,
    M/H -> 0-2, +1 to both bounds at level 20+. Access rides the Martial Training I-VI feat
    chain taken as deep as bab_total allows (I needs BAB +3, III +7, V +11; II/IV/VI arrive
    free via the feat-tax pairs in feat_tax.json). Counts come from
    martial_training_progression.json at that depth; initiator level = level // 2.

Maneuver/stance names are drawn from Martial_Disciplines.json restricted to the chosen
disciplines and the max maneuver level (min(ceil(IL/2), 9), MT users further capped by chain
depth). Selection is PREREQUISITE-LEGAL: each maneuver's "Prerequisites" count (e.g. "Two Iron
Tortoise maneuvers") must be covered by already-picked maneuvers+stances of that discipline
(stances count as maneuvers known, per PoW), with the usual higher-level weighting. Readied =
the highest-level chosen maneuvers. There are NO ability-modifier bonuses anywhere in this
subsystem -- counts mirror the spells known / spells per day concept straight from the tables.
"""
import random
import re
from math import ceil
from urllib.parse import unquote

import pandas as pd

from utils import data
from utils.class_func.feats import grab_and_clean_feats
from utils.class_func.path_of_war_funcs import select_disciplines
from utils.class_func.skill_ranks import final_ability_score

# Paid Martial Training picks by chain depth (the even tiers are feat-tax freebies).
_MT_FEATS = ["Martial Training I", "Martial Training II", "Martial Training III",
             "Martial Training IV", "Martial Training V", "Martial Training VI"]
_MT_PAID = ["Martial Training I", "Martial Training III", "Martial Training V"]
_MT_FREE = ["Martial Training II", "Martial Training IV", "Martial Training VI"]

_KIND_RE = re.compile(r'\b(strike|boost|counter|stance)\b', re.IGNORECASE)
_LEVEL_RE = re.compile(r'level\s*:?\s*(\d+)', re.IGNORECASE)
# Maneuver prerequisite counts: "Two Iron Tortoise maneuvers", ": 3 Unquiet Grave strikes", ...
# "Thee" is a recurring source typo for Three. Every prereq string in the scrape names the
# maneuver's OWN discipline, so only the count needs parsing.
_PREREQ_NUM_RE = re.compile(r'\b(one|two|three|thee|four|five|\d+)\b', re.IGNORECASE)
_WORD_NUMS = {'one': 1, 'two': 2, 'three': 3, 'thee': 3, 'four': 4, 'five': 5}


def randomize_path_of_war_num(character):
    '''How many martial disciplines ("paths") a NON-initiator character picks up. Initiator
    classes return 0 (their disciplines come from the class). House rule: BAB L -> 0-1,
    M/H -> 0-2; at level 20+ both bounds gain +1. A character whose bab_total can't reach
    Martial Training I (BAB +3) has no way into the system -> forced 0.'''
    if character.c_class in data.path_of_war_class:
        character.path_of_war_paths = 0
        return 0
    low, high = (0, 1) if character.bab == 'L' else (0, 2)
    if character.level >= 20:
        low, high = low + 1, high + 1
    n = random.randint(low, high)
    if martial_training_depth(character) == 0:
        n = 0
    character.path_of_war_paths = n
    return n


def martial_training_depth(character):
    '''Martial Training chain depth (0/2/4/6) the character qualifies for, by bab_total:
    MT I at BAB +3, MT III at +7, MT V at +11 (each paid feat tax-grants its partner, so
    depth comes in pairs). The free partners' own +5/+9/+13 gates are waived, consistent
    with the tax engine's _TAX_EXTRA_FILTER.'''
    bab = getattr(character, 'bab_total', 0) or 0
    if bab >= 11:
        return 6
    if bab >= 7:
        return 4
    if bab >= 3:
        return 2
    return 0


def initiation_stat(character):
    '''Initiating ability for the FoundryVTT side ("int"/"wis"/"cha"): arg-max of the FINAL
    mental scores (base + inherents + level-ups) -- the same calculation that drives the
    homebrew skill-rank scaling (skill_ranks.highest_mental_mod). max() keeps the first
    maximum, so ties break int > wis > cha, matching the Foundry module's mental-buff pick.'''
    return max(('int', 'wis', 'cha'), key=lambda s: final_ability_score(character, s))


def choose_path_of_war_attr(character):
    '''Orchestrates discipline choice + prereq-legal maneuver/stance selection + (initiators)
    style feat chains for both branches; returns the export bundle. Empty/zero defaults when
    the character has no paths.'''
    bundle = {
        'martial_disciplines': [], 'initiator_level': 0,
        'maneuvers_known_list': [], 'maneuvers_readied_list': [],
        'maneuvers_choose_from': [], 'maneuvers_readied_names': [],
        'stances_chosen': [], 'mt_feats': [], 'maneuvers_desc_dict': {},
        'style_feats': [], 'style_feat_tax': {}, 'mt_feat_tax': {},
        'homebrew_feat_desc_dict': {},
        # Exported for every character (even no-PoW): pf1-pow's initiating ability.
        'initiation_stat': initiation_stat(character),
    }
    # Initiators: one shared selection over the class's specialized disciplines (the class table
    # gives the counts). Non-initiators: ONE Martial Training chain PER rolled discipline, each
    # drawing only from its own discipline (built by _build_martial_training, which returns the
    # already-aggregated maneuver/stance/readied lists + the discipline-labeled feats).
    if character.c_class in data.path_of_war_class:
        counts = _initiator_counts(character)
        if counts is None:
            return bundle
        known_n, readied_n, stances_n, max_lvl, disciplines, _unused_mt, il = counts
        pool = _maneuver_pool(character, disciplines, max_lvl)
        chosen, chosen_stances = _constrained_pick(pool, known_n, stances_n)
        readied = sorted(chosen, key=lambda m: (-m[1], random.random()))[:min(readied_n, len(chosen))]
        mt_feats = []
    elif getattr(character, 'path_of_war_paths', 0) > 0:
        mt = _build_martial_training(character)
        if mt is None:
            return bundle
        disciplines, il, max_lvl = mt['disciplines'], mt['il'], mt['max_lvl']
        chosen, chosen_stances, readied = mt['known'], mt['stances'], mt['readied']
        mt_feats = mt['mt_feats']
        bundle['mt_feat_tax'] = mt['mt_feat_tax']
        bundle['homebrew_feat_desc_dict'] = {**bundle['homebrew_feat_desc_dict'], **mt['mt_descs']}
    else:
        return bundle

    bundle['martial_disciplines'] = disciplines
    bundle['initiator_level'] = il
    bundle['mt_feats'] = mt_feats
    bundle['maneuvers_choose_from'] = _group_by_level(chosen, max_lvl)
    bundle['maneuvers_readied_names'] = _group_by_level(readied, max_lvl)
    bundle['maneuvers_known_list'] = [len(lvl) for lvl in bundle['maneuvers_choose_from']]
    bundle['maneuvers_readied_list'] = [len(lvl) for lvl in bundle['maneuvers_readied_names']]
    bundle['stances_chosen'] = [m[0] for m in chosen_stances]
    bundle['maneuvers_desc_dict'] = {m[0]: _desc_entry(m) for m in chosen + chosen_stances}

    # Initiators always pick up 1..len(specialized) discipline style chains (base paid like a
    # Martial Training pick, followers always free). MT users already have their labeled feat
    # descriptions merged above; initiators get the style-chain descriptions instead.
    if character.c_class in data.path_of_war_class:
        style_feats, style_tax, style_descs = _choose_style_chains(character, disciplines)
        bundle['style_feats'] = style_feats
        bundle['style_feat_tax'] = style_tax
        bundle['homebrew_feat_desc_dict'] = style_descs
    return bundle


# --------------------------------------------------------------------------- #
# Counts per branch
# --------------------------------------------------------------------------- #

def _initiator_counts(character):
    '''Counts from the class's own table (path_of_war_maneuvers_known.json, scraped from the
    Library of Metzofitz -- treated as authoritative). Arrays are 20 long; epic levels read
    the level-20 row via capped_level_1.'''
    known = character.path_of_war_maneuvers_known
    # base PoW classes live under 'base'; Metzofitz homebrew initiators (e.g. Medic) under 'metzofitz'.
    table = known.get('base', {}).get(character.c_class) or known.get('metzofitz', {}).get(character.c_class)
    if not table:
        print(f"path of war: no maneuvers-known table for {character.c_class}")
        return None
    idx = max(0, min(getattr(character, 'capped_level_1', character.c_class_level), 20) - 1)
    il = character.c_class_level
    max_lvl = min(max(ceil(il / 2), 1), 9)
    disciplines = _specialize_disciplines(character, select_disciplines(character) or [])
    return (table['known'][idx], table['readied'][idx], table['stances'][idx],
            max_lvl, disciplines, [], il)


def _specialize_disciplines(character, disciplines):
    '''Initiator specialization: keep random.randint(2, 3) of the class's disciplines (clamped
    to what resolves in Martial_Disciplines.json -- drops scrape noise). All maneuvers, stances,
    and style chains draw only from this set.'''
    key_map = _discipline_key_map(character)
    resolvable = [d for d in disciplines if _dnorm(d) in key_map]
    if not resolvable:
        return []
    n = min(random.randint(2, 3), len(resolvable))
    return random.sample(resolvable, n)


def _deltas(cumulative):
    '''Per-tier increments from a cumulative array (deltas[0] is tier 1's own count, since the
    pre-tier-1 baseline is 0). e.g. known [2,4,5,7,8,9] -> [2,2,1,2,1,1].'''
    out, prev = [], 0
    for v in cumulative:
        out.append(v - prev)
        prev = v
    return out


def _level_floor_counts(total, n_levels):
    '''Per-maneuver-level pick counts for a fixed `total` spread over `n_levels` available levels
    (low->high). Campaign rule: learn AT LEAST 2 of every available maneuver level; when the
    class total can't afford 2x every level, fall back to 1 each (the extra +1s go to the LOWEST
    levels first). The per-level count is capped at 2 -- any surplus beyond 2-per-level is left at
    0 here so the caller can fill it randomly ("then truly random whichever"). Returns a list of
    length n_levels aligned to the levels low->high.
      total >= 2*n -> [2,2,...,2] (surplus = total-2n filled randomly afterward)
      n <= total < 2*n -> [2,..,2,1,..,1] (the first total-n levels get 2)
      total <  n      -> [1,..,1,0,..,0] (best effort: the lowest `total` levels get 1).'''
    if n_levels <= 0:
        return []
    per = [min(2, total // n_levels)] * n_levels
    extra = total - sum(per)
    i = 0
    while extra > 0 and i < n_levels and per[i] < 2:
        per[i] += 1
        extra -= 1
        i += 1
    return per


def _build_martial_training(character):
    '''Non-initiator Martial Training (house rule): ONE chain per rolled discipline, capped by
    available normal feat slots. Each chain is a full MT I..depth (depth 2/4/6 by BAB) drawing
    ONLY from its own discipline; the FEAT TIER is the level gate -- tier t grants level-t
    maneuvers (max maneuver level = depth, NOT the old initiator-level cap). Known maneuvers are
    spread >=2 (else >=1) per level via _level_floor_counts, so one chain still totals the table's
    depth row (e.g. depth 6 -> 9 maneuvers + 4 stances) but covers every level; N chains -> ~N x that.

    Paid feats (MT I/III/V per chain) are labeled by discipline -- e.g. "Martial Training I
    (Broken Blade)" -- so repeating the chain doesn't collapse under feat de-dup and the sheet
    shows which discipline each chain grants; the free partners (II/IV/VI) ride a hand-built tax
    bundle (their labeled names aren't in data/feats.csv, so feat_tax_func can't resolve them).

    Returns an aggregate dict (disciplines, il, max_lvl, known/stances/readied pool-tuple lists,
    mt_feats, mt_feat_tax, mt_descs), or None when no chain is affordable.'''
    depth = martial_training_depth(character)
    if depth == 0:
        return None
    prog = character.martial_training_progression['martial_training']
    # Maneuvers known: same chain total as the table's depth row, but spread as >=2 (else >=1)
    # per maneuver level instead of the raw cumulative deltas (e.g. depth 6: 9 -> [2,2,2,1,1,1]
    # rather than [2,2,1,2,1,1]) so every available level is represented. Stances keep the table.
    known_delta = _level_floor_counts(prog['known'][depth - 1], depth)
    stance_delta = _deltas(prog['stances'][:depth])
    readied_n = prog['readied'][depth - 1]
    il = max(character.level // 2, 1)          # exported for display / stance @pow.initLevel only
    max_lvl = depth                            # feat tier is the level gate
    paid_per_chain = depth // 2

    disciplines = _roll_disciplines(character, getattr(character, 'path_of_war_paths', 0))
    if not disciplines:
        return None
    # Each chain costs paid_per_chain paid feats; keep >=1 normal feat free (the old -1 buffer)
    # and only take whole chains the budget can pay for.
    affordable = max(0, getattr(character, 'normal_feat_amount', 0) - 1) // max(paid_per_chain, 1)
    n_chains = min(len(disciplines), affordable)
    if n_chains <= 0:
        return None
    disciplines = disciplines[:n_chains]

    base_descs = _mt_feat_descs()
    paid_tiers, free_tiers = _MT_PAID[:paid_per_chain], _MT_FREE[:paid_per_chain]
    all_m, all_s, all_r = [], [], []
    mt_feats, mt_feat_tax, mt_descs = [], {}, {}
    for disc in disciplines:
        chosen, stances = _pick_chain(character, disc, depth, known_delta, stance_delta, max_lvl)
        readied = sorted(chosen, key=lambda m: (-m[1], random.random()))[:min(readied_n, len(chosen))]
        all_m += chosen
        all_s += stances
        all_r += readied
        for paid, free in zip(paid_tiers, free_tiers):
            paid_l, free_l = f"{paid} ({disc})", f"{free} ({disc})"
            mt_feats.append(paid_l)
            mt_feat_tax[paid_l] = [free_l]
            mt_descs[paid_l] = base_descs.get(paid, "")
            mt_descs[free_l] = base_descs.get(free, "")
    return {
        'disciplines': disciplines, 'il': il, 'max_lvl': max_lvl,
        'known': all_m, 'stances': all_s, 'readied': all_r,
        'mt_feats': mt_feats, 'mt_feat_tax': mt_feat_tax, 'mt_descs': mt_descs,
    }


def _pick_chain(character, discipline, depth, known_delta, stance_delta, max_lvl):
    '''Tier-ordered, level-matched, prerequisite-legal selection for ONE Martial Training chain
    (one discipline). For tier t in 1..depth, take known_delta[t-1] maneuvers and stance_delta[t-1]
    stances PREFERRING level == t, falling back to the nearest available level <= max_lvl when a
    level is thin/exhausted. Picking low tiers first satisfies same-discipline "needs N maneuvers"
    prerequisites (stances count as maneuvers known, per PoW); the bootstrap relaxation handles
    the three disciplines with no prereq-free entries. Returns (chosen_maneuvers, chosen_stances)
    as pool tuples.'''
    remaining = _maneuver_pool(character, [discipline], max_lvl)
    out_m, out_s = [], []
    picked = [0]   # same-discipline maneuvers+stances picked so far (prereq currency)

    def take(want_stance, count, target_lvl):
        for _ in range(count):
            live = [m for m in remaining if (m[2] == 'stance') == want_stance]
            if not live:
                break
            eligible = [m for m in live if m[5] <= picked[0]]
            if not eligible:
                min_gap = min(m[5] - picked[0] for m in live)
                eligible = [m for m in live if m[5] - picked[0] == min_gap]
                print(f"path of war: prereq bootstrap (gap {min_gap}) in {discipline}")
            best_dist = min(abs(m[1] - target_lvl) for m in eligible)
            tier = [m for m in eligible if abs(m[1] - target_lvl) == best_dist]
            pick = random.choice(tier)
            remaining.remove(pick)
            picked[0] += 1
            (out_s if want_stance else out_m).append(pick)

    for t in range(1, depth + 1):
        take(False, known_delta[t - 1], t)
        take(True, stance_delta[t - 1], t)
    return out_m, out_s


def _roll_disciplines(character, n_paths):
    '''Pick n random disciplines from the curated data.disciplines list, restricted to names
    that actually resolve in Martial_Disciplines.json.'''
    key_map = _discipline_key_map(character)
    pool = [name for name in data.disciplines if _dnorm(name) in key_map]
    if not pool:
        print("path of war: no disciplines resolve against Martial_Disciplines.json")
        return []
    return random.sample(pool, k=min(n_paths, len(pool)))


# --------------------------------------------------------------------------- #
# Maneuver data access
# --------------------------------------------------------------------------- #

def _dnorm(s):
    '''Discipline/maneuver display-name comparison key (apostrophe- and case-insensitive,
    so "Fools Errand" matches the JSON's "Fool%27s_Errand").'''
    return re.sub(r'\s+', ' ', str(s).lower().replace("'", "").replace("’", "").strip())


def _display(key):
    return re.sub(r'\s+', ' ', unquote(str(key)).replace('_', ' ').strip())


def _discipline_key_map(character):
    '''{normalized display name -> raw JSON key} over Martial_Disciplines.json's top level
    (keys are URL-encoded with underscores, e.g. "Fool%27s_Errand").'''
    return {_dnorm(_display(k)): k for k in character.martial_disciplines}


def _maneuver_pool(character, disciplines, max_lvl):
    '''All parseable maneuvers/stances of the chosen disciplines with level <= max_lvl, as
    (display name, level, kind, entry, discipline display, prereq count) tuples. Entries whose
    level or kind can't be parsed (a handful of scrape artifacts) are skipped.'''
    key_map = _discipline_key_map(character)
    pool, skipped = [], 0
    for disc in disciplines:
        raw_key = key_map.get(_dnorm(disc))
        if raw_key is None:
            print(f"path of war: discipline {disc!r} not found in Martial_Disciplines.json")
            continue
        for m_key, entry in character.martial_disciplines[raw_key].items():
            if not isinstance(entry, dict):
                continue
            name, level, kind = _parse_maneuver(m_key, entry)
            if level is None or kind is None:
                skipped += 1
                continue
            if level <= max_lvl:
                pool.append((name, level, kind, entry, _display(raw_key), _prereq_count(entry)))
    if skipped:
        print(f"path of war: skipped {skipped} unparseable maneuver entries")
    return pool


def _parse_maneuver(key, entry):
    '''(display name, level, kind) for one maneuver entry. The scraped "Discipline" field
    carries both ("<Discipline> <Kind> [tags];Level: N" -- the separator varies); some
    entries instead hold a separate "Level" key.'''
    name = _display(key)
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
    return name, level, kind


def _prereq_count(entry):
    '''Same-discipline maneuver count this entry requires before it can be learned (PoW counts
    stances as maneuvers known). Tolerant of the scrape's variants: word numbers one..five,
    digits, the recurring "Thee" typo (= three), optional ": " prefixes, "maneuver(s)"/"strikes"
    nouns, a stray trailing backslash. "None"/missing/unparseable -> 0. The key appears as both
    "Prerequisites" and lowercase "prerequisites" (the latter always holding "None").'''
    raw = next((str(v) for k, v in entry.items() if k.lower() == 'prerequisites'), '')
    m = _PREREQ_NUM_RE.search(raw)
    if not m:
        return 0
    tok = m.group(1).lower()
    return int(tok) if tok.isdigit() else _WORD_NUMS.get(tok, 0)


def _desc_entry(m):
    name, level, kind, entry, discipline = m[:5]
    action = str(entry.get('Initiation', entry.get('Initiation Action', ''))).strip()
    action = re.sub(r'^(action)?\s*:\s*', '', action, flags=re.IGNORECASE)
    clean = lambda v: re.sub(r'^\s*:\s*', '', str(v)).strip()
    return {
        'description': clean(entry.get('Description', '')),
        'type': kind,
        'level': level,
        'discipline': discipline,
        'action': action,
        'range': clean(entry.get('Range', '')),
        'duration': clean(entry.get('Duration', '')),
    }


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #

def _constrained_pick(pool, known_n, stances_n):
    '''Prerequisite-legal selection in two phases. PHASE A (floor): guarantee a spread across the
    available maneuver levels -- >=2 of each present level (else >=1 when known_n can't afford 2x
    every level), filled low->high so same-discipline prereq currency builds before higher levels
    (_level_floor_counts sets the per-level targets; stances are not part of this floor). PHASE B
    (random): top up any remaining known_n AND all stances_n with the higher-level weighting
    ((index+1)^2 over level-sorted candidates), like generic_multi_chooser.

    Eligibility everywhere = candidates whose prereq count is already covered by previously picked
    maneuvers+stances OF THE SAME DISCIPLINE (PoW counts stances as maneuvers for prereqs).
    Bootstrap fallback: three disciplines (Roaring Mouse, Surging Shark, Unquiet Grave) have NO
    prereq-0 entries at all, so when nothing is eligible we relax to the candidates with the
    smallest unmet gap (logged) instead of deadlocking; the hard stop only fires when the pool
    itself runs out. Returns (chosen_maneuvers, chosen_stances) as pool tuples.'''
    candidates = sorted(pool, key=lambda m: (m[1], m[0]))     # level-ascending, stable
    picked_per_disc = {}                                      # discipline display -> count
    out_m, out_s = [], []

    def eligible(live):
        '''Prereq-legal subset of `live`, bootstrap-relaxed to the smallest unmet gap.'''
        elig = [m for m in live if m[5] <= picked_per_disc.get(m[4], 0)]
        if not elig and live:
            min_gap = min(m[5] - picked_per_disc.get(m[4], 0) for m in live)
            elig = [m for m in live if m[5] - picked_per_disc.get(m[4], 0) == min_gap]
            print(f"path of war: prereq bootstrap (gap {min_gap}) -- discipline has no "
                  f"prereq-free entries (e.g. Unquiet Grave)")
        return elig

    def commit(pick):
        candidates.remove(pick)
        picked_per_disc[pick[4]] = picked_per_disc.get(pick[4], 0) + 1
        (out_s if pick[2] == 'stance' else out_m).append(pick)

    # PHASE A: per-level floor over the KNOWN (non-stance) quota, low->high.
    levels_present = sorted({m[1] for m in candidates if m[2] != 'stance'})
    for lvl, target in zip(levels_present, _level_floor_counts(known_n, len(levels_present))):
        for _ in range(target):
            if len(out_m) >= known_n:
                break
            live = [m for m in candidates if m[2] != 'stance' and m[1] == lvl]
            if not live:
                break
            commit(random.choice(eligible(live)))

    # PHASE B: fill the remaining known + all stances, weighted toward higher levels.
    while len(out_m) < known_n or len(out_s) < stances_n:
        def quota_open(m):
            return (len(out_s) < stances_n) if m[2] == 'stance' else (len(out_m) < known_n)
        live = [m for m in candidates if quota_open(m)]
        if not live:
            if len(out_m) < known_n or len(out_s) < stances_n:
                print(f"path of war: maneuver pool exhausted at known {len(out_m)}/{known_n}, "
                      f"stances {len(out_s)}/{stances_n}")
            break
        elig = eligible(live)
        weights = [(i + 1) ** 2 for i in range(len(elig))]
        commit(random.choices(elig, weights=weights, k=1)[0])
    return out_m, out_s


def _group_by_level(maneuvers, max_lvl):
    '''list-of-lists of names indexed by maneuver level - 1 (the spells_known_selection
    layout: outer index = level, inner list = names at that level).'''
    grouped = [[] for _ in range(max(max_lvl, 1))]
    for m in maneuvers:
        grouped[m[1] - 1].append(m[0])
    return grouped


# --------------------------------------------------------------------------- #
# Style feat chains (Metzofitz catalogue) + homebrew feat descriptions
# --------------------------------------------------------------------------- #

_STYLE_CHAINS = None     # {discipline _dnorm key: {'base', 'children', 'descs'}}
_METZ_CSV = 'data/Metzofitz_Feats.csv'


def _style_chains(character):
    '''Lazy-build the discipline style chains from data/Metzofitz_Feats.csv (pipe-delimited,
    Style == "1"). Base = the row named "<Discipline> Style" for a discipline present in
    Martial_Disciplines.json (auto-excludes non-discipline styles like Mistmask / Slapping).
    Members come from a transitive closure over prereq-text mentions of already-found member
    names (catches Brutal Crocodile Desolation, whose prereq names only the middle feat).
    Children are ordered by mention depth (deepest tier wins: Black Seraph Annihilation
    mentions both base and child1 -> tier 2), tie-broken by the highest "<n> ranks" gate
    ascending (Radiant Dawn: Sunlight 7 before Daybreak 13).'''
    global _STYLE_CHAINS
    if _STYLE_CHAINS is None:
        df = pd.read_csv(_METZ_CSV, sep='|', dtype=str,
                         keep_default_na=False, on_bad_lines='skip')
        rows = []
        if 'Style' in df.columns:
            for _, r in df[df['Style'].str.strip() == '1'].iterrows():
                name = str(r.get('name', '')).strip()
                if not name:
                    continue
                desc = ' '.join(x for x in (str(r.get('description', '')).strip(),
                                            str(r.get('benefits', '')).strip()) if x)
                rows.append({'name': name, 'norm': _dnorm(name),
                             'prereq': _dnorm(r.get('prerequisites', '')), 'desc': desc})
        disciplines = {_dnorm(_display(k)) for k in character.martial_disciplines}
        chains = {}
        for base in rows:
            if not base['norm'].endswith(' style'):
                continue
            disc = base['norm'][:-len(' style')].strip()
            if disc not in disciplines:
                continue
            # membership: transitive closure over prereq mentions of member names
            member_norms = {base['norm']}
            changed = True
            while changed:
                changed = False
                for r in rows:
                    if r['norm'] not in member_norms and any(m in r['prereq'] for m in member_norms):
                        member_norms.add(r['norm'])
                        changed = True
            # tier = 1 + deepest mentioned member (iterate to fixpoint)
            tiers = {base['norm']: 0}
            for _ in range(len(member_norms)):
                for r in rows:
                    if r['norm'] in member_norms and r['norm'] != base['norm']:
                        mentioned = [t for m, t in tiers.items() if m != r['norm'] and m in r['prereq']]
                        if mentioned:
                            tiers[r['norm']] = max(mentioned) + 1
            max_ranks = lambda r: max((int(n) for n in re.findall(r'(\d+)\s*ranks', r['prereq'])),
                                      default=0)
            children = sorted((r for r in rows
                               if r['norm'] in member_norms and r['norm'] != base['norm']),
                              key=lambda r: (tiers.get(r['norm'], 99), max_ranks(r), r['name']))
            chains[disc] = {
                'base': base['name'],
                'children': [c['name'] for c in children],
                'descs': {base['name']: base['desc'],
                          **{c['name']: c['desc'] for c in children}},
            }
        _STYLE_CHAINS = chains
    return _STYLE_CHAINS


def _choose_style_chains(character, specialized):
    '''Pick random.randint(1, len(specialized)) style chains, restricted to chains whose name
    matches a SPECIALIZED discipline. Returns (style_feats, style_feat_tax, desc_dict):
      style_feats    -- [base display names]; each consumes a normal feat slot (MT pattern)
      style_feat_tax -- {base: [child display names]}; children are ALWAYS granted free
                        ("feat tax all the way through"), merged straight into the export
                        tax dict because Metzofitz feats are absent from data/feats.csv
      desc_dict      -- {display name: description} for every base + child picked.'''
    if not specialized:
        return [], {}, {}
    chains = _style_chains(character)
    eligible = [d for d in specialized if _dnorm(d) in chains]
    if not eligible:
        return [], {}, {}
    n = min(random.randint(1, len(specialized)), len(eligible))
    picked = random.sample(eligible, n)
    style_feats, style_tax, descs = [], {}, {}
    for disc in picked:
        chain = chains[_dnorm(disc)]
        style_feats.append(chain['base'])
        style_tax[chain['base']] = list(chain['children'])
        descs.update(chain['descs'])
    return style_feats, style_tax, descs


def _mt_feat_descs():
    '''{name: description} for all six Martial Training feats, from the cached data/feats.csv
    rows (type "Path of War"). Exported so the FoundryVTT module can render them -- they are
    absent from its every_feat.json template and were previously dropped silently.'''
    df = grab_and_clean_feats('data/feats.csv')
    out = {}
    for _, r in df[df['name'].isin(_MT_FEATS)].iterrows():
        parts = [str(r.get(col, '')).strip() for col in ('description', 'benefit')]
        text = ' '.join(p for p in parts if p and p.lower() != 'nan')
        out[str(r['name'])] = text
    return out
