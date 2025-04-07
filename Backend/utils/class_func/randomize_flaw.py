import random
def randomize_flaw_amount():
    flaw_chance = random.randint(0,100)
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