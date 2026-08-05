"""Run every Backend/scripts/test_*.py and fail if any of them does.

    C:\\Python310\\python.exe Backend/scripts/test_all.py
    C:\\Python310\\python.exe Backend/scripts/test_all.py --list
    C:\\Python310\\python.exe Backend/scripts/test_all.py --skip test_house_invariants
    C:\\Python310\\python.exe Backend/scripts/test_all.py --full        # untrimmed sweeps

WHY THIS EXISTS
---------------
`validate_all.py` was written because eleven validators existed and nothing ran them. The test
family was in the same state one step further along: eleven `test_*.py` scripts, of which CI ran
exactly one (`test_house_invariants.py`, trimmed). The other ten only ran when somebody remembered
them.

The expensive one to forget is `test_golden_payload.py` -- seven seeded characters with every
payload key diffed byte for byte. That is the only thing standing between a "pure move" refactor and
a quietly different character, and the phase-extraction work about to start leans on it entirely. A
net that is not attached to CI is not a net.

Same shape as `validate_all.py` on purpose: glob discovery so a new test is covered the moment it is
written, and a subprocess per script so one crash cannot hide the rest.

TRIMMED BY DEFAULT
------------------
Two of these sweep the whole class roster and take minutes. They run trimmed here -- the same flags
CI already passed to `test_house_invariants` -- so that "run the tests" stays a thing you actually
do. `--full` drops the trimming for a pre-release run. The trimming is printed in the summary
rather than applied silently: a suite that quietly tests less than it appears to is the failure this
directory exists to prevent.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SELF = Path(__file__).resolve().name

# stem -> the arguments that keep a full-roster sweep to a sane runtime. `--full` ignores this.
TRIMMED = {
    "test_house_invariants": ["--levels", "1,20", "--seeds", "1"],
}


def tests():
    # tests/ rather than HERE -- see the matching note in validate_all.py.
    return sorted(p for p in (HERE / "tests").glob("test_*.py") if p.name != SELF)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true", help="list what would run, then exit")
    parser.add_argument("--skip", action="append", default=[],
                        help="a test to skip, by stem; repeatable")
    parser.add_argument("--quiet", action="store_true",
                        help="only show output for tests that fail")
    parser.add_argument("--full", action="store_true",
                        help="run the roster sweeps unabridged (slow; do this before a release)")
    args = parser.parse_args()

    scripts = [p for p in tests() if p.stem not in args.skip]
    if args.list:
        for script in scripts:
            extra = "" if args.full else " ".join(TRIMMED.get(script.stem, []))
            print(f"{script.name} {extra}".rstrip())
        return 0
    if not scripts:
        print("no tests found -- has Backend/scripts moved?")
        return 1

    failures, results = [], []
    for script in scripts:
        extra = [] if args.full else TRIMMED.get(script.stem, [])
        started = time.monotonic()
        result = subprocess.run([sys.executable, str(script), *extra],
                                capture_output=True, text=True)
        elapsed = time.monotonic() - started
        ok = result.returncode == 0
        results.append((script.name, ok, elapsed, extra))
        if not ok:
            failures.append(script.name)
        if not ok or not args.quiet:
            print(f"===== {script.name} {'ok' if ok else 'FAILED'} ({elapsed:.1f}s)")
            body = (result.stdout or "").rstrip()
            if body:
                print(body)
            if result.stderr.strip():
                print(result.stderr.rstrip())
            print()

    width = max(len(name) for name, _, _, _ in results)
    print("summary")
    for name, ok, elapsed, extra in results:
        note = f"  [{' '.join(extra)}]" if extra else ""
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<{width}}  {elapsed:5.1f}s{note}")
    if not args.full:
        # Never let a trimmed run read as a full one.
        trimmed_here = [name for name, _, _, extra in results if extra]
        if trimmed_here:
            print(f"\nNOTE: {len(trimmed_here)} sweep(s) ran trimmed -- "
                  f"{', '.join(trimmed_here)}. Use --full before a release.")
    if failures:
        print(f"\nFAILED: {len(failures)} of {len(results)} tests -- {', '.join(failures)}")
        return 1
    print(f"\nPASS -- {len(results)} tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
