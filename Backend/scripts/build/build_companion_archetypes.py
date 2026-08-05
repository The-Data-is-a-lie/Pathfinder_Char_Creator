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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO as ROOT, SCRIPTS as HERE   # noqa: E402

# One owner for the closed vocabulary. `validate_companion_data.py` declares itself the owner of
# #38's closed sets and validate_companion_archetypes.py already imports from it; this file used to
# restate EFFECTS verbatim, which is the "restate a symbol instead of naming its owner" pattern
# CLAUDE.md calls a bug magnet. A new effect added to one copy and not the other either hard-fails
# validation or silently vanishes from this builder's own summary.
from validate_companion_data import EFFECTS                      # noqa: E402

ARCHETYPES = ROOT / "Backend/json/archetypes.json"
SPECIES = ROOT / "Backend/json/animal_choices.json"
OVERRIDES = ROOT / "Backend/json/companion_archetypes_overrides.json"
VERIFIED = ROOT / "Backend/json/companion_archetypes_verified.json"
OUT = ROOT / "Backend/json/companion_archetypes.json"
REVIEW = ROOT / "docs/companion_archetype_signoff.md"

# The ten classes whose progression contains a bond feature (#23: shifter and antipaladin do not).
GRANTORS = ("Druid", "Ranger", "Wizard", "Sorcerer", "Paladin",
            "Cavalier", "Samurai", "Summoner", "Hunter", "Witch")

# What each grantor's bond feature is called in prose. `mount` needs a word boundary: as a bare
# substring it matches inside "mountain" and "mountaineer", which pulled Mountain Druid, Summit
# Sentinel and Mountain Witch into the set although none of them touches a bond feature at all.
BOND_TARGETS = (
    "nature bond", "hunter's bond", "hunters bond", "arcane bond", "divine bond",
    "animal companion", "eidolon", "familiar", "bonded object", "bonded mount",
)
TARGET_RE = re.compile("|".join([*(re.escape(t) for t in BOND_TARGETS), r"\bmounts?\b"]), re.I)

# "This ability replaces nature bond." / "This alters the druid's animal companion."
SENTENCE_RE = re.compile(
    r"\bthis\s+[a-z' ]{0,40}?\b(replaces|alters|modifies|changes)\b([^.]*)\.", re.I)

# ---------------------------------------------------------------------------------------------
# Clause-level vocabulary.
#
# The first pass classified a whole-archetype prose blob and scored 6/15 against human sign-off.
# The blob is the bug: the druid's nature bond has TWO SIDES, and once concatenated a sentence about
# domains is indistinguishable from one about the companion. Cave Druid's bond text is purely a
# domain list and was read as a species restriction; Nithveil Adept forbids the companion outright
# and was read as no effect at all because there is no "replaces" sentence to key on.
#
# So: split the bond feature's own text into clauses, decide which SIDE each clause is about, and
# bind each prohibition or obligation to its own object.
# ---------------------------------------------------------------------------------------------

# Strict creature terms only. Bare "animal" is deliberately NOT here: the PF1e *Animal domain* is a
# domain called "Animal", so "must choose from the Animal, Community ... domains" would read as a
# creature clause. Every real creature clause names the bond explicitly ("an animal companion").
CREATURE_RE = re.compile(
    r"animal companion|\bcompanions?\b|\bfamiliars?\b|\beidolons?\b|\bmounts?\b|\bdrakes?\b", re.I)
DOMAIN_RE = re.compile(r"\bsub ?domains?\b|\bdomains?\b|\bbonded object\b|"
                       r"\bbond with (?:allies|companions)\b", re.I)

# "who chooses an animal companion", "if choosing a domain", "if the aerie protector chooses" --
# the clause only applies IF that side was taken, so it restricts without forcing. This is the sole
# discriminator between the totem shamans (species_pool) and Sunrider/Devolutionist (forces too).
#
# A clause that OPENS with if/when/while is situational and never establishes the baseline bond:
# "If one of the elemental ally's eidolons is killed, she cannot summon any eidolons for 24 hours"
# is a downtime rule, and reading it as a prohibition made Elemental Ally lose its eidolons entirely.
CONDITIONAL_RE = re.compile(r"^(?:if|when|while|should|unless)\b"
                            r"|\bwho chooses\b|\bif choosing\b|\bif (?:s?he|the [a-z' ]{1,30}?)\s*"
                            r"(?:chooses|selects|takes)\b|\bwhen (?:s?he )?chooses\b", re.I)

