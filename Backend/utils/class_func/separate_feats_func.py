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

   # E-Kat feats are held OUT of the four specialised buckets and handed back with the general
   # remainder, so they always render under the ordinary "Feats" heading.
   #
   # They used to be swept up by the front-popping like anything else, and after the feat-tax
   # reorder six of a character's ten could land in `class_feats` -- rendering as *Class Bonus
   # Feats* and occupying a slot the story/flaw/flavour/class budgets are meant to pay for. An
   # E-Kat feat is an ordinary feat bought with an ordinary feat slot; it is not a story feat.
   #
   # The bucket SIZES are untouched: the four `take()` calls still ask for exactly what the house
   # formula grants, they just draw from a pool with the E-Kat picks removed. Taking them out of
   # the requested counts instead would silently shrink the story/flaw/flavour budgets.
   #
   # The luck-bought feats ("a feat for -5 luck") are held back for exactly the same reason, and it
   # is even starker for them: on a low-level or heavily-subsystemed character the four buckets can
   # drain the ENTIRE general list, so a character that sold luck for two feats ended up with the
   # feats rendering as story feats and an empty "(-5 Luck)" ledger. The sale bought ordinary feats;
   # they must reach the ordinary heading, and the negative-luck ledger names them by identity.
   protected = {str(n).lower() for n in (getattr(character, 'e_kat_feats_chosen', None) or [])}
   protected |= {str(n).lower() for n in (getattr(character, 'luck_bought_feats', None) or [])}
   # SELECTION MODE: pinned feats are held back the same way, for the same reason -- a feat the
   # player asked for by name is an ordinary feat, not a story or flaw feat. Empty without pins.
   pinned = {str(n).lower() for n in (getattr(character, 'pinned_feats_chosen', None) or [])}
   protected |= pinned
   held_back = []
   if protected:
      remaining = []
      for f in feats:
         (held_back if str(f).lower() in protected else remaining).append(f)
      feats[:] = remaining          # in place: callers rebind, but the list object is shared

   story_feats  = take(character.story_feat_amount)
   flaw_feats   = take(character.flaw_feat_amount)
   flavor_feats = take(character.flavor_feat_amount)
   # Pins that do not fit the ordinary track spill into the class bonus slots, ahead of the
   # random picks those slots would have taken: a fighter who pinned eight combat feats has the
   # slots for them, and the count guarantee would otherwise trim the overflow. The ordinary track
   # holds normal_feat_amount rows, so that is where the spill starts.
   spill = []
   if pinned:
      kept_pins = [f for f in held_back if str(f).lower() in pinned]
      room = max(int(getattr(character, 'normal_feat_amount', 0) or 0), 0)
      spill = kept_pins[room:][:max(character.class_feats_amount, 0)]
      for f in spill:
         held_back.remove(f)
   class_feats  = spill + take(character.class_feats_amount - len(spill))

   print("character.class_feats_amount: ", character.class_feats_amount)

   feats.extend(held_back)
   return story_feats, flaw_feats, flavor_feats, class_feats, feats