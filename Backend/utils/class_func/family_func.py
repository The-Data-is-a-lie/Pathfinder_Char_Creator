import random
def randomize_parents(character):
    random_num = random.randint(1, 60)
    if random_num <= 5:
        parents = "loving and kind, raised by both parents"
    elif random_num <= 10:
        parents = "absent father, loving mother"
    elif random_num <= 15:
        parents = "dead father, loving mother"
    elif random_num <= 20:
        parents = "absent mother, loving father"
    elif random_num <= 25:
        parents = "dead mother, loving father"
    elif random_num <= 30:
        parents = "absent parents"
    elif random_num <= 35:
        parents = "dead parents"        
    elif random_num <= 40:
        parents = "adopted into a wealthy family"
    elif random_num <= 45:
        parents = "adopted into a poor family" 
    elif random_num <= 50:
        parents = "adopted into a middle income family"                
    elif random_num <= 55:
        parents = "raised in an orphange"     
    else:
        parents = "loving and kind, raised by both parents"

    return parents

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