NEGATION = r"(?:cannot|can ?not|may not|must not|does ?n[o']?t|do ?n[o']?t|no longer|never)"

# The alternative is made compulsory, which removes the creature just as surely as forbidding it.
# Ancient Guardian: "must choose the domain nature bond ability and select from the following
# domains". Nithveil Adept: "can take only a domain".
FORCED_ALTERNATIVE_RE = re.compile(
    r"\bcan take only (?:a|the)\s+(?:domain|bonded object)\b"
    r"|\bmust (?:choose|select|take|use)\b[^;.]{0,40}?\b(?:domain|bonded object)\b", re.I)

# The creature is compulsory -> the flip disappears.
#
# The obligation must govern a SELECTION verb, and a grant must have the creature as its direct
# object. Without that, "it must be able to fly on its own before it becomes her companion" reads as
# "must ... companion" (Aerie Protector forced a companion it merely describes), and "As the
# elemental ally gains levels, her elemental eidolons' statistics increase" reads as a grant.
_CREATURE = r"(?:animal companion|companions?|familiars?|eidolons?|mounts?)"
MANDATORY_CREATURE_RE = re.compile(
    rf"\bmust\b[^;.]{{0,45}}?\b(?:choose|select|take|bond with|have|use)\b[^;.]{{0,55}}?\b{_CREATURE}\b"
    rf"|\b(?:gains?|has|have|receives?)\s+(?:an?|the|four|two|three|his|her|its)?\s*"
    rf"(?:[a-z]+\s+){{0,2}}?{_CREATURE}\b"
    r"|\bgains? the service of\b", re.I)

# A restriction on WHICH creature. The captured tail is mined for species names. "use the stats for"
# is here because Devolutionist names its species that way rather than as a choice
# ("Use the stats for an ape animal companion").
POOL_RE = re.compile(
    r"\b(?:must (?:be|select|choose)|may (?:only )?select|"
    r"(?:chosen|selected) from|choose from|limited to|instead of the normal|"
    r"use the stats for|bond(?:s|ed)? with)\b([^;.]{0,160})", re.I)

# Restrictions stated as a property rather than a list -- derivable from animal_choices.json.
PROPERTY_RES = (
    (re.compile(r"\bfly speed\b|\bcan fly\b|\bflying\b", re.I), "fly"),
    (re.compile(r"\bswim speed\b|\baquatic\b", re.I), "swim"),
)

# The advancement / effective level is altered.
PROGRESSION_RE = re.compile(
    r"\b(?:does ?n[o']t increase|does not increase|effective (?:druid|class) level|"
    r"level (?:is )?equal to|treats? her .{0,30}level as|minus 3|-\s?3 levels|"
    r"levels? stack|counts? as (?:a )?(?:druid|ranger) level)\b", re.I)

# What each grantor class's bond yields WITHOUT an archetype. `creature_type` means the bond yields
# something ELSE, so naming a class's own default is not an effect at all -- every summoner's bond is
# an eidolon, and tagging Broodmaster or Storm Caller `creature_type: eidolon` said nothing while
# hiding what they really do.
# `forces` means "the flip disappears", so it only says something for a class whose bond IS a
# choice. A hunter, witch, cavalier, samurai or summoner always has its creature -- there is no
# alternative to suppress -- and a paladin's mount is granted unconditionally by
# companion_grantors.json. Tagging those `forces` described nothing and hid the real effect. Keep
# this in step with which rows in companion_grantors.json carry a `choice`.
CHOICE_CLASSES = ("Druid", "Ranger", "Wizard", "Sorcerer")

DEFAULT_BOND = {
    "Druid": None, "Ranger": None, "Hunter": None,          # an ordinary animal companion
    "Wizard": None, "Witch": None, "Sorcerer": None,        # an ordinary familiar
    "Paladin": None, "Cavalier": None, "Samurai": None,     # an ordinary mount
    "Summoner": "eidolon",
}

