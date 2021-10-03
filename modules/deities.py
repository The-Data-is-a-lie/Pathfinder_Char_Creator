from utils.data import *
from utils.util import *

def randomDeity():
    deity = deities[randrange(len(deities))]
    print(f"Deity: {deity}\n")

def deityFavour():
    divine_favour = randrange(0,100)
    print(f"Divine Favour: {divine_favour}")

def runDeities():
    randomDeity()
    deityFavour()