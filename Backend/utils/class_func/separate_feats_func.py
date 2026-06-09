def separate_feats_func(character, feats):
   # Pull each feat bucket off the FRONT of the list, bounded by what's actually available.
   # The old version did `feats[i]; feats.pop(i); i -= 1` in range() loops: the `i -= 1` is a
   # no-op inside a `for`, which caused an every-other selection bug AND a "list index out of
   # range" crash whenever fewer feats were produced than requested (e.g. the curated path for a
   # high-level Fighter/Brawler). Front-popping is bounded, takes the correct count, and degrades
   # gracefully (later buckets just get fewer) instead of crashing.
   def take(n):
      out = []
      for _ in range(max(n, 0)):
         if not feats:
            break
         out.append(feats.pop(0))
      return out

   story_feats  = take(character.story_feat_amount)
   flaw_feats   = take(character.flaw_feat_amount)
   flavor_feats = take(character.flavor_feat_amount)
   class_feats  = take(character.class_feats_amount)

   print("character.class_feats_amount: ", character.class_feats_amount)

   return story_feats, flaw_feats, flavor_feats, class_feats, feats