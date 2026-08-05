#!/usr/bin/env python3
"""
Compile a unified feat table -> data/feats_new.csv

Gathers every feat the project knows about into ONE pipe-delimited file matching the
canonical data/feats.csv schema, plus a trailing `source_dataset` column recording where
each feat came from.

Sources:
  * data/feats.csv             -> Archive of Nethys / official set      (source_dataset="AoN")
  * data/Metzofitz_Feats.csv   -> Metzofitz homebrew library            (source_dataset="Metzofitz")
  * Sieg's Guide "Feats" Google Doc (public txt export)                 (source_dataset="Sieg's Feats Doc")
  * d20 SRD (3.5e) feats page  (https://www.d20srd.org/srd/feats.htm)   (source_dataset="d20srd")

The Google Doc is freeform prose, so its parser is best-effort; the run prints a coverage
report and the full list of parsed feat names so the result can be sanity-checked.

Dedupe precedence on identical (normalized) names: AoN > Metzofitz > Google Doc.

Usage:
    C:\\Python310\\python.exe Backend/scripts/compile_feats_new.py
(bare `python`/`py` are not wired to the backend deps on this machine)

Dependencies: pandas (already a project dep) + stdlib only (urllib) for the fetch.
"""
import re
import sys
import urllib.request
from html import unescape
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _harness import REPO as ROOT   # noqa: E402
DATA = ROOT / "data"
FEATS_CSV = DATA / "feats.csv"
METZ_CSV = DATA / "Metzofitz_Feats.csv"
OUT_CSV = DATA / "feats_new.csv"

DOC_ID = "1H_5OzZSb5fd-tEkX7VYX85_aHrFjBsaESLlhwsoxJ3Q"
DOC_URL = f"https://docs.google.com/document/d/{DOC_ID}/export?format=txt"
D20SRD_URL = "https://www.d20srd.org/srd/feats.htm"

# Canonical 22-column schema of data/feats.csv, plus the new provenance column (23rd).
CANON = [
    "name", "type", "description", "prerequisites", "prerequisite_feats", "benefit",
    "normal", "special", "source", "teamwork", "critical", "grit", "style",
    "performance", "racial", "companion_familiar", "race_name", "note", "goal",
    "completion_benefit", "multiples", "suggested_traits", "source_dataset",
]
BIN_COLS = ["teamwork", "critical", "grit", "style", "performance",
            "racial", "companion_familiar", "multiples"]


# --------------------------------------------------------------------------- #
# Google Doc parsing (best-effort)
# --------------------------------------------------------------------------- #
# Sub-section headers that do NOT end in "Feats" but still partition the list.
EXTRA_SUBHEADERS = {
    "kalyptran",
    "dolistani",
    "bloodlines/domains/school/psychic discipline",
}
# Field labels: "Prerequisite(s):", "Benefit:", "Special", "Normal:", "Notes:" -- with the
# colon optional and sometimes a hyphen instead ("Prerequisite -Violet Ki").
FIELD_RE = re.compile(
    r"^(prerequisite[s]?(?:\(s\))?|benefit[s]?|special|normal|note[s]?)\s*[:\-]?\s*(.*)$",
    re.I,
)


def header_category(line):
    """Return the cleaned category name if `line` is a section header, else None."""
    s = line.strip()
    low = s.lower()
    if low in EXTRA_SUBHEADERS:
        return s
    if low.endswith("feats") and len(s.split()) <= 6:
        cat = re.sub(r"\s*feats\s*$", "", s, flags=re.I).strip()
        return cat or None   # bare "Feats" (doc title) -> not a real category
    return None


def _clean_name(s):
    s = re.sub(r"\s*:\s*$", "", s.strip())   # drop trailing colon
    return re.sub(r"\s+", " ", s).strip()


def looks_like_name(line):
    """Heuristic: short, letter-initial, label-free, non-sentence -> a feat name."""
    s = re.sub(r"\s*:\s*$", "", line.strip())
    if not s or not re.match(r"^[A-Za-z]", s):
        return False
    if "://" in s or s.lower().startswith(("http", "www.")):
        return False
    if len(s) > 60 or len(s.split()) > 8 or s.endswith("."):
        return False
    return FIELD_RE.match(s) is None


