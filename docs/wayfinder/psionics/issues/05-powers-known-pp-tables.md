# 05 — Reconcile the scraped class tables against RAW and the house rules

Type: research
Status: resolved
Blocked by: 01
Map: [Psionics](../map.md)

**Narrowed 2026-07-31 by [ticket 01](01-inventory-packs-source.md), which sourced the tables.**
This ticket no longer produces data — `Backend/json/class_data/psionics/psionic_classes.json` and
`psionic_powers_known.json` already hold real `bab` / hit die / skill points / good saves and 20-row
`pp_per_day` / `powers_known` / `max_power_level` progressions for all twelve classes. What is left
is judging them.

## Question

The Metzofitz wiki is the locked source of truth, and one strong cross-check already passed: every
manifesting class's power-points column matches one of `pf1-psionics`' three hardcoded progressions
exactly. But the wiki is a *homebrew republication* of Ultimate Psionics, and nobody has checked
whether it diverges from RAW anywhere it matters.

Settle, per class:

- **Which of the twelve actually manifest, and in what sense.** The scrape says the **soulknife has
  no power points and no powers known at all**, and the **aegis has power points but no powers-known
  column**. If that is right, "manifester" is not one category but three, and the payload
  ([ticket 06](06-manifesters-payload-shape.md)) has to model that.
- **Where the wiki disagrees with d20pfsrd's Ultimate Psionics pages.** Three rows look worth
  checking against RAW before they become `class_data.json` entries: **voyager** (d6 hit die with
  medium BAB and 6 + Int skills is an unusual combination), **vitalist** (d6 / low BAB), and
  **dread** (6 + Int). Report agreement or divergence with a citation; do **not** "fix" the wiki —
  it is the campaign's authority, and a deliberate divergence is a finding, not a bug.
- **Whether any house rule in the OKF `pathfinder` bundle deviates** from either — particularly
  around skill ranks, where `docs/plan_1.0_finish.md` already records the house numbers as suspect.
- **The manifesting ability per class**, which the scrape does not derive: psion is Int, wilder is
  Cha, psychic warrior is Wis, and the rest need sourcing. Casters need this for `data.caster_mod`
  and it has no home in the scraped data yet.
- **Bonus power points from a high manifesting ability** — the psionic analogue of
  `Backend/json/spells_from_ability_mod.json`. Not scraped; find out whether it is a table or a
  formula.

Deliver findings plus provenance per class. Do not design the payload — that is ticket 06.

## Answer

Run as a **scrape-error detector**, not a RAW audit — the wiki is the locked source of truth, so RAW
is only a control sample. A mismatch means either our parser misread the page (fix it) or Metzofitz
changed it deliberately (record it). Result: **eleven of twelve classes match RAW exactly, and the
parser is not at fault anywhere.**

### The three suspicious rows are all correct

All three the ticket flagged check out against d20pfsrd and against the wiki's own wikitext:

- **voyager** — d6 hit die with medium BAB and 6 + Int skills really is what *Psionics Augmented*
  wrote. Unusual, not wrong.
- **vitalist** — d6 / low BAB confirmed.
- **dread** — 6 + Int confirmed.

Highlord and voyager have no d20pfsrd page at all (*Psionics Augmented* is not OGL-mirrored there);
both were verified against the wiki wikitext and published reviews instead.

### The one real divergence was not on the watch list

**Psychic warrior.** RAW gives it good Fort **and** Will. The wiki gives it **good Fort only** — poor
Will, +6 rather than +12 at level 20 — and replaces its feature track wholesale with a Path system
(Warrior's Path / Path Skill / Twisting Path / Pathweaving / Eternal Warrior) that does not exist in
RAW. Verified directly against the wiki's `api.php` output, not just our scrape, so this is a
**deliberate house divergence, not a parser artifact**. Recorded in §9. **Do not "fix" it back to
RAW** — the wiki is the campaign's authority, and this is exactly the case the ticket was written to
distinguish.

### Manifesting ability, all twelve

Derived from each class's own power-points prose, which the scrape had already captured:

| Ability | Classes |
|---|---|
| **Int** | aegis, cryptic, psion, tactician, voyager |
| **Wis** | marksman, psychic warrior, vitalist |
| **Cha** | dread, highlord, wilder |

This confirms the three-category split [ticket 06](06-manifesters-payload-shape.md) models:
**soulknife has no power points at all** (the mind blade runs off a granted Wild Talent / Psionic
Talent, not an ability-scaled reserve — no manifester level, no powers known), and **aegis has
Int-keyed power points but no powers-known list** (they fund Augment Suit instead).

### Bonus power points — a formula, not a table

```
bonus_pp = floor(key_ability_mod × manifester_level / 2)
```

From d20SRD's *Ability Modifiers and Bonus Power Points*, unchanged in Ultimate Psionics. Separately,
a **key ability score of 9 or lower means the class cannot manifest at all** — a distinct gate from
the bonus, and one the generator must honour when it rolls stats. This is simpler than the caster
analogue: no `spells_from_ability_mod.json` equivalent is needed.

### House rules

**None specific to psionics** in the OKF bundle. The universal 2→4 skill-rank floor in
`Backend/utils/class_func/skill_ranks.py` is class-name-agnostic, so it applies to psion's and
vitalist's RAW `2 + Int` automatically once they are wired in — no psionics-specific handling, and
the scraped JSON correctly preserves the RAW value rather than the house-adjusted one. That is the
right layering: data holds the source value, code owns the house transform.

### Action items for the scraper (P2)

1. **No re-scraping of bab / hit die / skill ranks / saves.** All twelve are correct as captured.
2. Add **`manifesting_ability`** to each class's `derived` block — regex over the already-captured
   power-points feature prose, per the table above.
3. Add the **bonus-PP helper** `floor(mod × ML / 2)` plus the score-≤9-cannot-manifest gate.
4. **Special-case soulknife (no PP mechanic) and aegis (PP but no powers-known)** everywhere that
   logic is consumed — not just in the payload.
5. Cosmetic but load-bearing for the `class_data.json` merge: `derived['hit die']` carries a trailing
   period (`"d6."`) and `derived['skill points at each level']` is a **string** (`"2"`). Both need
   normalising to the shapes `class_data.json` expects.

*(Checked and dismissed: the `` seen in `class skills` prose while investigating is a Git-Bash
console rendering artifact. All five files contain **zero** U+FFFD; the byte is a real U+2019.)*
