"""Merge the spheres-data-harvest workflow output into the extracted data files.

The harvest workflow returns {magic_advanced, combat_legendary, traditions, tradition_verdicts}. Save
that return value to ``Backend/scripts/_spheres_harvest_result.json`` and run this script. It:
  * GROUNDS every proposed advanced/legendary talent name against the REAL talent keys in
    spheres_of_power.json / spheres_of_might_enriched.json (normalized match) so nothing hallucinated
    enters -- only names that correspond to an actual talent are accepted;
  * unions the grounded names into advanced_talents.json and flips those talents' ``type`` to
    "advanced" in the talent files (the §8 runtime gate reads ``type``);
  * writes spheres_traditions.json from the synthesized tradition data, dropping any drawback/boon the
    adversarial verifiers flagged as fabricated.

Run:  C:\\Python310\\python.exe Backend/scripts/merge_spheres_harvest.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "json", "class_data", "spheres")
RESULT = os.path.join(HERE, "_spheres_harvest_result.json")


def norm(s):
    s = re.sub(r"\s*\[[^\]]*\]\s*", " ", str(s).lower())
    return re.sub(r"\s+", " ", s).strip()


def norm_loose(s):
    """norm() with trailing/inline ``(descriptor)`` parens also stripped (Foundry magic names are clean,
    but the workflow proposes e.g. ``Material Body (alter)`` / ``Star-Spawn Body (body)``)."""
    s = re.sub(r"\([^)]*\)", " ", norm(s))
    return re.sub(r"\s+", " ", s).strip()


def flagged_name(s):
    """A verdict's fabricated_* entry is ``Name — explanation``; pull just the name for matching."""
    return norm(re.split(r"[—–\-:(]", str(s), 1)[0])


def load(name):
    with open(os.path.join(OUT, name), encoding="utf-8") as fh:
        return json.load(fh)


def dump(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)


def ground_and_merge(talent_file, proposed_by_sphere, registry_key, registry):
    """Flip matched talents' type->advanced in `talent_file`; union grounded names into the registry."""
    data = load(talent_file)
    sphere_index = {norm(s): s for s in data}
    sphere_index.update({norm_loose(s): s for s in data})
    added = unmatched = 0
    for prop_sphere, names in (proposed_by_sphere or {}).items():
        real_sphere = sphere_index.get(norm(prop_sphere)) or sphere_index.get(norm_loose(prop_sphere))
        if not real_sphere:
            continue
        # index every real key under both its strict and loose normalized forms
        key_index = {}
        for k in data[real_sphere]:
            key_index.setdefault(norm(k), k)
            key_index.setdefault(norm_loose(k), k)
        for nm in names:
            real_key = key_index.get(norm(nm)) or key_index.get(norm_loose(nm))
            if not real_key:
                unmatched += 1
                continue                      # not a real talent in our data -> reject (anti-hallucination)
            if data[real_sphere][real_key].get("type") != "advanced":
                data[real_sphere][real_key]["type"] = "advanced"
                added += 1
    dump(talent_file, data)
    return added, unmatched


def rebuild_registry(talent_file, registry, registry_key):
    """advanced_talents.json is a clean generated MIRROR of the talent files' type==advanced flags
    (the runtime's single source of truth), so it stays consistent and dedup-free."""
    data = load(talent_file)
    out = {}
    for sphere, talents in data.items():
        adv = sorted(k for k, v in talents.items() if str(v.get("type", "")).lower() == "advanced")
        if adv:
            out[sphere] = adv
    registry[registry_key] = out


def main():
    if not os.path.exists(RESULT):
        raise SystemExit(f"Save the workflow return value to {RESULT} first.")
    with open(RESULT, encoding="utf-8") as fh:
        res = json.load(fh)

    registry = load("advanced_talents.json")
    registry.setdefault("power", {})
    registry.setdefault("might", {})

    p_added, p_un = ground_and_merge("spheres_of_power.json", res.get("magic_advanced"), "power", registry)
    m_added, m_un = ground_and_merge("spheres_of_might_enriched.json", res.get("combat_legendary"), "might", registry)
    rebuild_registry("spheres_of_power.json", registry, "power")
    rebuild_registry("spheres_of_might_enriched.json", registry, "might")
    dump("advanced_talents.json", {k: registry[k] for k in ("power", "might")})

    # ---- traditions (drop EITHER verifier's flagged fabrications; keep correct mechanics/chart) ----
    trad = res.get("traditions") or {}
    flagged_db, flagged_bn = set(), set()
    for v in res.get("tradition_verdicts", []) or []:
        flagged_db.update(flagged_name(x) for x in (v.get("fabricated_drawbacks") or []))
        flagged_bn.update(flagged_name(x) for x in (v.get("fabricated_boons") or []))
    drop_db = drop_bn = 0
    if trad:
        kept_db = [d for d in trad.get("general_drawbacks", []) if norm(d.get("name", "")) not in flagged_db]
        kept_bn = [b for b in trad.get("boons", []) if norm(b.get("name", "")) not in flagged_bn]
        drop_db = len(trad.get("general_drawbacks", [])) - len(kept_db)
        drop_bn = len(trad.get("boons", [])) - len(kept_bn)
        trad["general_drawbacks"], trad["boons"] = kept_db, kept_bn
        # canonical triangular chart (math-verified; one verifier mis-flagged it)
        trad["bonus_spell_point_chart"] = [{"drawbacks": n, "bonus_spell_points": n * (n + 1) // 2}
                                           for n in range(0, 12)]
        dump("spheres_traditions.json", trad)

    print(f"magic advanced flipped: +{p_added} (rejected {p_un} unmatched)   "
          f"combat legendary flipped: +{m_added} (rejected {m_un} unmatched)")
    print(f"advanced_talents.json: power={sum(len(v) for v in registry['power'].values())} "
          f"might={sum(len(v) for v in registry['might'].values())}")
    if trad:
        print(f"spheres_traditions.json: {len(trad.get('general_drawbacks', []))} drawbacks, "
              f"{len(trad.get('boons', []))} boons, "
              f"{len(trad.get('sphere_specific_drawbacks', []))} sphere-specific "
              f"(dropped {drop_db} drawbacks / {drop_bn} boons flagged as fabricated/5E)")


if __name__ == "__main__":
    main()
