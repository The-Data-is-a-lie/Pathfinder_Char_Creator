# Homebrew Pathfinder 1E Rules — Reference

> **Source:** [Sieg's Guide to Dungeons, Dragons, and Life](https://docs.google.com/document/d/1PLsqBzF_QB8QQsv5vBGHtMWTD4shc3E8IPfsbmGe82Q/edit)
> (the hub doc) and its linked sub-documents.
>
> **Purpose:** A catalog of the house rules this campaign uses, so the generator can be aligned to
> them. The last column of each section maps a rule to where it plugs into the codebase.
>
> **How this was built:** fetched the hub doc + 4 sub-docs (June 2026) and synthesized. The hub is a
> mix of **base Pathfinder optional systems** (linked out to d20pfsrd / Spheres wikidot / AoNPRD) plus
> **custom additions** living in the linked Google Docs. Extraction used an automated summarizer —
> **verify exact numbers against the live docs before implementing.**
>
> **Coverage:** 4 of the ~17 sub-docs are deep-read (Character Building, Skills, Feats, Feat Tax). The
> rest are indexed but **not yet deep-read** — see [§7 Link index](#7-link-index--coverage). Say which
> ones to expand and I'll pull them in.

---

## 1. Character building

| Rule | Detail | Generator mapping |
|---|---|---|
| **Ability scores** | Generation method is GM/campaign-set (not fixed in the doc). The generator already takes *stat dice count* + *stat dice size* as inputs. | `Backend/utils/class_func/stats.py` |
| **Starting wealth** | Standard wealth-by-level; doc suggests keeping 500+ gp spare. GM-set per campaign. | Existing *starting gold* input |
| **Hit points** | **Full (max) hit die at every level**, all sources, including racial HD. Can trade permanent HP for skill ranks 1:1. | HP roll logic (see `level_and_bab.py` / hp funcs) |
| **Traits** | Pick **8 traits** (or roll), GM keeps **4** based on backstory. +1 extra trait per minor flaw. May buy 3 traits for 1 feat. Custom positive/negative trade-off traits allowed w/ GM approval. | `Backend/utils/class_func` trait selection + `data/traits.csv` |
| **Flaws** | **Minor flaw** → +1 bonus feat (from PF drawbacks list). **Major flaw** → +1 bonus feat (custom). Flaws can be "overloaded" for more slots. | Feat-count logic (`level_and_bab.py`) |
| **Proficiencies** | One free weapon proficiency, **or** trade all base proficiencies for a Martial Tradition (Spheres of Might). | `armor_and_weapon_chooser.py` |
| **Free skill unlock** | One free [Skill Unlock](https://paizo.com/pathfinderRPG/prd/unchained/skills-and-options/skill-unlocks.html) at level 5+. | `skill_ranks.py` |

### Bonus feats at creation (additive on top of normal progression)
- **+2** bonus feats at character creation
- **+1** per minor flaw, **+1** per major flaw
- **+1** "flavor" feat (for writing a backstory)
- **+1** story feat at levels **1, 5, 10, 15, 20**
- Class/racial bonus feats as normal

> **Note:** the existing homebrew branch in
> [Backend/utils/class_func/level_and_bab.py](Backend/utils/class_func/level_and_bab.py) already
> encodes the story-feat cadence — `story_feat_amount = 1 + floor(level/5)` yields 1/2/3/4/5 feats at
> L1/5/10/15/20, matching this rule. The **+2 creation feats** and **per-flaw feats** are **not yet
> implemented** → backlog.

---

## 2. Skills

| Rule | Detail | Generator mapping |
|---|---|---|
| **Skill ranks/level** | Any class with **+2 skill ranks/level instead gets +4**. | `Backend/utils/class_func/skill_ranks.py` |
| **Per-skill cap** | Max **3 ranks** in any single skill per level. | `skill_ranks.py` |
| **Bonus-rank ability** | At level 1, pick **Int / Wis / Cha** to govern bonus skill ranks/level (permanent). | `skill_ranks.py` |
| **Background skills** | **+2 background skill ranks/level** (background-only). Standard ranks may also go to background skills (but required background skills can't draw on adventurer ranks). | `skill_ranks.py` |
| **Dual ability mods** | Abilities like Deceptive Expertise / Intimidating Prowess let you add **both** ability mods to a skill. | skill total calc |
| **Class skill (Profession)** | If Profession would be a class skill, instead get **+1 to all Professions**. | `skill_ranks.py` |

### 2a. Skills usable with alternate ability scores ⭐ (the rule you called out)
When first ranking a skill, the player picks **one** of the allowed abilities for it:

| Skill | Allowed abilities | Skill | Allowed abilities |
|---|---|---|---|
| Acrobatics | Dex / Str | Knowledge (Local) | Cha / Int / Wis |
| Appraise | Int / Wis | Knowledge (Martial) | Str/Dex/Con/Int/Wis/Cha |
| Bluff | Cha / Wis | Knowledge (Nature) | Int / Wis |
| Climb | Dex / Str | Knowledge (Nobility) | Cha / Int |
| Craft | Int / Wis | Knowledge (Religion) | Cha / Int / Wis |
| Diplomacy | Cha / Wis | Linguistics | Cha / Int |
| Disable Device | Dex / Int | Perception | Wis / Int |
| Disguise | Cha / Dex | Perform | Cha / Dex / Str |
| Escape Artist | Dex / Str | Profession | Cha / Int / Wis |
| Gather Information | Cha / Int | Ride | Dex / Str |
| Handle Animal | Cha / Wis | Sense Motive | Cha / Wis |
| Heal | Int / Wis | Swim | Dex / Str |
| Intimidate | Cha / Str | Use Magic Device | Cha / Int |
| Knowledge (Dungeoneering) | Int / Wis | | |
| Knowledge (Geography) | Int / Wis | **Fly** | Dex only |
| Knowledge (History) | Cha / Int | **Spellcraft** | Int only |
| | | **Stealth** | Dex only |
| | | **Survival** | Wis only |

> **Generator mapping:** skill→ability is currently fixed. To honor this, `skill_ranks.py` (+ the skill
> definitions in `Backend/utils/data.py`) need an "allowed abilities" set per skill and a chooser that
> picks the best/most-fitting ability for the generated NPC. Compare with the existing
> *"Wisdom in the Flesh"* trait already in `data/traits.csv`, which does a narrower version of this.

### 2b. Profession as an expanded sub-system
New "Gather Information" = Cha-based subcategory of Knowledge (Local) (+½ Know. Local ranks). Professions
have rank caps (5 + CR; individual cap 10), income (½ Profession check in gp/week), associate-skill
unlocks at ranks 1/4/7/10, GM trait at 5, hero point at 15, and a **Trainer** profession that can grant
feats/traits/stats. Related feats: **True Calling**, **Multi Talented**, **Always Improving**. *(Niche
for NPC generation — low priority.)*

---

## 3. Homebrew feats

A large custom feat pool (likely the same library as `data/Metzofitz_Feats.csv`). Selection is currently
**commented out** in [Backend/utils/class_func/feats.py](Backend/utils/class_func/feats.py) (~L243–248)
→ wiring it in behind the homebrew flag is the main backlog item. Categories observed:

- **Combat/general:** Defensive Strike, Track Star, Comeback (+Improved), Greater Diehard, Incredible Resilience, Fragile Strength, Great Ability Score, Perfect Called Shot, Heroic Brawn, Legendary Brawn (Mythic), Might Makes Right, Sniper Shot, Overbear
- **Resource/Mana casting:** Unified Power, Singular Locus, Efficient Output, Life Energy, Improved/Greater Strain Recovery, Fount of Will, Overcharged
- **Bloodline/Domain/School:** Awakened Power, Charge-less Bloodline/Domain, Empowered (+Greater), Extra Power Use, Casting from Within (+Improved/Perfected)
- **Ki:** Ki Charge, Ki Barrier (Improved/Greater/Ultimate), Source of Ki, Violent Ki (Aura/Projection/Weapon), Viscous Ki (+Improved), Ki Healing
- **Armor:** Unbreakable, All Purpose Defenses, Strength of a Warrior, Dauntless Frame
- **Psionic:** Mindscape (+Greater), Instigate Psychic Duel, Psychic Combatant
- **Initiative:** Quick Action (+Mythic), Hard to Shake Off (+Mythic), Battlefield Intuition, Noble Scion, Presence of Mind, Muscle Reaction, Improved Initiative (Mythic)
- **E-Kat (hero points/luck):** Double Down, Stream of Luck, Sweet Dreams, Lucky Boy (+Very), Ass Pull, It Just Works, Middle Finger, Right of Deferment, Luck God
- **Technique (Path-of-War-like):** Adept Initiator, Burning Technique, Companion Techniques, Coordinated/Group Initiation, Extensive Technique Study, Improved Assistance, Ready Initiation, Technique Prowess
- **Profession:** True Calling, Multi Talented, Always Improving
- **Racial:** Loxo (Crush, Trunk Training, Loxo Neutrality), Kalyptran (Adaptive Evolution +Improved/Perfect), Dolistani (Dolistani Martial Casting, Martial Sage)

> **Custom races spotted:** **Loxo, Kalyptran, Dolistani** — candidates for `Backend/json/PlayableRaces.json`.

---

## 4. Feat tax / tax exemptions
Based on the Pathfinder "Feat Tax" system — many prerequisites are removed, feats are auto-granted, or
chains collapse. Affects **feat prerequisite checking** in `feats.py`.

- **Free actions for anyone with BAB ≥ 1:** Combat Expertise, Power Attack, Deadly Aim, Piranha Strike (no stat/feat prereqs). Also free: Point Blank Shot, Improved Unarmed Strike (effect, not the feat), Agile Maneuvers.
- **Weapon Finesse baked in:** all light/natural/finesse weapons may use **Str or Dex** to attack. Weapon-specific feats apply to the whole **Fighter weapon group**.
- **Auto-granted when prereqs met** (~50 feats): e.g. Mounted Combat (Ride 1), Master Craftsman (5 Craft/Prof ranks), Raging Vitality, Shadow Strike, Charming Performance, Call Out, Combat Advice, Death from Above, Taunt, …
- **Chain collapses** (`➞` = granted 2 levels later if no new prereqs; `+` = simultaneously): Arcane Strike ➞ Riving ➞ Blooded; Cleave ➞ Great Cleave + Whirlwind; Point Blank ➞ Precise ➞ Rapid Shot ➞ Manyshot; Style ➞ Secondary ➞ Final.
- **No-cost exemptions:** all Style feats, any Improved/Greater variant of a held feat, Martial/Magic/Combat Training every other tier, Extra Ki/Grit/Pool once after 2 levels.

---

## 5. Optional rule systems used (base-PF, linked from the hub)
These are standard Pathfinder optional systems the campaign turns **on** (not custom text):

| System | Link |
|---|---|
| Wound Thresholds | https://www.d20pfsrd.com/gamemastering/other-rules/unchained-rules/wound-thresholds-optional-rules/ |
| Mythic | https://www.d20pfsrd.com/alternative-rule-systems/mythic/ |
| Spheres of Power | http://spheresofpower.wikidot.com/ |
| Spheres — Seraph Feats | http://spheresofpower.wikidot.com/seraph-feats |
| Spheres — Mythic Spheres / Rules | http://spheresofpower.wikidot.com/mythic-spheres · http://spheresofpower.wikidot.com/mythic-rules |
| Aristeia (hero-point feats) | http://spheresofpower.wikidot.com/aristeia |
| Spheres of Might (combat training) | http://spheresofpower.wikidot.com/using-spheres-of-might |
| Called Shots | https://www.d20pfsrd.com/gamemastering/other-rules/called-shots/ |
| Skill Unlocks | http://legacy.aonprd.com/unchained/skillsAndOptions/skillUnlocks.html |
| Stamina & Combat Tricks | https://www.d20pfsrd.com/gamemastering/other-rules/stamina-and-combat-tricks-optional-rules/ |
| Path of War | https://www.d20pfsrd.com/alternative-rule-systems/path-of-war/ |
| Kingdom Building | https://www.d20pfsrd.com/gamemastering/other-rules/kingdom-building/ |

House notes: Stamina is free for Fighters at L1; hero-point feats act as Aristeia feats; Mythic "Boon:
Expertise" limited to class abilities you qualify for but didn't select.

---

## 6. Generator implementation backlog (derived)
Highest-value, most generation-relevant first:

1. **Wire homebrew feats** — uncomment/finish Metzofitz selection in `feats.py` behind the homebrew flag; source from `data/Metzofitz_Feats.csv`.
2. **Homebrew feat counts** — add `+2` creation feats and per-flaw feats in `level_and_bab.py` (story feats already handled).
3. **Skill alternate abilities** — add allowed-ability sets per skill in `data.py` + chooser in `skill_ranks.py` (§2a table).
4. **Skill rank changes** — `+2→+4`, 3/level cap, mental-ability pick, +2 background ranks (`skill_ranks.py`).
5. **Full HP** — max hit die per level including racial HD.
6. **Feat-tax prereqs** — relax prerequisite checks + Weapon Finesse default (§4).
7. **Custom races** — add Loxo / Kalyptran / Dolistani to `PlayableRaces.json` (needs the race stat blocks).
8. **Flaws/traits** — flaw→feat and 8-pick-4 trait flow.

---

## 7. Link index & coverage
**Deep-read** ✅ · **Indexed, not yet read** ⏳

| Sub-doc | Status | Relevance to generation |
|---|---|---|
| [Skills](https://docs.google.com/document/d/1laZ118hezgJ9AdwoXHPgKOnofRYYP7h-ciOSh54DrCE/edit) | ✅ | High |
| [Character Building](https://docs.google.com/document/d/1_OBzLlCCogTfzKdLOqhlHdQ-aZmWEXwiU3L68pV8yQI/edit) | ✅ | High |
| [Feats](https://docs.google.com/document/d/1H_5OzZSb5fd-tEkX7VYX85_aHrFjBsaESLlhwsoxJ3Q/edit) | ✅ | High |
| [Feat Tax / Exemptions](https://docs.google.com/document/d/1wv2IGBWFh4QUoCr_H5UtAsT1xxTVGNR1E_4sP-7_--w/edit) | ✅ | High |
| [Deities](https://docs.google.com/document/d/1uDLW8VEryGgC_YcvG58rn6ef0oLEtx3IhRGKkvqWFxM/edit) | ⏳ | Med (deity randomization) |
| [Rulesets/Fiats](https://docs.google.com/document/d/14EA3U5LZiBPIv0CzrcYv1--G368IcqaQ0lWSSVpXhOI/edit) | ⏳ | Med |
| [Combat References](https://docs.google.com/document/d/1ANXtDCF8-6gzV1GeRiMHHtRKFFbXA7i2SLZMCUv-zas/edit) | ⏳ | Med |
| [Luck](https://docs.google.com/document/d/1po0ieGEU2efK9iyj2QNeG0eeEyS9mXgIf6ptHE8v1pU/edit) | ⏳ | Med (hero points / E-Kat feats) |
| [Techniques](https://docs.google.com/document/d/1j7mPSoMalZE5wLs9wmwRzycNpyfNwCRhqOiCP2tG-iA/edit) | ⏳ | Med (Path-of-War-like) |
| [Spellcrafting](https://docs.google.com/document/d/1h5-RPODN97x-cs5cNkz10d65xY5-r1Y2mdikQQBbKC8/edit) | ⏳ | Med |
| [Oaths](https://docs.google.com/document/d/1v3XJO4avOaKbCf5xosZ-BHcVy2vFJPPK6RmL7_VkoSs/edit) | ⏳ | Low/Med |
| [Conditions](https://docs.google.com/document/d/133CtoP6L7NoqyA8W0znU5EfBz42LOSiXjmVPfV3X5yU/edit) | ⏳ | Low |
| [Troops](https://docs.google.com/document/d/1iPutxTRGx4JgfbYwgFLg0GcFDiPu4NXjzhXXIbPiExY/edit) | ⏳ | Low |
| [Factions](https://docs.google.com/document/d/11_gE9xAKife4Ka4ORO6VuT_wxVllV_TlKFotdXGv4rA/edit) | ⏳ | Low |
| [Calendar](https://docs.google.com/document/d/1Oh2bl9dfPQfimwmjQdL0NQWI23n6t-DEJ59WXL76ClE/edit) | ⏳ | Low |
| [Character Sheet Macros](https://docs.google.com/document/d/1IX2yRzDgke-ux4UFvxINef-njjWRhL5v8SlCsqbBTnc/edit) | ⏳ | Low |
| [Maps (Dropbox)](https://www.dropbox.com/sh/km9anbv8zxvw209/AADd7pHWrwkoIaCSy-isbb2ia?dl=0) | ⏳ | None |
