# Build Archetypes — Research, Taxonomy & Decision Engine

How the generator decides what a rolled NPC *is* — not its class, but how it actually fights.
Researched 2026-07-17 (deep-research pass), then **generalized to v3 the same day** after user
review: system-branded and one-build entries folded into generalized archetypes (see §6).

- **Roster (data):** `Backend/json/build_archetypes.json` — 33 entries
- **Engine (code):** `Backend/utils/class_func/build_archetype.py`
- **Tests:** `Backend/scripts/test_build_archetype.py` (37-fixture matrix + invariants; every
  non-Generalist archetype has a proving fixture; `... explain <fixture>` dumps scores/signals
  for weight tuning)
- **Consumers:** `main_test.py` assembles the `_build` facts and exports `build_archetype`
  (label) + `build_tactics` (playstyle sentence); the bio fact block shows both
  (`- Archetype:` / `- Tactics:` lines via `backstory.py`).

## 1. What an archetype is

An archetype is **role × playstyle**, judged from the *actual build* (weapon, armor, stats,
feats, casting, Path of War disciplines, Spheres talents, pets) — never from the class name
alone. A fighter can be an AC Tank, a Keep Away Fighter, a Switch Hitter, or a Harrier; a
cleric can be a Healer, a Self Buffer, or an Area Denier.