# The bond yields a different KIND of creature -- a sixth effect #38's vocabulary lacks. Ordered:
# the first match wins, so "drake companion" beats the generic "companion".
CREATURE_TYPES = (
    (re.compile(r"\bdrakes?\b", re.I), "drake"),
    (re.compile(r"\belemental eidolons?\b", re.I), "eidolon"),
    (re.compile(r"\beidolons?\b", re.I), "eidolon"),
    (re.compile(r"\bconstructs?\b|\bhomunculus\b", re.I), "construct"),
    (re.compile(r"\bundead\b|\bskeletal\b", re.I), "undead"),
    (re.compile(r"\bplant creature\b|\bawakened plant\b", re.I), "plant"),
)

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


def clauses(text):
    """Sentences, then semicolon-separated parts -- the granularity a prohibition binds at."""
    out = []
    for sentence in re.split(r"(?<=[.])\s+", str(text)):
        for part in sentence.split(";"):
            part = " ".join(part.split())
            if part:
                out.append(part)
    return out


def bond_text(body, own_keys, sentences):
    """Only the text that actually describes the bond -- never the whole archetype."""
    keys = list(own_keys) + [key for key, _, _ in sentences]
    seen, parts = set(), []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        value = body.get(key)
        if isinstance(value, str):
            parts.append(value)
    return " ".join(parts)


def derived_pool(clause, species_index):
    """A property restriction resolved against the data, e.g. fly speed -> the 21 species."""
    for pattern, prop in PROPERTY_RES:
        if pattern.search(clause):
            return prop, sorted(species_index.get(prop, ()))
    return None, []


ARTICLES = re.compile(r"^(?:a|an|the|any|only|either|one|its|her|his)\s+", re.I)

# Verbs that mean "acquire or keep the bond", as opposed to merely describing how it behaves.
SELECT_VERB_RE = re.compile(
    r"\b(?:select|selects|choose|chooses|gain|gains|have|has|take|takes|acquire|acquires|"
    r"receive|receives|bond|bonds|get|gets|possess|keep|keeps)\b", re.I)


def named_species(tail, species_index):
    """Species named in a restriction tail that actually exist in animal_choices.json.

    The tail is prose -- "an ape or related primate", "a crocodile or monitor lizard", "a horse or a
    pony" -- so split on the conjunctions the books use, strip articles, and try the phrase plus its
    trailing words ("monitor lizard" -> also "lizard"). Only names the data actually has are kept;
    a species animal_choices.json lacks is a hard validator failure, so a guess must not land here.
    """
    found = []
    for segment in re.split(r"\bor\b|\band\b|,|/", tail.lower()):
        segment = ARTICLES.sub("", " ".join(segment.split()).strip(" -'’"))
        if not segment:
            continue
        words = segment.split()
        # Every contiguous run, longest first, so "ape animal companion" still yields "ape" and
        # "owl, giant" style multiword keys win over a bare noun.
        candidates = sorted(
            {" ".join(words[i:j]) for i in range(len(words)) for j in range(i + 1, len(words) + 1)},
            key=lambda s: -len(s))
        candidates += [f"{words[-1]}, {' '.join(words[:-1])}"] if len(words) > 1 else []
        for candidate in candidates:
            candidate = candidate.strip(" -'")
            if candidate in species_index["names"] and candidate not in found:
                found.append(candidate)
                break
    return found


def negation_signals(clause):
    """What each negation in the clause actually forbids.

    A single regex cannot bind a prohibition to its object, and getting that wrong flips the
    verdict: Sunrider's "cannot choose a DIFFERENT animal or choose a domain instead" restricts the
    pool and forbids the alternative -- it does not remove the creature, which is what a naive
    negation-near-creature match concluded.
    """
    signals = set()
    for match in re.finditer(NEGATION, clause, re.I):
        tail = clause[match.end():match.end() + 110]
        # "a different animal" / "any other animal" narrows the choice; it does not delete it.
        narrows = re.search(r"\b(?:different|other|another)\b", tail[:45], re.I)
        if narrows:
            signals.add("pool")
        domain = DOMAIN_RE.search(tail)
        creature = CREATURE_RE.search(tail)
        if domain and (not creature or domain.start() < creature.start()):
            signals.add("alternative")          # the domain is forbidden -> the flip is suppressed
        elif creature and not narrows and SELECT_VERB_RE.search(tail[:creature.start()]):
            # The prohibition has to be about ACQUIRING the creature. "Abilities that grant
            # evolution points to eidolons do not function for elemental eidolons" is a rules
            # detail, and reading it as a prohibition deleted Elemental Ally's eidolons.
            signals.add("creature")             # the creature itself is forbidden
    return signals


