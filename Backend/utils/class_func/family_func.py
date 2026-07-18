import random
def randomize_parents(character):
    """Roll the family independently: a status for EACH parent plus the household the character
    was raised in, so every NPC has mother + father + financial situation (the old single-phrase
    roll produced EITHER parents OR a situation, leaving the sheet's Family section with only one).
    Returns one comma-joined phrase ("<status> mother, <status> father, raised in ...") -- the
    structured bio splits it on commas into bullets; prose/legacy consumers use it verbatim."""
    statuses = ["loving", "absent", "dead"]
    mother = random.choices(statuses, weights=[60, 20, 20])[0]
    father = random.choices(statuses, weights=[60, 20, 20])[0]
    parts = [f"{mother} mother", f"{father} father"]
    if mother != "loving" and father != "loving":
        # No present, caring parent -> raised elsewhere (matches the old adopted/orphanage rolls).
        parts.append(random.choice([
            "raised in an orphanage",
            "adopted into a wealthy family",
            "adopted into a poor family",
            "adopted into a middle income family",
        ]))
    else:
        wealth = random.choice(["wealthy", "middle income", "poor"])
        parts.append(f"raised in a {wealth} household")
    return ", ".join(parts)

def randomize_siblings(character):
    # Define probabilities for each category of siblings
    probabilities = {
        "older_brothers": [0.8, 0.1, 0.05, 0.05],  
        "younger_brothers": [0.8, 0.1, 0.05, 0.05], 
        "older_sisters": [0.8, 0.1, 0.05, 0.05],  
        "younger_sisters": [0.8, 0.1, 0.05, 0.05]  
    }

    # Weighted random selection for each category
    random_older_brothers = random.choices(range(4), weights=probabilities["older_brothers"])[0]
    random_younger_brothers = random.choices(range(4), weights=probabilities["younger_brothers"])[0]
    random_older_sisters = random.choices(range(4), weights=probabilities["older_sisters"])[0]
    random_younger_sisters = random.choices(range(4), weights=probabilities["younger_sisters"])[0]

    random_older_brothers = f" you have {random_older_brothers} older brothers"
    random_younger_brothers = f" you have {random_younger_brothers} younger brothers"
    random_older_sisters = f" you have {random_older_sisters} older sisters"
    random_younger_sisters = f" you have {random_younger_sisters} younger sisters"

    
    return random_older_brothers, random_younger_brothers, random_older_sisters, random_younger_sisters