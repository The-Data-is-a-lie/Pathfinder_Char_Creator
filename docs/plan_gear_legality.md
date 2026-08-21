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
| D13 | An arcane caster **may** wear armour past its own exemption — the exemption is a **weighted preference** (`ASF_RESTRAINT_CHANCE = 75`), not a cap. When it does, it is granted `Arcane Armor Training` free if it qualifies (caster level 3) | forcing the safe band, which made a wizard/fighter unarmoured *every* time; granting the whole Arcane Armor chain |

### The rules, stated

```
armor:   band = highest granted by any rolled class
                ∩ every rolled class's prohibition
         then, if a rolled class is an ARCANE CASTER and the band exceeds its own
         exemption:  75% -> drop to the exemption
                     25% -> keep it, and grant Arcane Armor Training free (needs CL 3)
         None means NO armor
         (before this plan None meant "random section", which is how a wizard got Full plate)

shield:  shield-proficient? roll ~20%
           hit + One-Handed/Light  -> shield from the curated ten
           hit + Two-Handed        -> enabler ladder (CORRECTED -- see the census):
                                        polearm/spear         -> grant Pikemans Training
                                        Titan Mauler, level 2 -> keep (jotungrip)
                                        else                  -> DROP the shield
           hit + Ranged            -> no shield
         Tower only where the table says `tower` (fighter, warder,
         aristocrat, warrior), ~10%

weapon:  no shield, but an oversizing source held -> +1 size step
           full Titan Slayer chain                -> +2
         sources do NOT stack; -2 attack per step,
         reduced by Titan Fighter's `incredible heft`
```

### The enabler census

> ⚠ **The first census (2026-08-17, pre-step-2) was wrong in four ways** and has been replaced by
> the gated file **`Backend/json/two_hand_enablers.json`**, which is now the authority — every row
> is resolved against the pool file it names on every gate run, and the two absent rows are proved
> still absent. Read that file, not a table in this doc. What it corrected:
>
> 1. **Titan Technique and Titan Grip do not one-hand anything.** Titan Technique's benefit is
>    *"wield weapons intended for creatures one size category larger than you, **using the same
>    handedness**"*, and Titan Grip only reduces the penalty. **D7's second rung is therefore
>    void** — see the corrected ladder below.
> 2. **Their prerequisites were attributed to the wrong feat.** Power Attack + Str 15 is *Titan
>    Technique*; Str 17 + BAB +4 is *Titan Grip*.
> 3. **Three enablers were missed**: `Phalanx_Lancer` (Piercing Thunder, level **1**, one-hands a
>    polearm *specifically when using a shield* — the cheapest thing on the ladder),
>    `massive weapons (ex)` (Titan Mauler 3rd, an oversizer, so a Titan Mauler is both), and
>    `Bigfolk Training` (the small-race oversizer). `Quarterstaff Master` is a fourth, weapon-locked
>    to the quarterstaff and gated behind Weapon Focus.
> 4. **Every name was spelled wrong.** The pool has `Pikemans Training` (no apostrophe),
>    `Titan Grip (Combat)` and `Titan Technique (Combat, Technique)` — the parenthetical is *inside
>    the name field*. A grant of the census spelling would have resolved to nothing, silently,
>    which is the failure this plan exists to remove. The gate now fails on it.

*False positives, checked and recorded in the file so they are not re-checked:* Effortless Lace
(makes a one-hander **light**; name-only in `foundry_item_names.json`), `Scarlet_Einhander` (a
shield bonus, not a handedness change), `Twin Thunders` (a real UC feat about fighting giants, and
a near-miss for the stance), `Titan Strike` (a **mythic** unarmed feat), and `armament shield` (the
*inverse* — a shield bonus for going two-handed).

### The corrected two-hander ladder (supersedes D7's rungs)

```
hit + Two-Handed -> polearm/spear                     -> grant Pikemans Training   (BAB +1)
                    Titan Mauler barbarian, level >=2 -> keep; jotungrip already one-hands it
                    else                              -> DROP the shield
```

