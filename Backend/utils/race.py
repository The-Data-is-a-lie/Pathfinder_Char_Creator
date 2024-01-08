import json

#anytime we want to deal with external files, we need to have a file handler -> in python we create a file handle with this:

with open("utils/race.json","r") as f:
    j = json.load(f)
#    print(j.items())




# for k,v in j.items():
#     v['first names'] = [n.lower() for n in v['first names'] ]



class NamesParse():
    
    def move_names(self,j):
        self.first_names = []
        self.last_names = []
        for k, v in j.items():
           
            print(k)
            if 'first names' in v:    
                f_names = v['first names']  
                self.first_names += f_names
                del v['first names']

            if 'last names' in v:
                l_names = v['last names']
                self.last_names += l_names
                del v['last names'] 



        return self.first_names, self.last_names
    
    def make_new_json(self, f_path):
        a = {
            'first names': self.first_names,
            'last names': self.last_names
            }

        with open(f_path, 'w') as f:
            f.write(str(a))

np = NamesParse()

f, l = np.move_names(j)
np.make_new_json("names.json")

# we can put all the code into this class to be able to do things with names by region:

# define a function that 
# structure it by region programmatically

# np = NamesParse()
# np_2 = NamesParse()




# f, l = move_names(j)
# f






# RACE_ATTR=[
#     'first names','last names','age',
#     'height','weight','size','speed',
#     'traits','languages', 'hair_colors',
#     'hair_types','eye_colors','appearance', 'class']

# class RaceCreater:
#     def __init__(self, attr=RACE_ATTR, ):
#         self.attr={a:'' for a in attr}
    
#     def set_age(self, age, dice='1d6'):
#         self.attr['age'] = (age, dice)

#     def set_attr(self, attr, value):
#         self.attr[attr] = value
# aasimar = RaceCreater(RACE_ATTR)



#build