def classify(body, own_keys, sentences, species_index, cls=None):
    """Propose every effect that applies, reading the bond text clause by clause.

    Deliberately NOT single-valued: Devolutionist forces a species, restricts it, AND vetoes a field
    of the advancement merge. Collapsing that drops whichever effect was tested last.
    """
    text = bond_text(body, own_keys, sentences)
    replaced = any(verb in ("replaces", "changes") for _, verb, _ in sentences)

    found, pool_names, pool_property, ctype = [], [], None, None
    pool_raw = []
    creature_clauses = 0

    for clause in clauses(text):
        is_creature = bool(CREATURE_RE.search(clause))
        is_domain = bool(DOMAIN_RE.search(clause))
        conditional = bool(CONDITIONAL_RE.search(clause))

        # Being FORCED onto the alternative removes the creature, and such a clause need not mention
        # the creature at all -- Ancient Guardian's "must choose the domain nature bond ability and
        # select from the following domains" names no animal, so the creature-side gate below would
        # skip it and the archetype would read as harmless. Checked before that gate for exactly
        # that reason. Cave Druid says "may select", not "must", so it stays `none`.
        if not conditional and FORCED_ALTERNATIVE_RE.search(clause):
            found.append(("removes", "high",
                          "forced onto the alternative, so no creature is gained", clause[:170]))
            continue

        if not is_creature:
            continue                      # R2: a domain-only clause says nothing about the creature
        creature_clauses += 1

        # R4 -- does the bond now yield a different KIND of creature? Naming the class's own default
        # is not a change, so a summoner's eidolon is skipped here.
        if ctype is None:
            for pattern, name in CREATURE_TYPES:
                if pattern.search(clause) and name != DEFAULT_BOND.get(cls):
                    ctype = name
                    found.append(("creature_type", "high",
                                  f"the bond yields a {name}, not an animal companion", clause[:160]))
                    break

        signals = negation_signals(clause)
        forced_to_alternative = FORCED_ALTERNATIVE_RE.search(clause)

        # R1 -- the creature itself is forbidden.
        if not conditional and "creature" in signals:
            found.append(("removes", "high", "the creature is forbidden", clause[:170]))

        # R3 -- the alternative is forbidden, or the creature is mandatory. A conditional clause
        # ("who chooses an animal companion") restricts without forcing, which is the only thing
        # separating the totem shamans from Sunrider.
        mandatory = MANDATORY_CREATURE_RE.search(clause)
        if not conditional and ("alternative" in signals or mandatory):
            found.append(("forces", "high", "the alternative is forbidden, or the creature is "
                                            "mandatory -- the flip is suppressed", clause[:170]))

        # R5 -- which creature. Property restrictions resolve against the data.
        pool = POOL_RE.search(clause)
        if "pool" in signals and not pool:
            # "any OTHER class features a summoner gains" is not a species restriction, so the
            # narrowing word has to be attached to a creature.
            pool = re.search(r"\b(?:different|other|another)\s+(?:\w+\s+){0,2}?"
                             r"(?:animal|creature|companion|beast|mount)\b([^;.]{0,120})",
                             clause, re.I)
        if pool and (not is_domain or not DOMAIN_RE.search(pool.group(1))):
            prop, derived = derived_pool(clause, species_index)
            names = derived or named_species(pool.group(1), species_index)
            pool_property = pool_property or prop
            for name in names:
                if name not in pool_names:
                    pool_names.append(name)
            # The EFFECT holds even when no name resolves. "an eagle or a hawk" is a real
            # restriction whether or not animal_choices.json spells those creatures that way, and
            # only resolved names may enter species_pool -- an unresolved guess would trip the
            # validator's hard fail. The phrase is carried for the reviewer instead.
            if prop:
                why = f"restricts the species by {prop} speed ({len(names)} qualify)"
            elif names:
                why = "names the legal species"
            else:
                why = "restricts the species, but none of the names resolve to animal_choices.json"
            found.append(("species_pool", "high" if (prop or names) else "low", why,
                          snippet(pool, clause)))
            if not names:
                pool_raw.append(" ".join(pool.group(1).split())[:120])

        if PROGRESSION_RE.search(clause):
            found.append(("progression", "medium", "changes level or size advancement", clause[:160]))
        elif re.search(r"does ?n[o']?t increase to size", clause, re.I):
            found.append(("progression", "high", "vetoes the size step of the advancement merge",
                          clause[:160]))

    # A replaces-sentence with no creature clause anywhere means it was traded for something else.
    if replaced and not any(e for e, *_ in found if e in ("forces", "removes", "creature_type")):
        found.append(("removes", "medium", "traded away, and nothing in the bond text grants a "
                                           "creature", " ".join(text.split())[-160:]))

    if not found:
        why = ("the bond text restricts only the domain side" if creature_clauses == 0 and text
               else "mentions a bond feature without changing it")
        found.append(("none", "medium" if text else "low", why, ""))

    # Dedupe, keeping the first (most confident) reason for each effect.
    unique, seen = [], set()
    for effect, confidence, why, evidence in found:
        if effect in seen:
            continue
        seen.add(effect)
        unique.append((effect, confidence, why, evidence))

    # `forces` and `removes` are mutually exclusive -- the character cannot be both guaranteed a
    # creature and denied one. Where the bond yields a different KIND of creature, the prohibition
    # is on the animal companion and the grant is the replacement, so it is not a removal at all:
    # "a draconic druid gains a drake companion INSTEAD OF an animal companion".
    if cls is not None and cls not in CHOICE_CLASSES:
        unique = [row for row in unique if row[0] != "forces"]
        if not unique:
            unique = [("none", "medium", "the bond is unconditional for this class and nothing "
                                         "else about it changes", "")]

    kinds = {effect for effect, *_ in unique}
    conflict = False
    if {"forces", "removes"} <= kinds:
        if ctype:
            unique = [row for row in unique if row[0] != "removes"]
        else:
            # Genuinely ambiguous prose. Keep both and say so, rather than silently picking one --
            # this is the shortlist a human or an agent should read in full.
            conflict = True
            unique = [(e, "low", w, ev) for e, c, w, ev in unique]

    return unique, pool_names, pool_property, ctype, pool_raw, conflict


