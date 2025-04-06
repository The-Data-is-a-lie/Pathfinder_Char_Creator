import random
from utils import data

def choose_alignment(self, alignments, alignment_input):
    alignment_data = getattr(data,alignments)
    # alignment_input = input("If you want to choose an alignment, type: CG CN CE NG N NE LG LN LE ").upper()
    self.alignment = alignment_data.get(alignment_input, None)

    if self.alignment is None:
        random_alignment_code = random.choice(list(alignment_data.keys()))
        self.alignment = alignment_data[random_alignment_code].lower()
    else:
        self.alignment = self.alignment.lower()

    return self.alignment

def randomize_deity(self):
    self.deity_choice = random.choice(list(self.deity[self.alignment]))
    return self.deity_choice

# def print_all_deities(self):
#     all_deities = []

#     for alignment, deities in self.deity.items():
#         # Iterate through each deity in the list for the alignment
#         for deity in deities:
#             if isinstance(deity, dict) and "Name" in deity:
#                 # Add all names from the "Name" list
#                 all_deities.extend(deity["Name"])
#             elif isinstance(deity, str):
#                 # If the deity is a string, add it directly
#                 all_deities.append(deity)

#     # Remove duplicates and sort the list for consistent output
#     unique_deities = sorted(set(all_deities))
#     print("All Unique Deities:", unique_deities)
#     return unique_deities