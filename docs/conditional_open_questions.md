# Conditional curation — open questions

Things the 2026-07-22 curation sweep could not settle from source text alone. Each needs a check
against a live FoundryVTT world; none is blocking, and all are currently encoded the safe way.

## 1. Three feats whose modifier may double-apply — CHECK IN FOUNDRY

These were authored with a structured `modifiers[]` entry, then deliberately reduced to **rider text
only** because pf1 may already apply the same bonus natively. Under-applying is visible on the roll
card and easy to fix; double-applying looks correct and is nearly impossible to notice in play.

| Feat | What was removed | What to check |
|---|---|---|
| `Two-Handed Thrower` | `floor(1.5*@abilities.str.mod)` damage | Does pf1 already apply ×1 Str to a two-handed thrown weapon? If it applies only ×1, the feat's top-up to ×1.5 is `floor(0.5*@abilities.str.mod)`, not the full 1.5×. |
| `Two-Weapon Rend` | `1d10+floor(1.5*@abilities.str.mod)` damage | Same Str question. The `1d10` itself is safe and could be restored alone. |
| `Improved Low Blow` | `+2` attack (crit confirmation) | Two issues: the +2 may already include the base low-blow racial trait's bonus (automated elsewhere), and a confirm-only bonus has no distinct modifier target — an `attack` modifier would wrongly buff the initial roll too. |

To restore any of them, put the modifier back in `Backend/json/feats/feat_conditionals.json` for that
feat. The rider text already describes the effect, so nothing is lost meanwhile.

## 2. Confirm-only bonuses have no schema slot — RESOLVED (2026-07-23)

The premise was wrong: pf1 **does** expose a confirm slot. An `attack` modifier's `critical` field
takes `"crit"` (labeled "Critical Confirm Bonus"), and `chat-attack.mjs` pushes `attack.crit`
conditional parts **only** onto the confirmation roll while `attack.normal` parts go **only** onto
the initial roll (`partID = target.subTarget.critical`). So `critical:"crit"` is the confirm-only
slot — and, conversely, every plain `attack`/`normal` modifier had been silently applying to the
initial roll *only*, never the confirmation.

What changed:
- The 7 confirm-only feats (`Object Of Legend`, `Improved Low Blow`, `Planar Wild Shape`,
  `Net and Trident`, `Demonic Nemesis`, `Greater Snap Shot`, `Desperate Swing`) now carry a
  structured `{target:"attack", critical:"crit"}` modifier; the redundant "+N to confirm" prose was
  trimmed from each name. (`Redemption` turned out to be an initial-roll reroll bonus, not
  confirm-only, and was left alone.)
