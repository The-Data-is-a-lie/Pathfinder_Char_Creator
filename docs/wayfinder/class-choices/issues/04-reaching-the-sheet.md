# 04 — What does "reaches the sheet" mean, per bucket?

Type: grilling
Status: open
Blocked by: 01, 02
Map: [Class choices](../map.md)

## Question

A pick that is correct, legal, and invisible is worth nothing. **For each choice bucket, what must be
true for a player to actually see it on the Foundry sheet and on the web sheet?**

The failure has a name already. `test_house_invariants.py` guards psionic subsystem picks with this
comment:

> The failure this guards is "generated but invisible": the picks land in the class features dict
> under a bucket name only `main_test.py` knew, so a renderer showing a class's psionics had no way
> to reach them. The aegis and soulknife are the proof cases — their tab has nothing else on it, so a
> missing pointer reads as an empty tab.

That guard covers twelve psionic classes. Every other class is unguarded.

### The pipeline as it stands

- Choosers write into `character.data_dict['class features']`, and record two side-tables:
  `class feature levels` (bucket → choice → level, `_record_choice_level`, `generic_func.py:7`) and
  `class feature owners` (bucket → granting class, `record_bucket_owner`, `:14`, first writer wins so
  barbarian and skald can share `rage_powers`).
- `main_test.py:1800-1840` exports them as `class_features`, `class_feature_levels`,
  `class_feature_owners`.
- **Foundry:** `modify-abilities.js` reads all three and uses the owners to draw per-class Class
  Features dividers.
- **Web sheet:** `scripts/tabs/features.js` reads `class_features` and falls back to
  `class_ability_desc` for descriptions.

Both renderers are wired to the emitted keys, so the plumbing works. What is unverified is whether it
works **for every bucket**.

### What to establish

- **Bucket-name coverage.** Every `dict_name` passed to a chooser in `main_test.py` — `rogue_talents`,
  `rage_powers`, `arcana`, `customizations`, `decrees`, `blade_skills`, and the rest. Does each one
  have a home in both renderers, or do some land in a generic bucket that renders as an
  undifferentiated list?
- **Dividers.** `record_bucket_owner` is "first writer wins". On a barbarian/skald multiclass, both
  classes' rage powers land under one bucket owned by whichever chose first — so the divider says one
  class and the contents come from two. Is that acceptable, or does the bucket need to split?
- **Level stamps.** `class_feature_levels` is what the sheet shows as "gained at". Ticket 01 shows the
  stamp is derived from the same arithmetic as the count, so **a wrong count is a wrong stamp** — the
  user-visible half of that bug lives here.
- **Descriptions.** `chosen_set_append` degrades to a case-insensitive lookup and then to `{}`
  (`generic_func.py:248-256`), which renders as a name-only item — the exact symptom
  `audit_class_choice_descriptions.py` was written to catch upstream. Confirm the two agree on what
  counts as "has a description".
- **Tab homes.** Path of War and psionics each earned a dedicated web-sheet tab
  (`path-of-war.js`, `psionics.js`) with an `emptyState` for irrelevant characters. Whatever
  [Map: Class pool](../../class-pool/map.md) adds may need the same, and that decision is cheaper made
  here than after six occult classes are already emitting buckets nobody tabbed.

### The decision

A **rule** for what a bucket must supply to count as "reaching the sheet" — name, description, owner,
level, and a renderer that knows the bucket — stated tightly enough that ticket 05 can assert it for
every bucket rather than for twelve psionic classes.

### What "resolved" looks like

The rule, plus a bucket-by-bucket coverage table across both renderers, with anything unhomed listed
as a §11 build slice. Note that both renderers live in **other repos** — the module in
`FoundryVTT\Data\modules\pf1e_random_char_generator`, the web sheet in
`FoundryVTT\Data\Pathfinder-Character-Sheet` — so any change there is a separate PR, logged in this
repo's `changelog.md` per the central-changelog rule.
