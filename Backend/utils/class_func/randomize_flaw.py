import random


def randomize_flaw_amount(rng=None):
    """How many mechanical flaws to roll: a d100 ladder, 0-4.

    `rng` defaults to the module-level `random`, which is the PC path and must stay byte-identical.
    A bonded creature passes its own generator so its flaws cannot churn its master's rolls
    (spec section 8, D16).
    """
    rng = rng or random
    flaw_chance = rng.randint(0, 100)
    if int(flaw_chance) <= 50:
        flaw_amount = 2
    elif 50 < int(flaw_chance) <= 65:
        flaw_amount = 3
    elif 65 < int(flaw_chance) <= 80:
        flaw_amount = 1
    elif 80 < int(flaw_chance) <= 95:
        flaw_amount = 0
    else:
        flaw_amount = 4
    return flaw_amount
