"""Extract Spheres of Power / Might talent + feat data from the FoundryVTT ``pf1spheres`` module.

The pf1spheres module ships its compendia as binary ClassicLevel (LevelDB) packs, which are not
directly machine-readable.  This script copies the packs out of the live Foundry data dir (Foundry
locks them while running, so we copy and drop the ``LOCK`` file), unpacks them to per-document JSON
via ``@foundryvtt/foundryvtt-cli``, then normalizes them into the shapes the generator's spheres
chooser (``Backend/utils/class_func/spheres.py``) consumes.

Outputs (under ``Backend/json/class_data/spheres/``):
  * ``spheres_of_power.json``        {sphere: {talent: {prerequisites, benefit, type}}}
  * ``spheres_of_might_enriched.json`` scraped spheres_of_might.json + {type, description}
  * ``sphere_feats.json``            {feat: {prerequisites, benefit, system}}   system in {power, might}
  * ``advanced_talents.json``        {"power": {sphere: [names]}, "might": {sphere: [names]}}

``advanced_talents.json`` is the human-auditable registry of which talents are advanced/legendary and
is the override point if the auto-classifier misses one (the §8 advanced-talent gate reads ``type``).

Advanced/legendary classification (the pf1spheres packs carry NO structured flag for it):
  * Magic "advanced": the talent's Prerequisites block names a ``caster level Nth`` gate, OR the talent
    is cross-referenced elsewhere as ``<Name> (advanced)``.  (~274 talents; only edge case observed was
    "Split Blast", caught by the cross-ref pass.)
  * Combat "legendary": the talent is cross-referenced as ``<Name> (legendary)`` / "the <Name> legendary
    talent" anywhere in the compiled or scraped text.  This is necessarily incomplete -- the data has no
    clean marker -- so the runtime ALSO leans on the prerequisite engine (legendary talents carry high
    BAB gates) and the §8 quota; edit advanced_talents.json to add any the scan misses.

Run:  C:\\Python310\\python.exe Backend/scripts/extract_spheres_talents.py
Requires:  Node + npx (uses ``npx --yes @foundryvtt/foundryvtt-cli@latest``).  Foundry may stay open.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(REPO, "Backend", "json", "class_data", "spheres")
SCRAPED_MIGHT = os.path.join(OUT_DIR, "spheres_of_might.json")
SCRATCH = os.path.join(HERE, "_spheres_scratch")

# Default live module location (per project memory); override with $PF1SPHERES_PACKS.
DEFAULT_MODULE = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "FoundryVTT", "Data", "modules", "pf1spheres",
)
PACKS = ("magic-talents", "combat-talents", "sphere-feats")


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #
_BLOCK = re.compile(r"</(?:p|div|li|h[1-6]|tr)>|<br\s*/?>", re.I)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t]+")


def html_to_text(html):
    """Strip HTML to plain text, turning block-closers into newlines and decoding a few entities."""
    if not html:
        return ""
    s = _BLOCK.sub("\n", html)
    s = _TAG.sub("", s)
    for ent, ch in (("&nbsp;", " "), ("&amp;", "&"), ("&#8217;", "'"), ("&#8216;", "'"),
                    ("&#8211;", "-"), ("&#8212;", "-"), ("&#8220;", '"'), ("&#8221;", '"'),
                    ("&rsquo;", "'"), ("&ldquo;", '"'), ("&rdquo;", '"'), ("&quot;", '"')):
        s = s.replace(ent, ch)
    s = "\n".join(_WS.sub(" ", ln).strip() for ln in s.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def norm(s):
    """Comparison key: lower, collapse whitespace, strip trailing source tags like ``[apoc]``."""
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", str(s).lower())
    return _WS.sub(" ", s).strip()


def camel_to_words(s):
    """``dualWielding`` -> ``dual wielding``; ``fallenFey`` -> ``fallen fey``; plain words pass through."""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(s))
    return _WS.sub(" ", s).lower().strip()


def split_prereq_and_benefit(text):
    """Magic talents prefix their description with a ``Prerequisites: ...`` line; split it off.

    Returns (prerequisites, benefit).  Base talents have no prereq line -> ("", full text)."""
    if not text:
        return "", ""
    lines = text.split("\n")
    first = lines[0].strip()
    if re.match(r"^prerequisites?\s*:", first, re.I):
        prereq = re.sub(r"^prerequisites?\s*:\s*", "", first, flags=re.I).strip().rstrip(".")
        benefit = "\n".join(lines[1:]).strip()
        return prereq, benefit
    return "", text


# --------------------------------------------------------------------------- #
# Unpack
# --------------------------------------------------------------------------- #
def unpack_packs(module_dir):
    """Copy the three packs out (dropping the live LOCK) and unpack each to JSON via foundryvtt-cli."""
    src_packs = os.path.join(module_dir, "packs")
    if not os.path.isdir(src_packs):
        sys.exit(f"pf1spheres packs not found at {src_packs} -- set $PF1SPHERES_PACKS to the module dir.")
    packs_in = os.path.join(SCRATCH, "packs_in")
    json_out = os.path.join(SCRATCH, "json_out")
    shutil.rmtree(SCRATCH, ignore_errors=True)
    os.makedirs(packs_in)
    for p in PACKS:
        shutil.copytree(os.path.join(src_packs, p), os.path.join(packs_in, p),
                        ignore=lambda d, names: [n for n in names if n == "LOCK"])
    for p in PACKS:
        out = os.path.join(json_out, p)
        os.makedirs(out, exist_ok=True)
        print(f"  unpacking {p} ...")
        subprocess.run(
            ["npx", "--yes", "@foundryvtt/foundryvtt-cli@latest", "package", "unpack",
             "--id", "pf1spheres", "--type", "Module", "--compendiumName", p,
             "--inputDirectory", packs_in, "--outputDirectory", out],
            check=True, shell=(os.name == "nt"),
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
    return json_out


def load_docs(folder):
    docs = []
    for fn in os.listdir(folder):
        if fn.endswith(".json"):
            with open(os.path.join(folder, fn), encoding="utf-8") as fh:
                docs.append(json.load(fh))
    return docs


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #
_CL_GATE = re.compile(r"caster level\s+\d", re.I)


def collect_descriptor_refs(texts, word):
    """Names cross-referenced as ``<Name> (word)`` or "the <Name> <word> talent" anywhere in `texts`."""
    refs = set()
    paren = re.compile(r"([A-Z][A-Za-z0-9'\-/ ]{2,40}?)\s*\(" + word + r"\)")
    phrase = re.compile(r"\b([A-Z][A-Za-z0-9'\-/ ]{2,40}?)\s+" + word + r"\s+(?:sphere\s+)?talent", re.I)
    for t in texts:
        for rx in (paren, phrase):
            for m in rx.finditer(t):
                refs.add(norm(m.group(1).split(",")[-1]))
    return refs


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    module_dir = os.environ.get("PF1SPHERES_PACKS", DEFAULT_MODULE)
    print(f"pf1spheres module: {module_dir}")
    json_out = unpack_packs(module_dir)

    # ---- magic talents -> spheres_of_power.json -------------------------- #
    magic_docs = load_docs(os.path.join(json_out, "magic-talents"))
    magic_text = {}   # norm name -> {sphere, name, prereq, benefit}
    for d in magic_docs:
        name = d.get("name", "")
        if name.lower().startswith("advanced "):    # per-sphere header docs, not talents
            continue
        sphere = camel_to_words(d.get("flags", {}).get("pf1spheres", {}).get("sphere") or "")
        body = html_to_text(d.get("system", {}).get("description", {}).get("value", ""))
        prereq, benefit = split_prereq_and_benefit(body)
        magic_text[norm(name)] = {"sphere": sphere, "name": name, "prereq": prereq, "benefit": benefit}

    adv_refs = collect_descriptor_refs([v["prereq"] + " " + v["benefit"] for v in magic_text.values()],
                                       "advanced")
    power = defaultdict(dict)
    power_adv = defaultdict(list)
    for key, v in magic_text.items():
        is_adv = bool(_CL_GATE.search(v["prereq"])) or key in adv_refs
        t = "advanced" if is_adv else "base"
        power[v["sphere"]][v["name"].lower()] = {
            "prerequisites": v["prereq"], "benefit": v["benefit"], "type": t,
        }
        if is_adv:
            power_adv[v["sphere"]].append(v["name"])

    # ---- combat talents: build legendary set + description lookup -------- #
    combat_docs = load_docs(os.path.join(json_out, "combat-talents"))
    combat_desc = {}   # norm name -> (sphere, clean description)
    for d in combat_docs:
        name = d.get("name", "")
        if name.lower().startswith("legendary "):
            continue
        sphere = camel_to_words(d.get("flags", {}).get("pf1spheres", {}).get("sphere") or "")
        combat_desc[norm(name)] = (sphere, html_to_text(d.get("system", {}).get("description", {}).get("value", "")))

    # ---- enrich scraped spheres_of_might.json --------------------------- #
    with open(SCRAPED_MIGHT, encoding="utf-8") as fh:
        scraped = json.load(fh)
    legend_refs = collect_descriptor_refs(
        [t for _, t in combat_desc.values()]
        + [str(info.get("benefit", "")) for talents in scraped.values() for info in talents.values()],
        "legendary",
    )
    might = {}
    might_adv = defaultdict(list)
    matched = unmatched = 0
    for sphere, talents in scraped.items():
        might[sphere] = {}
        for name, info in talents.items():
            key = norm(name)
            sphere_desc = combat_desc.get(key)
            description = sphere_desc[1] if sphere_desc else str(info.get("benefit", ""))
            matched += 1 if sphere_desc else 0
            unmatched += 0 if sphere_desc else 1
            is_leg = key in legend_refs or re.search(r"\blegendary talent\b", str(info.get("benefit", "")), re.I) is not None
            t = "advanced" if is_leg else "base"
            might[sphere][name] = {
                "prerequisites": info.get("prerequisites", ""),
                "benefit": info.get("benefit", ""),
                "description": description,
                "type": t,
            }
            if is_leg:
                might_adv[sphere].append(name)

    # ---- sphere feats -> sphere_feats.json ------------------------------ #
    feat_docs = load_docs(os.path.join(json_out, "sphere-feats"))
    sphere_feats = {}
    for d in feat_docs:
        name = d.get("name", "")
        body = html_to_text(d.get("system", {}).get("description", {}).get("value", ""))
        prereq, benefit = split_prereq_and_benefit(body)
        low = body.lower()
        system = "power" if ("magic talent" in low or "spell point" in low or "casting tradition" in low) \
            else "might" if ("combat talent" in low or "martial focus" in low) else "either"
        sphere_feats[name.lower()] = {"prerequisites": prereq, "benefit": benefit or body, "system": system}

    # ---- write --------------------------------------------------------- #
    os.makedirs(OUT_DIR, exist_ok=True)

    def dump(fname, obj):
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)

    dump("spheres_of_power.json", {k: power[k] for k in sorted(power)})
    dump("spheres_of_might_enriched.json", might)
    dump("sphere_feats.json", sphere_feats)
    dump("advanced_talents.json", {
        "power": {k: sorted(power_adv[k]) for k in sorted(power_adv)},
        "might": {k: sorted(might_adv[k]) for k in sorted(might_adv)},
    })

    n_power_adv = sum(len(v) for v in power_adv.values())
    n_might_adv = sum(len(v) for v in might_adv.values())
    print(f"\nspheres_of_power.json:        {sum(len(v) for v in power.values())} talents, "
          f"{len(power)} spheres, {n_power_adv} advanced")
    print(f"spheres_of_might_enriched.json: {sum(len(v) for v in might.values())} talents, "
          f"{len(might)} spheres, {n_might_adv} legendary  (Foundry desc matched {matched}, unmatched {unmatched})")
    print(f"sphere_feats.json:            {len(sphere_feats)} feats")
    print(f"advanced_talents.json:        registry written (edit to add any missed legendary talents)")


if __name__ == "__main__":
    main()