**The roster is deliberately generalized.** No entry is branded to a rules system or a single
famous build: Path of War initiators and Spheres practitioners classify into the *same*
archetypes as everyone else, reached through their `disc_*`/`sph_*` signals (an Iron Tortoise
warder is an AC Tank; a Primal Fury ravager is a Charger; a warlord is a Team Buffer; a
Destruction-sphere incanter is a Blaster). Named-build entries from community guides ("God
Wizard", "Reach Tripper") were folded into the generalized concepts they exemplify.

- **Axis 1 — Family (7): the role noun.** Tank · Bruiser · Striker · Skirmisher · Blaster ·
  Controller · Support. Power-source-agnostic: each family is reachable by a martial, a Vancian
  caster, a PoW initiator, and a Spheres practitioner. Synthesized from D&D 4e PC/monster roles,
  the MMO trinity + sub-roles, and MOBA class vocabulary. Social/skill archetypes were
  deliberately excluded — the roster describes round-to-round combat behavior only.
- **Axis 2 — Tactical pattern (16): the round-to-round verb.** charge-alpha,
  full-attack-grind, hit-and-run, ambush-strike, flank-precision, zone-denial,
  lockdown-maneuver, turtle-counter, anchor-guard, ranged-barrage, aimed-shot, nova-burst,
  save-or-suck, buff-and-sustain, pet-action-economy, adaptive-generalist. Compressed from
  fighting-game archetypes (rushdown/zoner/grappler/turtle), TVTropes Competitive Balance
  (Glass Cannon, Mighty Glacier, …), and wargaming tactics vocabulary (alpha strike, attrition,
  kiting, area denial) — keeping only patterns observable in a PF1e stat block. (Some patterns
  are currently unused by the v3 roster; they remain valid vocabulary for future entries.)

Playstyle stays first-class through pairings like Bruiser (stand and grind) vs Charger (alpha
strike), Self Buffer vs Team Buffer (who the buffs are for), and Magic vs Martial Battlefield
Controller (what the control is made of).

## 2. How the decision is made (deterministic scorer)

Implemented in `build_archetype.py`; identical results with or without Ollama, so the deployed
backend (no Ollama on Render) and local runs always agree.

1. **Signals.** `_signals(build)` computes ~65 named features, each 0.0–1.0, once per character
   (vocabulary in §3). Roster entries may only reference these names.
2. **Hard gates.** Per entry: `requires_any` / `requires_all` (`{signal, min}` — entry is
   *excluded*, not zero-scored, when unmet) and `vetoes` (excluded when any listed signal ≥ min).
   Gates encode categorical identity — `caster_primary` vetoes martial-only entries, which is
   the structural fix for "wizard with a backup crossbow classifies as Archer".
3. **Score.** Weighted sum of the entry's declared signals, **L1-normalized by the entry's own
   Σ|weight|** so many-signal entries can't dominate sharper profiles. Negative weights are
   anti-signals (e.g. Trickster pushes `precision` builds *out* of Harrier and Dual Wielder).
4. **Winner.** Highest score wins outright unless runners-up land within
   `CONFIDENCE_MARGIN = 0.02` — a deliberate photo-finish-only window. Within it, the lowest
   `tie_break_rank` (unique per entry; specific < generic; Generalist last) wins. When the
   backstory-API toggle is on and a genuine near-tie exists, Ollama may pick among the 2–4
   finalists using their definition+tactics text; any failure leaves the deterministic winner.
5. **Result.** `ArchetypeResult(label, tactics, family, pattern, confidence, gap, contenders)`;
   `str(result)` is the label so string consumers work unchanged. Never raises — any internal
   error returns Generalist.

`Generalist` is the sole empty-gate catch-all at max rank: it only wins when nothing sharper
is eligible. Its signal profile is a deliberately diluted "one-hot spread" (all three BAB tiers,
several weapon/armor styles) so its normalized score stays in the 0.25–0.45 band — beatable by
any entry with a real identity.

## 3. Signal vocabulary (frozen — roster entries reference these names)

All values 0.0–1.0, computed by `_signals()` from the `_build` dict `main_test.py` assembles.

**Casting** — `caster_tier` (highest castable spell level /9); `caster_primary` (magic is the
primary offense: 2nd+ level spells on a non-full-BAB chassis — a full-BAB caster like a paladin
or ranger is never caster-primary); `spell_blast` /
`spell_control` / `spell_heal` / `spell_buff` / `spell_summon` (share of notable spells per
keyword family).

**Chassis** — `bab_high` / `bab_mid` / `bab_low` (one-hot; primary class's BAB tier from
`class_data.json`).

**Path of War** — `initiator` (initiator level / character level); `disc_tank`, `disc_control`,
`disc_support`, `disc_rage`, `disc_mobile`, `disc_stealth`, `disc_ranged`, `disc_dual`,
`disc_counter` (discipline→tag table in the engine).

**Spheres** — `sphere_power` / `sphere_might` (share of chosen spheres per system);
`sph_blast`, `sph_control`, `sph_heal`, `sph_tank`, `sph_beast`, `sph_skirmish`, `sph_buff`,
`sph_summon`, `sph_grapple`, `sph_rage` (sphere→tag table); `sphere_invest` (mana pool /10).

**Weapon** — `wpn_light` / `wpn_one_handed` / `wpn_two_handed` / `wpn_ranged` / `wpn_unarmed` /
`wpn_none` (style one-hot; unarmed = Monk group or true unarmed/handwraps only — the Close
group's cestus/gauntlets are ordinary light weapons); `wpn_firearm`, `wpn_thrown` (sub-flags);
`wpn_finesse`; `wpn_reach` (weapon special or Lunge); `crit_fisher` (18–20 threat or
Improved Critical/Critical Focus — a plain 19-20 longsword is *not* a crit build);
`two_weapon`.

**Defense** — `armor_none` / `armor_light` / `armor_medium` / `armor_heavy` (one-hot); `shield`.

**Feat leanings** — `feat_melee_attack`, `feat_melee_full`, `feat_cmb`, `feat_tank`,
`feat_ranged_attack`, `feat_ranged_full`, `feat_magic_control`, `feat_magic_blast`,
`feat_magic_buff` — hits against the curated `feat_buckets.json` pools, min(1, hits/3).
Feats curated into **both** the melee and ranged buckets (Weapon Focus, …) carry no
melee-vs-ranged information and are excluded from these counts.

**Stats** — `main_str` … `main_cha` (one-hot from class main stat); `con_focus`;
`str_over_dex` / `dex_over_str`.

**Tactics & pets** — `precision` (sneak/death-attack classes or features); `stealthy`;
`mobile` (mobility feats or monk); `aoo_control` (Combat Reflexes/Stand Still/trip package);
`companion`; `summoner_pet`; `mounted`; `multiclass`; `class_split`.

**Class-identity accents** (offense/support engines invisible to spell & weapon signals) —
`kinetic_blast` (kineticist), `bomb_thrower` (alchemist), `performer` (bard/skald).

## 4. The roster (33 archetypes, by tie-break rank)

Rank order ≈ specificity: hard-gated/narrow entries first, broad ones later, the three
low-investment catch-alls (Man-at-Arms / Hedge Mage / Generalist) last. "Absorbs" records which
v2 (59-entry) labels folded into the entry.

| Rank | Label | Family | Pattern | Definition | Absorbs (v2) |
|---|---|---|---|---|---|
| 1 | Mounted Lancer | Striker | charge-alpha | Cavalry striker whose multiplied lance charge is the hardest single opening hit in the game. | Mounted Lancer |
| 2 | Mounted Archer | Skirmisher | ranged-barrage | Mounted ranged attacker who kites on horseback, firing full volleys while the mount does the moving. | Horse Archer |
| 3 | Zen Archer | Skirmisher | ranged-barrage | Unarmored Wisdom-based monk who flurries with a bow instead of fists. | Zen Archer |
| 4 | Kinetic Blaster | Blaster | ranged-barrage | Kineticist channeling at-will elemental blasts through its own body, paying in burn instead of spell slots. | Kinetic Blaster |
| 5 | Mad Bomber | Blaster | ranged-barrage | Alchemist who fights by lobbing splash-damage bombs, softening clusters before they close. | Mad Bomber |
| 6 | Eidolon Master | Support | pet-action-economy | Summoner who fights through one powerful bonded eidolon while supporting it from range. | Eidolon Master |
| 7 | Shapeshifter | Bruiser | full-attack-grind | Wildshaper or natural-weapon fighter who mauls with claw-and-bite full attacks instead of weapons. | Wildshape Mauler |
| 8 | Keep Away Fighter | Controller | zone-denial | Reach martial who fences off a zone — attacks of opportunity, trips, and braced polearms; nobody closes for free. | Reach Tripper, Reach Sentinel |
| 9 | Martial Battlefield Controller | Controller | lockdown-maneuver | Maneuver martial — grapples, trips, disarms, and control strikes that delete enemy turns instead of hit points. | Grappler, Curse Blade, Sphere Brawler |
| 10 | Switch Hitter | Skirmisher | adaptive-generalist | Combatant with full feat investment in both bow and blade, toggling on range to target. | Switch Hitter |
| 11 | Spellblade | Striker | nova-burst | Gish who channels spells through weapon strikes for combined spell-plus-steel damage. | Spellblade, Sacred Fist |
| 12 | Area Denier | Controller | zone-denial | Caster who fences off ground both ways — reach-weapon attacks of opportunity layered under control magic. | Area Denier |
| 13 | Sharpshooter | Skirmisher | aimed-shot | Firearm specialist landing high-accuracy touch-AC shots, round after round. | Deadeye Gunner, Gun Tank |
| 14 | Trickster | Striker | ambush-strike | Stealth-and-precision killer, blade or bow — sneak attacks, ambushes, and flat-footed windows. | Sneak Attacker, Assassin, Sniper, Veiled Moon Ghost |
| 15 | Dual Wielder | Striker | full-attack-grind | Two-weapon fighter converting maximum attacks per round into steady attrition damage. | Dual Wielder, Thrashing Dragon |
| 16 | Brawler | Striker | full-attack-grind | Unarmed martial artist flurrying fists, elbows, and knees — no weapon to sunder, disarm, or take away. | Flurry Monk, Broken Blade Adept |
| 17 | Charger | Bruiser | charge-alpha | Fast, lightly armored two-hander who opens every fight at a dead run with an all-out assault. | Raging Charger, Primal Fury Ravager |
| 18 | Harrier | Skirmisher | hit-and-run | Dex-based mobile melee — darts in, lands a finesse strike, and repositions before the answer comes. | Dervish Blade, Spring Attacker, Sphere Scout, Riposte Duelist |
| 19 | Beastmaster | Support | pet-action-economy | Handler who fights as a pair with a heavily invested animal companion. | Beastmaster |
| 20 | Summoner | Support | pet-action-economy | Caster who floods the field with summoned monsters, winning through sheer action economy. | Master Summoner |
| 21 | Healer | Support | buff-and-sustain | Dedicated mender who keeps everyone standing — cures, restorations, and condition removal under fire. | Combat Medic |
| 22 | Self Buffer | Striker | buff-and-sustain | Buffs itself, then wades in — the war-priest pattern: divine favor, enlarge, transformation, then steel. | Battle Priest, Sacred Fist |
| 23 | Team Buffer | Support | buff-and-sustain | Action economy spent on allies — haste, songs, commands, and inspiration over personal offense. | Battle Bard, Buffbot, Battle Commander |
| 24 | Magic Battlefield Controller | Controller | zone-denial | Caster who redraws the map — walls, pits, fogs, difficult ground, and locked doors of force. | God Wizard, Battlefield Shaper |
| 25 | Debuffer | Controller | save-or-suck | Strips enemy saves, stats, and actions — hexes, curses, and save-or-suck magic instead of damage. | Hex Debuffer, Sphere Binder, Dazing Blaster |
| 26 | Blaster | Blaster | ranged-barrage | Direct-damage caster — the biggest blast available, every single round, from spells or sphere effects. | Nuker, Destruction Adept |
| 27 | Archer | Skirmisher | ranged-barrage | Dedicated ranged combatant — bow, crossbow, or thrown steel — firing full volleys from safety. | Archer, Knife Thrower, Arcane Archer, Solar Wind Marksman |
| 28 | AC Tank | Tank | anchor-guard | Armor-and-shield wall the enemy cannot reliably hit — trades offense for a line that holds. | Shield Wall, Iron Tortoise Warder, Sphere Guardian |
| 29 | HP Tank | Tank | anchor-guard | High-Constitution soak — wins by having more hit points than the enemy has rounds. | Juggernaut |
| 30 | Bruiser | Bruiser | full-attack-grind | Two-handed Power Attacker maximizing per-hit damage through repeated stationary full attacks. | Greatweapon Bruiser, Crit Fisher |
| 31 | Man-at-Arms | Bruiser | full-attack-grind | Plain armored soldier — the guard, mercenary, or town watchman line-fighter with no specialist build identity. | Man-at-Arms |
| 32 | Hedge Mage | Controller | adaptive-generalist | Minor caster with a grab-bag spell list — the village adept who plinks, hinders, and mends as needed. | Hedge Mage |
| 33 | Generalist | Striker | adaptive-generalist | Broadly competent combatant with no dominant specialization — fills whatever gap the fight presents. | Generalist |

**How 3rd-party systems land (no branded entries):**
`disc_tank`→AC Tank · `disc_rage`→Charger · `disc_ranged`→Archer · `disc_stealth`→Trickster ·
`disc_dual`→Dual Wielder/Brawler · `disc_counter`→AC Tank/Keep Away/Harrier ·
`disc_control`→Martial Battlefield Controller · `disc_support`→Team Buffer ·
`disc_mobile`→Harrier · `sph_blast`→Blaster · `sph_control`→Debuffer · `sph_heal`→Healer ·
`sph_tank`→AC Tank · `sph_beast`→Beastmaster · `sph_skirmish`→Harrier · `sph_buff`→Team Buffer ·
`sph_summon`→Summoner · `sph_grapple`→Martial Battlefield Controller · `sph_rage`→Charger.

**Deliberate discriminators** (the pairs most likely to collide, and what splits them):
- *Self vs Team Buffer:* martial chassis (mid/high BAB, armor, melee weapon) vs support chassis
  (`performer`, `disc_support`, `sph_buff`, high buff-share on a low-BAB frame).
- *Magic Battlefield Controller vs Debuffer:* caster tier — MBC requires `caster_tier ≥ 0.44`
  (4th-level spells) and outscores on tier; Debuffer is vetoed at `caster_tier ≥ 0.8`, so
  hex-tier casters (witch, mid-tier oracle) fall to Debuffer while wall-of-force-tier full
  casters read as MBC.
- *Keep Away Fighter vs Martial Battlefield Controller:* reach + AoO package vs grapple/CMB
  package; a polearm tripper is Keep Away, a grappler is MBC.
- *Charger vs Bruiser:* Charger hard-requires a two-hander **plus** mobility/rage/Con evidence
  and is vetoed by heavy armor and shields; the default two-hander grinder stays Bruiser.
- *Bruiser vs Man-at-Arms:* real feat investment (`feat_melee_full`) pushes toward Bruiser;
  Man-at-Arms carries negative feat weights and vetoes `initiator`/sphere signals, so it only
  catches the genuinely plain soldier.
- *Trickster vs Harrier/Dual Wielder:* `precision` is a positive on Trickster and an
  anti-signal on both neighbors, so rogues land Trickster even when finessing or dual-wielding.

## 5. Sources consulted

**PF1e community build vocabulary** — Zenith Games "Comprehensive Pathfinder Guides" index +
build posts (AM BARBARIAN, Admixture Blaster, Mad Bomber, Debuffer Witch); FeeneyGames
PFGuideArchive (Treantmonk's "Being a God", Hexcrafter, Reach Cleric, Trip Builds, Summoner
guides); RPGBOT PF1e class guides; d20pfsrd (Dervish Dance, Gun Tank, Sacred Fist, lance, PoW
and Spheres pages); Paizo Advice forum threads (switch hitter, crit fisher, god wizard,
battlefield control); GITP archives; minmaxforum Sword-and-Board Handbook; Know Direction
sneak-attack primer; N. Jolly / Tark guides.

**Cross-game role taxonomies** — D&D 4e PC roles (Defender/Striker/Controller/Leader) and
monster roles (Soldier/Brute/Artillery/Skirmisher/Lurker); MMO trinity & sub-roles (main/off/
evasion tank, burst vs sustained DPS, healer/shielder/enabler); MOBA classes (Assassin, Diver,
Juggernaut, Marksman, Catcher, Enchanter); fighting-game archetypes (Rushdown, Zoner, Grappler,
Footsies, Turtle, Mix-up, Puppet); TVTropes Competitive Balance ladder; military/wargaming
tactics vocabulary (alpha strike, attrition, kiting, area denial, zone of control).

**3rd-party ground truth** — the repo's rollable PoW discipline list
(`Martial_Disciplines.json`, incl. Metzofitz homebrew) + d20pfsrd/libraryofmetzofitz discipline
pages; Spheres of Might/Power sphere pages (spheresofpower.wikidot, d20pfsrd); this repo's
`path-of-war` and `spheres-of-power` skills.

## 6. Revision history

**v1 (first-match heuristic, 18 labels).** Sharpshooter, Archer, Controller, Blaster,
Shapeshifter, War Priest, Healer, Summoner, Support, Brawler, Gish, AC Tank, HP Tank, Bruiser,
Harrier, Sword & Board, Trickster, Generalist — first-match-wins rules on class + weapon +
armor + stat. Misclassified edge cases (wizard with a backup crossbow → "Archer").

**v2 (deep-research roster, 59 entries).** The research workflow produced the two-axis taxonomy,
the signal vocabulary, and the gate/score/tie-break engine — all retained — plus a 59-entry
roster with 14 PoW/Spheres-branded entries and many named community builds.

**v3 (generalization, 33 entries — current).** User review of v2: the PoW/Spheres-branded
entries were poorly made, one-build labels (God Wizard, Curse Blade) too cute, and
Reach Tripper/Reach Sentinel sliced one concept too thin. v3 rebuilt the roster from the v1
labels plus the strong v2 survivors and new generalized pairs (Self vs Team Buffer, Magic vs
Martial Battlefield Controller, Keep Away Fighter). Every v2 entry folded into a v3 home (table
in §4); 3rd-party builds now reach generalized entries through their `disc_*`/`sph_*` signals.
Engine-side, three refinements came out of v3's live-fire sweep (200 generated characters):
1. Generalist's score profile became a one-hot spread so multiclass martials can't ride
   `multiclass`/`class_split` past real identities (a fighter/warder scored 0.651 as Generalist
   vs 0.655 as AC Tank).
2. `_signals()` strips parenthetical class qualifiers, so "summoner (unchained)" etc. hit the
   class-identity checks (`summoner_pet`, `precision`, `stealthy`, `mobile`, …) — an unchained
   summoner had classified as Spellblade.
3. `caster_primary` dropped its bare `highest >= 4` arm: a full-BAB chassis is never
   caster-primary, so high-level paladins/rangers stopped being vetoed out of every martial
   archetype (a paladin 13 had fallen through to Generalist).

Carried-over v2 engine fixes that remain load-bearing: `crit_fisher` ignores plain 19-20
threat ranges; dual-curated (melee+ranged) feats are excluded from feat leanings;
`CONFIDENCE_MARGIN` = 0.02 photo-finish window; `wpn_unarmed` restricted to the Monk
group/true unarmed.

## 7. Tuning workflow

1. Reproduce: `C:\Python310\python.exe Backend/scripts/test_build_archetype.py explain <fixture>`
   → top-5 normalized scores with per-signal contributions + the live signal vector.
2. Adjust the roster entry's weights/gates in `Backend/json/build_archetypes.json` (prefer a
   discriminating signal or gate over a tie_break_rank change; rank settles coin flips only).
3. Re-run the suite; it enforces the full 37-fixture matrix, determinism, api-parity,
   never-raises, and roster mechanics (known signals, unique ranks, one catch-all).
