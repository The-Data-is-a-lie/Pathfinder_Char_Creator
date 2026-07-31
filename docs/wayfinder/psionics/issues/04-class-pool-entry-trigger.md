# 04 — How do psionic classes enter the random pool, and what turns them on?

Type: grilling
Status: resolved
Blocked by: 01
Map: [Psionics](../map.md)

## Question

Twelve new classes is a large change to the class pool — enough to noticeably shift what the
generator produces by default. The repo has three precedents and they disagree:

- **Path of War**: no flag at all. Classes are in the pool; being an initiator is a consequence of
  being rolled. Foundry-unready classes are held back by name in `pow_classes_pending_foundry`.
- **Spheres**: an API-exposed opt-in `spheres_of_power` flag, default off.
- **Metzofitz feats**: gated behind an internal homebrew flag with no API surface.

Decide: all 12 at once or a staged subset; flag-gated or class-driven; and if flagged, which
precedent.

Two constraints the answer must respect:

- Any new **request** field must be popped **by name** in `Backend/app.py` before the positional list
  is built (`process_input_values`, `input_values[0..18]`), and read by name in both the web sheet's
  `generate.js::buildPayload` and the module's `button.js`. Inserting a key mid-object silently
  corrupts every downstream argument.
- Each class needs a `class_data.json` entry and a `data.good_saves` entry or
  `Backend/scripts/test_house_invariants.py` fails. `Backend/scripts/build_pow_class_data.py` is the
  batch-merge template.

## Answer

**The Path of War precedent: no flag at all, all twelve at once, holdbacks by name.**

The twelve get `Backend/json/class_data.json` entries and `data.good_saves` rows (batch-merged via
the `build_pow_class_data.py` template) and are in the random pool by default. Being a manifester is
a consequence of being rolled, exactly as being an initiator is.

Holdbacks go in a new `data.psionic_classes_pending` list, mirroring `pow_classes_pending_foundry`
and read by the same `Backend/utils/util.py::_available_class_pool`. It starts empty; a class only
enters it by earning a holdback under [ticket 08](08-bespoke-subsystems.md), and §9 records what it
is waiting on.

Why not the Spheres flag. Spheres is a *replacement* subsystem for casting, so opting in is a real
campaign choice; psionics is *additive*, like Path of War. And the cost is not symmetric — a new
request field has to be popped by name in `app.py::process_input_values` before the positional list
is built, then read by name in the web sheet's `generate.js::buildPayload` and the module's
`button.js`. That is three plumbing sites across two repos plus a setting users must find, to buy a
switch nobody asked for.

**Accepted consequence, stated plainly:** the pool is 43 classes today (51 `class_data` keys minus 6
occult minus 2 PoW-pending). Twelve more makes psionics roughly **12 of 55 — about 22% of every
default random roll**. That is a deliberate, visible shift in what the generator produces, and it is
reversible in one line by populating `psionic_classes_pending`.

Also settled here: the **manifesting ability gets its own map in `data.py`**, not an entry in
`data.caster_mod`. Power points are not spells-per-day, and overloading the caster tables would make
manifesters look like casters to every downstream consumer of `data.base_classes`.

Rejected: *Spheres-style opt-in flag, default off* (three-repo plumbing, hides the content);
*flag defaulting on* (same plumbing cost, buys only an off switch).
