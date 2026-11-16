def druidic_flag_assigner(character):
    character.druidic_flag = any(c['name'] == 'druid' for c in character.classes)

def human_flag_assigner(character):
    character.human_flag = False
    if character.chosen_race.lower() == 'human':
        character.feat_amounts += 1
        # ...and the general track is one row longer. Without this the extra feat was DRAWN and
        # then trimmed straight back off: the track's count guarantee holds the list to
        # normal_feat_amount exactly, so a human ended up with the same feats as anyone else
        # (measured 2026-11-16: a human and an elf rogue 20 both had 12 general feats).
        character.normal_feat_amount += 1
        character.human_flag = True