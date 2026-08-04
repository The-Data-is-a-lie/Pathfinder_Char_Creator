# 05 — What is the durable gate that keeps this true?

Type: grilling
Status: open
Blocked by: 01, 02, 03
Map: [Class choices](../map.md)

## Question

Tickets 01–04 produce a table of what each class should pick, how many, when, legally, and where it
renders. **What stops that table from silently going stale?**

`CLAUDE.md` states the doctrine and the cautionary tale: a hard convention belongs in a
`Backend/scripts/validate_*.py`, not only in a sentence — *"a stale `critical: \"onCrit\"` in a doc
silently broke six weapons, and a `MOD_CRITICAL` whitelist fixed it."* §11 is exactly the kind of
document that decays: it will assert numbers, and numbers are edited.

### The precedent to extend

`Backend/scripts/test_house_invariants.py:205-222` already does this job, for psionics only:

```
schedule = next(iter((getattr(data, 'amount', {}).get(name) or {}).values()), None)
want_picks = len([a for a in schedule if a <= entry['level']]) if schedule else 1
check(len(picks) == want_picks, f"... picks that never land appear nowhere on a sheet")
```

It reads the schedule, computes what is due at the rolled level, and asserts the bucket holds exactly
that. Generalising it to every class is the obvious move — and note that it **reads `data.amount`
directly**, so whatever ticket 01 decides about where schedules live, this check follows it.

### The decision

**Where does the gate live, and how many gates are there?** Three candidate homes, not exclusive:

1. **A house invariant** in `test_house_invariants.py` — runs against generated characters across the
   level/class matrix, so it catches "this class at this level under-delivers". Catches *behaviour*.
   The psionics check already sits here.
2. **`Backend/scripts/validate_class_choices.py`** — runs against the *data*: every class in the pool
   has a schedule; every schedule references a bucket that exists; every bucket has a chooser call;
   every bucket has a renderer home (ticket 04's rule). Catches *configuration*, without generating
   anything, and is the natural sibling to `validate_companion_data.py` /
   `validate_companion_names.py` from §8 and to `audit_class_choice_descriptions.py`.
3. **The golden payload** (`test_golden_payload.py`) — pins actual picks for fixed seeds, catching
   unintended drift in the picks themselves rather than in the counts.

The likely answer is 1 **and** 2 — they catch different failures — but that should be argued, not
assumed, and the split should be stated so a future contributor knows which file a new rule belongs in.

### Sub-questions

- **Coverage vs. runtime.** `test_house_invariants.py` already runs ~15,560 checks. Asserting every
  class × every bucket × a level sweep multiplies that. What is the matrix — every class at a handful
  of levels, or a sampled sweep?
- **What the invariant asserts when the pool runs dry.** Ticket 03 rules on whether under-delivery
  from an exhausted pool is legal; if it is, the check needs to distinguish it from a bug, or it will
  fail on exactly the characters that are fine.
- **Does the validator gate CI, or is it run by hand?** The companion validators are run by hand
  today. Say which, and where it is written down.
- **Newly onboarded classes.** [Map: Class pool](../../class-pool/map.md) adds classes; the gate should
  fail loudly for a class that joins the pool without a schedule, so onboarding cannot skip this map's
  work. That is arguably the single most valuable assertion here.

### What "resolved" looks like

A ruling on which gate(s) exist, what each asserts, where the rule for adding a new class is written,
and how it is run. §11 then names those symbols rather than restating their contents — which is the
whole point.
