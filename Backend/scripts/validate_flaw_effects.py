"""Validate Backend/json/flaws/flaw_effects.json (mechanical character flaws).

Checks (all must pass; exits 1 with a report otherwise):
- JSON parses; only sections `minor` / `major` (+ `_readme`).
- Every entry has a non-empty `description` and at least one mechanic
  (changes and/or contextNotes non-empty).
- Changes/contextNotes use valid pf1 targets (same whitelists as quality_effects).
- [[ ]] inline-roll brackets balanced in every note text.

Usage: python Backend/scripts/validate_flaw_effects.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_quality_effects import (  # noqa: E402
    PF1_CHANGE_TARGETS, PF1_NOTE_TARGETS, valid_target, check_brackets, errors)

FLAWS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', 'json', 'flaws', 'flaw_effects.json')

ENTRY_KEYS = {'description', 'changes', 'contextNotes'}
CHANGE_KEYS = {'formula', 'target', 'type', 'operator', 'priority'}


def err(msg):
    errors.append(msg)


def check_entry(owner, entry):
    unknown = set(entry) - ENTRY_KEYS
    if unknown:
        err(f'{owner}: unknown entry keys {sorted(unknown)}')
    desc = entry.get('description')
    if not desc or not isinstance(desc, str):
        err(f'{owner}: missing description')
    changes = entry.get('changes')
    notes = entry.get('contextNotes')
    if not isinstance(changes, list) or not isinstance(notes, list):
        err(f'{owner}: needs "changes" and "contextNotes" lists')
        return
    if not changes and not notes:
        err(f'{owner}: a flaw must carry at least one change or contextNote')
    for ch in changes:
        unknown = set(ch) - CHANGE_KEYS
        if unknown:
            err(f'{owner}: unknown change keys {sorted(unknown)}')
        if not isinstance(ch.get('formula'), str) or not ch.get('formula'):
            err(f'{owner}: change missing formula')
        if not valid_target(ch.get('target'), PF1_CHANGE_TARGETS):
            err(f'{owner}: invalid change target {ch.get("target")!r}')
        if ch.get('operator') not in ('add', 'set'):
            err(f'{owner}: bad change operator {ch.get("operator")!r}')
    for note in notes:
        unknown = set(note) - {'text', 'target'}
        if unknown:
            err(f'{owner}: unknown contextNote keys {sorted(unknown)}')
        text = note.get('text')
        if not text or not isinstance(text, str):
            err(f'{owner}: contextNote missing text')
        else:
            check_brackets(owner, text)
        if not valid_target(note.get('target'), PF1_NOTE_TARGETS):
            err(f'{owner}: invalid contextNote target {note.get("target")!r}')


def main():
    with open(FLAWS_PATH, encoding='utf-8') as f:
        data = json.load(f)
    unknown = set(data) - {'_readme', 'minor', 'major'}
    if unknown:
        err(f'unknown top-level sections {sorted(unknown)}')
    for tier in ('minor', 'major'):
        entries = data.get(tier)
        if not isinstance(entries, dict) or not entries:
            err(f'section {tier!r} missing or empty')
            continue
        for name, entry in entries.items():
            check_entry(f'{tier}.{name}', entry)

    if errors:
        for e in errors:
            print(e)
        print(f'\nFAILED: {len(errors)} problem(s)')
        sys.exit(1)
    print(f'OK: {len(data.get("minor", {}))} minor + {len(data.get("major", {}))} major flaws.')


if __name__ == '__main__':
    main()
