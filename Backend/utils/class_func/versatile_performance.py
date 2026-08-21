import random

from utils.class_func.generic_func import class_entry_for


def versatile_perfomance(character):
    """The bard's three performance choices, each on its own schedule.

    WHAT THIS USED TO BE, and why it is worth knowing: a 70-line picker that rolled versatile
    performances, martial performances and expanded versatility, returned all four of its results
    in a tuple -- and had the tuple discarded at the call site. Nothing in Backend/ read any of it,
    so every bard shipped an empty class-features dict. Class-choices ticket 02 found it.

    Three things changed when it was wired up:

    1. THE PICKS LAND. Each pool is now an ordinary bucket in `class features`, chosen by
       generic_class_option_chooser against class_data/bard.json, so both renderers can reach them
       and validate_class_choices.py can gate them like any other class.
    2. THE BUDGET SPLITS. The old picker indexed ONE shared level list across all three pools with
       `i = len(chosen) + len(martial_set)`, so a bard got ~5 picks divided between them by a coin
       flip -- and the two loops were mutually exclusive, so a bard got martial performances OR
       expanded versatility, never both. The schedule table has no way to express a budget shared
       across buckets, and the shared budget was not a rule anybody had written down, so each bucket
       now carries its own row. A bard therefore gains MORE total picks than before; that is the
       intended change, not a side effect.
    3. `martial_performance` IS UNDOCUMENTED HOUSE CONTENT. It maps Perform categories to WEAPON
       GROUPS (act -> close, double), which is not RAW and is written down nowhere -- not in the
       OKF bundle, not in docs/. It is kept and made visible rather than deleted, and its schedule
       row is `source: unverified` pending a check against Sieg's Guide.

    THE LEADING DRAW IS DELIBERATE AND MUST STAY. `random.randint(1, 100)` ran here before the bard
    check did, so it consumed a number from the process-global stream for EVERY character, bard or
    not. Removing it shifts every subsequent roll and moves all seven golden fixtures for a change
    that only concerns bards. Keeping it holds the diff to what actually changed -- the same
    reasoning phase_class_options already applies to its three dead locals, which "stay only for
    their draws".
    """
    _stream_guard = random.randint(1, 100)   # see the docstring -- do not delete

    if class_entry_for(character, 'bard') is None:
        return None

    # Imported here rather than at module scope: generic_func imports this module's siblings, and a
    # top-level import of the chooser closes the cycle.
    from utils.class_func.generic_func import generic_class_option_chooser

    # Three explicit calls rather than a loop over (dataset, bucket) pairs, and deliberately:
    # validate_class_choices.py resolves call sites with `ast`, so a bucket name held in a loop
    # variable is invisible to it and the rows read as dead. A call site that a gate cannot see is
    # a call site that is not gated.
    generic_class_option_chooser(character, 'bard', dataset_name='versatile_perfomances',
                                 multiple='yes', dict_name='versatile_performances')
    generic_class_option_chooser(character, 'bard', dataset_name='martial_performance',
                                 multiple='yes', dict_name='martial_performance')
    generic_class_option_chooser(character, 'bard', dataset_name='expanded_versatility',
                                 multiple='yes', dict_name='expanded_versatility')
    return None
