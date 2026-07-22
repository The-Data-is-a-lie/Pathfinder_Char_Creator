# Why `@spheres.cl.total` is 0 and how to make it nonzero

## Question

Generated NPCs (and some real PCs) show `@spheres.cl.total` as `0` in FoundryVTT, even though they
have Spheres of Power magic talents. How do we get pf1spheres to compute a nonzero Sphere Caster
Level?

**One-paragraph answer:** `system.spheres.cl.total` is derived by the **pf1spheres** module
entirely from **class items flagged `flags.pf1spheres.casterProgression`** (High/Mid/Low) — it is
`min(HD, sum(progressionFormula[prog] * classLevel) + modCap)`. A talent-based "dabbler" (Basic
Magic Training, no real spherecasting class) has no such class item, so the base is `0` and the
formula caps at `0` regardless of HD. This repo's generator already works around that: it *stamps a
literal Change* (`target: "spherecl", formula: "1"`) onto the synthesized "Spheres Casting" summary
feat (`Backend/…/modify-abilities.js` `applySpheresFlags()`, called at the end of `processSpheres`'s
consumer chain), which is a first-class, GM-facing pf1spheres Change target — not a hack — and
*also* pre-bakes the literal `1` into every talent-conditional rider via `subSpheres()` so those
formulas don't depend on the actor's derived value at all. If a specific generated actor still shows
`0`, the most likely causes are (a) it's a **Might-only** dabbler (no magic talents → `castingAbility`
is never set → no stamped Change is added, and `0` is *correct* since Might uses BAB, not CL), or
(b) it's an **older actor** created before this stamped-Change code shipped, or (c) it's the
**palette/template actor**, which deliberately keeps the native `@spheres.cl.total` token unresolved
so it scales correctly once dropped onto a real spherecasting PC.

## UPDATE (implemented 2026-07-20) — dabbler CL now scales, tier-accurately

The workaround below (option 1) shipped, then was **upgraded**: `subSpheres()` /
`applySpheresFlags()` no longer bake the literal `1`. They now substitute `@spheres.cl.total` with a
**live, tier-accurate, multiclass-summed** sphere caster level built from the NPC's real caster classes
(`sphereCLExpr()` in `modify-abilities.js`):

```
max( Σ over caster spellbooks of  {high: @classes.<tag>.level,
                                    mid ('med'): floor(3·level/4),
                                    low: floor(level/2)} , 1)
```

Rationale + why this is safe (see `.claude/plans/…` / the grilling session that produced it):
- **Power/magic talents are only ever assigned to real casters** (`spheres.py:183-186`: non-casters get
  `p=0.0` → Might only), and every Power-eligible class is a real Vancian caster with a pf1 spellbook —
  so `@classes.<tag>.level` / the spellbook is always present for a Power-bearing NPC.
- Uses **class level**, not the pf1 spellbook CL, so a low caster contributes before it gains spells
  (paladin 3 → floor(3/2)=1) and the numbers match the campaign's ½/¾/full model exactly (raw
  `@spells.*.cl.total` would run hotter — mid = full level, low = level−3).
- Caster levels **stack** across classes (Spheres RAW); summing also makes the primary/secondary slot
  ordering irrelevant. Caster classes are now **capped at 3** at generation (`util.py select_classes`,
  `_is_caster`) so pf1's 3-spellbook limit never drops a caster book.
- **Option 4 below is only *partly* wrong-premised:** its "dabblers have no spellbook" claim is false for
  Power-bearing NPCs (they do), so `@spells.*.cl.total` *would* populate. The real reason we did **not**
  switch the authored token to `@spells.*` is the **palette actor** — a class-less template for real
  pf1spheres PCs with no Vancian spellbook. Keeping `@spheres.cl.total` in the authored data (+ palette)
  and doing the swap **only in the per-NPC substitution** preserves both populations.
- **Deferred:** kineticist / spell-point classes with no pf1 spellbook contribute no term → floor to 1.

## Why it's 0 (the pf1spheres derivation mechanism)

