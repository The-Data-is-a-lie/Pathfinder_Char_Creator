"""An alias was dropped because its writer runs once. Keep that true.

    C:/Python310/python.exe Backend/scripts/gates/validate_alias_invariants.py
    C:/Python310/python.exe Backend/scripts/gates/validate_alias_invariants.py --print

WHY THIS GATE EXISTS
--------------------
Extracting the phases turned a number of function locals into reads of the character attribute they
aliased. Most were trivial. Two were the SAME SHAPE and got OPPOSITE verdicts, and the thing that
separated them is not visible in the syntax:

  * `full_domain` was a bare alias of `character.chosen_domain`, bound right after `domain_chooser`
    set it. Safe to drop -- `domain_chooser` is the only writer and runs EXACTLY ONCE, so the
    attribute at export time still holds what the local held.
  * `day_list` / `known_list` were bare aliases bound right after `sync_legacy_spell_fields` set
    them. NOT safe to drop -- that function runs TWICE (main_test.py:444 and again at :1803), so the
    local froze the first pass's values while the attribute goes on to hold the second's.

Identical code, opposite answers, and the discriminator is the **writer count** rather than anything
you can see at the alias site. That is exactly the kind of rule this repo does not leave in prose:
CLAUDE.md -- "Hard conventions belong in a validator [...] a stale `critical: "onCrit"` in a doc
silently broke six weapons, and a MOD_CRITICAL whitelist fixed it."

The failure this prevents is silent and remote. Add a second `domain_chooser(character)` call
anywhere in the pipeline and nothing breaks here: the payload's `full_domain` quietly starts
reporting the second roll instead of the first, on somebody's character sheet, in another
repository. No exception, no test, no diff -- the key is still present and still a list of domains.

WHAT IT CHECKS
--------------
For every entry in ALIASES: the writer function is called exactly the declared number of times in
main_test.py, and the aliased attribute is assigned ONLY inside the module that owns it. A change to
either number means the verdict recorded in the phase docstring is now wrong, and the gate says which
way it moved -- a writer that dropped to one call makes an unsafe alias safe, which is worth knowing
too.

This gate is deliberately a WHITELIST of decisions actually made, not a general alias detector. It
records verdicts and the evidence they rest on; it does not try to police every attribute in the
generator.
"""
import argparse
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import Report, BACKEND  # noqa: E402

REPORT = Report('validate_alias_invariants')

MAIN = BACKEND / 'main_test.py'

# Each entry is a verdict that was reached by measuring, plus the measurement it rests on.
ALIASES = (
    dict(
        attribute='chosen_domain',
        dropped_local='full_domain',
        writer='domain_chooser',
        owner='utils/class_func/domain_inquisition.py',
        calls=1,
        verdict='SAFE -- the alias was dropped',
        why='one writer, called once, so the attribute at export still holds what the local held',
    ),
    dict(
        attribute=None,                      # the spell fields are several names; the call count is the fact
        dropped_local='day_list / known_list',
        writer='sync_legacy_spell_fields',
        owner='utils/class_func/spells.py',
        calls=2,
        verdict='UNSAFE -- the aliases were KEPT as phase outputs',
        why='runs twice, so a local froze the first pass while the attribute goes on to the second',
    ),
)


def _count_calls(tree, name):
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            called = func.id if isinstance(func, ast.Name) else getattr(func, 'attr', None)
            if called == name:
                n += 1
    return n


def _assigners(attribute):
    """Every file that assigns character.<attribute>, so a second writer cannot appear unnoticed."""
    hits = set()
    for path in sorted(BACKEND.rglob('*.py')):
        if '__pycache__' in path.parts or 'scripts' in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            for tgt in targets:
                if (isinstance(tgt, ast.Attribute) and tgt.attr == attribute
                        and isinstance(tgt.value, ast.Name) and tgt.value.id == 'character'):
                    hits.add(path.relative_to(BACKEND).as_posix())
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--print', action='store_true', dest='show')
    args = ap.parse_args()

    tree = ast.parse(MAIN.read_text(encoding='utf-8'))

    for entry in ALIASES:
        writer = entry['writer']
        expected = entry['calls']
        actual = _count_calls(tree, writer)

        if args.show:
            print(f"  {entry['dropped_local']:<24} writer {writer}() x{actual}  -> {entry['verdict']}")

        if actual != expected:
            direction = ('MORE' if actual > expected else 'FEWER')
            note = ''
            if expected == 1 and actual > 1:
                note = (f" The `{entry['dropped_local']}` alias was dropped ONLY because {writer} ran "
                        f"once; with {actual} calls the export now reports the LAST call's result "
                        f"where the original local held the first. Either restore the alias as a "
                        f"phase output or re-verify the verdict and update this gate.")
            elif expected > 1 and actual == 1:
                note = (f" {writer} now runs once, so the `{entry['dropped_local']}` aliases that "
                        f"were KEPT for this reason could be dropped. Not a bug -- but the recorded "
                        f"verdict is stale, and this gate is where it is recorded.")
            REPORT.error(
                f"{writer} is called {actual} time(s) in main_test.py, {direction} than the "
                f"{expected} this verdict rests on.{note}")

        if entry['attribute']:
            owners = _assigners(entry['attribute'])
            expected_owner = entry['owner']
            unexpected = sorted(o for o in owners if o != expected_owner)
            if unexpected:
                REPORT.error(
                    f"character.{entry['attribute']} is assigned outside {expected_owner} -- also in "
                    f"{', '.join(unexpected)}. The '{entry['why']}' verdict assumes a single writer; "
                    f"a second one means the attribute at export time may not hold what "
                    f"`{entry['dropped_local']}` held.")
            REPORT.check(
                owners,
                f"character.{entry['attribute']} is never assigned anywhere -- this gate is watching "
                f"an attribute that no longer exists, which means it is watching nothing")

    return REPORT.finish(f'{len(ALIASES)} alias verdict(s) still hold')


if __name__ == '__main__':
    sys.exit(main())
