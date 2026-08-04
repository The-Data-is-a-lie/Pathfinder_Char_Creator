# 02 — Does pf1 accept patched numbers on a cloned `pf-content` Actor?

Type: prototype
Status: resolved (2026-08-03) — recipe below; two claims flagged for slice 7's first live run
Blocked by: —
Map: [Companion sheets](../map.md)

## Answer — clone the body, delete its progression, drive the class item at HD

pf1 does **not** recompute over everything, and it does not honour everything either. The split is
exact and it is visible in the schema rather than a matter of taste: `systems/pf1/template.json`
declares what is **stored**, and anything not in it is rebuilt from the change system every
`prepareDerivedData`. Patch a stored field and it sticks; patch a derived total and it is gone on the
next render.

| stored — patch these | derived — never patch |
|---|---|
| `abilities.*.value` | `attributes.hp.max` / `hp.value` |
| `attributes.naturalAC` | `attributes.savingThrows.*.total` |
| `attributes.savingThrows.*.base` | `attributes.bab.total` |
| `attributes.speed.*.base` | `attributes.ac.{normal,touch,flatFooted}.total` |
| `attributes.hp.base` (seeds `hp.max`, `actor-pf.mjs:1983`) | `attributes.cmb`/`cmd` totals, `init.total` |
| `traits.size`, `skills.*.rank` | anything else with a `.total` |

`hp.offset` is **not** a max modifier — `hp.value = hp.max + hp.offset` (`actor-pf.mjs:1448`), so it
is damage tracking. HP, BAB and saves all reach the sheet through class items
(`base-character.mjs::_prepareTypeChanges` → `_calculateMaxHealth`), which is what makes the recipe
below work at all.

### What the clone actually is

Dumped all 205 `pf-companions` Actors (read from a copy of the pack, so Foundry never had to close).
The pack is perfectly uniform, and three of its properties decide the design:

1. **Every Actor is type `character`, not `npc`.** §8 **D1** assumed `npc`; that is right for the D3
   *bare* fallback and wrong for the clone path. This ticket amends D1's actor-type half: a cloned
   body stays a `character`. (It also means the world's `healthConfig` **character** rules apply to
   it — which is what we want, since that setting is where the house maximised-HP rule already
   lives.)
2. **Every Actor carries an `Animal Companion` class item** — `subType: base`, `hd: 8`, `bab: "med"`,
   Fort/Ref `high`, Will `low`, `level: 1`. 35 of them carry a second, *level 0* class item naming
   the creature type (Vermin ×22, Plant ×8, Magical Beast ×4, Animal ×1); those are markers with
   empty progressions and contribute nothing.
3. **Exactly two items on every Actor carry Changes**, and all three formulas are identical
   pack-wide:

   | item | change |
   |---|---|
   | STR/DEX Bonus | `floor(@class.level / 3)` → `str`, and again → `dex` |
   | Natural Armor Bonus | `floor(@class.level / 3) * 2` → `nac` |

### The double-count, and why "let pf1 derive it" is not the alternative

Those two items are **the companion table**, re-applied — and the backend already applies it
(`companion_stats.py::_abilities` adds the chassis row's `str/dex bonus` to both Str and Dex, and
`_natural_armor` folds in its `natural armor bonus`). Clone, set a class level, then patch our
abilities over it, and the table lands **twice**. This is [ticket 04](04-size-change-double-count.md)'s
bug on the far side of the wire, and it is why D2's "backend owns every number" has to be enforced by
*deleting* something rather than by writing carefully.

Handing the job to pf1 instead is not an option, because **its formula is wrong**. `floor(level / 3)`
bumps at 3rd, 6th, 9th…; PF1e's animal-companion table bumps at 4th, 7th, 10th, 13th, 16th and 19th.
The two agree only where `level % 3 != 0`; at 3rd, 6th, 9th, 12th, 15th and 18th the clone is a full
point of Str **and** Dex and two points of natural armour ahead of the rules. So the choice is not
"our numbers or pf1's numbers" — it is our numbers or wrong numbers.

### The recipe

Per entry in `bonded_creatures` with `species != null`:

1. **Find the body** by `species` in `pf-companions` / `pf-familiars` / `pf-eidolon-forms`. A miss is
   the D3 degrade: build a bare Actor from payload numbers with no clone to fight — which, given
   everything above, is *more* correct than a patched clone, not less. It just has no art and no
   natural attacks.
2. **Create it** from `source.toObject()` into the Random Characters folder, `type` untouched, name
   composed module-side per D10.
