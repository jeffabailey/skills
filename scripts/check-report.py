#!/usr/bin/env python3
"""Check the facts of a domain review report before it ships.

check-report.py <report.md> [--repo <root>] [--min-confidence N] [--all]

Prints one FAIL line per broken fact, then every Location citation with the first
100 characters of the cited line, so each claim can be confirmed from one output.

Checked: each finding has Severity, Confidence (>= --min-confidence, default 7) and
Location; each cited path is repo-relative and exists; each line number is inside
the file; the stated overall equals the mean of the scored dimensions in the scores
table, capped at 4.0 when a finding is CRITICAL; a Config: line sits in the first
10 lines. `path:line` text outside Location lines is checked for line range only
when the path resolves. Commit citations are not checked here.

--repo defaults to the git root above the report, else the current directory.
Secret-looking values in cited lines print as <redacted>. Exit 0 clean, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
FINDING = re.compile(r"^Finding\s+(\d+)\b", re.IGNORECASE)
FIELD = re.compile(r"^\s*[-*]?\s*\*\*(Severity|Confidence|Location):?\*\*:?\s*(.*)$", re.IGNORECASE)
NUMBER = re.compile(r"(\d+(?:\.\d+)?)")
SCORE = re.compile(r"(\d+(?:\.\d+)?)\s*/\s*10")
CITATION = re.compile(r"(?<![\w./@~+-])([\w.@~+/-]*[\w/])(?::|#L)(\d+)(?:\s*[-–]\s*(\d+))?")
MORE_LINES = re.compile(r"\s*,\s*:?(\d+)(?:\s*[-–]\s*(\d+))?(?![\w./:])")
LATER_LINES = re.compile(r"(?<![\w./:]):(\d+)(?:\s*[-–]\s*(\d+))?")
BARE_PATH = re.compile(r"^[\w.@~+/-]+$")
ABSENT = re.compile(r"\b(absent|none|missing|not found|no )", re.IGNORECASE)
OVERALL_LINE = re.compile(r"^\W*Overall\b[^|\n]*?(?:(\d+(?:\.\d+)?)\s*/\s*10|=\s*(\d+(?:\.\d+)?)(?![\d/]))", re.IGNORECASE)
SECRET_ASSIGN = re.compile(
    r"((?:api[_-]?key|secret|token|passw(?:or)?d|pwd|credential|private[_-]?key)\w*[\"']?\s*[:=]\s*)"
    r"([\"'][^\"']{4,}[\"']|[A-Za-z0-9+/_=-]{6,}(?![\w.(\[]))",
    re.IGNORECASE,
)
SECRET_TOKEN = re.compile(r"\b(?:AKIA|ASIA|ghp_|gho_|github_pat_|sk-|xox[abpr]-|glpat-)[\w-]{8,}|-----BEGIN[^-]*-----")
LONG_TOKEN = re.compile(r"[A-Za-z0-9+=_-]{40,}")
SKIP_DIRECTORIES = {".git", ".venv", "venv", "node_modules", "__pycache__", "target", "dist", "build"}
CITATION_CAP = 60
CRITICAL_CAP = 4.0


def find_repo(report: Path) -> Path:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(report.parent), "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
        )
        return Path(out.strip())
    except (subprocess.CalledProcessError, OSError):
        return Path.cwd()


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Report lines outside fenced code blocks, with their 1-based numbers."""
    lines, fenced = [], False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            lines.append((number, line))
    return lines


def parse_findings(lines: list[tuple[int, str]]) -> list[dict]:
    findings, current = [], None
    for _, line in lines:
        heading = HEADING.match(line)
        if heading:
            match = FINDING.match(heading.group(2).strip("* "))
            current = {"number": int(match.group(1))} if match else None
            if current:
                findings.append(current)
            continue
        field = FIELD.match(line) if current else None
        if field:
            current.setdefault(field.group(1).lower(), field.group(2).strip())
    return findings


