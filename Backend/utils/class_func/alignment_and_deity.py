import random
from utils import data

def choose_alignment(self, alignments, alignment_input):
    alignment_data = getattr(data,alignments)
    # alignment_input = input("If you want to choose an alignment, type: CG CN CE NG N NE LG LN LE ").upper()
    self.alignment = alignment_data.get(alignment_input, None)

    if self.alignment is None:
        print("Invalid alignment input. Randomizing alignment:")
        random_alignment_code = random.choice(list(alignment_data.keys()))
        print(alignment_data)
        print(random_alignment_code)
        self.alignment = alignment_data[random_alignment_code].lower()

        print(self.alignment)
    else:
        self.alignment = self.alignment.lower()

    return self.alignment





def randomize_deity(self):
    self.deity_choice = random.choice(list(self.deity[self.alignment]))
    return self.deity_choice