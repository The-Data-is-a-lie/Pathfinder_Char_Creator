import random
from utils import data

def choose_alignment(self, alignments, alignment_input):
    alignment_data = getattr(data,alignments)
    # alignment_input = input("If you want to choose an alignment, type: CG CN CE NG N NE LG LN LE ").upper()
    self.alignment = alignment_data.get(alignment_input.upper(), None)
    print()

    if self.alignment is None:
        random_alignment_code = random.choice(list(alignment_data.keys()))
        self.alignment = alignment_data[random_alignment_code].lower()
        mini_alignment = random_alignment_code.lower()
    else:
        self.alignment = self.alignment.lower()
        mini_alignment = alignment_input.lower()

    return self.alignment, mini_alignment.lower()

def randomize_deity(self, random_flag=True, deity_choice=None):
    if random_flag:
        self.deity_choice = random.choice(self.deity[self.alignment])

    try:
        found = None
        # Search through all alignments and deities
        for alignment, deity_list in self.deity.items():
            for deity in deity_list:
                if deity_choice in deity.get("Name", []):
                    found = deity
                    break
            if found:
                break

        if not found:
            self.deity_choice = random.choice(self.deity[self.alignment])
        else:
            self.deity_choice = found

    except:
        self.deity_choice = random.choice(self.deity[self.alignment])

    return self.deity_choice
