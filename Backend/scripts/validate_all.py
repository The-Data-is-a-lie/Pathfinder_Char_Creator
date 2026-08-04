"""Run every Backend/scripts/validate_*.py and fail if any of them does.

    C:\\Python310\\python.exe Backend/scripts/validate_all.py
    C:\\Python310\\python.exe Backend/scripts/validate_all.py --list
    C:\\Python310\\python.exe Backend/scripts/validate_all.py --skip validate_psionics_data

Written alongside map #18's gates (#27, #29, #40) for a plain reason: this repo had **eleven**
`validate_*.py` scripts and nothing that ran any of them. A gate nobody runs is a sentence, which
is the failure the docs doctrine exists to prevent -- the same one that let a stale
`critical: "onCrit"` break six weapons until a `MOD_CRITICAL` whitelist caught it.

Discovery is by glob, so a new validator is covered the moment it is added and never has to be
registered anywhere. Each runs in its own process: one crashing does not hide the others, and the
summary reports all of them rather than stopping at the first failure.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SELF = Path(__file__).resolve().name


def validators():
    return sorted(p for p in HERE.glob("validate_*.py") if p.name != SELF)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true", help="list what would run, then exit")
    parser.add_argument("--skip", action="append", default=[],
                        help="a validator to skip, by stem; repeatable")
    parser.add_argument("--quiet", action="store_true",
                        help="only show output for validators that fail")
    args = parser.parse_args()

    scripts = [p for p in validators() if p.stem not in args.skip]
    if args.list:
        for script in scripts:
            print(script.name)
        return 0
    if not scripts:
        print("no validators found -- has Backend/scripts moved?")
        return 1

    failures, results = [], []
    for script in scripts:
        started = time.monotonic()
        result = subprocess.run([sys.executable, str(script)],
                                capture_output=True, text=True)
        elapsed = time.monotonic() - started
        ok = result.returncode == 0
        results.append((script.name, ok, elapsed))
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

    width = max(len(name) for name, _, _ in results)
    print("summary")
    for name, ok, elapsed in results:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<{width}}  {elapsed:5.1f}s")
    if failures:
        print(f"\nFAILED: {len(failures)} of {len(results)} validators -- {', '.join(failures)}")
        return 1
    print(f"\nPASS -- {len(results)} validators")
    return 0


if __name__ == "__main__":
    sys.exit(main())
