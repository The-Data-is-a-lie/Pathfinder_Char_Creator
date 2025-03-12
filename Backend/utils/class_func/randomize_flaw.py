import random
def randomize_flaw(self):
    flaw_chance = random.randint(0,100)
    if int(flaw_chance) <= 50:
        flaw = random.sample(list(self.flaws),2)
    elif 50 < int(flaw_chance) <= 65:
        flaw = random.sample(list(self.flaws),3)
    elif 65 < int(flaw_chance) <= 80:
        flaw = random.sample(list(self.flaws),1)
    elif 80 < int(flaw_chance) <= 95:
        flaw = random.sample(list(self.flaws),0)
    else:
        flaw = random.sample(list(self.flaws),4)
    self.flaw = flaw
    return flaw