def species_index():
    """Species names, plus the property buckets a restriction can be derived from.

    Derived rather than hand-listed so "an animal with a fly speed" keeps meaning the right set as
    species are added to animal_choices.json.
    """
    with open(SPECIES, encoding="utf-8") as fh:
        data = json.load(fh)
    index = {"names": set(), "fly": set(), "swim": set()}
    for tier in data.values():
        for name, body in tier.items():
            index["names"].add(name.lower())
            speed = str((body.get("starting statistics") or {}).get("speed", "")).lower()
            if "fly" in speed:
                index["fly"].add(name.lower())
            if "swim" in speed:
                index["swim"].add(name.lower())
    return index


def build():
    with open(ARCHETYPES, encoding="utf-8") as fh:
        data = json.load(fh)
    index = species_index()

    entries = {}
    for cls in GRANTORS:
        for name, body in (data.get(cls) or {}).items():
            if not isinstance(body, dict):
                continue
            own_keys, sentences = bond_features(body)
            if not own_keys and not sentences:
                continue
            found, pool_names, pool_property, ctype, pool_raw, conflict = classify(
                body, own_keys, sentences, index, cls)
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
            entry = entries[f"{cls}/{name}"]
            if any(e == "removes" for e, *_ in found):
                # WHAT a `removes` took away, which is NOT the same question as whether it removed
                # something. A druid's nature bond has two sides; an archetype can forbid the
                # CREATURE while leaving the domain reachable ("a blight druid may not bond with an
                # animal companion, but may ... select from the Darkness, Death, and Destruction
                # domains"), or replace the WHOLE FEATURE with something unrelated ("this ability
                # replaces nature bond" -> a phantom, a bonded mask, an aura).
                #
                # `feature` is the default because it is both the conservative answer -- grant
                # nothing rather than invent a feature the archetype traded away -- and the
                # overwhelmingly common one: every one of the 25 Ranger and 18 Wizard `removes`
                # entries reads "this ability replaces hunter's bond / arcane bond". Druid is the
                # only class with a real split, and its six creature-only entries are marked
                # `creature` in companion_archetypes_overrides.json.
                #
                # Only classes whose bond IS a choice have anywhere to fall through to, so this
                # field says nothing for a hunter, witch, cavalier, samurai or summoner.
                entry["removes_scope"] = "feature"
            if ctype:
                entry["creature_type"] = ctype
            if pool_names:
                # Only resolved names go in species_pool -- validate_companion_archetypes.py
                # hard-fails on a species animal_choices.json lacks, so an unresolved phrase must
                # not land here. The phrase is kept for the reviewer instead.
                entry["species_pool"] = pool_names
            if pool_property:
                entry["species_pool_derived_from"] = pool_property
            if pool_raw:
                entry["species_pool_raw"] = pool_raw
            if conflict:
                entry["conflict"] = "forces and removes both detected -- read the full text"
    return entries


