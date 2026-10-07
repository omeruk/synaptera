#!/usr/bin/env python
"""Line-level similarity between the code of the public copy and the upstream NeuroFly source files (script only; no interpretation).

For every .py / .sh file of the public allow-list (docs/FILE_PROVENANCE.md section B, as scripts/make_public_snapshot.sh builds it) and
every .py / .sh file of the upstream commit (read with `git show <upstream>:<path>` from the local repository), after removing blank
lines, comments and docstrings and collapsing white space:
  shared lines      lines (multiset) present in both files, split into trivial (imports, bare brackets, `pass`, `else:` ...) and meaningful
  longest block     longest run of consecutive identical lines, with the number of meaningful lines in it
  ratio             shared meaningful lines / meaningful lines of the public file
The best upstream match (most shared meaningful lines) is reported per public file.

    env -u PYTHONPATH python scripts/check_originality.py [--md docs/ORIGINALITY_CHECK_table.md] [--upstream b59264a] [--threshold 5]

Exit status 1 if any file has a longest block of at least `threshold` meaningful lines.
"""
import argparse
import ast
import collections
import difflib
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIVIAL = re.compile(r"^(import .*|from .* import .*|[\]\[(){},:]+|pass|else:|try:|finally:|continue|break|return|return None|return True|return False|"
                     r"\"\"\"|'''|if __name__ == .__main__.:|main\(\)|#!.*|set -.*|fi|done|then|do|esac|\)|\}|\{)$")


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def normalise(text, kind):
    """List of normalised lines (no blanks, comments, docstrings)."""
    lines = text.splitlines()
    drop = set()
    if kind == "py":
        try:
            tree = ast.parse(text)
            for n in ast.walk(tree):
                if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                        and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str):
                    drop.update(range(n.body[0].lineno, n.body[0].end_lineno + 1))
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type == tokenize.COMMENT:
                    r, c = tok.start
                    lines[r - 1] = lines[r - 1][:c]
        except (SyntaxError, tokenize.TokenError):
            pass
    out = []
    for i, ln in enumerate(lines, 1):
        if i in drop:
            continue
        if kind == "sh":
            ln = re.sub(r"(^|\s)#.*$", "", ln) if not ln.lstrip().startswith("#!") else ln
        ln = re.sub(r"\s+", " ", ln.strip())
        if ln and not ln.startswith("#"):
            out.append(ln)
    return out


def is_trivial(ln):
    return bool(TRIVIAL.match(ln))


def public_files(upstream):
    """Allow-list of the public copy: .py/.sh files of FILE_PROVENANCE section B that are tracked at HEAD and not upstream paths."""
    prov = (ROOT / "docs" / "FILE_PROVENANCE.md").read_text()
    listed = re.findall(r"^\| `([^`]+)` \| [0-9a-f]{7}", prov[prov.index("## B. Files added in this work"):], re.M)
    head = set(git("ls-tree", "-r", "--name-only", "HEAD").split("\n"))
    up = set(git("ls-tree", "-r", "--name-only", upstream).split("\n"))
    excl = ("archive/", "brain_model/", "data/", "logs/", "plots/", "simulations/")
    return sorted(f for f in dict.fromkeys(listed) if f.endswith((".py", ".sh")) and f in head and f not in up and not f.startswith(excl))


def upstream_files(upstream):
    return sorted(f for f in git("ls-tree", "-r", "--name-only", upstream).split("\n") if f.endswith((".py", ".sh")))


def compare(a, b):
    """a, b: normalised line lists -> (shared meaningful, shared trivial, longest block length, meaningful lines in it)."""
    ca, cb = collections.Counter(a), collections.Counter(b)
    sm = sum(min(n, cb[l]) for l, n in ca.items() if l in cb and not is_trivial(l))
    st = sum(min(n, cb[l]) for l, n in ca.items() if l in cb and is_trivial(l))
    if sm == 0:
        return 0, st, 0, 0
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    blk = a[m.a:m.a + m.size]
    return sm, st, m.size, sum(not is_trivial(l) for l in blk)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--upstream", default="b59264a")
    ap.add_argument("--threshold", type=int, default=5)
    ap.add_argument("--md")
    a = ap.parse_args()
    ups = {f: normalise(git("show", f"{a.upstream}:{f}"), "py" if f.endswith(".py") else "sh") for f in upstream_files(a.upstream)}
    rows, flagged = [], []
    for f in public_files(a.upstream):
        kind = "py" if f.endswith(".py") else "sh"
        mine = normalise((ROOT / f).read_text() if (ROOT / f).exists() else git("show", f"HEAD:{f}"), kind)
        meaningful = sum(not is_trivial(l) for l in mine)
        best = (0, 0, 0, 0, "-")
        for uf, ul in ups.items():
            sm, st, bl, bm = compare(mine, ul)
            if (sm, bm) > best[:2] or (sm == best[0] and bm == best[1] and sm and best[4] == "-"):
                best = (sm, bm, st, bl, uf)
        sm, bm, st, bl, uf = best
        rows.append((f, len(mine), meaningful, sm, st, bl, bm, sm / meaningful if meaningful else 0.0, uf))
        if bm >= a.threshold:
            flagged.append((f, uf, bm))
    rows.sort(key=lambda r: (-r[3], r[0]))
    L = [f"Upstream: `{a.upstream}` ({len(ups)} .py/.sh files); public files compared: {len(rows)}; files with at least one shared meaningful line: "
         f"{sum(r[3] > 0 for r in rows)}.", "",
         "| public file | lines | meaningful lines | shared meaningful | shared trivial | longest block (lines) | meaningful lines in it | ratio | best upstream match |",
         "|---|---|---|---|---|---|---|---|---|"]
    for f, n, mn, sm, st, bl, bm, ratio, uf in rows:
        if sm:
            L.append(f"| `{f}` | {n} | {mn} | {sm} | {st} | {bl} | {bm} | {ratio:.3f} | `{uf}` |")
    L += ["", f"Files with a longest block of at least {a.threshold} meaningful lines: " + (", ".join(f"`{f}` ↔ `{u}` ({b})" for f, u, b in flagged) if flagged else "none") + "."]
    out = "\n".join(L)
    if a.md:
        Path(a.md).write_text(out + "\n")
    print(out)
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
