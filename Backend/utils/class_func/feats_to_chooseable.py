# add all feats to character.chooseable (for feat taxing purposes)
def add_feats_to_chooseable(character, *feat_lists):
    for feats in feat_lists:
        for feat in feats:
            # strip: some class JSON lists carry stray whitespace (e.g. ranger " Trick Riding"),
            # which would otherwise never match the lowercase prereq / re-pick checks
            feat = str(feat).strip()
            if feat and feat not in character.chooseable: # set -> add
                character.chooseable.add(feat.lower())
                character.chooseable.add(feat.upper())
                character.chooseable.add(feat.title())
                character.chooseable.add(feat)

    return character.chooseable