def apply_verified(entries):
    """Mark entries whose generated verdict was read against the rules text and confirmed.

    Confirmations are NOT overrides. An override wins permanently, so recording one here would
    freeze today's proposal and stop a later classifier fix from ever taking effect. Instead the
    verified answer is remembered, and if the classifier later disagrees with it the entry is
    flagged stale rather than silently changing under a "signed off" label.
    """
    if not VERIFIED.exists():
        return entries, 0, []
    with open(VERIFIED, encoding="utf-8") as fh:
        verified = (json.load(fh) or {}).get("verified") or {}
    stale = []
    for key, was in verified.items():
        entry = entries.get(key)
        if entry is None:
            stale.append((key, was, "no longer classified"))
            continue
        now = "+".join(sorted(item["effect"] for item in entry.get("effects", [])))
        if now == was:
            entry["signed_off"] = True
            entry["verdict_source"] = "read against the rules text; proposal confirmed"
        else:
            stale.append((key, was, now))
            entry["verification_stale"] = f"verified as {was}, now classified {now}"
    return entries, len(verified), stale


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


def ensure_removes_scope(entries):
    """Guarantee every `removes` carries a scope, whoever introduced it.

    The classifier stamps `removes_scope` when IT decides on `removes`, but an override can
    introduce that verdict where the classifier had something else -- 21 entries do. Those merge
    onto a base with no scope, and the resolver would then read `None` and fall back to `feature`
    anyway. Making it explicit here means the value is visible in the data and closed by the
    validator, rather than being an implicit default nobody can see.
    """
    for entry in entries.values():
        present = {(item.get("effect") if isinstance(item, dict) else item)
                   for item in (entry.get("effects") or [])} | {entry.get("effect")}
        if "removes" in present:
            entry.setdefault("removes_scope", "feature")
        elif "removes_scope" in entry:
            # An override moved the verdict off `removes`; the scope no longer scopes anything.
            entry.pop("removes_scope", None)
            entry.pop("removes_scope_why", None)
    return entries


def generate():
    """THE pipeline: classify, confirm, then correct. Returns (entries, verified, stale, overrides).

    This exists so there is exactly one definition of what the generated file IS.
    `validate_companion_archetypes.check_generated_is_current` used to hand-copy this sequence,
    kept in step by nothing but a comment saying "must mirror... exactly". A third step added to one
    and not the other drifts silently -- and the dangerous direction is not the loud one (every
    build reports stale) but the quiet one, where the two keep agreeing by coincidence until the
    new step first changes real output.

    Order matters and is not arbitrary: `apply_verified` must run BEFORE `apply_overrides`, because
    a confirmation is a statement about what the CLASSIFIER produced. Running it after the overrides
    would compare against the corrected answer and never detect staleness at all.
    """
    entries = build()
    entries, verified_count, stale = apply_verified(entries)
    entries, override_count = apply_overrides(entries)
    entries = ensure_removes_scope(entries)
    return entries, verified_count, stale, override_count


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--review", action="store_true",
                        help="also write the docs/ sign-off worksheet")
    args = parser.parse_args()

    entries, verified_count, stale, override_count = generate()

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
    print(f"  {'(confirmed)':<13} {verified_count:>4}")
    for key, was, now in stale:
        print(f"  STALE: {key} was verified as {was}, now {now}")
    signed = sum(1 for e in entries.values() if e.get("signed_off"))
    print(f"  {'signed off':<13} {signed:>4} / {len(entries)}")
    print(f"wrote {OUT}")

    if args.review:
        print(f"wrote {write_review(entries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
