"""Prerequisite- and BAB-aware feat -> level assignment.

Feat *selection* already guarantees the chosen set is legal at the character's FINAL level:
no_prereq_loop() gates each feat on character.chooseable, which holds the BAB/ability strings
("base attack bonus +0".."+N", "int 13", ...). But the feats were then dropped onto level slots by
list *position* -- separate_feats_func front-pops in selection order, then main_test labels normal
feats 1,3,5,... and class-bonus feats 1,2,4,6,... positionally. That let a feat land at a slot below
the level its prerequisites are actually met. Canonical bug: a Fighter showing "Greater Feint" at
level 4 (it needs Improved Feint + base attack bonus +6, i.e. Fighter 6) before "Improved Feint" at
level 8.

assign_feats_to_levels() reorders the normal + class-bonus feat lists as ONE combined pool so that
positional assignment to the fixed slot schedules places every feat at a slot whose level is >= the
feat's minimum legal acquisition level AND at or above every selected prerequisite feat it depends
on. Reordering (not re-leveling) is sufficient because the export pairs feats[i]/class_feats[i]
positionally with their level schedules.

Cheap by design: no new disk I/O or network -- it reuses the already-cached feat prerequisite graph
and the cached data/feats.csv via feat_tax.py, plus an in-memory schedule over the handful of feats a
single character has.
"""
import re
from math import ceil

# Reuse the cached prereq graph + cached-CSV lookup from the feat-tax module so we don't re-parse
# data/feats.csv or re-derive feat dependencies.
from utils.class_func.feat_tax import (
    _prereq_graph,
    feat_spell_searcher,
    determine_prerequisite_name,
)

# "base attack bonus +6" -- captured first, then stripped, so its trailing "+6" can't be misread by a
# bare level regex.
_BAB_RE = re.compile(r'base attack bonus\s*\+?\s*(\d+)')
# Explicit level / Hit-Dice gates (run AFTER the BAB span is removed). Dashes are normalized to spaces
# first so "7th-level" reads like "7th level".
_LEVEL_AFTER_RE = re.compile(r'level\s+(\d+)')                                   # "fighter level 4", "character level 7"
_LEVEL_BEFORE_RE = re.compile(r'(\d+)(?:st|nd|rd|th)\s+(?:character\s+)?level')  # "4th level", "7th character level"
_HD_RE = re.compile(r'(\d+)\s*(?:hd|hit dice)')                                  # "10 hit dice"


def normal_feat_slot_levels(character, count):
    """The acquisition levels of a character's `count` NORMAL feat slots, ascending.

    PF1 grants a feat at every odd level, so the schedule is 1, 3, 5, ... -- but a character always
    holds MORE normal feats than that ladder has rungs. The house feat economy adds two creation
    feats (`level_and_bab.update_level`), humans add a racial bonus feat, and a negative-luck seller
    can add up to ten more ("a feat for -5 luck"). Those are all granted AT CREATION or by a trade,
    not earned at a level the character has yet to reach.

    Walking the ladder positionally -- `[2 * i + 1 for i in range(len(feats))]`, which is what every
    call site used to do -- therefore ran off the end of the character: a 20th-level wizard with 12
    normal feats produced slots at levels 21 and 23. That is not merely a cosmetic label. These
    levels are the gate `assign_feats_to_levels` schedules against, so a phantom level-23 slot will
    happily seat a feat whose BAB or class-level prerequisite the character does not actually meet
    -- the exact bug this module exists to prevent.

    The surplus seats at level 1, where it was in fact granted, and the ladder stops at the
    character's level.
    """
    count = max(0, int(count or 0))
    level = max(1, int(getattr(character, 'level', 1) or 1))
    ladder = [lvl for lvl in (2 * i + 1 for i in range(count)) if lvl <= level]
    return sorted([1] * (count - len(ladder)) + ladder)


