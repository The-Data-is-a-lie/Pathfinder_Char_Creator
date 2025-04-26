def separate_feats_func(character, feats):
   # Instantiate empty lists for story and flaw feats
   story_feats = []
   flaw_feats = []
   flavor_feats = []
   class_feats = []

   i = 0

   for i in range(character.story_feat_amount):
      story_feat = feats[i]
      story_feats.append(story_feat)
      feats.pop(i)
      i -= 1 

   for i in range(character.flaw_feat_amount):
      flaw_feat = feats[i]
      flaw_feats.append(flaw_feat)
      feats.pop(i)
      i -= 1 

   for i in range(character.flavor_feat_amount):
      flavor_feat = feats[i]
      flavor_feats.append(flavor_feat)
      feats.pop(i)
      i -= 1

   for i in range(character.class_feats_amount):
      class_feat = feats[i]
      class_feats.append(class_feat)
      feats.pop(i)
      i -= 1

   print("character.class_feats_amount: ", character.class_feats_amount)

   return story_feats, flaw_feats, flavor_feats, class_feats, feats