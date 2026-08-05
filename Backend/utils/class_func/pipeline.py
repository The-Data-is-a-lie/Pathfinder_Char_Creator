"""Phase contracts for the generation pipeline.

``generate_random_char`` runs eight phases over one shared character object, and every rule about
what has to happen before what is written as a comment:

    main_test.py:305  "stats after level (because we roll inherents which depend on level)"
    main_test.py:490  "MUST run before skills_selector"
    main_test.py:632  free BAB-1 feats must be seeded before any feat chooser

Nothing enforced any of them. Reordering two calls didn't raise -- it produced a quietly worse
character: zero Profession ranks, undercounted inherents, empty bonus spells. Those are exactly the
bugs that surface weeks later on a Foundry sheet with no idea what caused them.

``@phase`` turns a comment into a checked contract. ``requires`` names attributes that must already
be set on the character; ``provides`` names what the phase is responsible for setting. A missing
requirement raises immediately, naming the phase and the attribute, instead of degrading silently.

    @phase(requires=['level', 'classes'], provides=['stats'])
    def roll_and_assign_stats(character, num_dice, num_sides, inherents):
        ...

The character object is the first positional argument by convention -- that is where the pipeline's
state already lives (140 assignment sites across 27 modules), so phases read and write it directly
rather than introducing a second place to look for state.

Sealing: some ordering constraints aren't "is this attribute set" but "is this bucket finished".
``character.data_dict['class features']`` always exists; the question is whether the choosers have
run. ``seal``/``require_sealed`` express that.

HOW HONEST SHOULD `requires` BE?
-------------------------------
The rule, decided before the remaining phases were extracted so they would not each answer it
differently. It matters because the blocks still to be split are not like the first two: the
class-options block reads twenty-plus attributes, and writing all twenty into a decorator rebuilds
the unreadable wall the decorator was meant to replace -- except now it fails at import time when it
drifts, which is worse than a stale comment, not better.

**`requires` names only what crosses IN from outside the phase.** Two to four attributes, the ones
another phase had to produce first. Not everything the block reads: a value the block computes and
then consumes is not a dependency, it is a local. The test for whether a name belongs is "could a
reordering make this absent?", not "does this code touch it?".

**`provides` is exhaustive.** The asymmetry is deliberate and it is free: `provides` is checked on
the way OUT, so an over-declared name fails on the very first run, loudly, at the phase that owns
it. There is no drift to accumulate. `requires` has to be curated because it fails on the way in,
where a wrong entry blocks a legitimate order.

**Bucket completion is a seal, not a `requires` entry.** `require_sealed` is for the state that
always exists and is only meaningful once its producers have run.

**A seal proves ordering. It does not prove completeness** -- and that gap is closed by a different
mechanism rather than by a finer-grained seal. `seal('class options')` says the block ran; it says
nothing about whether the psionic chooser inside it ran. Splitting into `seal('class options:
psionics')` just reinvents the twenty-entry `requires` with worse ergonomics, and it still cannot
catch a chooser nobody remembered to seal.

So completeness is proved by census instead, in the sweep tests, where it belongs: over many
generations, every chooser must fire at least once, and a count of zero fails the run and says so.
`test_house_invariants.py` already does this for bonded creatures and occult choices ("no bonded
creature was granted in N generations -- every companion check proved nothing"), and
`test_skill_ranks.py` does it for the Multi Talented ordering branch. The two mechanisms answer
different questions and neither substitutes for the other: the seal fails in-process the moment
order is wrong, the census fails in CI when coverage silently drops to zero.
"""
import functools

# Attributes whose value is legitimately falsy when set (0, '', {}), so presence must be tested with
# hasattr rather than truthiness. Everything else also accepts "set but empty" -- the check is about
# the phase having RUN, not about it having produced something non-empty.
_SEAL_ATTR = '_sealed_buckets'


class PhaseOrderError(RuntimeError):
    """A phase ran before something it depends on."""


def phase(requires=(), provides=()):
    """Declare a pipeline phase's prerequisites and outputs.

    ``requires`` are attribute names that must exist on the character before the phase runs;
    ``provides`` are the ones it is expected to set, checked on the way out so a phase that silently
    stops setting something is caught at its own boundary rather than at a distant reader.
    """
    def decorate(func):
        @functools.wraps(func)
        def wrapper(character, *args, **kwargs):
            missing = [name for name in requires if not hasattr(character, name)]
            if missing:
                plural = len(missing) > 1
                raise PhaseOrderError(
                    f"phase {func.__name__!r} requires {', '.join(missing)} on the character, "
                    f"but nothing has set {'them' if plural else 'it'} yet -- "
                    f"the phase that provides {'them' if plural else 'it'} must run first")
            result = func(character, *args, **kwargs)
            not_set = [name for name in provides if not hasattr(character, name)]
            if not_set:
                raise PhaseOrderError(
                    f"phase {func.__name__!r} declares it provides {', '.join(not_set)} "
                    f"but did not set {'them' if len(not_set) > 1 else 'it'}")
            return result

        wrapper.requires = tuple(requires)
        wrapper.provides = tuple(provides)
        return wrapper
    return decorate


def seal(character, name):
    """Mark a shared bucket as finished, so later phases can require it.

    For state that always EXISTS but is only meaningful once its producers have run --
    ``data_dict['class features']`` is `{}` from the first line of generation, so a presence check
    can't tell "no choosers ran" from "this class has no choices"."""
    if not hasattr(character, _SEAL_ATTR):
        setattr(character, _SEAL_ATTR, set())
    getattr(character, _SEAL_ATTR).add(name)


def is_sealed(character, name):
    return name in (getattr(character, _SEAL_ATTR, None) or set())


def require_sealed(character, name, reader):
    """Raise unless ``name`` has been sealed. ``reader`` names the code that needs it, so the error
    says who was reading and what hadn't finished."""
    if not is_sealed(character, name):
        raise PhaseOrderError(
            f"{reader} reads {name!r} before it was sealed -- the phase that fills it must run "
            f"first and call pipeline.seal(character, {name!r})")
