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

def _region_affinity_deity(deity_pool, region):
    """Pick a region-appropriate deity from `deity_pool` (the alignment-valid list) when the
    character's homeland has a documented faith affinity (data.region_deity_affinity), else None.
    Biases ~70% toward canon so setting flavor shows through without making every NPC predictable;
    returns None (so the caller's normal random choice runs) when the region has no affinity or none
    of its faiths are valid for the rolled alignment."""
    region_key = str(region or "").strip().lower()
    faiths = getattr(data, "region_deity_affinity", {}).get(region_key)
    if not faiths:
        return None
    wanted = {f.strip().lower() for f in faiths}
    matches = [d for d in deity_pool
               if any(str(n).strip().lower() in wanted for n in d.get("Name", []))]
    if matches and random.random() < 0.70:
        return random.choice(matches)
    return None


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
            pool = self.deity[self.alignment]
            self.deity_choice = (_region_affinity_deity(pool, getattr(self, "region", None))
                                 or random.choice(pool))
        else:
            self.deity_choice = found

    except:
        self.deity_choice = random.choice(self.deity[self.alignment])

    return self.deity_choice
