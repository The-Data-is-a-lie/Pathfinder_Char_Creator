"""Convert legacy JS-ternary roll formulas to current pf1 (v11+) function syntax.

FoundryVTT v13's pf1 system removed JS-style ternary/comparison formulas; e.g. a change
`@skills.per.rank>=10?4:2` now throws `Unresolved StringTerm`. The pf1 help docs
(systems/pf1/help/en/Formulas.md) define the function replacements:
    >= -> gte   <= -> lte   > -> gt   < -> lt   == / === -> eq   != / !== -> ne
    && -> and(...)        || -> or(...)        cond ? a : b -> ifelse(cond, a, b)
e.g.  @skills.per.rank>=10?4:2  ->  ifelse(gte(@skills.per.rank, 10), 4, 2)

It walks the pf1e_random_char_generator module's bundled item JSONs and converts ternaries
in the three contexts pf1 actually evaluates:
  * `formula` keys           -> whole-string convert (the reported skill-bonus crash)
  * `value` keys that parse   -> whole-string convert (conditional action durations, etc.)
  * `[[ ... ]]` inline rolls   -> inner-expression convert (context notes)
Arithmetic, @paths, dice (`NdM`), and existing function calls pass through verbatim; prose
strings (descriptions, question-mark names) fail to parse and are left untouched.

Dry-run by default (prints the distinct old->new map + parse failures); pass --apply to back
up each file (.bak) and rewrite it via exact-substring replacement (no whole-file reformat).

Run:  C:\\Python310\\python.exe Backend/scripts/fix_foundry_change_formulas.py [--apply]
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

MODULE_DIR = Path(
    r"C:\Users\Daniel\AppData\Local\FoundryVTT\Data\modules"
    r"\pf1e_random_char_generator\templates\character_sheet_folder"
)
FILES = [
    "every_feat.json", "every_feat_MODS.json",
    "every_class_feature.json", "every_class_feature_MODS.json",
    "every_trait.json", "every_trait_MODS.json",
    "every_class.json", "every_class_MODS.json",
]

# --------------------------------------------------------------------------- #
# Tokenizer + recursive-descent parser for the legacy formula grammar
# --------------------------------------------------------------------------- #
_TOKEN_RE = re.compile(r"""
    \s+
  | (?P<ATPATH>@[\w.]+)
  | (?P<DICE>\d+d\d+%?|\d+d%)
  | (?P<NUMBER>\d+(?:\.\d+)?)
  | (?P<IDENT>[A-Za-z_]\w*)
  | (?P<OP>===|!==|>=|<=|==|!=|&&|\|\||[?:()+\-*/%,<>])
