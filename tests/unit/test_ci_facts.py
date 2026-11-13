"""ci-facts.py: workflow, Dockerfile, compose, and scanner facts with known answers."""

import os
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/ci-facts.py"
SHA = "a" * 40

WORKFLOW = f"""name: CI
on:
  push:
  pull_request_target:
    types: [opened]
permissions:
  contents: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: acme/deploy@main
      - uses: actions/setup-python@{SHA}
      - uses: ./local-action
      - name: Greet
        timeout-minutes: 5
        run: |
          echo "${{{{ github.event.pull_request.title }}}}"
          # uses: fake/inside-shell@v1
      - name: Safe
        env:
          TITLE: ${{{{ github.event.issue.title }}}}
        run: echo "$TITLE" "${{{{ github.sha }}}}"
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    concurrency: test
    permissions:
      contents: read
    steps:
      - name: Checkout
        uses: actions/checkout@{SHA}
        with:
          persist-credentials: false
      - run: echo ${{{{ github.head_ref }}}}
  call:
    uses: acme/shared/.github/workflows/build.yml@v1
"""

DOCKERFILE = """ARG NPM_TOKEN
FROM node:latest AS build
ENV API_KEY=abc123 \\
    NODE_ENV=production
USER node
FROM build AS assets
FROM python
ENV DB_PASSWORD hunter2
CMD ["python", "app.py"]
"""

COMPOSE = """services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:16.2
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "pg_isready"]
    deploy:
      resources:
        limits:
          memory: 512M
  app:
    build: .
volumes:
  data: {}
"""


def run(*args, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True, text=True, env=env,
    )


def fixture(root: Path) -> Path:
    (root / ".git").mkdir()
    workflows = root / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(WORKFLOW)
    (root / "Dockerfile").write_text(DOCKERFILE)
    (root / "docker-compose.yml").write_text(COMPOSE)
    return root


def section(output: str, title: str) -> list[str]:
    """The indented rows under the line that starts with title."""
    lines = output.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(title))
    rows = []
    for line in lines[start + 1:]:
        if not line.startswith("  "):
            break
        rows.append(line.strip())
    return rows


def test_workflow_facts(tmp_path):
    out = run(fixture(tmp_path), "--no-scanners")
    assert out.returncode == 0, out.stderr
    text = out.stdout
    ci = ".github/workflows/ci.yml"

    assert "== workflows: 1 files, 3 jobs (1 call a reusable workflow)" in text
    # The step-level timeout at "Greet" does not count for the build job.
    assert section(text, "jobs without timeout-minutes (of 2): 1") == [f"{ci}:9 build"]
    assert "jobs with no permissions key at job or workflow level: 0" in text
    assert section(text, "write permissions: 1") == [f"{ci}:6 workflow: contents"]
    assert "files with no concurrency key (of 1): 0" in text
    assert "uses: 6 refs; 2 pinned to a SHA or digest, 1 local" in text
    assert section(text, "unpinned uses: 3") == [
        f"{ci}:13 acme/deploy@main (third-party)",
        f"{ci}:38 acme/shared/.github/workflows/build.yml@v1 (third-party)",
        f"{ci}:12 actions/checkout@v4 (first-party)",
    ]
    assert "fake/inside-shell" not in text
    assert section(text, "pull_request_target or workflow_run triggers: 1") == [
        f"{ci}:4 pull_request_target"
    ]
    # The env: pass-through at "Safe" and github.sha are not rows.
    assert section(text, "github.event.* or github.head_ref inside run/script: 2") == [
        f"{ci}:19 github.event.pull_request.title",
        f"{ci}:36 github.head_ref",
    ]
    assert section(
        text, "actions/checkout without persist-credentials: false (of 2): 1"
    ) == [f"{ci}:12"]


def test_dockerfile_and_compose_facts(tmp_path):
    text = run(fixture(tmp_path), "--no-scanners").stdout

    assert section(text, "final USER: 1") == [
        "Dockerfile no USER in the final stage (runs as root)"
    ]
    assert section(text, "FROM with :latest or no tag: 2") == [
        "Dockerfile:2 FROM node:latest",
        "Dockerfile:7 FROM python",
    ]
    assert section(text, "secret-like ENV/ARG names: 3") == [
        "Dockerfile:1 ARG NPM_TOKEN",
        "Dockerfile:3 ENV API_KEY (literal value set)",
        "Dockerfile:8 ENV DB_PASSWORD (literal value set)",
    ]
    assert "abc123" not in text and "hunter2" not in text
    assert section(text, "services: 3") == [
        "docker-compose.yml:2 web image=nginx:latest pin=unpinned healthcheck=no"
        " restart=none limits=no",
        "docker-compose.yml:6 db image=postgres:16.2 pin=tag healthcheck=yes"
        " restart=unless-stopped limits=yes",
        "docker-compose.yml:15 app image=- pin=build healthcheck=no restart=none limits=no",
    ]