Source: pf1spheres v-current TypeScript (recovered from
`pf1spheres.js.map`'s `sourcesContent`, since `pf1spheres.js` itself is a single minified line).

1. **Base data reset.** On every non-`"basic"` actor, `onActorBasePreparation` resets
   `actor.system.spheres = getBlankSphereData()` — `cl.base`, `cl.modCap`, `cl.total` all start at
   `0`. (`src/module/actor.ts:31-71`, blank template at `getBlankSphereData` `actor.ts:152-193`.)

2. **Which class items count.** `filterClasses` keeps only items where
   `item.type === "class" && Boolean(item.flags.pf1spheres?.casterProgression)`
   (`actor.ts:90-91`). A class item with no `flags.pf1spheres.casterProgression` contributes
   **nothing**, no matter its level or its native pf1 `spellcastingType`.

3. **Per-class CL contribution.** For each surviving class item, `getItemLevelData` computes
   ```
   rawLevel = progressionFormula[casterProgression] * item.system.level
   clPart   = floor(rawLevel)          // or fractional, if "useFractionalBaseBonuses" is on
   ```
   with `progressionFormula = { low: 0.5, mid: 0.75, high: 1 }` (`actor.ts:97-113`;
   `progressionFormula` defined in `config.ts:32-36`). This is the High/Mid/Low-caster progression
   from Spheres of Power, but it is driven by the module's **own flag**, not the pf1 system's
   built-in `spellcastingType`/caster-progression fields.

4. **Sum → base.** `casterLevel` accumulates `clPart` across all flagged class items;
   `sphereData.cl.base = useFractionalBAB ? Math.floor(casterLevel) : casterLevel` (`actor.ts:53-71`).
   With no flagged class item, this sum is `0`.

5. **Base → total, via a Change.** Every actor unconditionally gets a default Change
   (`onAddDefaultChanges` → `getDefaultChanges`, `changes.ts:213-220`):
   ```
   formula: "min(@attributes.hd.total, @spheres.cl.base + @spheres.cl.modCap)"
   target:  "~spherecl"   →  system.spheres.cl.total   (changes.ts:110-112)
   modifier: "untyped"
   ```
   So `cl.total = min(HD, cl.base + cl.modCap)`. With `cl.base = 0` and no other source of
   `modCap` (a Change with bonus-type `sphereCLCap`), `cl.total = min(HD, 0) = 0` — this holds
   **regardless of how high the actor's HD/level is**.

**Exact precondition for a nonzero `cl.total` "for real":** at least one `type: "class"` item on the
actor with `flags.pf1spheres.casterProgression` set to `"low" | "mid" | "high"` and `system.level >
0`. In the Foundry UI, a GM sets this via a dropdown pf1spheres injects into every class item sheet:
`onItemSheetRender`, `item.type === "class"` branch, renders the `class-progression` partial
(`src/module/item-sheet.ts:54-58`).

## Options to make it nonzero (ranked)

### 1. (Current design, recommended) Bake a literal into riders + stamp a `spherecl` Change — feed it a real backend CL instead of the hardcoded `1`

**What it is today:** two mechanisms, both already in `modify-abilities.js`, both bypassing the
derivation above entirely rather than trying to satisfy it:
- `makeSubSpheres()` / `subSpheres()` — a string substitution run over every talent-conditional
  rider/formula before it's written to the sheet: `.replaceAll('@spheres.cl.total', '1')` and
  `@spheres.cam/@spheres.pam → @abilities.<mod>.mod` (`modify-abilities.js:2851-2856`, comment block
  at `2837-2840`). Conditionals on the Destructive Blast attack (`2914`, `2923`) and every sphere
  talent conditional (`addSphereTalentConditionals`, `2935+`, called via `subSpheres(rider)` at
  `~2975-2981`) go through this, so their *formulas* never reference `@spheres.cl.total` at all —
  they already contain the concrete number.
- `applySpheresFlags(cam, pam)` (`modify-abilities.js:2860-2882`), called at `3176`: if the NPC has
  any `magic_talent_items`, it (a) sets `flags.pf1spheres.castingAbility` / `.practitionerAbility` on
  the actor (drives `@spheres.cam`/`@spheres.pam` for anything that *does* read live roll data, e.g.
  the sheet's own MSB/DC displays), and (b) pushes a Change onto the synthesized "Spheres Casting"
  summary feat: `{ formula: '1', target: 'spherecl', type: 'untyped', operator: 'add', ... }`. Since
  `spherecl` (no `~`) is the **general, GM-selectable** "Caster Level" buff target
  (`PF1CONFIG_EXTRA.buffTargets.spherecl`, `src/module/config-extra.ts:38-42`), and its change-flat
  target list is `["system.spheres.cl.total", ...every magicSphere.<sphere>.total]`
  (`config.ts:100-106`), this Change **adds `1` directly to `system.spheres.cl.total`** — it does not
  go through the HD-capped `cl.base + cl.modCap` formula at all, so it doesn't need a flagged class.
  So *if* the pf1spheres module is active and this feat item is on the sheet and enabled, the actor's
  live `@spheres.cl.total` should already read `1`, not `0`.

**Tradeoffs:**
- Cheap, zero-dependency, works for any actor type (character or npc), doesn't require touching real
  pf1 or pf1spheres class configuration.
- Only fires for **magic** dabblers (`hasMagic` gate at `2861-2863`); a Might-only dabbler correctly
  gets no stamped Change and no CL — that's expected, Might uses `@attributes.bab.total` /
  `@spheres.pam`, not CL, so `0` there is not a bug.
- **Only helps generated NPCs**, not real PCs who build up spheres organically in Foundry (a PC's
  sheet-added talents don't run through this backend/module pipeline) and not the **palette actor**
  (see option 4).
- Currently hardcodes `1` everywhere. `Backend/utils/class_func/spheres.py` computes a real per-sphere
  Might-vs-Power system and a casting tradition/mana pool (`_casting_level`, `_system_for_sphere`,
  `_mana_pool`, `spheres.py:175-186, ~309`) but **does not currently compute or export a numeric
  dabbler caster level** — there is no "effective CL" field in the backend payload today (confirmed:
  no `caster_level`/`effective_cl`/similar key produced by `spheres.py` or consumed by
  `build_talent_conditionals.py`). The `1` is a JS-side literal, not something fed from the backend.
  **Improvement, if desired:** compute a small real number backend-side (e.g. Basic Magic Training's
  RAW is CL = 1/2 class level, min 1, or this campaign could houserule CL = character level / 2
  rounded down, min 1) and export it as e.g. `sphere_effective_cl`, then have `applySpheresFlags`
  read `characterData.sphere_effective_cl` instead of the literal `'1'` in both the stamped Change and
  `makeSubSpheres`. This only matters if the campaign wants dabbler CL to scale with character level
  instead of staying pinned at 1 forever.
- If a generated actor is *still* showing `0` despite this: check (a) the pf1spheres module is
  enabled in that world, (b) the actor was generated **after** this code shipped (module JS is loaded
  once at Foundry startup and old actors bake their items at creation time — per this repo's own
  gotcha, a stale actor won't retroactively gain the Change; regenerate it), (c) the "Spheres Casting"
  feat item wasn't stripped/disabled, (d) it's the palette actor (see option 4, by design).

### 2. Give the actor a real spherecasting class + progression flag pf1spheres recognizes

**What it requires:** an actual class item (`type: "class"`) on the actor with
`flags.pf1spheres.casterProgression` = `"low"|"mid"|"high"` and levels in it — e.g. a compendium
Incanter/Soul Weaver/Fey Adept (high), Symbiat/Eliciter (mid), or Mageknight/Armorist (low) class, or
any homebrew class a GM manually flags via the class-progression dropdown pf1spheres adds to every
class item sheet (`item-sheet.ts:54-58`).

**Tradeoffs:**
- The "correct"/intended way per pf1spheres' own design — `cl.total` then scales properly with level,
  interacts correctly with `modCap`/HD-capping, multiclassing, energy drain, etc., with zero
  workarounds.
- **Out of scope for this generator today**: per `docs/feature_spec_todo.md` and the
  `spheres-of-power` skill, real spherecasting base classes are explicitly **not yet implemented** —
  the generator only does non-caster "dabbling" via Basic Magic Training / Extra Magic Talent. Adding
  this is a much bigger feature (full talent-count-per-level tables, spell-point-per-level tables,
  class selection into the random class pool) than "fix the CL fields."
- Fixes **real PCs** who pick an actual spherecasting class in Foundry normally, and would fix the
  **palette actor** if it were given a dummy caster class — but that's not how the palette is
  designed (see option 4).

### 3. Add a Change targeting `spherecl` (or a specific `spherecl<Sphere>`) directly — the manual override path

**What it requires:** any item (feat, buff, trait — doesn't need to be a class) with an embedded
Change whose `target` is `spherecl` (general, hits `cl.total` **and every magic sphere's** `.total`)
or `spherecl<Sphere>` (e.g. `sphereclDestruction`, hits just that sphere's `.total`) and a bonus
`type` that is **not** `sphereCLCap`. This is a real, GM-facing option in the Change editor
(`PF1CONFIG_EXTRA.buffTargets.spherecl`, `config-extra.ts:38-42`; per-sphere targets registered in
`registerChanges`, `config.ts:28-38`), and it's exactly what option 1's `applySpheresFlags` already
does programmatically. Using bonus type `sphereCLCap` instead routes the value into `cl.modCap`,
which **is** HD-capped via the base formula (`min(HD, base+modCap)`) — useful if you want a bonus
that respects HD scaling; a plain type (untyped/enhancement/etc.) bypasses the cap entirely.

**Tradeoffs:**
- Identical mechanism to option 1, just phrased as "you, a GM, can do this by hand in Foundry" rather
  than "the generator already does this automatically." Good escape hatch for **fixing a real PC or
  the palette actor by hand** without waiting on a class-progression setup, and good for QA
  (temporarily add a Change to sanity-check that `@spheres.cl.total` flows correctly downstream
  before wiring up option 2). Same drawback as option 1: bypasses the "real" derivation, so it won't
  automatically scale with level unless someone updates the Change's formula/value over time.

### 4. Why `@spells.primary.cl.total` is NOT a fix

Verified in the pf1 system source (`pf1.js.map` → `module/documents/actor/actor-pf.mjs`, function
computing each spellbook's CL, lines ~737-823):

- For a `type: "character"` actor (which is what this generator exports — confirmed
  `"type": "character"` at
  `.../pf1e_random_char_generator/templates/export/export_to_foundryVTT.json:4`), the NPC-only
  manual-entry path (`if (this.type === "npc") { classLevelTotal += book.cl.base ... }`, line
  744-750) **does not run at all**. A character-type actor's spellbook CL is built from:
  - `book.class` must be set to a class tag, and that class must exist on the actor
    (`this.classes[book.class]`) — `rollData.class = rollData.classes?.[book.class]`, then
    `value = rollData.class?.unlevel` is added to the total (lines 759-765). No assigned class → `0`.
  - Before any of that, the caster-type table lookup must succeed at all — if
    `castsPerDayTables` is falsy (i.e. the spellbook has no valid caster type / prep mode
    configured), the function **errors out and returns early** (`actor-pf.mjs:900-901`), meaning the
    spellbook doesn't even finish deriving cleanly.
  - There *is* a generic Change-injection path too (`clTotal += book.cl.total ?? 0` at line 820, since
    `spellbooks.<book>.cl.total` is itself a valid pf1 buff target) — but it still requires the
    spellbook to exist and be minimally configured (ability score, prep mode, caster type) before
    that addition means anything, and even then it only affects **that one spellbook's** CL, a
    concept entirely disconnected from pf1spheres.
- **The deeper problem:** `@spells.primary.cl.total` and `@spheres.cl.total` are two unrelated
  systems' roll-data namespaces. Nothing in pf1spheres — not the DC formulas
  (`10 + floor(@spheres.cl.total/2) + @spheres.cam`), not `getHighestCl` (`actor-util.ts:66-91`), not
  the sphere-CL Change targets — ever reads `@spells.*`. Rewiring the generator's sphere-talent
  conditionals to use `@spells.primary.cl.total` instead of `@spheres.cl.total` would require standing
  up a full (fake) pf1 spellbook — ability score assignment, prep mode, caster-type table, spell
  slots per level — purely as a numeric side channel, adding an entire irrelevant subsystem to the
  sheet (a "Spells" tab with spell slots nobody uses) just to get one number, when pf1spheres already
  exposes exactly the right number (`system.spheres.cl`) unconditionally on every actor via
  `getBlankSphereData()` (`actor.ts:152-193`) with no spellbook required. It also does nothing for
  Might-side DCs (`@spheres.pam`) at all. Confirmed **not a fix** — strictly worse than options 1-3.

## Recommendation for this generator

Keep the current design (option 1) as the baseline — it already works and is the only option that
requires zero new Spheres-caster-class infrastructure. Two follow-ups worth doing:

1. **Verify in-Foundry** that a freshly generated magic dabbler actually shows `@spheres.cl.total =
   1` on the pf1spheres tab (hard-refresh Foundry per the module's own load-once caveat, then generate
   a brand-new actor — don't test against a stale one). If it's still `0` on a fresh actor, the bug is
   likely that the "Spheres Casting" feat isn't present/enabled at the time `applySpheresFlags` runs,
   or the pf1spheres module isn't active in that world — both worth a quick sheet inspection before
   assuming the derivation logic itself is at fault.
2. **Optional enhancement:** compute a real numeric dabbler CL backend-side in `spheres.py` (e.g. tied
   to character level, min 1) and export it (`sphere_effective_cl` or similar) so `applySpheresFlags`
   and `makeSubSpheres` substitute that value instead of the hardcoded `'1'` — makes dabbler magic
   scale with level instead of staying pinned at CL 1 forever. Low priority unless playtesting shows
   CL-1 dabbler magic feels flat at higher levels.

Do **not** pursue `@spells.primary.cl.total` (option 4) or building out real spherecasting classes
(option 2) just to fix this specific "why is it 0" symptom — option 2 is a legitimate future feature
but far bigger in scope than the CL question, and option 4 is a dead end.

## Sources

- **pf1spheres** (recovered TypeScript source via `pf1spheres.js.map`'s `sourcesContent`, since
  `pf1spheres.js` is minified to one line):
  - `src/module/actor.ts` — `onActorBasePreparation` (base-data reset, per-class CL sum) lines 31-87;
    `filterClasses` lines 90-91; `getItemLevelData` (progression formula lookup) lines 97-113;
    `pushLevelSources` lines 119-147; `getBlankSphereData` lines 152-193.
  - `src/module/config.ts` — `progression`/`progressionFormula` (low 0.5/mid 0.75/high 1) lines 23-36;
    `registerChanges` (per-sphere CL/BAB targets) lines 28-51; `getChangeFlatTargets` (`~spherecl` →
    `system.spheres.cl.total`, `spherecl<Sphere>` → per-sphere `.total`/`.modCap`) lines 98-164;
    `getDefaultChanges` (`min(@attributes.hd.total, @spheres.cl.base + @spheres.cl.modCap)` → target
    `~spherecl`) lines 213-240.
  - `src/module/config-extra.ts` — `PF1CONFIG_EXTRA.buffTargets` including the GM-selectable
    `spherecl` ("Caster Level") target, `bonusTypes.sphereCLCap` lines 37-93.
  - `src/module/actor-util.ts` — `getHighestCl` (reads `actor.system.spheres.cl`) lines 66-91.
  - `src/module/item-sheet.ts` — `onItemSheetRender`, class-item progression dropdown injection lines
    18-59.
  - `src/module/actor-methods.ts` — `rollMsb`/`rollConcentration`, confirms `@spheres.*` is the
    module's roll-data namespace, not `@spells.*`.
  - Minified `pf1spheres.js` — grepped tokens confirming the same paths ship in the built bundle:
    `"cl":{...}`, `cl:{default:["system.spheres.cl.total",...]}`, `spheres.cl.base`, `spheres.cl.modCap`,
    `spheres.cl.total`.
- **pf1 system** (recovered via `pf1.js.map`'s `sourcesContent`):
  - `module/documents/actor/actor-pf.mjs` lines ~700-823 — per-spellbook CL derivation: NPC-only
    manual `cl.base` (line 745-750, gated on `this.type === "npc"`), class-level contribution via
    `book.class`/`rollData.classes[book.class].unlevel` (lines 752-765), caster-type table guard
    (`castsPerDayTables`, error+return at lines 900-901), Change-injected `book.cl.total` addend
    (line 820).
  - `module/documents/actor/utils/spellbook.mjs` — `Spellbook`/`SpellbookMode` wrapper classes,
    confirms spellbook config (`spellPreparationMode`, `spellPoints`) is a prerequisite structure.
  - `apply_changes_source.txt:591-602,649-656` (this repo's own prior extraction) — confirms
    `system.attributes.spells.spellbooks.<book>.cl.total`/`.cl.bonus` are the actual pf1 Change
    targets behind the `@spells.<book>.cl.total` roll-data shortcut.
- **This repo / the generator module:**
  - `Backend/utils/class_func/spheres.py` lines 175-192 (`_casting_level`, `_system_for_sphere`),
    ~293-309 (`casting_ability_modifier`, `_mana_pool`) — confirms no numeric "effective CL" is
    currently computed or exported for dabblers.
  - `.../pf1e_random_char_generator/scripts/modify-abilities.js`:
    - lines 2837-2856 — `sphereWordToAbbrev`, `resolveSphereAbilities`, `makeSubSpheres` (the
      `@spheres.cl.total → '1'` literal substitution).
    - lines 2857-2882 — `applySpheresFlags` (stamps `castingAbility`/`practitionerAbility` flags +
      pushes the `target: "spherecl", formula: "1"` Change onto the "Spheres Casting" feat).
    - lines 2884-2935+ — `addDestructiveBlastAttack`, `addSphereTalentConditionals` (both consume
      `subSpheres` so their formulas never reference the live `@spheres.cl.total`).
    - line 3176 — `applySpheresFlags(cam, pam)` call site in the main generation flow.
    - lines 1107-1137, 1403-1429 — `applyBuffData`/`processProfessionAbilities`, the established
      pattern for filling pf1's `ChangeModel` defaults (`_id`, `formula`, `target`, `type`,
      `operator`, `priority`, `value`) that `applySpheresFlags`'s stamped Change also follows.
  - `.../pf1e_random_char_generator/templates/export/export_to_foundryVTT.json:4` — confirms the
    generator exports `"type": "character"` actors, which rules out the NPC-only `spellbooks.*.cl.base`
    manual-entry shortcut in pf1's spellbook derivation.
