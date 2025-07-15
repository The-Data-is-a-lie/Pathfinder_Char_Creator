# add all feats to character.chooseable (for feat taxing purposes)
def add_feats_to_chooseable(character, *feat_lists):
    for feats in feat_lists:
        for feat in feats:
            if feat not in character.chooseable: # set -> add
                character.chooseable.add(feat.lower())
                character.chooseable.add(feat.upper())
                character.chooseable.add(feat.title())
                character.chooseable.add(feat)

    return character.chooseable