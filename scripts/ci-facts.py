#!/usr/bin/env python3
"""Print CI and container facts for a review target, as counts and file:line.

Usage:
    python3 ci-facts.py TARGET [--no-scanners] [--all] [--timeout SECONDS]

TARGET is a repository, a directory such as .github, or one file.

Workflows (.github/workflows/*.yml): per job, a missing timeout-minutes and
missing or write permissions; per file, missing concurrency; every uses: ref
and whether it is pinned to a 40-character SHA; pull_request_target and
workflow_run triggers; github.event.* and github.head_ref inside run: or
script:; actions/checkout without persist-credentials: false.
Dockerfiles: the last USER, unpinned FROM images, secret-like ENV/ARG names.
Compose files: per service, image pin, healthcheck, restart, and limits.
Scanners: runs the ones on PATH (gitleaks with --redact; zizmor, else
actionlint; osv-scanner, else pip-audit; npm audit when a lock file exists)
and prints rule and file:line. It installs nothing and prints no values.

The YAML and Dockerfile readers are line patterns, not parsers: the rows are
approximate, so open the cited line before a row becomes a finding.

Lists stop at 15 rows; --all prints every row. --no-scanners skips scanners.
Exit 0 with facts (also when nothing is found), 2 for a bad target.
Works on Windows, macOS, and Linux. Requires Python 3.10+. Standard library only.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CAP = 15
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", "vendor",
    "dist", "build", "target", ".tox", ".mypy_cache", ".pytest_cache",
}
SHA = re.compile(r"^[0-9a-f]{40}$")
KEY = re.compile(r"""^(\s*)(-\s+)?["']?([\w.-]+)["']?:(?:\s+(.*))?$""")
BLOCK = re.compile(r"^[|>][+-]?\d*[+-]?\s*(#.*)?$")
USES = re.compile(r"""^\s*(?:-\s+)?uses:\s*["']?([^\s"'#]+)""")
EXPR = re.compile(r"\$\{\{[^}]*?\b(github\.event\.[\w.\-\[\]'*]+|github\.head_ref)")
TRIGGER = re.compile(r"\b(pull_request_target|workflow_run)\b")
WRITE = re.compile(r"([\w-]+):\s*write\b")
SECRET_NAME = re.compile(
    r"(?i)(secret|token|passw|pwd|api_?key|private_?key|credential|auth)"
)
FIRST_PARTY = {"actions", "github"}
CI_DIRS = {".github", ".forgejo", ".gitea"}


# ---------- discovery ----------

def repo_root(start: Path) -> Path:
    """Nearest ancestor holding .git, so rows read as repository paths."""
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            return parent
    return start


def classify(path: Path) -> str | None:
    name = path.name
    lower = name.lower()
    if lower.endswith((".yml", ".yaml")):
        if re.match(r"^(docker-)?compose([.-][\w.-]*)?\.ya?ml$", lower):
            return "compose"
        if path.parent.name == "workflows" and path.parent.parent.name in CI_DIRS:
            return "workflow"
        return None
    if lower.startswith(("dockerfile", "containerfile")) or lower.endswith(
        (".dockerfile", ".containerfile")
    ):
        return "dockerfile"
    if re.match(r"^requirements[\w.-]*\.txt$", lower):
        return "requirements"
    return None


def discover(target: Path) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {
        "workflow": [], "dockerfile": [], "compose": [], "requirements": [],
    }
    if target.is_file():
        kind = classify(target)
        if kind is None and target.suffix.lower() in (".yml", ".yaml"):
            kind = "workflow"
        if kind:
            found[kind].append(target)
        return found
    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            path = Path(dirpath) / name
            kind = classify(path)
            if kind:
                found[kind].append(path)
    return found


def read_lines(path: Path) -> list[str] | None:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None


# ---------- YAML line reader ----------

def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def yaml_rows(lines: list[str]) -> list[tuple[int, int, str, str | None]]:
    """(line number, indent, text, block key) for each meaningful line.

    Block key is the key that owns a `|` or `>` scalar the line sits inside,
    so shell text is never read as YAML structure.
    """
    rows = []
    block_key, block_col = None, -1
    for number, raw in enumerate(lines, 1):
        text = raw.rstrip()
        if not text.strip():
            continue
        indent = indent_of(text)
        if block_key is not None:
            if indent > block_col:
                rows.append((number, indent, text, block_key))
                continue
            block_key = None
        if text.lstrip().startswith("#"):
            continue
        rows.append((number, indent, text, None))
        match = KEY.match(text)
        if match and match.group(4) and BLOCK.match(match.group(4)):
            block_key = match.group(3)
            block_col = indent + len(match.group(2) or "")
    return rows


def permission_writes(value: str | None, children: list[str]) -> list[str]:
    if value and value.strip().startswith("write-all"):
        return ["write-all"]
    return sorted(set(WRITE.findall(" ".join([value or "", *children]))))


def classify_uses(ref: str) -> str:
    if ref.startswith("./"):
        return "local"
    if ref.startswith("docker://"):
        return "pinned" if "@sha256:" in ref else "unpinned third-party"
    name, _, version = ref.partition("@")
    if SHA.match(version):
        return "pinned"
    owner = name.split("/")[0]
    return "unpinned first-party" if owner in FIRST_PARTY else "unpinned third-party"


def parse_workflow(lines: list[str]) -> dict:
    rows = yaml_rows(lines)
    facts = {
        "jobs": [], "uses": [], "triggers": [], "expressions": [],
        "checkouts": [], "permissions": None, "concurrency": False,
        "has_jobs": False,
    }
    section = None
    job = None
    job_indent = prop_indent = None
    perm_owner, perm_indent = None, -1

    for index, (number, indent, text, block_key) in enumerate(rows):
        if block_key is not None:
            if block_key in ("run", "script"):
                for name in sorted(set(EXPR.findall(text))):
                    facts["expressions"].append((number, name))
            continue
        match = KEY.match(text)
        key = match.group(3) if match else None
        value = (match.group(4) or "") if match else ""

        if perm_owner is not None:
            if indent > perm_indent:
                perm_owner["children"].append(text)
                continue
            perm_owner = None

        if indent == 0 and match:
            section = "on" if key in ("on", "true") else key
            job = None
            if section == "on":
                for name in sorted(set(TRIGGER.findall(value))):
                    facts["triggers"].append((number, name))
            elif section == "permissions":
                facts["permissions"] = {"line": number, "value": value, "children": []}
                perm_owner, perm_indent = facts["permissions"], 0
            elif section == "concurrency":
                facts["concurrency"] = True
            elif section == "jobs":
                facts["has_jobs"] = True
                job_indent = None
            continue

        if section == "on":
            name = TRIGGER.match(text.strip().lstrip("- ").strip("'\""))
            if name:
                facts["triggers"].append((number, name.group(1)))
            continue
        if section != "jobs":
            continue

        if job_indent is None:
            job_indent = indent
        if indent == job_indent and match and not match.group(2):
            job = {
                "name": key, "line": number, "timeout": False, "reusable": False,
                "permissions": None, "concurrency": False,
            }
            facts["jobs"].append(job)
            prop_indent = None
            continue
        if job is None:
            continue
        if prop_indent is None:
            prop_indent = indent
        if indent == prop_indent and match and not match.group(2):
            if key == "timeout-minutes":
                job["timeout"] = True
            elif key == "concurrency":
                job["concurrency"] = True
            elif key == "uses":
                job["reusable"] = True
            elif key == "permissions":
                job["permissions"] = {"line": number, "value": value, "children": []}
                perm_owner, perm_indent = job["permissions"], indent

        if key in ("run", "script") and value and not BLOCK.match(value):
            for name in sorted(set(EXPR.findall(value))):
                facts["expressions"].append((number, name))

        used = USES.match(text)
        if used:
            ref = used.group(1)
            facts["uses"].append((number, ref, classify_uses(ref)))
            if ref.split("@")[0].lower() == "actions/checkout":
                column = text.index("uses:")
                facts["checkouts"].append(
                    (number, step_has_persist_false(rows, index, column))
                )
    return facts


def step_has_persist_false(rows: list, index: int, column: int) -> bool:
    """Look through the step around rows[index] for persist-credentials: false."""
    pattern = re.compile(r"persist-credentials:\s*['\"]?false")
    for step in (range(index + 1, len(rows)), range(index - 1, -1, -1)):
        for position in step:
            _, indent, text, _ = rows[position]
            if indent < column:
                break
            if pattern.search(text):
                return True
    return False


# ---------- Dockerfile and compose readers ----------

def parse_dockerfile(lines: list[str]) -> dict:
    facts = {"user": None, "user_line": 0, "unpinned": [], "secrets": [], "stages": 0}
    stages: set[str] = set()
    joined: list[tuple[int, str]] = []
    pending, start = "", 0
    for number, raw in enumerate(lines, 1):
        text = raw.strip()
        if not pending and (not text or text.startswith("#")):
            continue
        if not pending:
            start = number
        if text.endswith("\\"):
            pending += text[:-1] + " "
            continue
        joined.append((start, pending + text))
        pending = ""
    if pending:
        joined.append((start, pending))

    for number, text in joined:
        parts = text.split()
        if not parts:
            continue
        word = parts[0].upper()
        args = [part for part in parts[1:] if not part.startswith("--")]
        if word == "FROM" and args:
            facts["stages"] += 1
            facts["user"], facts["user_line"] = None, 0
            image = args[0]
            if len(args) >= 3 and args[1].upper() == "AS":
                stages.add(args[2].lower())
            if image.lower() in stages or image.lower() == "scratch":
                continue
            pin = image_pin(image)
            if pin == "unpinned":
                facts["unpinned"].append((number, image))
        elif word == "USER" and args:
            facts["user"], facts["user_line"] = args[0], number
        elif word in ("ENV", "ARG") and args:
            pairs = args if "=" in args[0] or word == "ARG" else [" ".join(args)]
            for pair in pairs:
                name, has_value, value = pair.replace(" ", "=", 1).partition("=")
                if not SECRET_NAME.search(name):
                    continue
                literal = bool(has_value and value.strip("\"'") and "$" not in value)
                facts["secrets"].append((number, word, name, literal))
    return facts


def image_pin(image: str) -> str:
    image = image.strip("\"'")
    if "@sha256:" in image:
        return "digest"
    if "$" in image:
        return "variable"
    tag = image.rsplit("/", 1)[-1].partition(":")[2]
    return "tag" if tag and tag != "latest" else "unpinned"


def parse_compose(lines: list[str]) -> list[dict] | None:
    rows = yaml_rows(lines)
    services: list[dict] = []
    in_services = seen = False
    service = None
    name_indent = prop_indent = None
    for number, indent, text, block_key in rows:
        if block_key is not None:
            continue
        match = KEY.match(text)
        if indent == 0:
            in_services = bool(match and match.group(3) == "services")
            seen = seen or in_services
            service, name_indent = None, None
            continue
        if not in_services or not match:
            continue
        key, value = match.group(3), (match.group(4) or "")
        if name_indent is None:
            name_indent = indent
        if indent == name_indent and not match.group(2):
            service = {
                "name": key, "line": number, "image": None, "pin": "none",
                "healthcheck": False, "restart": None, "limits": False,
            }
            services.append(service)
            prop_indent = None
            continue
        if service is None:
            continue
        if prop_indent is None:
            prop_indent = indent
        if indent == prop_indent:
            if key == "image":
                service["image"] = value.split(" #")[0].strip().strip("\"'")
                service["pin"] = image_pin(service["image"])
            elif key == "build" and service["image"] is None:
                service["pin"] = "build"
            elif key == "healthcheck":
                service["healthcheck"] = True
            elif key == "restart":
                service["restart"] = value.split(" #")[0].strip().strip("\"'")
            elif key in ("mem_limit", "cpus", "pids_limit"):
                service["limits"] = True
        elif key == "limits":
            service["limits"] = True
        elif key == "restart_policy" and service["restart"] is None:
            service["restart"] = "deploy"
    return services if seen else None


# ---------- scanners ----------

def run(command: list[str], timeout: int, cwd: Path | None = None):
    try:
        done = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, cwd=cwd,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return "timeout"
    except OSError:
        return "failed"
    return done


def sarif_rows(text: str) -> list[tuple[str, int, str]] | None:
    """(file, line, rule) from SARIF; None when the text is not SARIF."""
    try:
        runs = json.loads(text)["runs"]
        rows = set()
        for item in runs:
            for result in item.get("results") or []:
                rule = str(result.get("ruleId", "?"))
                locations = result.get("locations") or [{}]
                physical = locations[0].get("physicalLocation", {})
                uri = physical.get("artifactLocation", {}).get("uri", "?")
                line = physical.get("region", {}).get("startLine", 0)
                rows.add((str(uri).removeprefix("file://"), int(line or 0), rule))
        return sorted(rows)
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def problem(done, timeout: int) -> str:
    if done == "timeout":
        return f"timed out after {timeout}s; run it by hand"
    if done == "failed":
        return "could not start"
    return f"output not parsed (exit {done.returncode}); run it by hand"


def scan_gitleaks(target: Path, timeout: int):
    source = target if target.is_dir() else target.parent
    with tempfile.TemporaryDirectory() as scratch:
        report = Path(scratch) / "gitleaks.sarif"
        command = [
            "gitleaks", "detect", "--no-banner", "--redact", "--exit-code", "0",
            "-s", str(source), "--report-format", "sarif", "--report-path", str(report),
        ]
        if not (repo_root(source.resolve()) / ".git").exists():
            command.append("--no-git")
        done = run(command, timeout)
        rows = None
        if not isinstance(done, str) and report.is_file():
            rows = sarif_rows(report.read_text(encoding="utf-8", errors="replace"))
    return rows if rows is not None else problem(done, timeout)


def scan_zizmor(files: list[Path], timeout: int):
    done = run(["zizmor", "--format", "sarif", *map(str, files)], timeout)
    rows = None if isinstance(done, str) else sarif_rows(done.stdout)
    return rows if rows is not None else problem(done, timeout)


def scan_actionlint(files: list[Path], timeout: int):
    done = run(["actionlint", "-format", "{{json .}}", *map(str, files)], timeout)
    if isinstance(done, str):
        return problem(done, timeout)
    try:
        return sorted(
            (str(item["filepath"]), int(item["line"]), str(item.get("kind", "?")))
            for item in json.loads(done.stdout or "[]")
        )
    except (ValueError, KeyError, TypeError):
        return problem(done, timeout)


def scan_osv(target: Path, timeout: int):
    done = run(["osv-scanner", "--format", "sarif", "-r", str(target)], timeout)
    rows = None if isinstance(done, str) else sarif_rows(done.stdout)
    return rows if rows is not None else problem(done, timeout)


def scan_pip_audit(files: list[Path], timeout: int):
    rows = set()
    for path in files[:3]:
        done = run(
            ["pip-audit", "-r", str(path), "-f", "json", "--progress-spinner", "off"],
            timeout,
        )
        if isinstance(done, str):
            return problem(done, timeout)
        try:
            data = json.loads(done.stdout)
            packages = data["dependencies"] if isinstance(data, dict) else data
            for package in packages:
                for vuln in package.get("vulns") or []:
                    label = f"{vuln['id']} {package['name']} {package.get('version', '?')}"
                    rows.add((str(path), 0, label))
        except (ValueError, KeyError, TypeError):
            return problem(done, timeout)
    return sorted(rows)


def scan_npm(target: Path, timeout: int):
    done = run(["npm", "audit", "--omit=dev", "--json"], timeout, cwd=target)
    if isinstance(done, str):
        return problem(done, timeout)
    try:
        counts = json.loads(done.stdout)["metadata"]["vulnerabilities"]
        levels = ("critical", "high", "moderate", "low")
        return "packages by severity: " + ", ".join(
            f"{level} {int(counts.get(level, 0))}" for level in levels
        )
    except (ValueError, KeyError, TypeError):
        return problem(done, timeout)


def plan_scanners(target: Path, found: dict) -> tuple[list, list[str], list[str]]:
    """(jobs to run, tools not installed, tools with nothing to scan)."""
    jobs, missing, idle = [], [], []
    have = {tool: shutil.which(tool) is not None for tool in (
        "gitleaks", "zizmor", "actionlint", "osv-scanner", "pip-audit", "npm",
    )}
    if have["gitleaks"]:
        jobs.append(("gitleaks", scan_gitleaks, target))
    else:
        missing.append("gitleaks")

    workflows = found["workflow"]
    linter = "zizmor" if have["zizmor"] else "actionlint" if have["actionlint"] else None
    if linter is None:
        missing.append("zizmor/actionlint")
    elif not workflows:
        idle.append(linter)
    else:
        scan = scan_zizmor if linter == "zizmor" else scan_actionlint
        jobs.append((linter, scan, workflows))

    if have["osv-scanner"]:
        jobs.append(("osv-scanner", scan_osv, target if target.is_dir() else target.parent))
    elif have["pip-audit"]:
        if found["requirements"]:
            jobs.append(("pip-audit", scan_pip_audit, found["requirements"]))
        else:
            idle.append("pip-audit")
    else:
        missing.append("osv-scanner/pip-audit")

    if target.is_dir() and (target / "package-lock.json").is_file():
        if have["npm"]:
            jobs.append(("npm audit", scan_npm, target))
        else:
            missing.append("npm")
    return jobs, missing, idle


# ---------- report ----------

class Report:
    def __init__(self, show_all: bool):
        self.lines: list[str] = []
        self.show_all = show_all

    def add(self, text: str) -> None:
        self.lines.append(text)

    def listing(self, title: str, rows: list[str]) -> None:
        self.add(f"{title}: {len(rows)}")
        shown = rows if self.show_all else rows[:CAP]
        for row in shown:
            self.add(f"  {row}")
        if len(rows) > len(shown):
            self.add(f"  ... and {len(rows) - len(shown)} more (--all)")


def report_workflows(report: Report, files: list[Path], rel) -> None:
    if not files:
        report.add("== workflows: none found")
        return
    parsed = []
    unread = []
    for path in files:
        lines = read_lines(path)
        facts = parse_workflow(lines) if lines is not None else None
        if facts is None or not facts["has_jobs"]:
            unread.append(f"{rel(path)} {'unreadable' if facts is None else 'no jobs: key'}")
        else:
            parsed.append((rel(path), facts))
    jobs = [(name, job, facts) for name, facts in parsed for job in facts["jobs"]]
    own = [entry for entry in jobs if not entry[1]["reusable"]]
    report.add(
        f"== workflows: {len(parsed)} files, {len(jobs)} jobs"
        f" ({len(jobs) - len(own)} call a reusable workflow)"
    )
    if unread:
        report.listing("not parsed", unread)
    report.listing(
        f"jobs without timeout-minutes (of {len(own)})",
        [f"{name}:{job['line']} {job['name']}" for name, job, _ in own if not job["timeout"]],
    )
    report.listing(
        "jobs with no permissions key at job or workflow level",
        [
            f"{name}:{job['line']} {job['name']}" for name, job, facts in jobs
            if job["permissions"] is None and facts["permissions"] is None
        ],
    )
    writes = []
    for name, facts in parsed:
        scopes = [("workflow", facts["permissions"])]
        scopes += [(f"job {job['name']}", job["permissions"]) for job in facts["jobs"]]
        for label, perm in scopes:
            granted = permission_writes(perm["value"], perm["children"]) if perm else []
            if granted:
                writes.append(f"{name}:{perm['line']} {label}: {','.join(granted)}")
    report.listing("write permissions", writes)
    report.listing(
        f"files with no concurrency key (of {len(parsed)})",
        [
            name for name, facts in parsed
            if not facts["concurrency"] and not any(j["concurrency"] for j in facts["jobs"])
        ],
    )
    uses = [(name, *use) for name, facts in parsed for use in facts["uses"]]
    count = {kind: sum(1 for use in uses if use[3] == kind) for kind in (
        "pinned", "local", "unpinned first-party", "unpinned third-party",
    )}
    report.add(
        f"uses: {len(uses)} refs; {count['pinned']} pinned to a SHA or digest,"
        f" {count['local']} local"
    )
    unpinned = [use for use in uses if use[3].startswith("unpinned")]
    unpinned.sort(key=lambda use: (use[3] != "unpinned third-party", use[0], use[1]))
    report.listing(
        "unpinned uses",
        [f"{name}:{line} {ref} ({kind[9:]})" for name, line, ref, kind in unpinned],
    )
    report.listing(
        "pull_request_target or workflow_run triggers",
        [f"{name}:{line} {trigger}" for name, facts in parsed
         for line, trigger in facts["triggers"]],
    )
    report.listing(
        "github.event.* or github.head_ref inside run/script",
        [f"{name}:{line} {expr}" for name, facts in parsed
         for line, expr in facts["expressions"]],
    )
    checkouts = [(name, *c) for name, facts in parsed for c in facts["checkouts"]]
    report.listing(
        f"actions/checkout without persist-credentials: false (of {len(checkouts)})",
        [f"{name}:{line}" for name, line, safe in checkouts if not safe],
    )


def report_dockerfiles(report: Report, files: list[Path], rel) -> None:
    if not files:
        report.add("== dockerfiles: none found")
        return
    report.add(f"== dockerfiles: {len(files)}")
    users, unpinned, secrets = [], [], []
    for path in files:
        lines = read_lines(path)
        name = rel(path)
        if lines is None:
            users.append(f"{name} unreadable")
            continue
        facts = parse_dockerfile(lines)
        if not facts["stages"]:
            users.append(f"{name} no FROM line")
            continue
        if facts["user"] is None:
            users.append(f"{name} no USER in the final stage (runs as root)")
        else:
            root = " (root)" if facts["user"].split(":")[0] in ("root", "0") else ""
            users.append(f"{name}:{facts['user_line']} USER {facts['user']}{root}")
        unpinned += [f"{name}:{line} FROM {image}" for line, image in facts["unpinned"]]
        secrets += [
            f"{name}:{line} {word} {key}" + (" (literal value set)" if literal else "")
            for line, word, key, literal in facts["secrets"]
        ]
    report.listing("final USER", users)
    report.listing("FROM with :latest or no tag", unpinned)
    report.listing("secret-like ENV/ARG names", secrets)


def report_compose(report: Report, files: list[Path], rel) -> None:
    if not files:
        report.add("== compose: none found")
        return
    rows, unread = [], []
    for path in files:
        lines = read_lines(path)
        services = parse_compose(lines) if lines is not None else None
        if services is None:
            unread.append(f"{rel(path)} {'unreadable' if lines is None else 'no services: key'}")
            continue
        for item in services:
            image = item["image"] or "-"
            rows.append(
                f"{rel(path)}:{item['line']} {item['name']} image={image}"
                f" pin={item['pin']}"
                f" healthcheck={'yes' if item['healthcheck'] else 'no'}"
                f" restart={item['restart'] or 'none'}"
                f" limits={'yes' if item['limits'] else 'no'}"
            )
    report.add(f"== compose: {len(files)} files")
    if unread:
        report.listing("not parsed", unread)
    report.listing("services", rows)


def report_scanners(report: Report, target: Path, found: dict, timeout: int, rel) -> None:
    jobs, missing, idle = plan_scanners(target, found)
    report.add("== scanners (evidence, not a verdict)")
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        futures = [(name, pool.submit(scan, arg, timeout)) for name, scan, arg in jobs]
        results = [(name, future.result()) for name, future in futures]
    for name, result in results:
        if isinstance(result, str):
            report.add(f"{name}: {result}")
        else:
            report.listing(
                f"{name} findings",
                sorted(f"{rel(path)}:{line} {rule}" if line else f"{rel(path)} {rule}"
                       for path, line, rule in result),
            )
    if idle:
        report.add(f"nothing to scan: {', '.join(idle)}")
    if missing:
        report.add(f"not installed: {', '.join(missing)}")
    if not jobs:
        report.add("ran: none")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("target")
    parser.add_argument("--no-scanners", action="store_true", help="skip installed scanners")
    parser.add_argument("--all", action="store_true", help="print every row")
    parser.add_argument("--timeout", type=int, default=90, help="seconds per scanner")
    args = parser.parse_args(argv)

    target = Path(args.target)
    if not target.exists():
        print(f"ci-facts: no such path: {args.target}", file=sys.stderr)
        return 2
    target = target.resolve()
    root = repo_root(target if target.is_dir() else target.parent)

    def rel(path: Path | str) -> str:
        path = Path(path)
        if not path.is_absolute():
            return path.as_posix()
        try:
            return path.resolve().relative_to(root).as_posix()
        except ValueError:
            return path.as_posix()

    found = discover(target)
    report = Report(args.all)
    report.add("ci-facts: line patterns, approximate; paths are relative to the repository root")
    report_workflows(report, found["workflow"], rel)
    report_dockerfiles(report, found["dockerfile"], rel)
    report_compose(report, found["compose"], rel)
    if not args.no_scanners:
        report_scanners(report, target, found, args.timeout, rel)
    print("\n".join(report.lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