def test_output_is_stable_and_a_subdirectory_target_keeps_repo_paths(tmp_path):
    root = fixture(tmp_path)
    first = run(root, "--no-scanners").stdout
    assert first == run(root, "--no-scanners").stdout

    scoped = run(root / ".github", "--no-scanners").stdout
    assert ".github/workflows/ci.yml:9 build" in scoped
    assert "== dockerfiles: none found" in scoped


def test_empty_target_and_missing_target(tmp_path):
    out = run(tmp_path, "--no-scanners")
    assert out.returncode == 0
    assert out.stdout.splitlines()[1:] == [
        "== workflows: none found",
        "== dockerfiles: none found",
        "== compose: none found",
    ]

    missing = run(tmp_path / "nope")
    assert missing.returncode == 2
    assert missing.stdout == ""
    assert missing.stderr.strip() == f"ci-facts: no such path: {tmp_path / 'nope'}"


def test_malformed_files_are_named_not_fatal(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "broken.yml").write_text("this is: [not a workflow\n\t- at all\n")
    (workflows / "binary.yml").write_bytes(b"\xff\xfe\x00jobs")
    (tmp_path / "Dockerfile").write_text("# nothing here\n")
    (tmp_path / "compose.yaml").write_text("version: '3'\n")

    out = run(tmp_path, "--no-scanners")
    assert out.returncode == 0, out.stderr
    assert "Traceback" not in out.stderr
    assert section(out.stdout, "not parsed: 2") == [
        ".github/workflows/binary.yml unreadable",
        ".github/workflows/broken.yml no jobs: key",
    ]
    assert "Dockerfile no FROM line" in out.stdout
    assert "compose.yaml no services: key" in out.stdout


def test_lists_are_capped_unless_all(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    jobs = "".join(f"  job{n:02d}:\n    runs-on: x\n" for n in range(20))
    (workflows / "many.yml").write_text(f"on: push\njobs:\n{jobs}")

    capped = run(tmp_path, "--no-scanners").stdout
    assert len(section(capped, "jobs without timeout-minutes (of 20): 20")) == 16
    assert "... and 5 more (--all)" in capped
    full = run(tmp_path, "--no-scanners", "--all").stdout
    assert len(section(full, "jobs without timeout-minutes (of 20): 20")) == 20


def test_no_scanner_installed(tmp_path):
    empty = tmp_path / "bin"
    empty.mkdir()
    root = tmp_path / "repo"
    root.mkdir()
    out = run(fixture(root), env={"PATH": str(empty)})
    assert out.returncode == 0, out.stderr
    tail = out.stdout.split("== scanners (evidence, not a verdict)\n")[1].splitlines()
    assert tail == [
        "not installed: gitleaks, zizmor/actionlint, osv-scanner/pip-audit",
        "ran: none",
    ]


def test_installed_scanners_report_rule_and_location_only(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    fixture(root)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    sarif = (
        '{"runs":[{"results":[{"ruleId":"generic-api-key","message":{"text":"LEAKED-VALUE"},'
        '"locations":[{"physicalLocation":{"artifactLocation":{"uri":"app/settings.py"},'
        '"region":{"startLine":7}}}]}]}]}'
    )
    # A stand-in gitleaks: records its arguments and writes a SARIF report.
    gitleaks = bin_dir / "gitleaks"
    gitleaks.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        f"open({str(tmp_path / 'args.txt')!r}, 'w').write(' '.join(args))\n"
        f"open(args[args.index('--report-path') + 1], 'w').write({sarif!r})\n"
        "sys.exit(1)\n"
    )
    # A stand-in zizmor that prints something that is not SARIF.
    zizmor = bin_dir / "zizmor"
    zizmor.write_text(f"#!{sys.executable}\nprint('not json')\nraise SystemExit(3)\n")
    for tool in (gitleaks, zizmor):
        tool.chmod(tool.stat().st_mode | stat.S_IXUSR)

    out = run(root, env={"PATH": str(bin_dir), "HOME": os.environ.get("HOME", "")})
    assert out.returncode == 0, out.stderr
    assert section(out.stdout, "gitleaks findings: 1") == ["app/settings.py:7 generic-api-key"]
    assert "LEAKED-VALUE" not in out.stdout
    assert "zizmor: output not parsed (exit 3); run it by hand" in out.stdout
    assert "not installed: osv-scanner/pip-audit" in out.stdout
    assert "--redact" in (tmp_path / "args.txt").read_text()
