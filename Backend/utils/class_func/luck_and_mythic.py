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


def randomize_luck(character):
    if random.randint(1, 100) >= 95:
        character.luck_score = random.randint(1, 40)
    #using a -40 to make it a negative luck score when you roll low
    elif random.randint(1, 100) <= 5:
        character.luck_score = random.randint(1, 40) - 40
    else:
        character.luck_score = 0
    return character.luck_score