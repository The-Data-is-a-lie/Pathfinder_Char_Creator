RACE_ATTR=[
    'first names','last names','age',
    'height','weight','size','speed',
    'traits','languages', 'hair_colors',
    'hair_types','eye_colors','appearance', 'class']

class RaceCreater:
    def __init__(self, attr=RACE_ATTR, ):
        self.attr={a:'' for a in attr}
    
    def set_age(self, age, dice='1d6'):
        self.attr['age'] = (age, dice)

    def set_attr(self, attr, value):
        self.attr[attr] = value
aasimar = RaceCreater(RACE_ATTR)