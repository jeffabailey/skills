#!/usr/bin/env python3
"""Before/after check that a sanitize pass removed tells, not substance.

Usage: survival-check.py <before-file> <after-file> [--keep WORD ...]

Compares the original and edited file and lists anything that was lost:
front matter, profanity (voice), numbers, link targets, inline and fenced
code, <script> blocks, and element ids. Deleting a whole sentence on purpose
can legitimately drop a number or link; every LOST line needs either a fix or
a reason in the report. Exit 0 when nothing was lost, 1 otherwise.
"""
import re
import sys
from collections import Counter

VOICE = ["fuck", "fucking", "shit", "damn", "bitch", "son of a bitch", "asshole",
         "bastard", "crap", "piss", "dick", "hell", "masturbate"]


def front_matter(s):
    m = re.match(r"\A(---|\+\+\+)\n.*?\n\1\n", s, re.S)
    return m.group(0) if m else None


def words(s, w):
    return len(re.findall(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", s, re.I))


def visible_text(s):
    """Text a reader sees: drop styles, scripts, tags, and code so CSS values do not count as facts."""
    s = re.sub(r"<(style|script)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"^```.*?^```", " ", s, flags=re.S | re.M)
    s = re.sub(REF_DEF, " ", s, flags=re.M)
    s = re.sub(r"\]\[[^\]]*\]", "]", s)
    return re.sub(r"\]\([^)]*\)", "]", s)


REF_DEF = r"^ {0,3}\[[^\]\n]+\]:[ \t]*(\S.*)$"
SHORTCODE = r"\{\{[<%]\s*(?:rel)?ref\s+\"?([^\"\s>%}]+)\"?\s*[>%]\}\}"


def link_targets(s):
    """Resolved link targets, independent of style: inline, reference definition, ref shortcode, href/src."""
    targets = set(re.findall(SHORTCODE, s))
    s = re.sub(SHORTCODE, " ", s)
    raw = re.findall(r"\]\(\s*<?([^)\s>]+)", s)
    raw += [d.split()[0].strip("<>") for d in re.findall(REF_DEF, s, re.M) if d.split()]
    raw += re.findall(r"(?:href|src)=[\"']([^\"']+)", s)
    return Counter({t for t in targets.union(raw) if t})


def extract(s):
    return {
        "numbers in text": Counter(re.findall(r"(?<![\w#])\d[\d,.:%]*\d|(?<![\w#])\d", visible_text(s))),
        "links": link_targets(s),
        "code spans": Counter(re.findall(r"`([^`\n]+)`", s)),
        "fenced code": Counter(re.findall(r"^```.*?^```", s, re.S | re.M)),
        "script blocks": Counter(re.findall(r"<script\b.*?</script>", s, re.S | re.I)),
        "element ids": Counter(re.findall(r"\bid=[\"']([^\"']+)", s)),
    }


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    before, after = (open(p, encoding="utf-8").read() for p in argv[1:3])
    keep = VOICE + [a for i, a in enumerate(argv) if i > 0 and argv[i - 1] == "--keep"]
    lost = []

    if front_matter(before) != front_matter(after):
        lost.append("front matter: changed")
    for w in dict.fromkeys(keep):
        b, a = words(before, w), words(after, w)
        if a < b:
            lost.append(f"voice: '{w}' {b} -> {a}")
    eb, ea = extract(before), extract(after)
    for kind in eb:
        for item, n in (eb[kind] - ea[kind]).items():
            short = item if len(item) < 70 else item[:67] + "..."
            lost.append(f"{kind}: {short!r} x{n}")

    dashes = after.count("—")
    print(f"emdashes after: {dashes}")
    if lost:
        print("LOST (fix, or give the reason in the report):")
        for line in lost:
            print("  " + line)
        return 1
    print("survival: ok (front matter, voice, numbers, links, code, scripts, ids)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
