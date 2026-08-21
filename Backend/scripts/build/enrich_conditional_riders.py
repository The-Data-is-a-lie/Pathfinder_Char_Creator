"""IDEMPOTENT enrichment pass: give every already-curated spell / talent conditional the full
six-detail rider (damage, save DC/type, range, aux effects, activation, cost).

Damage already lives on `modifiers[]`; save TYPE and aux effects are already curated. This pass
APPENDS ONLY THE MISSING labeled clauses -- `Cost:` (gp material components / real spell-point count)
and `Range:` (computed, CL-scaled distance + delivery) -- and injects the computed spell save DC into
an existing `<Type> Save` that has no number. It NEVER reorders or rewords curated text, and is safe
to run repeatedly (a second run is a no-op).

Targets the CURATED FINALS in place:
  * spells  -> Backend/json/spells/spell_riders.json  (Buckets B/C -- full treatment)
              + spell_changes.json entries that carry a `rider` (Bucket-A toggles)
              range/cost source = data/spells.csv (joined by name)
  * talents -> the live module's magic_/combat_talent_conditionals.json
              (fix the seed's hardcoded `[[1]]` spell point + add a Range clause where derivable)
              benefit source = Backend/json/class_data/spheres/spheres_of_power.json /
                               spheres_of_might_enriched.json

    C:\\Python310\\python.exe Backend/scripts/enrich_conditional_riders.py [--dry-run]

Run validate_spell_conditionals.py / validate_talent_conditionals.py afterwards.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO   # noqa: E402
import conditional_clauses as cc
from build_talent_conditionals import _display_name

SPELLS_CSV = REPO / "data" / "spells.csv"
SPELL_RIDERS = REPO / "Backend" / "json" / "spells" / "spell_riders.json"
SPELL_CHANGES = REPO / "Backend" / "json" / "spells" / "spell_changes.json"
SPHERES_DIR = REPO / "Backend" / "json" / "class_data" / "spheres"
MODULE_CS = Path(
    r"C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules\pf1e_random_char_generator"
    r"\templates\character_sheet_folder")
TALENT_FILES = {
    "magic": (MODULE_CS / "magic_talent_conditionals.json", SPHERES_DIR / "spheres_of_power.json"),
    "combat": (MODULE_CS / "combat_talent_conditionals.json",
               SPHERES_DIR / "spheres_of_might_enriched.json"),
}


# --- spells --------------------------------------------------------------------------------------
def _load_spell_rows():
    """name(lower) -> {range, components, material_costs, description} from the CSV."""
    df = pd.read_csv(SPELLS_CSV, sep="|", on_bad_lines="skip", dtype=str, keep_default_na=False)
    rows = {}
    for _, r in df.iterrows():
        name = str(r.get("name", "")).strip()
        if name:
            rows[name.lower()] = {
                "range": str(r.get("range", "")),
                "components": str(r.get("components", "")),
                "material_costs": str(r.get("material_costs", "")),
                "description": str(r.get("short_description", "")) + " " + str(r.get("description", "")),
            }
    return rows


def _enrich_rider_text(text, row, save_block, changed):
    """Prepend the missing Cost/Range/Save clauses to one rider string. `changed` is a 1-elem list
    flag flipped when anything actually changes. When the entry has a save block we add ONE labeled
    `Save:` clause carrying the DC and do NOT inject a DC into the body (the verbose effect mentions
    the save in prose — repeating the DC per mention is noise); otherwise inject_dc is the fallback
    for a body that names a save with no separate block."""
    before = text
    has_save = bool(save_block and str(save_block.get("type", "")).lower()
                    in ("fortitude", "reflex", "will"))
    if not has_save:
        text = cc.inject_dc(text)
    clauses = cc.split_clauses(text)
    prepend = []
    if row:
        cost = cc.spell_cost_clause(row["components"], row["material_costs"])
        if cost and not cc.states_cost(clauses):
            prepend.append(cost)
        rng = cc.spell_range_clause(row["range"], cc.spell_delivery(
            save_block and save_block.get("_attack"), row["description"]))
        if rng and not cc.states_range(clauses):
            prepend.append(rng)
    if has_save and not cc.has_label(clauses, "Save"):
        prepend.append(cc.spell_save_dc_clause(save_block))     # the single primary Save clause + DC
    text = cc.compose(text, prepend)
    text = cc.brackify(text)                          # enforce the validator's all-numbers-bracketed
    if text != before:                               # rule (no-op on already-clean riders; self-heals)
        changed[0] = True
    return text


def enrich_spell_riders(rows, dry):
    data = json.loads(SPELL_RIDERS.read_text(encoding="utf-8"))
    touched = 0
    for name, entry in data.items():
        if not isinstance(entry, dict):
            continue
        row = rows.get(name.lower())
        save = dict(entry.get("save") or {})
        save["_attack"] = entry.get("attack")            # let spell_delivery see melee/ranged
        changed = [False]
        riders = entry.get("riders") or []
        if riders:
            riders = list(riders)
            riders[0] = _enrich_rider_text(riders[0], row, save, changed)
            entry["riders"] = riders
        elif entry.get("save"):
            # No rider text, but a formal save -> synthesize the labeled Save clause (+ range/cost).
            base = cc.spell_save_dc_clause(entry["save"]) or ""
            entry["riders"] = [_enrich_rider_text(base, row, save, changed)] if base else riders
        if changed[0]:
            touched += 1
    print(f"spell_riders: enriched {touched}/{len(data)} entries")
    if not dry:
        SPELL_RIDERS.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def enrich_spell_changes(rows, dry):
    data = json.loads(SPELL_CHANGES.read_text(encoding="utf-8"))
    touched = 0
    for name, entry in data.items():
        if not isinstance(entry, dict) or "rider" not in entry:
            continue                                     # only the A-toggle entries that carry a rider
        row = rows.get(name.lower())
        changed = [False]
        entry["rider"] = _enrich_rider_text(entry["rider"], row, None, changed)
        if changed[0]:
            touched += 1
    print(f"spell_changes: enriched {touched} rider-bearing entries")
    if not dry:
        SPELL_CHANGES.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# --- talents -------------------------------------------------------------------------------------
def _benefit_index(source_path):
    """(_display_name(sphere), _display_name(talent)) -> benefit text."""
    idx = {}
    if not source_path.exists():
        return idx
    data = json.loads(source_path.read_text(encoding="utf-8"))
    for sphere, talents in data.items():
        if not isinstance(talents, dict):
            continue
        for tname, rec in talents.items():
            if isinstance(rec, dict):
                idx[(_display_name(sphere), _display_name(tname))] = str(
                    rec.get("benefit", "") or rec.get("description", "")).strip()
    return idx


def enrich_talents(system, path, source, dry):
    if not path.exists():
        print(f"talents[{system}]: SKIP (module file not found at {path})")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    idx = _benefit_index(source)
    touched = total = 0
    for sphere, talents in data.items():
        if not isinstance(talents, dict):
            continue
        for tname, entry in talents.items():
            if not isinstance(entry, dict):
                continue
            total += 1
            benefit = idx.get((sphere, tname), "")
            rider = str(entry.get("rider", "") or "")
            before = rider
            rider = cc.talent_fix_spellpoint(rider, benefit)         # real spell-point count
            rng = cc.talent_range_clause(benefit)
            if rng and not cc.states_range(cc.split_clauses(rider)):
                rider = cc.compose(rider, [rng])
            if rider != before:
                entry["rider"] = rider
                touched += 1
    print(f"talents[{system}]: enriched {touched}/{total} entries")
    if not dry:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report counts, write nothing")
    args = ap.parse_args()
    rows = _load_spell_rows()
    enrich_spell_riders(rows, args.dry_run)
    enrich_spell_changes(rows, args.dry_run)
    for system, (path, source) in TALENT_FILES.items():
        enrich_talents(system, path, source, args.dry_run)
    if args.dry_run:
        print("(dry run -- no files written)")


if __name__ == "__main__":
    main()