3. **Delete `STR/DEX Bonus` and `Natural Armor Bonus`.** Match by name is safe — they are the only
   change-bearing items in the pack, on all 205. Keep Link, Share Spells, Bonus Tricks and Animal
   Companion Feats: they are rules text and carry no changes.
4. **Set the `Animal Companion` class item's `level` to the creature's HD count** — `stats.hd`, the
   chassis row — **not to `effective_level`**. This is the single easiest thing to get wrong. At
   effective level 11 a companion has **9** HD; pf1 derives HD, BAB and both save progressions from
   this one number, and the chassis table it is being fed is the same table pf1 implements, so they
   agree by construction: `med` BAB at 9 = +6 = chassis BAB; `high` save at 9 = 2 + 4 = +6 = chassis
   Fort/Ref; `low` = 3 = chassis Will. HP likewise falls out at `hd × 8 + Con × HD` under the world's
   maximised health config, which is the house rule the backend already used.
5. **Write the stored fields** from `stats`: `abilities.*.value` (the merged, advanced scores),
   `naturalAC`, `traits.size`, `speed.*.base`, `skills.*.rank` (the pack ships none, so nothing
   collides).
6. **Do not** patch attack damage. Natural attacks use `sizeRoll(1, 6, @size)` and scale off
   `traits.size` on their own — step 5 already did it. `stats.attacks[]` is for the web sheet, which
   has no such engine.
7. **Do not** re-apply `stats.size_change` (D11) and do not attach the chassis `feats` blind — check
   for an existing item of the same name first, the same guard `every_feat.json` provides on the PC.

Saves are the one place both halves are live: `savingThrows.*.base` is a stored seed **and** the
class item adds its progression on top. Leave `base` at 0 (as the pack ships it) and let the class
item own the number; writing both is a third double-count waiting to happen.

### Still wants a live run (slice 7's first import, not a blocker)

- That a sheet re-render after `Actor.create` + `update` shows the patched abilities and naturalAC
  unchanged. The schema says it must; nobody has watched it happen.
- That the world's `healthConfig` character rules maximise a cloned companion's HD the same way they
  maximise a PC's, so step 4's HP lands on the payload's number rather than near it.

*Rejected:* patching `hp.max` / save and BAB totals directly (they are rebuilt every render);
expressing the numbers as Changes on a carrier item (works, but re-implements what the class item
already does correctly, and leaves the wrong-formula items in place); converting the clone to `npc`
(loses nothing but gains nothing, and the character health config is the one we want).

## Question

§8 **D2** says the backend computes every number and the module **clones the `pf-content` Actor for
the body, then patches the payload's numbers over it** — Foundry supplies identity (art, natural
attacks, senses, special qualities), never math.

That decision was reached *without* prototyping. [Ticket 01 of the closed map](../../companions/issues/01-rendering-model.md)
framed exactly this experiment and then declared it *"the wrong question"*, because the web sheet has
no game system and therefore the backend had to own the numbers regardless. That reasoning is sound
for the **spec**. It does not survive contact with **slice 7**, which has to actually write the
patch.

The unknown: pf1 recomputes derived data from ability scores, size, class levels and items on every
update. Patch `hp`/`ac`/`saves`/`bab` onto a cloned `pf-companions` Actor and pf1 may honour them,
silently recompute over them, or produce a sheet where the header and the tabs disagree.

Prototype it — hand-build one companion Actor from a real generated entry and find out:

- Which fields **stick** after `actor.update()` and a sheet re-render, and which pf1 overwrites from
  its own derivation.
- Whether the numbers are better expressed as **Changes** (the mechanism the module already uses
  everywhere else — see the buff/conditional pipeline) rather than as raw attribute writes.
- Whether the **cloned body's own** natural attacks and abilities double up with anything the payload
  carries, and what happens to the clone's ability scores when ours differ.
- Whether the chassis row's **`feats`** (already resolved by `animal_feats()`,
  `Backend/utils/class_func/animal_companions.py:365-389`) attach as feat items, and whether the
  clone already has some of them — the double-apply problem the every_feat guard exists for on the PC.
- What the **D3 fallback** actually looks like in practice: a bare `npc` built from payload numbers
  alone, with no clone to fight, may be *more* correct than a patched clone. If so, say so — that
  would be an amendment to D2's rendering half, not to its "backend owns the numbers" half.

Answer with a working recipe the module can implement, not a verdict. `Actor` type is `npc` per D1
(`systems/pf1/template.json` registers only `character, npc, vehicle, haunt, trap`).

Note: `pf1-statblock-converter` was already evaluated and set aside by the closed map — its parser is
minified and UI-driven, a manual fallback only. Do not re-evaluate it.
