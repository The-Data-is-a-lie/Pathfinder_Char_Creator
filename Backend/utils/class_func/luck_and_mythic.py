import random

def randomize_mythic(character):
    character.mythic_rank = 0
    if random.randint(1, 1000) >= 995:
        character.mythic_rank = 1					
        for j in range(2, 11):
            roll = random.randint(1, 100)
            if roll >= 90:
                character.mythic_rank += 1
    else:
        character.mythic_rank = 0
    return character.mythic_rank


# randomize_luck() was DELETED here, deliberately, rather than repaired.
#
# It did not implement a weakened version of the luck rule -- it implemented a different rule. The
# Doc's luck is BOUGHT (point buy / level-up points / 5 skill ranks or HP) and caps at +25/-50;
# randomize_luck rolled +-1..40 on a 5%/5% chance. There was nothing in it to keep. It was also
# already unwired (its import in main_test.py had been commented out), so nothing changed behaviour
# when it went.
#
# The real subsystem lives in class_func/luck.py, resolved by phase_luck_stake and
# phase_luck_resolution. randomize_mythic above is untouched: it belongs to the Mythic map, which
# owns the other half of this file.