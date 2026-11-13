#!/usr/bin/env python3
"""Run every Detect hint from the references over the targets, in one call.

Usage: scan-tells.py <target...> [--before ORIGINAL] [--medium prose|ui|graphics] [--all]

Targets are files, directories (walked for known file types), or - for pasted
text on stdin (prose). The patterns come from the **Detect:** lines of
references/prose.md, ui.md, and graphics.md; this script holds no list of its
own. The file type picks the medium: prose files get the prose rules, UI files
the UI and prose rules, .svg the graphics rules. --medium forces one.

Prints `file:line  rule  "match"` for each candidate (30, or all with --all),
then hits per rule (* = the reference marks it high signal), hits per section
(Markdown heading, or the whole file for code), and whether any section holds
3 or more hits. A hit is a candidate, not a finding.

--before ORIGINAL (one target file) also prints which hits are gone and which
are new, or "unchanged" when the two files are the same.

Only the code spans between `**Detect:**` and `**By reading:**` are patterns.
A span is a regex when it is a grep command, holds a backslash, starts with ^,
or has an (a|b) group; otherwise it is literal text, with | for alternatives
and * as a wildcard. Hints after `**By reading:**`, `**Detect by reading:**`
lines, and Detect lines with no code span need a read; they are counted as
skipped. Exit 0 after a scan, 2 on a usage or file error.
"""
import argparse
import os
import re
import sys
from collections import Counter

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references")
MEDIA = {
    "prose": {".md", ".mdx", ".markdown", ".txt", ".rst"},
    "ui": {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts",
           ".tsx", ".vue", ".svelte", ".astro"},
    "graphics": {".svg"},
}
RULESETS = {"prose": ("prose",), "ui": ("ui", "prose"), "graphics": ("graphics",)}
SKIP_DIRS = {"node_modules", "dist", "build", "vendor", "__pycache__"}
SPAN = re.compile(r"`([^`]+)`")
GREP = re.compile(r'^grep\s+-(\w+)\s+"(.*)"$')
HEADING = re.compile(r"^#{2,3}\s+(\d+)\.\s+(.*)$")
CAP = 30


def die(msg):
    print(f"scan-tells: {msg}", file=sys.stderr)
    sys.exit(2)


def from_grep(flags, pattern):
    pattern = re.sub(r"\\x\{([0-9A-Fa-f]+)\}", lambda m: "\\U%08x" % int(m.group(1), 16), pattern)
    pattern = pattern.replace("[[:space:]]", r"\s")
    return re.compile(pattern, re.I if "i" in flags else 0)


def literal(text):
    text = text.strip()
    out = re.escape(text).replace(r"\*", r"[\w.\[\]-]*")
    out = re.sub(r"(\\ )+", lambda _: r"\s*", out)
    if re.match(r"\w", text):
        out = r"(?<![\w-])" + out
    if re.search(r"\w$", text):
        out += r"(?!\w)"
    return out


def to_regex(span):
    """Compile one code span of a Detect line."""
    grep = GREP.match(span.strip())
    if grep:
        return from_grep(*grep.groups())
    core = span.strip()
    if "\\" in core or core.startswith("^") or re.search(r"\([^)]*\|[^)]*\)", core):
        return re.compile(core)
    return re.compile("|".join(literal(part) for part in core.split("|")))


def load_rules(refs=REFS):
    """Return ({medium: [(rule_id, high_signal, regex)]}, detect_lines, skipped)."""
    rules, lines, skipped = {}, 0, 0
    for medium in ("prose", "ui", "graphics"):
        path = os.path.join(refs, medium + ".md")
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            die(f"cannot read {path}")
        rules[medium] = []
        number, high = "0", False
        for line in text.splitlines():
            head = HEADING.match(line)
            if head:
                number, high = head.group(1), "high signal" in head.group(2)
                continue
            if not line.startswith(("**Detect:**", "**Detect by reading:**")):
                continue
            lines += 1
            scan_part, _, read_part = line.partition("**By reading:**")
            if line.startswith("**Detect by reading:**"):
                scan_part, read_part = "", line
            spans = SPAN.findall(scan_part)
            skipped += len(SPAN.findall(read_part)) or (0 if spans else 1)
            for span in spans:
                try:
                    rules[medium].append((f"{medium}-{number}", high, to_regex(span)))
                except re.error:
                    skipped += 1
    return rules, lines, skipped


def medium_of(path):
    ext = os.path.splitext(path)[1].lower()
    return next((m for m, exts in MEDIA.items() if ext in exts), None)