""", re.VERBOSE)

_CMP = {">=": "gte", "<=": "lte", "==": "eq", "===": "eq",
        "!=": "ne", "!==": "ne", ">": "gt", "<": "lt"}
_DIE_SUFFIX = re.compile(r"^d\d+%?$|^d%$")


def _tokenize(s):
    toks, i = [], 0
    while i < len(s):
        m = _TOKEN_RE.match(s, i)
        if not m:
            raise ValueError(f"bad char at {i}: {s[i:i+12]!r}")
        i = m.end()
        if m.lastgroup is not None:          # skip the unnamed whitespace branch
            toks.append((m.lastgroup, m.group()))
    toks.append(("EOF", ""))
    return toks


class _Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0

    def peek(self):
        return self.toks[self.i]

    def nxt(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, val):
        t = self.nxt()
        if t[1] != val:
            raise ValueError(f"expected {val!r} got {t!r}")
        return t

    def ternary(self):
        cond = self.logic_or()
        if self.peek()[1] == "?":
            self.nxt()
            a = self.ternary()
            self.expect(":")
            b = self.ternary()
            return f"ifelse({cond}, {a}, {b})"
        return cond

    def logic_or(self):
        parts = [self.logic_and()]
        while self.peek()[1] == "||":
            self.nxt()
            parts.append(self.logic_and())
        return parts[0] if len(parts) == 1 else "or(" + ", ".join(parts) + ")"

    def logic_and(self):
        parts = [self.comparison()]
        while self.peek()[1] == "&&":
            self.nxt()
            parts.append(self.comparison())
        return parts[0] if len(parts) == 1 else "and(" + ", ".join(parts) + ")"

    def comparison(self):
        left = self.additive()
        if self.peek()[1] in _CMP:
            op = self.nxt()[1]
            return f"{_CMP[op]}({left}, {self.additive()})"
        return left

    def additive(self):
        left = self.multiplicative()
        while self.peek()[1] in ("+", "-"):
            op = self.nxt()[1]
            left = f"{left} {op} {self.multiplicative()}"
        return left

    def multiplicative(self):
        left = self.unary()
        while self.peek()[1] in ("*", "/", "%"):
            op = self.nxt()[1]
            left = f"{left} {op} {self.unary()}"
        return left

    def unary(self):
        if self.peek()[1] in ("-", "+"):
            op = self.nxt()[1]
            return f"{op}{self.unary()}"
        return self.atom_with_dice()

    def atom_with_dice(self):
        atom = self.primary()
        # a ternary/number used as a dice count, e.g. (cond ? 2 : 1)d8  -> (ifelse(...))d8
        if self.peek()[0] == "IDENT" and _DIE_SUFFIX.match(self.peek()[1]):
            atom += self.nxt()[1]
        return atom

    def primary(self):
        typ, val = self.peek()
        if val == "(":
            self.nxt()
            e = self.ternary()
            self.expect(")")
            return f"({e})"
        if typ in ("NUMBER", "ATPATH", "DICE"):
            self.nxt()
            return val
        if typ == "IDENT":
            self.nxt()
            if self.peek()[1] == "(":                # function call
                self.nxt()
                args = []
                if self.peek()[1] != ")":
                    args.append(self.ternary())
                    while self.peek()[1] == ",":
                        self.nxt()
                        args.append(self.ternary())
                self.expect(")")
                return f"{val}(" + ", ".join(args) + ")"
            return val                               # bare identifier
        raise ValueError(f"unexpected token {self.peek()!r}")


def convert_expr(s):
    s = s.strip()
    # tolerate a stray over-closing trailing paren (one malformed source formula)
    while s.endswith(")") and s.count(")") > s.count("("):
        s = s[:-1].rstrip()
    p = _Parser(_tokenize(s))
    out = p.ternary()
    if p.peek()[0] != "EOF":
        raise ValueError(f"trailing tokens: {p.toks[p.i:]!r}")
    for bad in ("?", "<", ">", "&", "|", "=", "!"):
        if bad in out:
            raise ValueError(f"residual {bad!r} in output {out!r}")
    if out.count("(") != out.count(")"):
        raise ValueError(f"unbalanced parens in {out!r}")
    return out


_INLINE_RE = re.compile(r"\[\[(.+?)\]\]")


def convert_inline_rolls(text):
    """Return (new_text, [(old_span, new_span)...]) converting only [[...]] rolls with a '?'."""
    spans = []

    def repl(m):
        inner = m.group(1)
        if "?" not in inner:
            return m.group(0)
        try:
            new_inner = convert_expr(inner)
        except Exception:
            return m.group(0)                       # not a parseable roll -> leave as-is
        old_span, new_span = m.group(0), f"[[{new_inner}]]"
        if old_span != new_span:
            spans.append((old_span, new_span))
        return new_span

    return _INLINE_RE.sub(repl, text), spans


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def walk(node, whole, inline, failures, fname):
    """whole: {(key, old) -> new}; inline: {old_span -> new_span}."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str):
                kl = k.lower()
                if "?" in v and ("[[" in v):
                    _, spans = convert_inline_rolls(v)
                    for old_s, new_s in spans:
                        inline[old_s] = new_s
                if "?" in v and "[[" not in v and (kl == "formula" or "formula" in kl or kl == "value"):
                    if v.lstrip().startswith("<"):
                        continue                     # HTML prose
                    try:
                        whole[(k, v)] = convert_expr(v)
                    except Exception as e:           # noqa: BLE001 - prose/odd -> report
                        if kl == "formula" or "formula" in kl:
                            failures.append((fname, k, v, str(e)))
                else:
                    continue
            else:
                walk(v, whole, inline, failures, fname)
    elif isinstance(node, list):
        for v in node:
            walk(v, whole, inline, failures, fname)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    whole, inline, failures = {}, {}, []
    for fname in FILES:
        path = MODULE_DIR / fname
        if not path.exists():
            print(f"!! missing: {path}")
            continue
        walk(json.loads(path.read_text(encoding="utf-8")), whole, inline, failures, fname)

    distinct_whole = {old: new for (_, old), new in whole.items()}
    print(f"=== whole-string formulas: {len(distinct_whole)} distinct ===")
    for old in sorted(distinct_whole):
        print(f"  {old!r}\n    -> {distinct_whole[old]!r}")
    print(f"\n=== inline [[...]] rolls: {len(inline)} distinct ===")
    for old in sorted(inline):
        print(f"  {old!r} -> {inline[old]!r}")
    if failures:
        print(f"\n=== PARSE FAILURES (formula keys): {len(failures)} ===")
        for f, k, v, e in failures:
            print(f"  {f}: {v!r} :: {e}")

    if not args.apply:
        print("\n(dry run -- re-run with --apply to write changes)")
        return 1 if failures else 0
    if failures:
        print("\nRefusing to --apply with unresolved formula-key failures.")
        return 1

    for fname in FILES:
        path = MODULE_DIR / fname
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        n = 0
        for (key, old), new in whole.items():
            if old == new:
                continue
            for sep in (": ", ":"):
                tok = f'"{key}"{sep}{json.dumps(old)}'
                c = text.count(tok)
                if c:
                    text = text.replace(tok, f'"{key}"{sep}{json.dumps(new)}')
                    n += c
        for old_s, new_s in inline.items():
            c = text.count(old_s)
            if c:
                text = text.replace(old_s, new_s)
                n += c
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(path, bak)
        path.write_text(text, encoding="utf-8")
        json.loads(text)                             # re-validate
        print(f"  {fname}: {n} replacements, JSON re-validated, backup={bak.name}")
    print("\napplied. verify in Foundry (no 'Unresolved StringTerm'; Alertness +2/+4).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
