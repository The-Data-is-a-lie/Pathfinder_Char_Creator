import random
from utils import data
def randomize_path_of_war_num(self, path_of_war_class):
    self.path = 0
    chance = random.randint(1,100)
    getattr(data,path_of_war_class)
    if self.c_class not in path_of_war_class:
        if self.bab == 'H':
            if chance >= 25:
                self.path = 1
            else:
                self.path = 0

        elif self.bab == 'M':
            if chance >= 50:
                self.path = 1
            else:
                self.path = 0                    

        else:
            if chance >= 90:
                self.path = 1
    return self.path

def choose_path_of_war_attr(self, disciplines):
    #choosing path of war discipline
    potential_disciplines = getattr(data, disciplines)
    if self.path > 0:
        return random.sample(potential_disciplines, k=self.path)
    else:
        return None