def collect(targets, forced):
    files = []
    for target in targets:
        if target == "-":
            files.append(("-", forced or "prose"))
        elif os.path.isdir(target):
            for root, dirs, names in os.walk(target):
                dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
                files += [(os.path.join(root, n), forced or medium_of(n))
                          for n in sorted(names) if medium_of(n)]
        elif os.path.isfile(target):
            medium = forced or medium_of(target)
            if not medium:
                die(f"cannot pick a medium for {target}; pass --medium prose|ui|graphics")
            files.append((target, medium))
        else:
            die(f"no such file or directory: {target}")
    return sorted(set(files))


def read(path):
    if path == "-":
        return sys.stdin.read()
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError as exc:
        die(f"cannot read {path}: {exc.strerror}")


def scan(path, medium, text, rules):
    """Return sorted hits: (path, line, rule_id, match, section)."""
    hits, section, fenced = set(), "(top)" if medium == "prose" else "(file)", False
    active = [r for ref in RULESETS[medium] for r in rules[ref]]
    for number, line in enumerate(text.splitlines(), 1):
        if medium == "prose":
            if re.match(r"\s*(```|~~~)", line):
                fenced = not fenced
                continue
            if fenced:
                continue
            head = re.match(r"#{1,6}\s+(.*)", line)
            if head:
                section = head.group(1).strip()[:40]
        for rule_id, _, regex in active:
            for m in regex.finditer(line):
                if m.group(0):
                    hits.add((path, number, rule_id, " ".join(m.group(0).split())[:40], section))
    return sorted(hits)


def order(rule_id):
    medium, number = rule_id.rsplit("-", 1)
    return medium, int(number)


def diff(before, after):
    old = Counter((h[2], h[3].lower()) for h in before)
    new = Counter((h[2], h[3].lower()) for h in after)
    for label, delta in (("gone", old - new), ("new", new - old)):
        items = sorted(delta.items(), key=lambda kv: (order(kv[0][0]), kv[0][1]))
        shown = ", ".join(f'{rule} "{text}" x{n}' for (rule, text), n in items[:CAP])
        more = f", +{len(items) - CAP} more" if len(items) > CAP else ""
        print(f"{label} ({sum(delta.values())}): {shown or 'none'}{more}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], usage=__doc__.split("\n\n")[1])
    parser.add_argument("targets", nargs="+")
    parser.add_argument("--before")
    parser.add_argument("--medium", choices=sorted(MEDIA))
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)

    rules, detect_lines, skipped = load_rules()
    files = collect(args.targets, args.medium)
    if args.before and (len(files) != 1 or not os.path.isfile(args.before)):
        die("--before needs one target file and an existing original file")
    high = {rule_id for group in rules.values() for rule_id, flag, _ in group if flag}
    texts = {path: read(path) for path, _ in files}
    hits = [h for path, medium in files for h in scan(path, medium, texts[path], rules)]

    patterns = sum(len(group) for group in rules.values())
    print(f"scanned {len(files)} file(s): {len(hits)} candidate hit(s); {patterns} patterns from "
          f"{detect_lines} Detect lines, {skipped} hints skipped (need a read)")
    for path, line, rule_id, text, _ in hits if args.all else hits[:CAP]:
        print(f'{path}:{line}  {rule_id}  "{text}"')
    if len(hits) > CAP and not args.all:
        print(f"... {len(hits) - CAP} more (--all)")

    by_rule = Counter(h[2] for h in hits)
    by_section = Counter((path, section) for path, _, _, section in
                         {(h[0], h[1], h[3].lower(), h[4]) for h in hits})
    if hits:
        print("by rule: " + ", ".join(
            f"{r}{'*' if r in high else ''} {by_rule[r]}" for r in sorted(by_rule, key=order)))
        top = sorted(by_section.items(), key=lambda kv: (-kv[1], kv[0]))
        limit = len(top) if args.all else 8
        print("by section (distinct matches): " + "; ".join(f"{p}#{s} {n}" for (p, s), n in top[:limit])
              + (f"; +{len(top) - limit} more" if len(top) > limit else ""))
    clusters = sum(1 for n in by_section.values() if n >= 3)
    print(f"3+ hits in one section: {'yes (' + str(clusters) + ' section(s))' if clusters else 'no'}")

    if args.before:
        path, medium = files[0]
        original = read(args.before)
        if original == texts[path]:
            print(f"unchanged: {path} is identical to {args.before}")
        else:
            diff(scan(args.before, medium, original, rules), hits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
