# 01 — How are a companion's attacks and skills derived?

Type: grilling
Status: resolved (2026-08-03)
Blocked by: —
Map: [Companion sheets](../map.md)

## Answer — every number, and who owns it

Built as `Backend/utils/class_func/companion_stats.py`. The module docstring is the live version of
this table; what follows is the reasoning, which code cannot hold.

| field | source | new or reused |
|---|---|---|
| `abilities` | species `starting statistics` (absolute) + merged deltas + the chassis row's `str/dex bonus`, which PF1e adds to **both** Str and Dex | new |
| `hp` | chassis `hd` x the tier's hit die + Con mod per HD | rule reused, code new |
| `ac` / `touch_ac` / `flat_footed_ac` | 10 + size + Dex + natural armour (species `ac` + merged delta + the chassis row's own `natural armor bonus`) | new |
| `saves` | chassis `fort`/`ref`/`will` — these **are** the base saves — + Con / Dex / Wis | new |
| `bab` | chassis `bab`, verbatim | new |
| `cmb` / `cmd` | BAB + Str + size special; 10 + BAB + Str + Dex + size special | new |
| `size`, `speed` | the merged block (both are REPLACE fields) | new |
| `attacks` | parsed from the `attack` prose | new |
| `skills` | chassis `skills` total, spent over the RAW animal list, capped at HD | new |
| `feats` | already resolved by `animal_companions.animal_feats` | reused |

**Nothing on the PC side was reusable**, which the ticket suspected and is worth recording as a
finding rather than a guess. `hp_rolls.roll_hp` and `skill_ranks.skill_rank_budget` both iterate
`character.classes`; a companion has none, and the chassis table hands over absolute totals rather
than per-level rates. What carries is the **rule**, not the code — `homebrew_enabled` is imported so
the maximised-HP house rule cannot drift apart from the PC's, and that is the only shared symbol.

### Attacks

The prose is regular enough to parse: `[<count> ]<name> (<damage>[ plus <rider>])`, comma-separated.
The bonus is **BAB + Str + size**, and every natural attack in a printed routine is **primary** — the
−5 secondary penalty never applies to what is written there, so all lines sit at full BAB. Damage is
as printed plus Str, except that PF1e gives **1.5x Str to a creature with exactly one natural
attack** — rounded **down**, and a Str *penalty* applies at 1x. (`round(str_mod * 1.5)` would turn a
+5 into +8 under banker's rounding; the code floors instead.)

### Skills

**The house rank floor does not carry over, and that is the answer to the ticket's sharpest
sub-question.** `skill_ranks.class_skill_points` floors *a 2-ranks-per-level class* to 4. An animal
has no class and no per-level rate — the chassis row gives one absolute total — so there is nothing
for the floor to key off. The per-skill cap is RAW (**HD**) for the same reason: the house 3x cap
multiplies a *character* level the creature does not have. This matches the stance `animal_feats`
already took on the feat economy, so the companion is consistently "house rules apply to dice, not
to class-shaped budgets".

Allocation follows the PF1e animal-companion rule directly: at Int 1–2 it may take ranks only in
Acrobatics, Climb, Escape Artist, Fly, Intimidate, Perception, Stealth, Survival and Swim; at Int 3+
it may buy any skill (only the **griffon** reaches that branch — the Int census is 1×33, 2×138,
5×1, **None×24**). A **mindless** creature — that `None`, which is the vermin and most of the plants
— gets **no ranks at all**, because PF1e says it cannot hold them; the chassis row still offers a
total, since that table was written for animals. Two further refinements the rules leave open:
**movement-gated skills are dropped**
unless the merged `speed` string actually carries that mode (a wolf has no business with Fly ranks),
and **Perception is spent first**, the rest round-robin over a shuffled queue. That shuffle is the
only randomness in a stat block, and it draws from a **per-creature `random.Random`**, never the
global stream — otherwise adding a companion's skills would churn every downstream roll for that
character and every future golden diff would carry the noise.

### The derived middle

CMB/CMD, the size modifiers and the natural-armour stack are all in the table above; the D5 repair
being done is what makes the ability scores feeding them trustworthy, as the ticket noted.
[Ticket 04](04-size-change-double-count.md) settles the one place two authorities overlap.

### Named holdbacks

- **`progression_override` is prose.** The 17 archetypes carrying it record `why` / `confidence`,
  not a structured veto, and `SESSION_PLAN.md` §3's scope boundary forbids building a classifier for
  it. The stat block therefore carries an `unapplied` note rather than implying it was honoured.
- **Reach is not emitted** — it depends on tall vs long and the data records neither. `space` is.
- **Quadruped CMD vs trip (+4)** is not modelled; the data does not say which bodies are quadruped.

## Question

§8's *The snapshot* section specs how the advancement block **merges** — per field, `size`/`attack`/
`speed` replace, `ac` and ability scores add, the rest append. It does not spec how any of that
becomes a **number on a sheet**, and that is the whole of #31.

Three sub-questions, all currently unanswered:

**Attacks.** `Backend/json/animal_choices.json` stores the attack routine as prose — `"bite (1d6)"`,
`'40 ft. '` — but both renderers want structure. The web sheet's `newCompanion()`
(`Pathfinder-Character-Sheet/scripts/tabs/companions.js:25-42`) declares
`attacks: [{name, atk, dmg}]`; a pf1 Actor wants attack *items*. So: does the backend parse those
strings into structured lines, and if so where does the **attack bonus** come from — the chassis
row's BAB plus Str/Dex and size, computed by us? The PC side already has this machinery; it is not
obviously reusable for a creature with no class and no equipment.

**Skills.** The house skill-rank floor lives in `Backend/utils/class_func/skill_ranks.py` and is
deliberately class-name-agnostic (§8 says it "should stay that way"). But an animal has **no class**
and no skill list — the chassis row in `Backend/json/animal_companion.json` gives a rank count and
nothing about allocation. Which skills does a companion put ranks into, and does the house floor even
apply to a creature that never had a class skill list?

**The derived middle.** CMB/CMD, size modifiers to AC and attack, and the natural-armour stacking
that the D5 repair exists to make safe. `species_stats` after the merge carries `"+N natural armor"`
strings; something has to turn those into an AC.

The answer should be concrete enough that #31 is mechanical: name the source of each number in the
`stats` block (`hp`, `ac`, `saves`, `bab`, `cmb`/`cmd`, `abilities`, `size`, `speed`, `attacks`,
`skills`), and say explicitly which existing helper is reused versus what is new. Where a PF1e rule
is being applied, cite it; where a house rule is, say which and why it carries over to an animal.

Worth checking while grilling: `Backend/scripts/validate_companion_data.py` already asserts the PF1e
size-up package holds, so the ability scores feeding these formulas can be trusted post-repair.
