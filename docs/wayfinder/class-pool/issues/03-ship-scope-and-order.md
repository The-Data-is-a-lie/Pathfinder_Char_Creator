# 03 — Which occult classes ship, in what order, and which of them degrade?

Type: grilling
Status: resolved (2026-08-03) -- answered by the build; see feature_spec_todo.md section 10
Blocked by: 01 (resolved), 02 (resolved)
Map: [Class pool](../map.md)

## Question

Given the census (01) and the onboarding checklist (02): **which of the six Occult Adventures classes
enter the random pool, in what order, and at what fidelity?**

This is the scope decision the whole map turns on, and it is the one that fixes what §10 promises.

### Three dispositions, not two

§8 settled the shape of this question for bonded creatures and the ruling should be reused unless
there is a reason not to: the eidolon **degrades rather than suppressing the summoner**. The class
stayed rollable and emitted a named base form plus text, instead of being held out until evolutions
could be modelled. Applied here, each class lands in one of three states:

1. **Full support** — rolls, makes its class-specific choices, renders on both sheets.
2. **Degraded** — rolls and generates a valid character, but its bespoke subsystem is stubbed: the
   feature is named and described, nothing is *chosen*. The character is playable with a human
   filling the gap.
3. **Held out** — stays in `occult_classes`, with a named blocker published in §10.

The question is which class gets which, and the honest answer may be different per class: the
mesmerist may be a full-support one-shot while the kineticist is held out.

### The sub-questions

- **Is "degraded" acceptable here?** A degraded eidolon is one feature on a summoner's sheet. A
  degraded kineticist is a character whose *entire* class is wild talents — there may be no playable
  character underneath the stub. Where is the line between "degrades gracefully" and "reads as
  broken"? The companion map asked exactly this and left it in its fog; here it is load-bearing.
- **Does the medium fit the generator's model at all?** Its spirit is a daily choice and the
  generator emits static snapshots. Rolling one spirit and freezing it is a *house ruling*, not a
  rendering decision — decide it deliberately or hold the class out.
- **Order.** Ship the data-shape adds first to prove the onboarding checklist works end to end, then
  the bespoke engines? Or one vertical slice first, all the way to a Foundry import, to find the
  renderer problems early? §9 did the former across twelve classes; §8's build did the latter.
- **All at once or in waves?** Six classes arriving together roughly doubles the random pool's occult
  share, which changes what a batch of rolled NPCs looks like. That is a play-feel consequence worth
  naming, not just an engineering one.

### Constraint

Whatever ships must ship **completely enough to audit**. [Map: Class choices](../../class-choices/map.md)
blocks on this ticket precisely so its audit covers the final class list — a class that enters the
pool *after* that audit has been done gets no coverage. So a class shipping in state 2 (degraded)
must have its degradation written down here, or the audit will read it as a bug.

### What "resolved" looks like

A per-class disposition table (class → full / degraded / held out → the reason), a ship order, and,
for anything degraded, exactly what the stub emits. Anything held out gets its blocker named in words
§10 can publish verbatim. If a class turns out to sit past this map's destination entirely, rule it
**out of scope** on the map rather than resolving it here.