def _new_feat(name, cat):
    return {
        "name": name, "type": cat or "", "description": "", "prerequisites": "",
        "benefit": "", "normal": "", "special": "", "note": "", "_mode": "desc",
    }


def parse_doc(text):
    """Parse the plain-text Google Doc into a list of feat dicts (best-effort)."""
    text = text.lstrip("﻿")
    feats, seen = [], set()
    cat, cur, prev_blank = None, None, True

    def finalize(cur):
        if not cur:
            return
        if cur["benefit"].strip() or cur["prerequisites"].strip() or cur["description"].strip():
            key = re.sub(r"\s+", " ", cur["name"].strip().lower())
            if cur["name"].strip() and key not in seen:
                seen.add(key)
                cur.pop("_mode", None)
                feats.append(cur)

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            prev_blank = True
            continue

        hc = header_category(line)
        if hc is not None:
            finalize(cur)
            cur, cat, prev_blank = None, hc, True
            continue

        if cat is None:          # still in the document preamble
            prev_blank = False
            continue

        m = FIELD_RE.match(line)
        if m:
            label, rest = m.group(1).lower(), m.group(2).strip()
            if cur is not None:
                if label.startswith("prerequisite"):
                    cur["prerequisites"] = (cur["prerequisites"] + " " + rest).strip()
                    cur["_mode"] = "benefit"        # flavor is done after a prereq
                elif label.startswith("benefit"):
                    cur["benefit"] = (cur["benefit"] + " " + rest).strip()
                    cur["_mode"] = "benefit"
                elif label.startswith("special"):
                    cur["special"] = (cur["special"] + " " + rest).strip()
                    cur["_mode"] = "special"
                elif label.startswith("normal"):
                    cur["normal"] = (cur["normal"] + " " + rest).strip()
                    cur["_mode"] = "normal"
                elif label.startswith("note"):
                    cur["note"] = (cur["note"] + " " + rest).strip()
                    cur["_mode"] = "note"
            prev_blank = False
            continue

        if line.startswith("[") and line.endswith("]"):
            if cur is not None:
                tag = line.strip("[]").strip()
                cur["note"] = (cur["note"] + "; " + tag).strip("; ").strip() if cur["note"] else tag
            prev_blank = False
            continue

        # plain line: new feat name, or continuation of the current feat
        if cur is not None and prev_blank and looks_like_name(line):
            finalize(cur)
            cur = _new_feat(_clean_name(line), cat)
        elif cur is None:
            if looks_like_name(line):
                cur = _new_feat(_clean_name(line), cat)
        else:
            mode = cur.get("_mode", "desc")
            if mode == "desc":
                cur["description"] = (cur["description"] + " " + line).strip()
            elif mode in ("special", "normal", "note"):
                cur[mode] = (cur[mode] + " " + line).strip()
            else:
                cur["benefit"] = (cur["benefit"] + " " + line).strip()
                cur["_mode"] = "benefit"
        prev_blank = False

    finalize(cur)
    return feats


