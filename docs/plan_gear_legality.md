# Gear legality — shields, armor bands, and oversized weapons

> **This is a live multi-session plan.** To continue in a fresh session, prompt:
> `Read docs/plan_gear_legality.md and continue the gear-legality plan`. Update the checkboxes
> here as steps complete; append findings under "Found along the way".

**Origin:** [`tickets: feature/optimal-builder/11`](https://github.com/The-Data-is-a-lie/tickets/blob/main/tks/pathfinder-char-creator/feature/optimal-builder/11-shield-chooser-never-shields.md)
(escaped finding, V4 wall pass 2026-08-13). Design settled by grill on 2026-08-17; the rulings in
this file **supersede the single question ticket 11 asked**, and resolving it should point here.

**Branch:** `feat/gear-legality`, cut 2026-08-17 off `feat/eidolon`'s HEAD (`35f97a4`, shared with
`feat/mythic`). Not off `main`: `main` is 79 commits behind and has neither `scripts/power_metric.py`
nor the V4 wall-pass patch this plan deletes, so every line reference in it would be wrong there.
The eidolon scrape/curate work stays untracked in the working tree and is never staged here.

---

## Why (the verified findings)

Ticket 11's two defects are confirmed exactly as written:

1. `shield_chooser` (`Backend/utils/class_func/armor_and_weapon_chooser.py:103`) computes
   `limits = 'Shield'` for every one-handed character but **only `return`s on its ~10% Tower
   branch** — the `'Shield'` case falls off the end and returns `None`.
2. `shield_flag_func` (`:111`) **mutates `character.shield_flag` and returns `None`**, and
   `main_test.py:966` assigns that `None` straight back over the attribute it just set.

Pulling the thread found **the same failure mode three more times in the same call path** — a
lookup that silently misses and yields a falsy default:

3. **`armor_type_mapping` (`data.py:148`) is dead code.** Its keys are *tuples*
   (`('rogue','bard','brawler'): 'L'`); `armor_chooser` (`:182`) looks up a *string*. It has never
   hit, so every character falls to `'H'`. And when `armor_type` is `None`, `list_selection`
   (`:131`) draws a **random section out of all five** — Shields and Tower included.
   *The goldens prove it:* `optimized_controller` is a **wizard in Full plate**, `witch` is in a
   Chain coat, `rogue` in Hellknight half-plate, and `companion` is a **druid in Half-plate**.
4. **`payload.py::gear_display` has three dead lookups.** `:244`/`:261` read `'spell_failure'`
   where `armor.json`'s key is `'arcane spell failure chance'` (`"35%"`) — which is why arcane
   spell failure is `0` in all eleven goldens. `:262` reads `'shield check penalty'` where the
   real key is `'armor check penalty'`. And **`:264` reads `armor_dict` for the *shield's*
   max-dex** — the `'1'` on `optimized_wall`'s shield is the Full plate's number; every shield in
   `armor.json` has an empty max-dex, correctly.

**Four downstream consumers are dead as a result:**

| Consumer | Why it never fires |
|---|---|
| `build_archetype.py:319` `sig['shield']` | `shield_flag` is always `None` → `0.0` for every character ever generated |
| `build_archetype.py:316-317` `sig['armor_light']`, `sig['armor_medium']` | `armor_type` is only ever `'H'` or `None` |
| `power_metric.py:867` `requires_shield` sphere-defence rows | `has_shield = shield_ac > 0`, and `shield_ac` is always 0 |
| `power_metric.py:879` monk Wis-to-AC adder | `unarmored` requires `armor_ac == 0`, and every monk wears plate |

---

## The rulings (Daniel, 2026-08-17 grill)

| # | Decision | Rejected |
|---|---|---|
| D1 | Scope is the **whole gear-legality cluster**, one ruling, one plan | shields alone; a second rebaseline later |
| D2 | Authority is a **derived, gated table** parsed from `class_data.json`'s proficiency prose | runtime prose parsing; hand-authored; merely flattening the tuple keys |
| D3 | **Heaviest legal armor band, always**; the item pick inside the band stays random | rolling a band; Dex-aware bands |
| D4 | The table carries bands, the druid allowlist and the ASF exemptions. Emitted `*_spell_failure` is the **item's true value**, not exemption-adjusted | character-level ASF (cannot survive a multiclass caster); leaving ASF at 0 |
| D5 | Multiclass: **union of bands, intersection of restrictions**, capped so it never breaks a rolled caster | primary class only; pure RAW union |
| D6 | Shield roll is **~20% of every shield-proficient character**, regardless of weapon; ranged excluded outright | one-handers only; per-weapon rates |
| D7 | Shield + two-hander → **enabler ladder**; drop the shield if nothing is legal | re-drawing the weapon; forbidding the combination |
| D8 | Enabler feats are **granted free**, via the existing `grants` path | paid out of `feat_amounts` |
| D9 | Shield pool is the **curated ten**; Tower keyed to proficiency (fighter only), ~10% | all 14; dropping Tower entirely |
| D10 | Oversizing: **+1 size step, cap 1** — only the full Titan Slayer chain reaches +2. Sources do **not** stack; take the best, not the sum | one step per feat to a cap of 2 |

