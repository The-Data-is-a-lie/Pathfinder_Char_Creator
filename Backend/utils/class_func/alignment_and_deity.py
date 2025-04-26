import random
from utils import data

def choose_alignment(self, alignments, alignment_input):
    alignment_data = getattr(data,alignments)
    # alignment_input = input("If you want to choose an alignment, type: CG CN CE NG N NE LG LN LE ").upper()
    self.alignment = alignment_data.get(alignment_input.upper(), None)
    print("Alignment data: ", alignment_data)

    if self.alignment is None:
        random_alignment_code = random.choice(list(alignment_data.keys()))
        self.alignment = alignment_data[random_alignment_code].lower()
        mini_alignment = random_alignment_code.lower()
    else:
        self.alignment = self.alignment.lower()
        mini_alignment = alignment_input.lower()

    return self.alignment, mini_alignment.lower()

def randomize_deity(self, random_flag=True, deity_choice=None):
    # Check if a deity name is provided
    if deity_choice:
        # Find the deity based on its 'Name'
        for deity in self.deity["All"]:
            if deity["Name"][0] == deity_choice:
                self.deity_choice = deity
                break
        else:
            print(f"Deity {deity_choice} not found.")
    else:
        # If no deity_choice is provided, you could choose randomly
        self.deity_choice = random.choice(self.deity["Other"])
    
    return self.deity_choice

