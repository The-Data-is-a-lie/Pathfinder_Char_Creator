# 05 — Reconcile the scraped class tables against RAW and the house rules

Type: research
Status: open
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

_Unresolved._