### The rules, stated

```
armor:   band = highest granted by any rolled class
                ∩ every rolled class's prohibition
                capped so it never breaks a rolled caster
         None means NO armor
         (today None means "random section", which is how a wizard got Full plate)

shield:  shield-proficient? roll ~20%
           hit + One-Handed/Light  -> shield from the curated ten
           hit + Two-Handed        -> enabler ladder:
                                        polearm/spear    -> grant Pikeman's Training
                                        Str>=17 & BAB>=4 -> grant Titan Technique + Titan Grip
                                                            (+ Power Attack if absent)
                                        already has Jotungrip / Twin Thunder Stance -> keep
                                        else             -> DROP the shield
           hit + Ranged            -> no shield
         Tower only where the table says `tower` (fighter), ~10%

weapon:  no shield, but an oversizing source held -> +1 size step
           full Titan Slayer chain                -> +2
         sources do NOT stack; -2 attack per step,
         reduced by Titan Fighter's `incredible heft`
```

### The enabler census (searched 2026-08-17 — do not redo this)

Two distinct effects, which is what makes the two rules separable:

| Effect | Source | Kind | Where | In pool? | Known at gear time? |
|---|---|---|---|---|---|
| one-hand a 2H | **Jotungrip (Ex)** | Barbarian *Titan Mauler* archetype | `json/archetypes.json` | yes | **yes** |
| one-hand a 2H | **Pikeman's Training** | Combat feat, BAB +1, polearm/spear, *requires a shield* | `data/feats_new.csv`, `data/Metzofitz_Feats.csv` | yes | no (feat phase) |
| one-hand a 2H | **Twin Thunder Stance** | PoW, Piercing Thunder discipline | `json/class_data/path_of_war/Martial_Disciplines.json` | yes | no (PoW phase) |
| one-hand a 2H | **Lighten Weapon** | Kobold Press 3pp combat feat | — | **NO** | — |
| oversize | **Titan Technique → Titan Grip → Titan Slayer** | Ascension Games 3pp Combat/Technique feats; Grip needs Power Attack + Str 17 + BAB +4, Slayer Str 19 + BAB +8 | `data/feats_new.csv`, `data/Metzofitz_Feats.csv` | yes | no (feat phase) |
| oversize | **Titan Fighter** *giant weapon wielder (ex)* / *incredible heft (ex)* | Fighter archetype | `json/archetypes.json:3366-3367` | yes | **yes** |
| oversize | **Equipment sphere advanced talent** | Spheres of Might | — | **NO** (the `Equipment` key in `spheres_of_might_cleaned.json` is a kit/gear list, not the talent tree) | — |

*Effortless Lace is a false positive* — it makes a one-hander count as **light**, and it exists in
`json/foundry_item_names.json` as a name only, with no rules text.

### Facts the design leans on (verified, don't re-derive)

- **Phase order** (`main_test.py`): `phase_class_options` (`:641`, sets archetypes) → **gear
  (`:938`)** → PoW/Spheres (`:1199`) → feats (`:1597`). So archetypes are visible at gear time and
  feats and stances are not.
- **`grants` is an existing free-grant mechanism**: `phase_feat_selection(character, grants, …)`
  (`:1600`) extends `character.feats` with `grants.ranger_style_feats` / `monk_bonus_feats`
  (`:1709-1710`) **after** the feat-count guarantee at `:1729`. The enabler grant rides this.
- **`armor.json` sections** are `Light / Medium / Heavy / Shields / Tower`, matched by
  `list_selection_limits`'s skip-count map (`:155`). 65 armors, 14 shields, 1 tower.
- **Shield pool**: ten ordinary (Buckler, Klar, Light steel, Light steel quickdraw, Light wooden,
  Light wooden quickdraw, Madu ×2, Poisoner's Buckler, War-shield dwarven, Heavy steel, Heavy
  wooden, Snarlshield ×2). **Excluded by D9:** Klar and Madu ×2 (exotic weapon-shields), and
  Poisoner's Buckler (1,505 gp **and** empty ACP/ASF fields — a data gap).