def _bab_to_level(bab_type, bab_req):
    """First character level at which a single-classed character of this BAB progression reaches
    `bab_req`. Mirrors _update_bab_total: H -> level, M -> floor(level*0.75), L -> floor(level*0.5)."""
    if bab_type == 'M':
        return ceil(bab_req / 0.75)
    if bab_type == 'L':
        return ceil(bab_req / 0.5)
    return bab_req                       # 'H' (full BAB) or unknown -> BAB == level


def _min_level_from_prereq(bab_type, prereq_lower):
    """Lowest character level at which the numeric gates in a feat's prerequisite string are met:
    max of BAB requirement (inverted via progression), explicit class/character-level requirements,
    and Hit-Dice requirements. Ability-score gates ("int 13") are treated as met at level 1 -- feat
    selection already guaranteed final-level legality, and the per-level stat history isn't tracked.
    Defaults to 1 (every feat is legal at level 1 unless a numeric gate raises it)."""
    if not prereq_lower:
        return 1
    text = prereq_lower.replace('-', ' ')          # "7th-level" -> "7th level"
    needs = [1]
    for m in _BAB_RE.finditer(text):
        needs.append(_bab_to_level(bab_type, int(m.group(1))))
    text = _BAB_RE.sub(' ', text)                  # drop BAB spans before scanning for levels
    for rx in (_LEVEL_AFTER_RE, _LEVEL_BEFORE_RE, _HD_RE):
        for m in rx.finditer(text):
            needs.append(int(m.group(1)))
    return max(needs)


def _prereq_strings(character, names):
    """{lower feat name -> cleaned prerequisite string} for `names`, from the cached data/feats.csv.
    Feats absent from the CSV (e.g. homebrew, or weapon-specific variants) are simply omitted ->
    callers default them to min level 1."""
    if not names:
        return {}
    info = feat_spell_searcher(
        character, character.c_class, list(names), "feats", "prerequisites", "description", {}
    ) or {}
    return {str(k).lower(): determine_prerequisite_name(v) for k, v in info.items()}