Only two rungs, because only two things in the pool can be *granted* at gear time and actually
work. `Twin_Thunder_Stance` and `Phalanx_Lancer` are Path-of-War stances chosen in a phase that
runs **after** gear, so they can be honoured when already present but never granted; `Quarterstaff
Master` would cost two feats (it needs Weapon Focus in the quarterstaff) to arm one build.
**Open for Daniel:** whether the quarterstaff rung is worth two free feats. Implemented as *no*
— the shield drops — until told otherwise.

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
- [x] **2. Enabler + size tables.** `two_hand_enablers.json` + `weapon_size_damage.json` + their
      gate rows. Still no behaviour change; goldens byte-identical again.
      **Done 2026-08-17.** 14 enabler rows (12 in pool, 2 proved absent) and 11 size rows; all 32
      validators pass. The census corrections above came out of this step. Sabotage-proven: the
      census spelling `Pikeman's Training` fails to resolve, a closed gap fails, and a transposed
      size cell fails on monotonicity.
- [x] **3. Payload field fixes.** `payload.py::gear_display` — the three dead lookups and the
      armor/shield mixup at `:264`. Goldens move on display fields only.
      **Done 2026-08-17.** Exactly the predicted blast radius: `armor_spell_failure` on all eleven
      (`0` → `"35%"` / `"40%"` / `"30%"`) and three more on `optimized_wall`, the only shielded
      golden — `shield_spell_failure` `0` → `"15%"`, `shield_armor_check_penalty` `0` → `"-2"`,
      `shield_max_dex_bonus` `"1"` → `""`. Every value re-checked against `armor.json` by hand.
      Full `test_all.py` green. The latent NameError was fixed in the same pass, because step 4
      makes it reachable.
- [x] **4. Armor bands.** `armor_chooser` reads the table (D3/D5); `armor_type=None` returns *no
      armor* instead of falling into `list_selection`'s random-section draw. **Census: 68 classes ×
      L1/5/10/20**, band distribution before/after. Goldens: armor moves.
      **Done 2026-08-17.** Census (`scripts/build/report_gear_census.py`, 272 characters):

      | band | before | after |
      |---|---|---|
      | none | 36 | **40** |
      | light | 0 | **100** |
      | medium | 0 | **88** |
      | heavy | **236** | 44 |

      Read and accepted: the after column is exactly the table (25 L + 22 M + 11 H + 10 none
      rollable classes × 4 levels). Goldens: the wizard and the witch now wear nothing, the druid
      wears Leather, the rogue Rosewood, the summoner a Chain shirt; the four fighters keep heavy.
      Full `test_all.py` and all 32 validators green.