- **Druid taboo is an exact allowlist**, in the prose the build script will already be reading:
  *"they may wear only padded, leather, or hide armor"* and *"shields … crafted from wood"*. Three
  wooden shields exist in the curated pool.
- **ASF exemptions are in the same prose** — bard, magus, summoner and skald each state theirs
  verbatim.
- **`weapons_data.json` carries only `"damage": "1d4 (small), 1d6 (medium)"`.** There is **no**
  size-progression table anywhere in the backend; `companion_stats._size_change` is creature stat
  deltas, not weapon dice. Module-side, `createScalingAttackItem` already owns size scaling.

---

## New data and gates

| File | Holds |
|---|---|
| `Backend/scripts/build/build_armor_proficiency.py` | parses `class_data.json`'s `weapon and armor proficiency` prose |
| `Backend/json/armor_proficiency.json` | per class: `armor` band, `shield` band, `asf_exempt`, druid `armor_allow` + `shield_material` |
| `Backend/json/two_hand_enablers.json` | every enabler above with kind + effect; the two absent rows flagged **not-in-pool**, not hidden |
| `Backend/json/weapon_size_damage.json` | the PF1e size → damage-dice step table |
| `Backend/scripts/gates/validate_gear_legality.py` | **config layer**: every rollable class has a row; a re-parse matches the file; an unparseable row fails loudly; every enabler row resolves to a real feat/archetype/stance or is flagged not-in-pool |
| `Backend/scripts/tests/test_house_invariants.py` (extended) | **behaviour layer**: no illegal band; no metal on a druid; no shield without proficiency; `shield + 2H ⇒ enabler present`; oversized ⇒ source held |

Two layers sharing no code, per the §11 precedent. The behaviour layer must **count branches
reached and fail if the sweep never produced a shielded character**, so a green run cannot mean
"asserted nothing."

Lighten Weapon and the Equipment advanced talent stay **visible gated gaps** — the same pattern as
the 246 missing item names. Sourcing them is a separate scrape + OGL job, not part of this plan.

---

## Commit sequence

Each behaviour step regenerates goldens on its own, so a surprising diff has exactly one candidate
cause. The census runs are the defence against the re-seed trap that has bitten twice —
**re-scan, never edit the expectation to match.**

- [x] **1. Proficiency table.** `build_armor_proficiency.py` + `armor_proficiency.json` + the gate
      skeleton. No behaviour change. *Goldens must stay byte-identical — that is the proof.*
      **Done 2026-08-17.** 70 classes parsed, 0 unparseable: 10 no-armor / 26 L / 22 M / 12 H,
      41 shield-proficient. Goldens byte-identical (no tracked file changed). The gate's three
      checks were sabotage-proven on the spot — a hand-edited table trips staleness, and a
      *loosened parser with the file regenerated* (staleness silent) trips the token re-read alone.
- [ ] **2. Enabler + size tables.** `two_hand_enablers.json` + `weapon_size_damage.json` + their
      gate rows. Still no behaviour change; goldens byte-identical again.
- [ ] **3. Payload field fixes.** `payload.py::gear_display` — the three dead lookups and the
      armor/shield mixup at `:264`. Goldens move on display fields only.
- [ ] **4. Armor bands.** `armor_chooser` reads the table (D3/D5); `armor_type=None` returns *no
      armor* instead of falling into `list_selection`'s random-section draw. **Census: 68 classes ×
      L1/5/10/20**, band distribution before/after. Goldens: armor moves.
- [ ] **5. Shields.** `shield_chooser` / `shield_flag_func` return properly; curated pool; Tower by
      proficiency; the ~20% roll (D6/D9). Delete the V4 wall-pass patch at `main_test.py:967-980`,
      which the real fix supersedes. **Census: shield rate and shield distribution.** Goldens:
      shields appear.
- [ ] **6. Enabler ladder.** `grants.enabler_feats` alongside `ranger_style_feats` /
      `monk_bonus_feats`, appended after the count guarantee. Goldens: enabler feats appear on the
      affected builds.
- [ ] **7. Oversized weapons.** Size step, damage dice from the new table, −2/step attack penalty
      with Titan Fighter's `incredible heft` reduction. ⚠ **Checkpoint: agree the payload shape
      with the module repo before this lands** — `createScalingAttackItem` already owns size
      scaling module-side. Census + goldens: weapon damage moves.