def parse_scores(lines: list[tuple[int, str]]) -> tuple[bool, dict[str, float], list[str], list[float]]:
    """Return (table found, scored dimensions, unreadable rows, stated overalls)."""
    scores: dict[str, float] = {}
    unreadable: list[str] = []
    overalls: list[float] = []
    found = in_table = False
    for _, line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")] if line.lstrip().startswith("|") else []
        if not cells:
            in_table = False
            match = OVERALL_LINE.match(line)
            if match:
                overalls.append(float(match.group(1) or match.group(2)))
            continue
        if not found and len(cells) >= 2 and cells[0].lower() == "dimension" and cells[1].lower() == "score":
            found = in_table = True
            continue
        if not in_table or len(cells) < 2 or set(cells[0]) <= set("-: "):
            continue
        name, cell = cells[0].strip("* "), cells[1].strip("* ")
        score = SCORE.search(cell)
        if name.lower().startswith("overall"):
            if score:
                overalls.append(float(score.group(1)))
        elif cell.upper().startswith("N/A"):
            continue
        elif score:
            scores[name] = float(score.group(1))
        else:
            unreadable.append(name)
    return found, scores, unreadable, overalls


def location_citations(location: str) -> tuple[list[tuple[str, int, int]], list[tuple[str, bool]]]:
    """Split a Location value into (path, first, last) citations and bare (path, claimed absent)."""
    cited, bare = [], []
    for segment in location.replace("`", "").split(";"):
        segment = segment.strip()
        if segment.lower().startswith(("commit ", "git ")):
            continue
        position, hit = 0, False
        while True:
            match = CITATION.search(segment, position)
            if not match:
                break
            hit = True
            path = match.group(1)
            cited.append((path, int(match.group(2)), int(match.group(3) or match.group(2))))
            position = match.end()
            while True:
                more = MORE_LINES.match(segment, position)
                if not more:
                    break
                cited.append((path, int(more.group(1)), int(more.group(2) or more.group(1))))
                position = more.end()
            following = CITATION.search(segment, position)
            for later in LATER_LINES.finditer(segment, position, following.start() if following else len(segment)):
                cited.append((path, int(later.group(1)), int(later.group(2) or later.group(1))))
        first = segment.split()[0].rstrip(",.") if segment.split() else ""
        if not hit and BARE_PATH.match(first) and ("/" in first or re.search(r"\.[A-Za-z]\w*$", first)):
            bare.append((first, bool(ABSENT.search(segment[len(first):]))))
    return cited, bare


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._names: list[str] | None = None
        self._lines: dict[str, list[str] | None] = {}

    def names(self) -> list[str]:
        if self._names is None:
            try:
                out = subprocess.check_output(
                    ["git", "-C", str(self.root), "ls-files", "-z", "-co", "--exclude-standard"],
                    text=True, stderr=subprocess.DEVNULL,
                )
                self._names = [name for name in out.split("\0") if name]
            except (subprocess.CalledProcessError, OSError):
                self._names = []
                for current, dirs, files in os.walk(self.root):
                    dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORIES]
                    self._names.extend(str((Path(current) / name).relative_to(self.root)) for name in files)
        return self._names

    def suggest(self, path: str) -> str:
        matches = sorted(name for name in self.names() if name == path or name.endswith("/" + path.lstrip("./")))
        return f" (did you mean {matches[0]}?)" if len(matches) == 1 else ""

    def lines(self, path: str) -> list[str] | None:
        if path not in self._lines:
            target = self.root / path
            try:
                self._lines[path] = target.read_text(encoding="utf-8", errors="replace").splitlines() if target.is_file() else None
            except OSError:
                self._lines[path] = None
        return self._lines[path]

    def check(self, path: str, first: int, last: int) -> str | None:
        """Return a failure message for a path:line citation, or None."""
        if os.path.isabs(path) or path.startswith("~"):
            return "not repo-relative"
        if not (self.root / path).exists():
            return "missing path" + self.suggest(path)
        lines = self.lines(path)
        if lines is None:
            return "not a readable file"
        if first < 1 or last < first:
            return f"bad line range {first}-{last}"
        if last > len(lines):
            return f"line {last} > {len(lines)} lines"
        return None


def mixed(token: str) -> bool:
    """True for a long token with upper, lower, and digit characters (not a hex commit id)."""
    return any(c.isupper() for c in token) and any(c.islower() for c in token) and any(c.isdigit() for c in token)


def redact(line: str) -> str:
    line = SECRET_ASSIGN.sub(lambda match: match.group(1) + "<redacted>", line.strip())
    line = SECRET_TOKEN.sub("<redacted>", line)
    return LONG_TOKEN.sub(lambda match: "<redacted>" if mixed(match.group(0)) else match.group(0), line)[:100]