- [x] **5. Shields.** `shield_chooser` / `shield_flag_func` return properly; curated pool; Tower by
      proficiency; the ~20% roll (D6/D9). Delete the V4 wall-pass patch at `main_test.py:967-980`,
      which the real fix supersedes. **Census: shield rate and shield distribution.** Goldens:
      shields appear.
      **Done 2026-08-17.** The rule measured in isolation over 20,000 rolls, which is the only way
      to see the rate rather than the outcome: one-handed **20.03%**, two-handed **0%**, ranged
      **0%**, Tower **9.4% of shields** (D9's ~10%), non-proficient 0%. End-to-end over 816
      characters: 373 proficient-and-not-ranged cells, 38 shields (10.2%) — the gap is the 115
      two-handed cells that step 6's ladder has not rescued yet. Distribution spans nine of the
      curated ten plus one Tower; no illegal shield in the sweep. `optimized_wall` **reseeded
      5150 → 5159**: the real roll consumes a draw the dead code never took, and its Active
      Defense talent fell out of the realigned stream. Re-swept on the *predicate*, per that
      file's own rule; it still draws the same Heavy steel shield.
- [x] **6. Enabler ladder.** `grants.enabler_feats` alongside `ranger_style_feats` /
      `monk_bonus_feats`, appended after the count guarantee. Goldens: enabler feats appear on the
      affected builds.
      **Done 2026-08-17.** The corrected two-rung ladder (see the census section). Each rung
      measured over 20,000 rolls: fighter + glaive → 20.4% shield, **every one** granted
      `Pikemans Training`; the same at BAB 0 → 0% (the prereq bites); fighter + greatsword → 0%
      (dropped, nothing rescues it); Titan Mauler barbarian at 5th + greatsword → 20.2% with **no**
      grant, because jotungrip is already held; the same at 1st → 0%. End-to-end the shield rate
      over proficient non-ranged characters rose 10.2% → **13.4%**, which is the 12 polearm cells
      the ladder rescued. Six real generated fighters spot-checked: all six two-handed shield users
      drew a Polearms weapon and all six carry the feat.
      **Goldens are byte-identical** — the ladder consumes no random draws, so none of the eleven
      moved.
- [~] **7. Oversized weapons.** ⚠ **Checkpoint CLEARED by Daniel, 2026-08-17.** Two rulings:

      - **D11 — the backend emits a size MARKER, never scaled dice.** `weapon_size`,
        `weapon_size_steps`, `weapon_size_source`, `weapon_size_attack_penalty`, appended at the
        END of `PAYLOAD_KEYS` (the order is positional for both consumers). **The web sheet
        pre-scales**; the FoundryVTT module's `createScalingAttackItem` does its own. Rejected:
        emitting pre-scaled dice, which would put a second implementation of the ladder in the
        backend where it can disagree with the two that already exist.
      - **D12 — the damage ladder is Daniel's, not RAW.** `Base_Weapon_Damage_Dice.JS` in
        `FoundryVTT/Data/Foundry_VTT_Pf_1e_Handy_Macros` is the live implementation: it reads the
        actor resource **`sizefordamage`** and moves **two positions per size category** along a
        44-entry average-ordered ladder. That resolves the Medium +2 gap RAW could not — the
        ladder runs to 26d12. `weapon_size_damage.json` now carries that ladder as the authority,
        with CRB Table 6-5 demoted to a `raw_reference` recording the deliberate divergence
        (RAW steps 1d8→2d6; the ladder steps it 1d8→1d12).

      **The Foundry side is already built.** `scripts/build/weapon-finishing.js`
      (`addSizeForDamageFeature`) puts a `sizefordamage` feature on **every** generated sheet, and
      `templates/character_sheet_folder/sizefordamage_feature.json` gives it
      `uses: {value: 0, per: "charges", maxFormula: "99"}`. The scaling script on the attack item
      reads `@resources.sizefordamage`, and the weapon already carries the two actions it needs
      (`[0] Attack`, `[1] Don't Touch`, the pristine base damage it scales from). So the module
      work is **not new machinery** — it is setting that one `uses.value` from the payload instead
      of leaving it at 0, which makes `weapon_size_steps` map 1:1 onto it. `createScalingAttackItem`
      is downstream of the resource, not a second scaler to negotiate with. **The web sheet is
      therefore the only consumer that needs new scaling code**, which is what D11 already says.

      **Done 2026-08-17.** `weapon_size_marker` computes the step at the very END of the pipeline,
      off `_render_feat_names` (post tax, post swap, post luck) — three of the five sources are
      feats and are not chosen until two phases after gear. Four keys appended at the tail of
      `PAYLOAD_KEYS`; the goldens gained exactly those four and nothing else moved (44 insertions,
      0 deletions), with the halfling rogue correctly reading `Small`. Every branch exercised
      directly:

      | held | result |
      |---|---|
      | nothing | Medium, 0 steps, no source, no penalty |
      | Titan Fighter 1st | Large, 1, `giant weapon wielder (ex)`, −2 |
      | Titan Fighter 10th | same, penalty **0** — `incredible heft` reduces 2 |
      | Titan Fighter, one-handed weapon | **no** oversize — the `two_handed_melee` filter |
      | Titan Mauler 3rd | Large, 1, `massive weapons (ex)`, **−4** (its own stated penalty) |
      | Titan Technique | Large, 1, −2 |
      | full Titan Slayer chain, BAB 16 | **Huge, 2**, penalty 0 via Titan Grip |
      | Titan Slayer *without* the chain | **capped to 1** (D10) |
      | Bigfolk Training, gnome | Small→Medium, 1, penalty **0** |

      Two corrections came out of this against a flat −2/step rule: `massive weapons` states −4,
      and `Bigfolk Training` states none — the source's own `attack_penalty` is used, not a
      formula. The `validate_luck.py` payload-tail allowlist was extended deliberately; it caught
      the contract change, which is what it is for.
- [x] **8. Both gate layers complete and sabotage-proven** — perturb the table, perturb a generated
      character, prove each layer fails independently and for a different reason.
      **Done 2026-08-17, including the oversized-weapon invariant.**
      `check_gear_legality` in `test_house_invariants.py` re-implements the band union, the caster
      cap and the taboo intersection rather than importing them, and 98,392 checks pass. Three
      sabotages, three different failures:

      | perturbation | config gate | behaviour gate |
      |---|---|---|
      | table hand-edited | **fails** (staleness + token re-read) | — |
      | parser loosened, file regenerated | **fails** (token re-read alone) | — |
      | chooser ignores the band | **green** | **fails** — 68 classes in illegal armour |
      | shields made unreachable again | **green** | **fails** — *"every shield assertion passed vacuously"* |
      | every character oversized, no source held | **green** | **fails** — 77 × *"which the character does not hold"* |

      That last row is the one that matters: it restores the repo's actual prior state, and the
      gate now refuses to call it a pass.
- [x] **9. Re-derive baselines and document.** `test_build_archetype.py` (three armor signals and
      the shield signal go live), `power_metric.py` (the monk AC adder and the `requires_shield`
      sphere rows start firing), `changelog.md` with the decision **and the rejected alternative**,
      a `feature_spec_todo.md` section, and ticket 11's resolution in the tickets repo.
      **Done 2026-08-17**, except ticket 11 (see below). The four dead consumers were **measured,
      not assumed** — over 1,029 scored characters, `monk_ac` fired **0 → 30 times** (its note
      lands in `diagnostics.defense_notes`, not a top-level field, which is why a first grep read
      zero). The metric's AC axes moved with it: mean `ac` ratio 1.049 → 0.936 and `ac_combat`
      1.363 → 1.273, with 252 and 260 of 343 comparable rows changing — characters no longer being
      scored in armour they could never legally have worn. The `requires_shield` sphere rows read
      0 in the sweep because it runs `spheres_flag='N'`; that path is pinned by `optimized_wall`
      instead, which now carries both a Heavy steel shield and Active Defense.
      `_power_baseline.json` is untracked — a regenerated report, not a committed baseline — so
      "re-derive" meant regenerate and **read**, which is what the numbers above are.
      Also updated: `changelog.md` (with the rejected alternatives), `docs/CODEBASE_MAP.md` (the
      three new JSON files and where gear legality lives in the module index), and
      `docs/feature_spec_todo.md` **§16**.
      **Ticket 11 is resolved** in the `tickets` repo (`resolve(optimal-builder/11)`), pointing
      here and at §16 rather than answering the single question it asked — and flagging tickets
      03/04 that any A/B delta baseline taken before today is stale.

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

**Step 2 (2026-08-17).** The four census corrections are written up under "The enabler census"
above; these are the rest.

- **PF1e never published a Huge weapon damage table.** The Core Rulebook has exactly one
  conversion table — Table 6-5, *Tiny and Large* — verified row-for-row against two independent
  copies (Archives of Nethys and Roll20, which agree exactly). So **a Medium wielder cannot be
  oversized two steps**, and applying the Large column twice does not work either: it has no row
  for 3d6, 3d8, 4d6 or 4d8. Declared as a gap in the file rather than filled from the community
  "Medium and Larger" table, which could not be verified first-party in the same pass.
  ⚠ **D10's +2 case is therefore unresolvable for Medium characters** — step 7 must cap them at
  +1 and say so. A **Small** character is fully covered: +1 is the weapon's own printed medium
  damage, +2 is the `large` column.
- **The Paizo FAQ dice chart is a different rule and must not be used here.** It steps 1d8→1d10
  and 2d6→2d8 where the weapon-size table steps them to 2d6 and 3d6. It governs *effective* size
  increases (`lead blades`, `enlarge person`); a physically larger weapon uses Table 6-5.
- **Only two enablers are visible at gear time**, and both are archetype features
  (`jotungrip (ex)`, `giant weapon wielder (ex)`, plus `massive weapons (ex)` and
  `incredible heft (ex)` on the same two archetypes). The gate now asserts that: a feat or stance
  claiming `visible_at_gear_time` fails, because gear runs before both the feat and PoW phases.
- **Every Titan feat and Pikemans Training carries `source_dataset: Metzofitz`** in
  `feats_new.csv`. That does not block step 6 — D8 grants them free, bypassing selection — but it
  does mean nothing reaches them by ordinary rolling while Metzofitz selection stays commented out
  in `feats.py`, so **+2 oversizing effectively cannot occur** and D10's cap is doing no work.

**Step 4 (2026-08-17).**

- **`magus_armor_chooser` is deleted, and D5 is why.** It promoted a magus to medium armour at 7th
  and heavy at 13th — via an `elif` that could never fire after the `if` above it, so the heavy
  branch was already dead. Both are real class features, and both are now moot: the magus's ASF
  exemption covers *light* armour only, so the caster cap holds it at Light regardless. Keeping the
  ladder would have left code computing a band nothing uses.
- **The shifter ruling, made in the open:** a metal-prohibited class with no allowlist of its own
  gets the druid's `(Padded, Leather, Hide)`, named as `_METAL_FREE_FALLBACK` next to the gate that
  reports the gap. Both the druid and the shifter therefore always wear **Hide** — band M, and Hide
  is the only allowlisted Medium armour. That is D3 working as written ("heaviest legal band; the
  pick inside the band stays random"), not a bug, but it does mean two classes have a deterministic
  armour.
- **The cap only bites in multiclass, so the single-class census cannot see it.** Verified
  directly instead: wizard/fighter → **no armour** (capped by wizard), bard/fighter → light,
  magus/fighter → light, bloodrager/fighter → medium, druid/fighter → medium *with the druid's
  allowlist still intersected in*, and cleric/fighter → heavy (divine, no ASF). psion/fighter →
  heavy, because psionic prose says armour does not interfere with manifesting.
- **A wizard/fighter goes unarmoured.** That is D5 read literally and it is a real consequence
  worth seeing before it ships: the plate would not stop the fighter working, only the wizard.
  ~~⚠ Open for Daniel~~ → **ruled 2026-08-17 as D13, and reversed.** See the step-9½ note below.
- **`asf_sensitive` had to be added to the table** to make D5's cap expressible.
  `data.base_classes` is the Paizo base-class *roster* (it contains the fighter), so it cannot
  answer "is this an arcane caster"; the prose can, and does, for all ten.
- **The census read the wrong field on its first run** and reported every band as `none` while the
  armour names were visibly correct — `armor_type` is not a payload key. It now derives the band by
  looking the worn armour back up in `armor.json`, which is a second opinion rather than the
  generator agreeing with itself.
- **Two goldens moved far more than their armour** (`caster` 465 lines, `companion` 321). Cascade,
  not corruption: cheaper armour leaves more purse, which changes the enhancement budget and the
  item rolls downstream.

**Step 5 (2026-08-17).**

- **The optimizer's shield promise moved into `shield_chooser` rather than being deleted.** The V4
  patch is gone from `main_test.py`, but a role declaring `one_handed_shield` still gets its
  shield — it is a declared build, exactly like `optimized_armor_pick` choosing the best armour,
  not a random draw. It is applied *after* the roll so the RNG stream is identical in random mode
  and adding a role cannot move a random golden.
- **`shield_flag` is not a payload key.** It goes to `build_archetype`'s signal dict as
  `character.shield_flag`, which is what step 9's `sig['shield']` reads. Reading the payload for
  it returns `None` whether or not a shield was drawn — a trap worth knowing before step 9.
- **The end-to-end rate is not the roll.** 20% of the proficient roll a shield; the two-handed ones
  are then dropped, which is why the sweep reads 10.2%. Both numbers are real and they answer
  different questions — assert the rule in isolation, read the distribution end-to-end.
- **A tower shield is now reachable by exactly four classes** — fighter, warder, aristocrat,
  warrior — and one turned up in an 816-character sweep, which is about right for 10% of 10% of
  four classes.

**Step 8 (2026-08-17).**

- **The behaviour gate caught a bug that 20,000 unit rolls and a six-character spot-check both
  missed.** Six swept characters held a shield and a two-handed polearm with **no enabler**. The
  grant was firing correctly — `enabler_feats: ['Pikemans Training']` was on the character — and it
  survived the free-feat filter and the bucket split. **The trainer swap then spent it**: a swap
  trades an ordinary feat for a trainer feat, and a granted feat sitting in the general list looks
  ordinary. Fixed by moving the join to *after* `phase_feat_tax_and_swaps`, which is the only place
  D8's "free" actually holds. The unit check could never have found this — it never reached the
  swap.
- **The house damage ladder has two out-of-order pairs**, and this repo copies them rather than
  fixing them: `8d6` (avg 28) sits above `5d10` (27.5), and `16d6` (56) above `10d10` (55), in
  `Base_Weapon_Damage_Dice.JS` itself. Re-sorting the copy would make it disagree with the macro it
  mirrors — and since a size step moves by INDEX, that disagreement would be silent. The gate
  **warns** on both every run. ⚠ **Open for Daniel:** fix the macro and re-transcribe, or leave it
  (the cost is at most half a point of average damage on one step).
- **Two branches the standing sweep does not reach**, and both are reported as `0` on every run
  rather than hidden: **tower shields** (a 10% roll on a 10% roll for four classes), and the
  **caster cap**, which cannot fire single-class — every ASF-sensitive class's own band already
  equals its exemption, so only a multiclass roll caps. Both were verified directly instead
  (see steps 4 and 5). ⚠ A multiclass gear sweep would close this properly.

**Step 9½ — D13, the caster cap reversed (2026-08-17).**

Daniel's ruling after reading step 4's consequence: *"wizard/fighter or sorc/fighter can go
armoured (but then they just need to commit to one of the multiple feats that can decrease spell
failure)... we can also just make it more likely instead of forcing it, some builds can be bad."*

- **The exemption is now a weighted preference, not a ceiling.** `ASF_RESTRAINT_CHANCE = 75`: an
  arcane caster who *could* wear heavier armour than its class exempts stays inside the exemption
  ~75% of the time and goes heavier ~25%. Measured over 4,000 rolls: wizard/fighter 76% unarmoured
  / 23% heavy, bard/fighter 76% light / 23% heavy, cleric/fighter 100% heavy (divine, no ASF), and
  a **pure** wizard is untouched at 100% unarmoured — it has no armour proficiency to argue about,
  so the roll never fires and no single-class RNG stream moves.
- **Going heavy grants `Arcane Armor Training` free** (caster level 3 and light-armour
  proficiency, which the band already proves), through the same channel the two-hander enabler
  uses. Verified end-to-end: **51 of 51** armoured multiclass wizards carry it. At caster level 2
  the grant correctly does not fire and the character simply eats the failure — the "some builds
  can be bad" half.
- **The ASF-mitigation census** (do not redo): `Arcane Armor Training` (AoN, 10%, Light Armor
  Prof + CL 3) is the only one cheap enough to grant. Also in the pool and deliberately not
  granted — `Arcane Armor Mastery` (20%, but needs Training + Medium Armor Prof + CL 7, so
  granting it means granting a chain), `Still Spell` (avoids ASF entirely at +1 spell slot, a
  playstyle choice not a gear fix), the Spheres of Might Equipment talent **`arcane armor`**
  (`spheres_of_might_enriched.json` `/equipment/arcane armor`, 10% and repeatable, but it belongs
  to the sphere economy), and `Arcane Armor Affinity` (Metzofitz, race-gated to pragians).
- ⚠ **`Arcane Armor Training` appears TWICE in `feats_new.csv`** — the second row is really the
  *Improved* variant (its prerequisite is "Arcane Armor Training" and it removes the swift action)
  scraped under the base name. A name-based grant is therefore ambiguous. Harmless today, worth
  fixing at the scrape.
- **Two goldens moved**, both legitimately: `caster` (summoner/cleric) rolled the 25% branch and is
  now in an **Erutaki coat with Arcane Armor Training**; `companion` (druid/magus/ranger/samurai)
  rolled restraint and stayed in Leather. Both coverage predicates survived.
- **The behaviour gate changed with the rule**: the exemption is no longer asserted as a ceiling
  (only the union is), and a new invariant takes its place — *exceeding the exemption is fine, but
  the character must then hold Arcane Armor Training unless it is below caster level 3*. The
  now-unreachable `capped` coverage counter was **deleted** rather than left reading 0 forever.
- The standing sweep is single-class, so it reports **0 ASF-exposed**; the branch is exercised
  directly instead, as with the tower and oversize branches.

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