- [ ] **8. Both gate layers complete and sabotage-proven** — perturb the table, perturb a generated
      character, prove each layer fails independently and for a different reason.
- [ ] **9. Re-derive baselines and document.** `test_build_archetype.py` (three armor signals and
      the shield signal go live), `power_metric.py` (the monk AC adder and the `requires_shield`
      sphere rows start firing), `changelog.md` with the decision **and the rejected alternative**,
      a `feature_spec_todo.md` section, and ticket 11's resolution in the tickets repo.

## Files to modify

- `Backend/utils/class_func/armor_and_weapon_chooser.py` — `armor_chooser`, `shield_chooser`,
  `shield_flag_func`, `list_selection`, `list_selection_limits`
- `Backend/utils/payload.py` — `gear_display` (`:239-282`)
- `Backend/main_test.py` — the gear phase (`:958-981`, incl. deleting the wall-pass patch at
  `:967-980`), `phase_feat_selection` (`:1600`)
- `Backend/utils/data.py` — retire `armor_type_mapping` (`:148`) in favour of the table
- `Backend/scripts/golden/*.json` — all eleven
- `Backend/scripts/tests/test_house_invariants.py`, `Backend/scripts/tests/test_build_archetype.py`

## Verification

- `validate_gear_legality.py` → 0 errors; sabotage it and it fails.
- Full `test_all.py` family green, including the sweep with the new gear invariants **and a
  non-zero shielded-character count**.
- Census diffs at steps 4, 5 and 7 **read and accepted**, not merely generated.
- `optimized_wall` still pins a shielded build — now for the right reason.
- A generated fighter and a generated druid injected into Foundry: the shield appears as an item,
  the druid is not in metal, and the sheet's AC agrees with `armor_ac + shield_ac`.
- Web sheet renders `shield_name` / `shield_ac` — its payload key order is positional, so check it
  rather than assume.

## Found along the way

**Step 1 (2026-08-17).**

- **Tower is four classes, not one.** D9's "(fighter only)" was an estimate; the prose keys it to
  `fighter` and `warder` (both say *"including tower shields"*) plus `aristocrat` and `warrior`,
  whose scrape reads *"all types of armor and shields"* — the SRD's *"(including tower shields)"*
  parenthetical was lost on the way in. The ruling's substance ("keyed to proficiency") is what the
  table implements; the parenthetical is the part that was wrong.
- **The shifter has no allowlist.** The druid's exact list (*"padded, leather, or hide"*) is
  druid-only prose. The shifter is *"prohibited from wearing metal armor"* and never says what is
  left, and `armor.json` has no material column. Emitted as `metal_prohibited: true,
  armor_allow: null` and reported as a SKIP on every gate run rather than quietly handed the
  druid's list. **Step 4 must make that ruling in the open.**
- **Six classes are non-shield-proficient by silence, not denial** — gunslinger, magus, shaman,
  spiritualist, summoner, summoner (unchained). Correct RAW, but indistinguishable from a dropped
  sentence, so the gate asserts the set exactly.
- **The magus is right only because of the sentence narrowing.** Its sole mention of a shield is in
  the arcane-spell-failure sentence; a paragraph-wide search makes it shield-proficient, and makes
  the bard, bloodrager and summoner heavy-armor classes.
- **Four wooden shields in the curated pool, not three** as this plan said: Light wooden, Light
  wooden quickdraw, Heavy wooden, *and* Snarlshield (wooden).
- **The old default's blast radius, measured:** `armor_type_mapping` sent all 70 classes to `'H'`.
  The table sends 10 to no armor at all and 26 to Light. Step 4's golden diff will be large.

## Adjacent, and deliberately not in this plan

- **`class-choices/04` is not resolvable yet** (asked this session). Spec §11 marks it "rendering
  outstanding" and hands it four unfixed defects — six call sites omitting `dict_name=`, the
  `manuevers` typo, the oracle's mystery sharing a bucket with its revelations, and three buckets
  with no level stamp — plus the bucket-by-bucket coverage table. The behaviour gate currently
  skips seven class/bucket pairs over exactly these.
- **`optimal-builder/03` and `04` will shift** once steps 7 and 9 land: the metric's AC and damage
  axes both move. Re-run the A/B delta baseline **after** this plan, not before — reading it now
  is reading a baseline that is about to move.
- **Oversized-weapon rendering** in the FoundryVTT module and the web sheet is a separate PR in
  another repo, logged in this repo's `changelog.md` per the central-changelog rule.