- A curated audit of the 127 hand-curated `attack`/`normal` modifiers added a `critical:"crit"`
  **twin** to every *standing* to-hit bonus (a bonus scoped to a state/duration/creature-type, which
  RAW applies to the confirmation roll too): 34 feats, 8 class-feature powers, and the 9 bane-family
  weapon qualities. Bonuses tied to one declared roll, penalties, stat-swaps consumed per-attack, and
  combat-maneuver checks (which don't confirm) were left `normal`-only — under-applying is visible
  and safe, over-applying is not.
- `Earth Child Topple` was reclassified `normal`→`crit`: the feat grants Wis to confirmation and to
  trip maneuvers, *not* to normal attacks, so the `normal` modifier had been over-applying.
- Six weapon **burst** qualities (`Flaming/Icy/Shocking/Corrosive Burst`, `Thundering`, `Shattering`)
  used `critical:"onCrit"` — never a pf1 value; pf1 deletes an unknown `critical` on the next sheet
  edit, silently breaking the burst dice. Corrected to `crit` (rolls in `critParts`, repeated
  `critMult-1` times — exactly burst RAW). The validator whitelist, which carried the bogus `onCrit`
  and lacked `crit`, was corrected to `{normal, crit, nonCrit}`.

Follow-up (not done here): the 18 PoW/Spheres/spell subsystem `attack`/`normal` modifiers
(`maneuver_changes`, `combat_talent_changes`, `spell_changes`) were out of scope; they get the same
standing-bonus twin pass under their own decision docs.

## 3. Source-data defects — AUDITED AND FIXED (2026-07-23)

All 18 pools were audited for the defect signatures behind the five the sweep tripped over. Raw hits
were 177 (10.1% of powers), but triage reduced that to **13 real defects**: 60 hits were terse
summaries without a full stop, 92 were complete phrases missing only punctuation, and all 7
"foreign-class" hits were legitimate cross-class talents (a ninja trick called *bomber* really does
grant alchemist bombs). Each real defect was re-checked against d20pfsrd / Archives of Nethys and
patched as a surgical text edit — 13 changed lines across 7 files, no reformatting.

| Pool file | Defect | Fix |
|---|---|---|
| `oracle.json` ×3 | Three revelation keys fused the **tail sentence of the previous power** onto the next power's name (`"…treat it as a wall of force Spray of Shooting Stars"`, same for `Moonlit Script`, and `"At 15th level…greater prying eyes Face in the Crowd"`) | keys restored, and the stolen sentence given back to `Moonlight Bridge` (Heavens + Lunar) and `Eyes of the Streets` |
| `witch.json` | `Cursed Wound`'s key held the first half of its own benefit text | key restored to `Cursed Wound (Su)`, text reassembled |
| `ninja.json` | `deadly shuriken`: "highest base attack bonus 5" | `-5` (d20pfsrd) |
| `fighter.json` | `steel headbutt`: "base attack bonus  5" | `-5` (AoN) |
| `barbarian.json` ×2 | `ancestor totem` ended `raging.a`; `beast totem, greater` ended `…rpg.) source` | residue stripped |
| `alchemist.json` | `greater change alignment` cut mid-word in a flavour sentence | trimmed to the d20pfsrd benefit ending |
| `vigilante.json` | `Renown` truncated at "…gained renown; he " | AoN verbatim ending restored |

**Not defects after checking the source** — left exactly as they are:

- `magus.json` / `flamboyant arcana` — the arcanum genuinely grants the *derring-do* and *opportune
  parry and riposte* **swashbuckler deeds**, so the panache text is correct content, not a bad paste.
- `magus.json` / `vision-clouding strike` — d20pfsrd really does read `DC = 1/2 the magus's level +
  his Intelligence modifier`, with no `10 +` base. Unusual for PF1, but faithful.
- `oracle.json` / `temporal celerity` vs `war sight` — the Time and Battle mysteries genuinely share
  near-identical initiative wording; the duplicate-text flag was a false positive.

**A parser bug, not a data bug:** four investigator talents (`Numerical Alchemy`,
`Investigator's Certainty`, `Relic Researcher`, `Signature Skill`) stored their text under a
capitalised `"Benefits"` key. `build_class_feature_changes.entry_text()` matched only lowercase and
then excluded the key from its fallback branch, so their text was dropped entirely and they reached
the curation agents blank. `entry_text()` is now case-insensitive.

## 4. Pool DC abilities still marked `assumed` — RESOLVED (2026-07-23)

A scan of every pool's own DC sentences reclassified all nine `assumed` pools (the ability was kept
in every case; only the confidence changed). This table is **offline-only** — imported by the
curation scripts, never by `main_test.py` — so the relabel has no runtime effect; it only makes the
metadata honest for the next curation pass. The DCs already baked into curated entries are literal
formulas in `class_feature_effects_overrides.json`, all spot-checked to use the table's ability
(the one apparent outlier, `mighty ambush` keying off Str, is correct — its own text reads "the
higher of Str and Dex," a `dc_stated` case that beats the pool default).

A new confidence **`rules`** was added for pools whose DC ability is fixed by the governing
subsystem's own rules rather than stated in the pool text (not a guess): `ki_powers` (Wis),
`discoveries` (Int), `mercy`/`cruelty` (Cha), `social_talents` (Cha). The rest moved to `varies`
(`rogue_talents`, `vigilante_talents`, plus `slayer_talents` and `curses`, which the scan showed
mix abilities) or `stated` (`investigator_talents`). `assumed` is now unused but kept documented for
a future pool whose ability is a genuine unverified guess.
