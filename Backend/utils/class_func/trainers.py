"""Trainer slots (homebrew) — bonus feats granted by the trainers a character has studied under.

A character can have studied under several trainers. The number of trainer "slots" scales with hit
dice (and, later, mythic rank); each occupied slot is a trainer of some *caliber* (1 terrible →
4 mythical) that teaches that many feats. The taught feats are real bonus feats added on top of the
normal budget (like bloodline/teamwork feats) and are feat-taxed by the caller, so taking a base feat
also bundles its progression chain. Each trainer's feats are tagged "(Trainer N)" so the sheet can
group them the way the example actors do (e.g. "(Trainer 1) Weapon Focus > ...").

    max trainer slots = 1 + (hit dice // 3) + mythic rank      (mythic = 0 for now)
    actual trainers   = a roll between 0 and that maximum
    trainer caliber   = weighted 1-4 (average/excellent common, terrible/mythical rare)

Selection reuses ``topup_feat_chooser`` (combat/metamagic-aware, widens to the general pool and
registers every pick in ``character.chooseable`` so nothing is re-picked). The actual feat-tax pass
runs in ``main_test`` alongside the other buckets, sharing its granted-set.
"""
import random

from utils.class_func.feats import topup_feat_chooser
from utils.class_func.feats_to_chooseable import add_feats_to_chooseable

# caliber -> descriptive name (the trainer's quality / how many feats they teach)
CALIBER_NAMES = {1: "terrible", 2: "average", 3: "excellent", 4: "mythical"}


def roll_trainer_slots(character):
    """How many trainers this character actually studied under: a roll from 0 to the maximum
    ``1 + hit_dice//3 + mythic_rank`` (mythic rank is not modelled yet, so it reads as 0)."""
    level = getattr(character, "level", 0) or 0
    mythic = getattr(character, "mythic_rank", 0) or 0
    max_slots = 1 + level // 3 + mythic
    return random.randint(0, max_slots)


def roll_caliber():
    """A trainer's caliber: weighted so average (2) and excellent (3) trainers are common, and
    terrible (1) and mythical (4) trainers are rare."""
    return random.choices([1, 2, 3, 4], weights=[15, 40, 30, 15], k=1)[0]


def select_trainer_feats(character, casting_level_str):
    """Roll the character's trainers and the feats each teaches.

    Returns ``(trainer_feats, trainer_feat_labels, trainer_calibers)`` where ``trainer_feats`` is a
    flat list of feat names and ``trainer_feat_labels`` is a parallel list of "(Trainer N)" tags
    (feats from the same trainer share a tag). ``trainer_calibers`` is the per-trainer caliber roll,
    for logging. The caller adds these to the normal feat total and runs the feat-tax pass.
    """
    slots = roll_trainer_slots(character)
    trainer_feats = []
    trainer_feat_labels = []
    trainer_calibers = []

    for idx in range(1, slots + 1):
        caliber = roll_caliber()
        trainer_calibers.append(caliber)
        # A caliber-C trainer teaches C feats. topup_feat_chooser registers each in
        # character.chooseable, so a later trainer (or any other bucket) won't re-pick them.
        picks = topup_feat_chooser(character, casting_level_str, caliber) or []
        add_feats_to_chooseable(character, picks)
        for feat in picks:
            trainer_feats.append(feat)
            trainer_feat_labels.append(f"(Trainer {idx})")

    print(f"trainers -> {slots} slot(s), calibers {trainer_calibers} "
          f"({[CALIBER_NAMES[c] for c in trainer_calibers]}), {len(trainer_feats)} feats")
    return trainer_feats, trainer_feat_labels, trainer_calibers
