"""Validate the mechanical-flaw catalogues under Backend/json/flaws/.

Two files, one gate: `flaw_effects.json` (the PC's) and `animal_flaw_effects.json` (bonded
creatures', spec section 8 D16). They share a shape, a tier ladder and a house DC convention, so
they share a validator -- a second copy would drift from this one within a release.

Checks (all must pass; exits 1 with a report otherwise):
- JSON parses; only sections `minor` / `major` (+ `_readme`).
- Every entry has a non-empty `description` and at least one mechanic
  (changes and/or contextNotes non-empty).
- Changes/contextNotes use valid pf1 targets (same whitelists as quality_effects).
- [[ ]] inline-roll brackets balanced in every note text.
- ANIMAL ONLY: every numeric change uses a target `companion_stats.apply_modifiers` can actually
  place. Nothing downstream would notice otherwise -- the module strips `system.changes` off the
  flaw item, so a mistargeted flaw would simply never apply to anything.

Usage: python Backend/scripts/validate_flaw_effects.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _harness import Report                                                  # noqa: E402
from validate_quality_effects import (  # noqa: E402
    PF1_CHANGE_TARGETS, PF1_NOTE_TARGETS, valid_target, check_brackets, errors)

from utils import data as game_data                                          # noqa: E402
from utils.class_func.companion_stats import (                               # noqa: E402
    MODIFIER_TARGETS, SKILL_TARGET_PREFIX)

# Bound to the imported list, not a fresh one: `check_brackets` above appends to its own module's
# accumulator, and those findings have to fail THIS gate.
REPORT = Report('validate_flaw_effects', errors=errors)

FLAWS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'json', 'flaws')
# (filename, must every numeric change be foldable by companion_stats?)
CATALOGUES = (('flaw_effects.json', False), ('animal_flaw_effects.json', True))

ENTRY_KEYS = {'description', 'changes', 'contextNotes'}
CHANGE_KEYS = {'formula', 'target', 'type', 'operator', 'priority'}


def err(msg):
    REPORT.error(msg)


def check_foldable(owner, change):
    """The animal catalogue's extra rule: a change the fold cannot place is a change nobody applies."""
    target = str(change.get('target') or '')
    if target.startswith(SKILL_TARGET_PREFIX):
        if target[len(SKILL_TARGET_PREFIX):] not in set(game_data.SKILL_IDS.values()):
            err(f'{owner}: {target!r} is not a pf1 skill id')
    elif target not in MODIFIER_TARGETS:
        err(f'{owner}: change target {target!r} is valid pf1 but companion_stats.apply_modifiers '
            f'cannot place it, so the flaw would never apply -- use one of '
            f'{sorted(MODIFIER_TARGETS)} or {SKILL_TARGET_PREFIX}<id>, or make it a contextNote')


def check_entry(owner, entry, foldable=False):
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
        if foldable:
            check_foldable(owner, ch)
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
    summary = []
    for filename, foldable in CATALOGUES:
        with open(os.path.join(FLAWS_DIR, filename), encoding='utf-8') as f:
            data = json.load(f)
        unknown = set(data) - {'_readme', 'minor', 'major'}
        if unknown:
            err(f'{filename}: unknown top-level sections {sorted(unknown)}')
        for tier in ('minor', 'major'):
            entries = data.get(tier)
            if not isinstance(entries, dict) or not entries:
                err(f'{filename}: section {tier!r} missing or empty')
                continue
            for name, entry in entries.items():
                check_entry(f'{filename} {tier}.{name}', entry, foldable=foldable)
        summary.append(f'{filename}: {len(data.get("minor", {}))} minor + '
                       f'{len(data.get("major", {}))} major')

    return REPORT.finish('; '.join(summary))


if __name__ == '__main__':
    sys.exit(main())