def assign_feats_to_levels(character, feats, class_feats, normal_slot_levels, class_slot_levels):
    """Reorder `feats` + `class_feats` (treated as one combined pool) so that positional assignment to
    the slot schedules is prerequisite- and BAB-legal.

    Returns (new_feats, new_class_feats, new_normal_levels, new_class_levels). The two *_levels lists
    are the same slot multisets as the inputs, re-paired to the reordered feat lists (ascending). A
    feat MAY migrate between the normal and class-bonus track -- that split is already positional, so
    no fidelity is lost. Raises ValueError on a slot/feat length mismatch so the caller can fall back
    to the original positional behavior."""
    feats = list(feats or [])
    class_feats = list(class_feats or [])
    normal_slot_levels = list(normal_slot_levels or [])
    class_slot_levels = list(class_slot_levels or [])

    if not feats and not class_feats:
        return feats, class_feats, normal_slot_levels, class_slot_levels
    if len(normal_slot_levels) != len(feats) or len(class_slot_levels) != len(class_feats):
        raise ValueError("feat/slot length mismatch")

    # Combined pool of (display name, lower name). Duplicates (e.g. the appended "two-weapon fighting")
    # are kept distinct -- never collapse into a set.
    pool = [(str(f), str(f).lower()) for f in feats] + [(str(f), str(f).lower()) for f in class_feats]

    bab_type = getattr(character, 'bab', 'H')
    prereqs = _prereq_strings(character, {lower for _, lower in pool})
    min_lvl = [_min_level_from_prereq(bab_type, prereqs.get(lower, '')) for _, lower in pool]

    # Per-element prerequisite map, restricted to prereqs that are themselves in this pool.
    requires_map = _prereq_graph()[0]                      # lower name -> set(prereq lower names)
    pool_names = {lower for _, lower in pool}
    prereq_names = []
    for _, lower in pool:
        pn = set(requires_map.get(lower, ())) & pool_names
        pn.discard(lower)
        prereq_names.append(pn)

    # E-Kat feats are pinned to the NORMAL track. This scheduler treats normal + class-bonus feats
    # as one pool, so without this an E-Kat feat migrates into a class-bonus slot and renders as a
    # *Class Bonus Feat* -- six of ten did, on a measured character. They are ordinary feats bought
    # with ordinary feat slots; a class did not grant them. Pinning here rather than at the two call
    # sites because both of them run this same reorder.
    #
    # The luck-bought feats are pinned for the same reason plus a sharper one: the FoundryVTT module
    # lifts them out of the ordinary feat list to render its "Negative Luck" section, and it does
    # that by name against `feats` ONLY. One that migrated into a class-bonus slot would therefore
    # survive in class_feats AND appear under Negative Luck -- the same feat twice on one sheet.
    pinned_normal = {str(n).lower() for n in (getattr(character, 'e_kat_feats_chosen', None) or [])}
    pinned_normal |= {str(n).lower() for n in (getattr(character, 'luck_bought_feats', None) or [])}

    # Slots tagged by origin bucket, considered lowest-level first.
    slots = [(lvl, 'normal') for lvl in normal_slot_levels] + [(lvl, 'class') for lvl in class_slot_levels]
    free = sorted(range(len(slots)), key=lambda s: slots[s][0])
    used = [False] * len(slots)

    # Kahn-style scheduler: repeatedly place the ready feat with the smallest minimum level into the
    # lowest free slot that (a) meets that feat's own level gate and (b) is at or above every selected
    # prerequisite's assigned level. A feat is "ready" only once all its in-pool prerequisites are
    # placed, so a dependent is floored at its prerequisites' levels -- never seated below them -- while
    # taking the lowest adequate slot keeps every chain as early as the rules allow.
    name_level = {}                                       # earliest level a feat name was placed at
    placement = {}
    remaining = set(range(len(pool)))
    while remaining:
        ready = [i for i in remaining if prereq_names[i].issubset(name_level)]
        if not ready:                                    # dependency cycle (shouldn't happen) -> ignore deps
            ready = list(remaining)
        elem = min(ready, key=lambda i: (min_lvl[i], i))
        floor = max([min_lvl[elem]] + [name_level[p] for p in prereq_names[elem] if p in name_level])
        # A pinned feat may only take a normal slot; everything else takes the lowest legal slot.
        want = (lambda s: slots[s][1] == 'normal') if pool[elem][1] in pinned_normal else (lambda s: True)
        chosen = next((s for s in free if not used[s] and slots[s][0] >= floor and want(s)), None)
        if chosen is None:                               # no legal slot at/above the floor
            chosen = next((s for s in free if not used[s] and want(s)), None)
        if chosen is None:                               # pinned track full -> best effort, any slot
            chosen = next((s for s in reversed(free) if not used[s]), None)
        used[chosen] = True
        placement[elem] = chosen
        lvl, _ = slots[chosen]
        name = pool[elem][1]
        if name not in name_level or lvl < name_level[name]:
            name_level[name] = lvl
        remaining.discard(elem)

    # Re-pair into buckets, ordered by ascending slot level so position N == the Nth slot.
    normal_out, class_out = [], []
    for elem_idx, slot_idx in placement.items():
        lvl, bucket = slots[slot_idx]
        (normal_out if bucket == 'normal' else class_out).append((lvl, slot_idx, pool[elem_idx][0]))
    normal_out.sort(key=lambda t: (t[0], t[1]))
    class_out.sort(key=lambda t: (t[0], t[1]))

    new_feats = [display for _, _, display in normal_out]
    new_class_feats = [display for _, _, display in class_out]
    new_normal_levels = [lvl for lvl, _, _ in normal_out]
    new_class_levels = [lvl for lvl, _, _ in class_out]
    return new_feats, new_class_feats, new_normal_levels, new_class_levels
