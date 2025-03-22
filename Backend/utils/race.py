import json

#anytime we want to deal with external files, we need to have a file handler -> in python we create a file handle with this:

with open("utils/race.json","r") as f:
    j = json.load(f)

class NamesParse():
    
    def move_names(self,j):
        self.first_names = []
        self.last_names = []
        for k, v in j.items():
           
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