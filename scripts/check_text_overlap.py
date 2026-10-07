#!/usr/bin/env python
"""Longest run of identical words between the documents of this repository and source texts saved in a directory (*.txt).

    env -u PYTHONPATH python scripts/check_text_overlap.py SOURCE_DIR [--min 8] [--flag 15] DOC [DOC ...]

Words are lower-cased and stripped of punctuation. For every (document, source text) pair the longest common word run is printed when it is
at least --min words; runs of at least --flag words are marked FLAG. Also lists quoted spans ("...") of --flag or more words in the documents.
The source texts are not part of the repository (they are fetched web pages, abstracts and READMEs saved for this check).
"""
import argparse
import difflib
import re
import sys
from pathlib import Path


def words(t):
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", t.lower())


def longest(a, b):
    m = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return m.size, a[m.a:m.a + m.size]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source_dir")
    ap.add_argument("docs", nargs="+")
    ap.add_argument("--min", type=int, default=8)
    ap.add_argument("--flag", type=int, default=15)
    a = ap.parse_args()
    srcs = {p.name: words(p.read_text(errors="replace")) for p in sorted(Path(a.source_dir).glob("*.txt")) if p.stat().st_size}
    n_flag = 0
    print(f"{len(srcs)} source texts")
    for d in a.docs:
        text = Path(d).read_text()
        dw = words(text)
        for name, sw in srcs.items():
            if not set(dw) & set(sw):
                continue
            n, run = longest(dw, sw)
            if n >= a.min:
                flag = n >= a.flag
                n_flag += flag
                print(f"{'FLAG' if flag else 'note'} {d} vs {name}: {n} words: {' '.join(run)}")
        for q in re.findall(r"\"([^\"\n]{20,})\"|“([^”\n]{20,})”", text):
            q = q[0] or q[1]
            if len(words(q)) >= a.flag:
                n_flag += 1
                print(f"FLAG quoted span of {len(words(q))} words in {d}: {q[:100]}…")
    print(f"flagged: {n_flag}")
    return 1 if n_flag else 0


if __name__ == "__main__":
    sys.exit(main())