def check(report: Path, root: Path, min_confidence: float, show_all: bool) -> tuple[list[str], list[str]]:
    text = report.read_text(encoding="utf-8", errors="replace")
    lines = prose_lines(text)
    repo = Repo(root)
    failures: list[str] = []
    rows: list[str] = []
    seen: set[tuple[str, int, int]] = set()

    if not any(re.match(r"\**Config\b[^:]*:", line) for line in text.splitlines()[:10]):
        failures.append("no Config: line in the first 10 lines")

    findings = parse_findings(lines)
    for finding in findings:
        label = f"finding {finding['number']}"
        if "severity" not in finding:
            failures.append(f"{label}: no severity")
        confidence = NUMBER.search(finding.get("confidence", ""))
        if not confidence:
            failures.append(f"{label}: no confidence")
        elif float(confidence.group(1)) < min_confidence:
            failures.append(f"{label}: confidence {confidence.group(1)} < {min_confidence:g}")
        if not finding.get("location"):
            failures.append(f"{label}: no location")
            continue
        cited, bare = location_citations(finding["location"])
        for path, first, last in cited:
            where = f"{path}:{first}" + (f"-{last}" if last != first else "")
            problem = repo.check(path, first, last)
            if problem:
                failures.append(f"{label}: {where}: {problem}")
            elif (path, first, last) not in seen:
                rows.append(f"F{finding['number']} {where} | {redact(repo.lines(path)[first - 1])}")
            seen.add((path, first, last))
        for path, claimed_absent in bare:
            exists = (root / path).exists()
            if os.path.isabs(path) or path.startswith("~"):
                failures.append(f"{label}: {path}: not repo-relative")
            elif claimed_absent:
                rows.append(f"F{finding['number']} {path} | ({'exists' if exists else 'absent'}; cited as an absence)")
            elif not exists:
                failures.append(f"{label}: {path}: missing path{repo.suggest(path)}")
            else:
                rows.append(f"F{finding['number']} {path} | (exists; no line cited)")

    for number, line in lines:
        if FIELD.match(line):
            continue
        for match in CITATION.finditer(line.replace("`", "")):
            path, first, last = match.group(1), int(match.group(2)), int(match.group(3) or match.group(2))
            if not re.search(r"\.[A-Za-z]\w*$", path) or (path, first, last) in seen or repo.lines(path) is None:
                continue
            seen.add((path, first, last))
            problem = repo.check(path, first, last)
            if problem:
                failures.append(f"report line {number}: {path}:{first}: {problem}")

    found, scores, unreadable, overalls = parse_scores(lines)
    critical = any(finding.get("severity", "").upper().startswith("CRITICAL") for finding in findings)
    failures.extend(f"scores table: no score in row \"{name}\"" for name in unreadable)
    if not found:
        failures.append("no scores table (header: | Dimension | Score |)")
    elif scores:
        mean = sum(scores.values()) / len(scores)
        expected = min(mean, CRITICAL_CAP) if critical else mean
        basis = f"mean {mean:.2f} of {len(scores)} scored dimensions" + (", CRITICAL cap 4.0" if critical else "")
        if not overalls:
            failures.append(f"no overall score stated (expected {expected:.1f}: {basis})")
        for stated in overalls:
            if abs(stated - expected) > 0.05 + 1e-9:
                failures.append(f"overall {stated:g} != {expected:.1f} ({basis})")
        rows.insert(0, f"overall: {basis}")
    else:
        rows.insert(0, "overall: no scored dimensions, nothing to average")

    if not show_all and len(rows) > CITATION_CAP + 1:
        rows = rows[: CITATION_CAP + 1] + [f"+{len(rows) - CITATION_CAP - 1} more citations (--all)"]
    return failures, [f"findings: {len(findings)}"] + rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report", type=Path)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--min-confidence", type=float, default=7)
    parser.add_argument("--all", action="store_true", help="do not cap the citation list")
    args = parser.parse_args()
    if not args.report.is_file():
        print(f"error: report not found: {args.report}", file=sys.stderr)
        return 1
    root = (args.repo or find_repo(args.report.resolve())).resolve()
    if not root.is_dir():
        print(f"error: repo root not found: {root}", file=sys.stderr)
        return 1
    failures, rows = check(args.report, root, args.min_confidence, args.all)
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"check-report: {len(failures)} failure(s)")
    print("\n".join(rows))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
