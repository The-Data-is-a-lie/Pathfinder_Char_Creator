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