def fetch_url(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; feat-compiler/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch_doc():
    return fetch_url(DOC_URL)


# --------------------------------------------------------------------------- #
# Source loaders -> canonical 23-column frames
# --------------------------------------------------------------------------- #
def _read_csv(path):
    return pd.read_csv(path, sep="|", dtype=str, keep_default_na=False, on_bad_lines="skip")


def _to_canon(df):
    """Add any missing canonical columns (binary->'0', text->'') and order them."""
    for c in CANON:
        if c not in df.columns:
            df[c] = "0" if c in BIN_COLS else ""
    return df[CANON]


def load_aon():
    df = _read_csv(FEATS_CSV)
    df["source_dataset"] = "AoN"
    return _to_canon(df)


def load_metz():
    src = _read_csv(METZ_CSV)
    out = pd.DataFrame()
    out["name"] = src.get("name", "")
    out["type"] = src.get("type", "")
    out["description"] = src.get("description", "")
    out["prerequisites"] = src.get("prerequisites", "")
    out["benefit"] = src.get("benefits", "")          # Metzofitz uses plural "benefits"
    out["teamwork"] = src.get("teamwork", "0")
    out["style"] = src.get("Style", "0")
    out["source"] = ""
    out["source_dataset"] = "Metzofitz"
    return _to_canon(out)


def load_doc(text):
    feats = parse_doc(text)
    out = pd.DataFrame(feats)
    out["source"] = "Sieg's Guide (homebrew)"
    out["source_dataset"] = "Sieg's Feats Doc"
    return _to_canon(out), feats


# --------------------------------------------------------------------------- #
# d20 SRD (3.5e) feats page parsing
# --------------------------------------------------------------------------- #
SRD_TYPES = {"general", "item creation", "metamagic", "special"}


def _strip_html(s):
    """Remove tags, unescape HTML entities, and collapse whitespace."""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def load_srd(html):
    """Parse the d20 SRD feats page into canonical-schema rows. Each feat is
    `<h3>Name [Type]</h3>` followed by `<h5>label</h5><p>text</p>` sections (Prerequisite / Benefit /
    Normal / Special). Nav-section headings (no real [Type]) are skipped."""
    rows = []
    for m in re.finditer(r"<h3\b[^>]*>(.*?)</h3>(.*?)(?=<h3\b|\Z)", html, re.I | re.S):
        head = _strip_html(m.group(1))
        tm = re.match(r"^(.*?)\s*\[([^\]]+)\]\s*$", head)
        if not tm:
            continue
        name, ftype = tm.group(1).strip(), tm.group(2).strip()
        if ftype.lower() not in SRD_TYPES:
            continue                                  # nav-section heading / "[Type Of Feat]" example
        fields = {"prerequisites": "", "benefit": "", "normal": "", "special": ""}
        for fm in re.finditer(r"<h5\b[^>]*>(.*?)</h5>(.*?)(?=<h5\b|\Z)", m.group(2), re.I | re.S):
            label = _strip_html(fm.group(1)).lower()
            text = _strip_html(fm.group(2))
            col = ("prerequisites" if label.startswith("prerequisite")
                   else "benefit" if label.startswith("benefit")
                   else "normal" if label.startswith("normal")
                   else "special" if label.startswith("special") else None)
            if col:
                fields[col] = (fields[col] + " " + text).strip()
        rows.append({"name": name, "type": ftype, **fields})
    out = pd.DataFrame(rows)
    out["source"] = "3.5 SRD"
    out["source_dataset"] = "d20srd"
    return _to_canon(out), rows


def _norm_key(series):
    return series.str.strip().str.lower().str.replace(r"\s+", " ", regex=True)


def _loose_key(series):
    """Order-insensitive dedup key: lowercase, keep alphanumeric tokens, then sort and join them -- so
    "Blind-Fight" == "Blind Fight" AND "Armor Proficiency (Heavy)" == "Heavy Armor Proficiency".
    Used to dedup the d20 SRD source against the rest."""
    return (series.astype(str).str.lower()
            .str.findall(r"[a-z0-9]+")
            .apply(lambda toks: " ".join(sorted(toks))))


def _sanitize(df):
    """Strip newlines / pipes / nbsp from every field so the pipe CSV round-trips cleanly."""
    for c in df.columns:
        df[c] = (
            df[c].astype(str)
            .str.replace("\r", " ", regex=False)
            .str.replace("\n", " ", regex=False)
            .str.replace("|", "/", regex=False)
            .str.replace(" ", " ", regex=False)
            .str.replace(r"[ \t]+", " ", regex=True)
            .str.strip()
        )
    return df


def main():
    print(f"repo root : {ROOT}")
    print("fetching Google Doc ...")
    try:
        text = fetch_doc()
    except Exception as exc:                      # noqa: BLE001
        print(f"ERROR: could not fetch the Google Doc: {exc}", file=sys.stderr)
        return 1
    print(f"  doc fetched: {len(text)} chars")

    aon = load_aon()
    metz = load_metz()
    doc, parsed = load_doc(text)

    print("fetching d20 SRD feats page ...")
    try:
        srd, _srd_rows = load_srd(fetch_url(D20SRD_URL))
    except Exception as exc:                          # noqa: BLE001
        print(f"  WARNING: could not fetch/parse d20 SRD page: {exc}", file=sys.stderr)
        srd = _to_canon(pd.DataFrame({"name": []}))
    print(f"\nrows loaded  ->  AoN: {len(aon)}  |  Metzofitz: {len(metz)}  |  "
          f"Google Doc parsed: {len(doc)}  |  d20 SRD parsed: {len(srd)}")

    # Preserve AoN + Metzofitz EXACTLY (their intra-file same-name rows are distinct feats, e.g. a base
    # feat and its Mythic version). Each additive source is deduped against everything already kept:
    # the Google Doc by normalized name, then the d20 SRD by a looser alphanumeric key.
    existing = set(_norm_key(pd.concat([aon["name"], metz["name"]], ignore_index=True)))
    shadow_mask = _norm_key(doc["name"]).isin(existing)
    doc_kept = doc[~shadow_mask].copy()
    shadowed_names = sorted(doc.loc[shadow_mask, "name"].tolist())

    existing_loose = set(_loose_key(pd.concat(
        [aon["name"], metz["name"], doc_kept["name"]], ignore_index=True)))
    srd_mask = _loose_key(srd["name"]).isin(existing_loose)
    srd_kept = srd[~srd_mask].copy()
    srd_skipped = sorted(srd.loc[srd_mask, "name"].tolist())

    combined = pd.concat([aon, metz, doc_kept, srd_kept], ignore_index=True)
    combined = combined[combined["name"].str.strip() != ""]
    combined = _sanitize(combined)[CANON]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_CSV, sep="|", index=False, encoding="utf-8")

    # ---- verify it re-loads exactly the way the backend reads feats ------------ #
    check = pd.read_csv(OUT_CSV, sep="|", dtype=str, keep_default_na=False, on_bad_lines="skip")
    ok_cols = list(check.columns) == CANON
    ok_rows = len(check) == len(combined)

    by_src = combined["source_dataset"].value_counts().to_dict()
    cross = len(set(_norm_key(aon["name"])) & set(_norm_key(metz["name"])))

    print("\n================ REPORT ================")
    print(f"written            : {OUT_CSV}")
    print(f"total feats         : {len(combined)}  "
          f"(AoN + Metzofitz preserved as-is; intra-file same-name rows kept)")
    print(f"by source_dataset   : {by_src}")
    print(f"Google Doc feats    : {len(parsed)} parsed -> {len(doc_kept)} added, "
          f"{len(shadowed_names)} already in AoN/Metzofitz (skipped)")
    print(f"d20 SRD feats       : {len(srd)} parsed -> {len(srd_kept)} added, "
          f"{len(srd_skipped)} already present (skipped)")
    print(f"AoN <-> Metzofitz    : {cross} shared feat names (kept in both, tagged by source_dataset)")
    print(f"reload check        : columns {'OK' if ok_cols else 'MISMATCH'}, "
          f"rows {'OK' if ok_rows else f'MISMATCH ({len(check)} vs {len(combined)})'}")
    print("\nMetzofitz NOTE      : homebrew tag columns beyond the canonical schema "
          "(Akashic, Kineticist, Psionic, ...) were dropped; current selection code reads "
          "only name/type/prerequisites/description/teamwork/critical.")

    print("\n-- Google Doc feats parsed (eyeball these) --")
    for f in parsed:
        print(f"   [{f['type']}] {f['name']}")
    if shadowed_names:
        print("\n-- Google Doc feats skipped (same name already in AoN/Metzofitz) --")
        print("   " + ", ".join(shadowed_names))
    if len(srd_kept):
        print("\n-- d20 SRD feats ADDED (net-new) --")
        print("   " + ", ".join(sorted(srd_kept["name"].tolist())))

    print("\n-- sample row per source --")
    for ds in ("AoN", "Metzofitz", "Sieg's Feats Doc", "d20srd"):
        sub = combined[combined["source_dataset"] == ds]
        if len(sub):
            r = sub.iloc[len(sub) // 2]
            print(f"   {ds}: {r['name']} | type={r['type']} | prereq={r['prerequisites'][:60]!r}")

    return 0 if (ok_cols and ok_rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
