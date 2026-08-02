"""Classify every archetype that touches a bond feature -> companion_archetypes.json.

    C:\\Python310\\python.exe Backend/scripts/build_companion_archetypes.py
    C:\\Python310\\python.exe Backend/scripts/build_companion_archetypes.py --review

Map #18, ticket #40, specified by the D8 grill (#38). `Backend/json/archetypes.json` holds 1,303
archetypes across 50 classes with no structured `replaces` field -- the relation between an
archetype and the class feature it swaps exists only as prose inside each feature description. 204
archetypes across the ten grantor classes structurally touch a bond feature, and
`Character.archetype_data()` picks one unconditionally for every rolled class, so a druid has a
~57% chance of rolling one.

The triad matches `build_item_changes.py`: this builder writes the generated file, a hand-authored
`companion_archetypes_overrides.json` wins over it, and `validate_companion_archetypes.py` gates
the result. Deterministic -- `sort_keys=True`, so a re-run against unchanged input is a no-op diff.

THE TRAP
--------
`forces` cannot be read off the closing sentence. Cinderwalker (deletes the companion) and Beast
Master (grants one) carry the IDENTICAL sentence -- "This ability replaces hunter's bond." A regex
on that sentence alone gets Beast Master exactly backwards. So classification reads what the
REPLACING FEATURE IS, from its own text, and the sentence only says which feature was traded.

Every verdict here is a proposal. `--review` emits the sign-off worksheet that turns proposals into
the overrides file; nothing in the generated JSON is authoritative until a human has signed it.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARCHETYPES = ROOT / "Backend/json/archetypes.json"
OVERRIDES = ROOT / "Backend/json/companion_archetypes_overrides.json"
OUT = ROOT / "Backend/json/companion_archetypes.json"
REVIEW = ROOT / "docs/companion_archetype_signoff.md"

# The ten classes whose progression contains a bond feature (#23: shifter and antipaladin do not).
GRANTORS = ("Druid", "Ranger", "Wizard", "Sorcerer", "Paladin",
            "Cavalier", "Samurai", "Summoner", "Hunter", "Witch")

# What each grantor's bond feature is called in prose. Order matters only for reporting.
BOND_TARGETS = (
    "nature bond", "hunter's bond", "hunters bond", "arcane bond", "divine bond",
    "animal companion", "eidolon", "familiar", "bonded object", "bonded mount", "mount",
)
TARGET_RE = re.compile("|".join(re.escape(t) for t in BOND_TARGETS), re.I)

# "This ability replaces nature bond." / "This alters the druid's animal companion."
SENTENCE_RE = re.compile(
    r"\bthis\s+[a-z' ]{0,40}?\b(replaces|alters|modifies|changes)\b([^.]*)\.", re.I)

# The replacing feature GRANTS a bonded creature -> forces, not removes.
GRANT_RE = re.compile(
    r"\bgains?\s+(?:an?\s+)?(?:animal companion|companion|familiar|eidolon|mount|bonded mount)"
    r"|\breceives?\s+(?:an?\s+)?(?:animal companion|familiar|eidolon|mount)"
    r"|\b(?:animal companion|familiar|eidolon|mount)\b[^.]{0,60}\bas (?:the|a|per)\b"
    r"|\btreat(?:ing|s)? her (?:druid|ranger|hunter) level as\b"
    r"|\bgains? the service of\b", re.I)

# The pool of legal species is redefined.
POOL_RE = re.compile(
    r"\b(?:must (?:be|select|choose)|may (?:only )?select|chosen from|selected from|"
    r"choose from|limited to|instead of the normal)\b[^.]{0,160}"
    r"|\bfrom the following(?: list)?\b", re.I)

# The advancement / effective level is altered.
PROGRESSION_RE = re.compile(
    r"\b(?:does ?n[o']t increase|does not increase|effective (?:druid|class) level|"
    r"level (?:is )?equal to|treats? her .{0,30}level as|minus 3|-\s?3 levels|"
    r"levels? stack|counts? as (?:a )?(?:druid|ranger) level|at 4th level|size (?:large|medium))\b",
    re.I)

EFFECTS = ("removes", "forces", "species_pool", "progression", "none")


def bond_features(body):
    """(features that ARE a bond feature, sentences that trade one away)."""
    own_keys, sentences = [], []
    for key, text in body.items():
        if key == "source" or not isinstance(text, str):
            continue
        if TARGET_RE.search(key):
            own_keys.append(key)
        for verb, obj in SENTENCE_RE.findall(text):
            if TARGET_RE.search(obj):
                sentences.append((key, verb.lower(), obj.strip()))
    return own_keys, sentences


def snippet(match, text, width=110):
    """The matched phrase in a little context, so a reviewer can judge without opening the book."""
    start = max(0, match.start() - 30)
    end = min(len(text), match.start() + width)
    return ("…" if start else "") + " ".join(text[start:end].split()) + ("…" if end < len(text) else "")


def classify(body, own_keys, sentences):
    """Propose every effect that applies, most decisive first.

    Deliberately NOT single-valued. Devolutionist both forces a species ("must choose a devolved
    humanoid ... use the stats for an ape animal companion") and suppresses a field of the
    advancement merge ("doesn't increase to size Large at 4th level"). #38's vocabulary gives an
    archetype one `effect`; the prose gives some of them two, and collapsing that would silently
    drop whichever the classifier happened to test second.
    """
    # The text of whatever feature does the replacing -- that is what decides forces vs removes.
    replacing = " ".join(str(body.get(key, "")) for key, verb, _ in sentences
                         if verb in ("replaces", "changes"))
    own_text = " ".join(str(body.get(key, "")) for key in own_keys)
    altering = " ".join(str(body.get(key, "")) for key, verb, _ in sentences
                        if verb in ("alters", "modifies"))
    described = " ".join(f"{own_text} {altering}".split())

    found = []
    grant = GRANT_RE.search(replacing) if replacing else None
    if grant:
        found.append(("forces", "high", "the replacing feature itself grants a bonded creature",
                      snippet(grant, replacing)))
    else:
        grant_own = GRANT_RE.search(own_text) if own_text else None
        if grant_own:
            found.append(("forces", "medium",
                          "redefines the bond feature, and the redefinition grants one",
                          snippet(grant_own, own_text)))
        elif replacing:
            found.append(("removes", "medium",
                          "traded away, and the replacing feature grants no creature",
                          " ".join(replacing.split())[-160:]))

    # Both of these can sit alongside a forces/removes verdict, and alongside each other.
    pool = POOL_RE.search(described) if described else None
    if pool:
        found.append(("species_pool", "medium", "restricts or lists the legal species",
                      snippet(pool, described)))
    progression = PROGRESSION_RE.search(described) if described else None
    if progression:
        found.append(("progression", "medium", "changes level or size advancement",
                      snippet(progression, described)))

    if not found:
        why = ("redefines the bond feature but states no mechanical change" if own_keys
               else "mentions a bond feature without replacing or altering it")
        found.append(("none", "low", why, ""))
    return found


def build():
    with open(ARCHETYPES, encoding="utf-8") as fh:
        data = json.load(fh)

    entries = {}
    for cls in GRANTORS:
        for name, body in (data.get(cls) or {}).items():
            if not isinstance(body, dict):
                continue
            own_keys, sentences = bond_features(body)
            if not own_keys and not sentences:
                continue
            found = classify(body, own_keys, sentences)
            entries[f"{cls}/{name}"] = {
                "archetype": name,
                "class": cls,
                # `effect` is the primary verdict, the one #38's single-valued vocabulary means.
                # `effects` is the full proposal -- see classify() on why some archetypes need two.
                "effect": found[0][0],
                "effects": [
                    {"effect": e, "confidence": c, "why": w, "evidence": ev}
                    for e, c, w, ev in found
                ],
                "confidence": found[0][1],
                "why": found[0][2],
                "bond_features": sorted(own_keys),
                "sentences": [{"feature": k, "verb": v, "object": o} for k, v, o in sentences],
                "source": body.get("source", ""),
                "signed_off": False,
            }
    return entries


def apply_overrides(entries):
    if not OVERRIDES.exists():
        return entries, 0
    with open(OVERRIDES, encoding="utf-8") as fh:
        overrides = json.load(fh)
    for key, entry in overrides.items():
        base = dict(entries.get(key, {}))
        base.update(entry)
        base["signed_off"] = True
        entries[key] = base
    return entries, len(overrides)


def aon_link(name):
    return ("https://www.aonprd.com/Search.aspx?Query="
            + name.replace(" ", "+").replace("'", "%27"))


def write_review(entries):
    order = {"low": 0, "medium": 1, "high": 2}
    by_class = {}
    for key, entry in entries.items():
        by_class.setdefault(entry["class"], []).append((key, entry))

    lines = [
        "# Companion archetype sign-off (#40)",
        "",
        "**Generated by `Backend/scripts/build_companion_archetypes.py --review`. Do not hand-edit "
        "this file** — it is regenerated. Record decisions in "
        "`Backend/json/companion_archetypes_overrides.json`, which wins over the generated "
        "`companion_archetypes.json`.",
        "",
        "Every verdict below is a **proposal from prose heuristics**, ordered least-confident "
        "first within each class. The one that cannot be automated is `forces` vs `removes`: "
        "Cinderwalker (deletes the companion) and Beast Master (grants one) carry the *identical* "
        "sentence, \"This ability replaces hunter's bond.\" The classifier reads what the "
        "replacing feature *is* rather than what it replaces, but that is a heuristic and this "
        "worksheet is the authority.",
        "",
        "## The five verdicts",
        "",
        "| effect | means |",
        "|---|---|",
        "| `removes` | no creature at all; the resolver emits an absence entry, "
        "`outcome: archetype_removed` |",
        "| `forces` | the coin flip disappears; grant the creature unconditionally |",
        "| `species_pool` | same creature, curated species list |",
        "| `progression` | per-field override on the advancement merge (size, effective level) |",
        "| `none` | no effect on the snapshot — an **explicit verdict**, not \"unclassified\" |",
        "",
        "## How to sign off",
        "",
        "For each archetype: confirm the proposal, or write the correct effect. Anything you "
        "change (and every `species_pool` / `progression`, which need their detail filled in) goes "
        "into the overrides file as:",
        "",
        "```json",
        '{ "Druid/Devolutionist": { "effect": "progression",',
        '                           "progression": { "suppress": ["size"] } },',
        '  "Ranger/Beast Master":  { "effect": "forces" } }',
        "```",
        "",
        f"**{len(entries)} archetypes across {len(by_class)} classes.**",
        "",
    ]

    counts = {}
    for entry in entries.values():
        counts[entry["effect"]] = counts.get(entry["effect"], 0) + 1
    lines += ["| proposed | count |", "|---|---|"]
    lines += [f"| `{effect}` | {counts.get(effect, 0)} |" for effect in EFFECTS]
    low = sum(1 for e in entries.values() if e["confidence"] == "low")
    lines += ["", f"Low confidence (read these first): **{low}**", ""]

    for cls in GRANTORS:
        rows = by_class.get(cls) or []
        if not rows:
            continue
        rows.sort(key=lambda kv: (order[kv[1]["confidence"]], kv[1]["archetype"]))
        lines += [f"## {cls} — {len(rows)} archetypes", ""]
        for key, entry in rows:
            mark = {"low": "🔴", "medium": "🟡", "high": "🟢"}[entry["confidence"]]
            proposed = " + ".join(f"`{e['effect']}`" for e in entry["effects"])
            both = "  ⚠ **two effects**" if len(entry["effects"]) > 1 else ""
            lines += [
                f"### {mark} {entry['archetype']}  ·  proposed {proposed}{both}",
                "",
            ]
            for item in entry["effects"]:
                lines.append(f"- **`{item['effect']}`** — {item['why']}")
                if item["evidence"]:
                    lines.append(f"  > {item['evidence']}")
                # The druid's nature bond has two sides. A restriction that names domains is
                # constraining the domain half and leaves the companion untouched -- which reads
                # identically to a species pool unless you look at what is being listed.
                if item["effect"] == "species_pool" and "domain" in item["evidence"].lower():
                    lines.append("  - ⚠ the restriction names **domains** — if it constrains only "
                                 "the domain side, this is `none`; if it forces the domain "
                                 "instead of a companion, it is `removes`")
            if entry["bond_features"]:
                lines.append("- **defines:** "
                             + ", ".join(f"`{k}`" for k in entry["bond_features"]))
            for sentence in entry["sentences"]:
                obj = sentence["object"]
                obj = (obj[:150] + "…") if len(obj) > 150 else obj
                lines.append(f"- **{sentence['verb']}:** {obj}  "
                             f"<sub>(in `{sentence['feature']}`)</sub>")
            if entry["source"]:
                lines.append(f"- **source:** {entry['source']}")
            lines += [
                f"- [{entry['archetype']} on Archives of Nethys]({aon_link(entry['archetype'])})",
                "- [ ] **signed off** — effect(s): `__________`",
                "",
            ]

    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEW, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return REVIEW


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--review", action="store_true",
                        help="also write the docs/ sign-off worksheet")
    args = parser.parse_args()

    entries = build()
    entries, override_count = apply_overrides(entries)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")

    counts = {}
    for entry in entries.values():
        counts[entry["effect"]] = counts.get(entry["effect"], 0) + 1
    print(f"classified {len(entries)} archetypes across {len(GRANTORS)} grantor classes")
    for effect in EFFECTS:
        print(f"  {effect:<13} {counts.get(effect, 0):>4}")
    print(f"  {'(overrides)':<13} {override_count:>4}")
    signed = sum(1 for e in entries.values() if e.get("signed_off"))
    print(f"  {'signed off':<13} {signed:>4} / {len(entries)}")
    print(f"wrote {OUT}")

    if args.review:
        print(f"wrote {write_review(entries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
