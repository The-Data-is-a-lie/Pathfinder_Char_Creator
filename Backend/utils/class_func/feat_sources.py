"""Where each feat row comes from: the source labels for the general feat track.

A character's general feats are not one kind of thing. Ten of a 20th-level character's come from
its levels (1st, 3rd, 5th ... 19th); the house feat economy adds two at creation; a human has one
more for being human; and several rows of the same list are not free choices at all but slots the
character SPENT -- on a profession feat, a Martial Training chain, a sphere talent.

The sheet used to number the whole list by position in twos, so a 20th-level character showed
"(Feat 21)" and "(Feat 23)", a human's racial feat was an anonymous "(Feat 1)", and nothing said
which rows had been spent on what. This module names each row by its source instead (ruled
2026-11-16):

    (Human)                      the human bonus feat
    (Creation 1), (Creation 2)   the house feat economy's two creation feats
    (Feat 1), (Feat 3), ...      a level feat, numbered by the level it is gained at
    (Profession N)               a slot spent on a profession feat
    (Martial Training N)         a slot spent on a Martial Training or style feat
    (Sphere N)                   a slot spent on a sphere talent's tracking feat
    (E-Kat N)                    a slot reserved for an E-Kat feat
    (Luck N)                     a feat bought by selling luck (the sheet files these under
                                 Negative Luck with their running cost; the label is for a client
                                 that does not)
    (Granted N)                  a feat handed over free to make the rolled gear legal

``general_slot_labels`` is the track's slots in order -- what a BLANK sheet shows, one placeholder
each. ``general_feat_labels`` is the same list laid over a generated character's actual rows: a
spent or granted row is named for what it is, and the free choices take the slot names in order,
the 1st-level sources first and then up the level ladder.

Story, flavor and flaw feats, class bonus feats, trainers and teamwork feats are separate lists
with labels of their own; this module is about the one list that mixed its sources.

THE COUNTS ARE NOT RESTATED: the level ladder is ``feat_level_assignment.normal_feat_slot_levels``,
the level-feat and creation-feat counts are ``level_and_bab.level_feat_count`` and
``CREATION_FEATS``, and the human feat is ``character.human_flag``.
"""
from collections import Counter

from .class_specific_feats import ranger_style_feat_levels
from .extra_combat_feats import class_bonus_feat_levels
from .feat_level_assignment import normal_feat_slot_levels
from .generic_func import class_entry_for
from .level_and_bab import CREATION_FEATS, level_feat_count
from .skill_ranks import homebrew_enabled

# What a slot gained at 1st level outside the level ladder is called, in the order the sheet lists
# them. The human feat first: it is the one a player looks for.
HUMAN = 'Human'
CREATION = 'Creation'
# What a level feat is called -- "(Feat 5)". The module's own word for the row.
LEVEL = 'Feat'
# A slot the track should not have had (more free choices than slots). Never seen; named so that
# if it ever happens the sheet says something true rather than inventing a level.
EXTRA = 'Bonus'


def general_slot_labels(character):
    """The general feat track's slots, in sheet order: the 1st-level sources, then the level
    ladder. ``["Human", "Creation 1", "Creation 2", "Feat 1", "Feat 3", ...]``."""
    extras = [HUMAN] if getattr(character, 'human_flag', False) else []
    if homebrew_enabled(character):
        extras += [f'{CREATION} {n}' for n in range(1, CREATION_FEATS + 1)]
    total = level_feat_count(character.level) + len(extras)
    # The owner seats the surplus at level 1 and stops the ladder at the character's level; the
    # surplus is exactly the extras named above, so only the ladder rungs are read from it.
    levels = normal_feat_slot_levels(character, total)
    ladder = levels[len(extras):]
    return extras + [f'{LEVEL} {level}' for level in ladder]


def general_feat_labels(character, feats, spent):
    """One label per row of ``feats`` (the final general feat list), parallel to it.

    ``spent`` maps a lower-cased feat name to the source word of a row that is not a free choice
    ("Profession", "Martial Training", ...); those rows are numbered within their source. Every
    other row takes the next slot name from ``general_slot_labels``.
    """
    slots = iter(general_slot_labels(character))
    counts = Counter()
    labels = []
    for name in feats:
        source = spent.get(str(name).lower())
        if source is None:
            label = next(slots, None)
            if label is None:
                counts[EXTRA] += 1
                label = f'{EXTRA} {counts[EXTRA]}'
        else:
            counts[source] += 1
            label = f'{source} {counts[source]}'
        labels.append(label)
    return labels


def spent_sources(*, profession=(), martial=(), sphere=(), e_kat=(), luck=(), granted=()):
    """``{lower-cased feat name: source word}`` for ``general_feat_labels``, from the lists the
    pipeline already keeps of what each subsystem put in the general track. Later arguments win a
    name held twice, which is the order of how specifically each one accounts for its feat."""
    out = {}
    for source, names in (('Profession', profession), ('Martial Training', martial),
                          ('Sphere', sphere), ('E-Kat', e_kat), ('Luck', luck),
                          ('Granted', granted)):
        for name in names or ():
            out[str(name).lower()] = source
    return out


def class_grant_slots(character):
    """``[(class display, level)]`` for the bonus feats two classes grant from lists of their own:
    the monk's bonus feats and the ranger's combat style feats. They are class bonus feats and are
    shown with the others, labelled "Monk 2" / "Ranger 6" -- but they are not drawn from the
    general pool, which is why ``extra_combat_feats.class_bonus_feat_slots`` leaves them out.
    """
    slots = []
    monk = class_entry_for(character, 'monk') or class_entry_for(character, 'unchained_monk')
    if monk is not None:
        slots += [(monk['display'], level) for level in class_bonus_feat_levels('monk', monk['level'])]
    ranger = class_entry_for(character, 'ranger')
    if ranger is not None:
        slots += [(ranger['display'], level) for level in ranger_style_feat_levels(ranger['level'])]
    return slots


def class_grant_rows(character, monk_feats, ranger_feats, clean):
    """``(names, labels)`` for the monk and ranger feats a generated character was actually granted,
    ready to join ``class_feats`` / ``class_feat_labels``.

    The choosers return sets, so the names are sorted: which feat sits at which of the class's
    levels is not something the generator decides, and a stable order keeps a seed reproducible.
    A list that ran out before its schedule did simply fills fewer of the class's levels.
    ``clean`` is the caller's name normaliser (casing, the free-feat filter).
    """
    names, labels = [], []
    for entry, granted, levels_for_class in (
            (class_entry_for(character, 'monk') or class_entry_for(character, 'unchained_monk'),
             monk_feats, lambda level: class_bonus_feat_levels('monk', level)),
            (class_entry_for(character, 'ranger'), ranger_feats, ranger_style_feat_levels)):
        if entry is None:
            continue
        held = clean(sorted(str(name) for name in granted or ()))
        for name, level in zip(held, levels_for_class(entry['level'])):
            names.append(name)
            labels.append(f'{entry["display"]} {level}')
    return names, labels
