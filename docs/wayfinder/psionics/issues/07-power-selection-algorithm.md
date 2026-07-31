# 07 — How are powers actually picked?

Type: grilling
Status: resolved
Blocked by: 05
Map: [Psionics](../map.md)

## Question

Counts alone do not make a manifester. Something has to choose *which* powers, legally and in a way
that reads as a coherent build.

The repo has two precedents worth stealing from:

- `Backend/utils/class_func/spells.py::spells_known_selection` — rolls names per spell level into
  `spell_list_choose_from`.
- `Backend/utils/class_func/path_of_war.py` — the more sophisticated one: it specialises into 2–3
  disciplines, then picks **prerequisite-legally** via `_constrained_pick`, weighting toward higher
  levels and respecting same-discipline prerequisite counts.

Psionics needs the PoW-shaped version, because the psion's identity *is* its discipline: a discipline
choice unlocks a restricted power list on top of the general one, and the other classes have their
own narrower lists.

Decide: how discipline choice constrains the pool, whether classes specialise the way initiators do,
how max power level gates selection (manifester level based), and how strictly prerequisites are
enforced. Say what happens for the classes that manifest little or not at all.

## Answer

**The Path of War shape, minus the prerequisite machinery.** In `Backend/utils/class_func/psionics.py`:

```
1. max_power_level ← the class's own table at manifester level
2. legal pool      ← psionic_power_lists.json[<class>]['levels'][0..max]
3. psion           → pick its discipline (rules-mandated, sourced by ticket 05)
   every other class → soft bias toward 2–3 disciplines
4. per power level, pick powers_known_list[level] names,
   weighted toward the highest levels available
```

**The prerequisite question dissolved.** Inspecting `psionic_powers.json` shows power records carry
`name / discipline / level / level_by_class / power points / augment / text` and friends — but **no
prerequisites field**. Psionic powers, unlike Path of War maneuvers, have no prerequisite graph. So
`_constrained_pick`'s same-discipline prerequisite counting has no analogue and is not ported; what
*is* ported is its level-weighting and its specialisation behaviour.

**Discipline bias for every class, not just the psion.** The psion's is rules-mandated — its
discipline *is* its identity. The other classes have no such rule, so the bias is soft: pick 2–3
disciplines and weight toward them without excluding anything legal. This is a deliberate
build-quality choice rather than a rules one, and it is the same reason initiators specialise into
2–3 disciplines in `path_of_war.py` — a spread of unrelated powers reads as a grab bag, not a
character. Rejected the stricter alternative (only the psion specialises) as rules-faithful but
producing scattered builds, and the simpler one (straight port of `spells_known_selection`) as
giving up the coherence that makes §1's output good.

**Gating is by class list and power level only.** Each class draws from its *own* list in
`psionic_power_lists.json` — cryptic, dread, highlord, marksman, psion/wilder, psychic warrior,
tactician, vitalist, voyager. The psion's discipline unlocks that discipline's powers on top of the
general list. `max_power_level` comes from the class's scraped table at manifester level, so nothing
above it is ever offered.

**The classes that manifest little or not at all.** This is where "manifester" splits three ways:

- **Full manifesters** (9 classes) run the algorithm above.
- **Aegis** has `pp_per_day` but **no `powers_known` column** — it spends power points on its astral
  suit rather than on powers. It gets no power selection at all; its selection is customization
  points, which is [ticket 08](08-bespoke-subsystems.md)'s problem.
- **Soulknife** has **neither power points nor powers known**. It never enters this module. Its
  entire resource story is the mind blade and blade skills, again ticket 08.

Three of the twelve power lists the scrape captured — Gambler, Gifted Blade, Sighted Seeker — belong
to out-of-scope classes and archetypes. They stay in the data because in-scope powers' `Level:` lines
cite them, but no in-scope class selects from them.
