"""Tests for skills/the-deterministic-maker/scripts/measure_skills.py, run on a throwaway skills dir and transcripts."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "skills" / "the-deterministic-maker" / "scripts" / "measure_skills.py"
OLD, NEW = "2020-01-01T00:00:00.000Z", "2999-01-01T00:00:00.000Z"

PROSE_SKILL = """---
name: digest
description: "Summarizes change files."
metadata:
  version: "1.0.0"
---

# Digest

1. Read the files and count the entries of each type.

```bash
ls changes
cat changes/a.md
wc -l changes/a.md
```
"""

SCRIPTED_SKILL = """---
name: deps
description: >
  Lists dependencies
  with a script.
---

# Deps

Run `python3 scripts/list_deps.py` and judge the result.
"""


def run(cwd, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True)


def make_skills(root):
    for name, text in (("digest", PROSE_SKILL), ("deps", SCRIPTED_SKILL)):
        (root / "skills" / name).mkdir(parents=True)
        (root / "skills" / name / "SKILL.md").write_text(text)
    (root / "skills" / "deps" / "scripts").mkdir()
    (root / "skills" / "deps" / "scripts" / "list_deps.py").write_text("print('ok')\n")
    (root / "skills" / "deps" / "references").mkdir()
    (root / "skills" / "deps" / "references" / "notes.md").write_text("x" * 400)


def assistant(mid, ts, *blocks, out=10):
    usage = {"input_tokens": 100, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 1000, "output_tokens": out}
    return {"type": "assistant", "timestamp": ts, "message": {"id": mid, "usage": usage, "content": list(blocks)}}


def tool_use(tid, name, **inp):
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def tool_result(tid, text, ts, error=False, **extra):
    block = {"type": "tool_result", "tool_use_id": tid, "content": text, "is_error": error}
    return {"type": "user", "timestamp": ts, "message": {"content": [block]}, **extra}


def prompt(text, ts):
    return {"type": "user", "timestamp": ts, "message": {"content": text}}


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def make_transcripts(root, ts=OLD):
    """One session: a digest run by hand (with a subagent), then a deps run through its script."""
    proj = root / "projects" / "-tmp-proj"
    write_jsonl(proj / "s1.jsonl", [
        prompt("please digest", ts),
        assistant("m0", ts, tool_use("t0", "Bash", command="echo before the run")),
        assistant("m1", ts, tool_use("t1", "Skill", skill="plug:digest")),
        tool_result("t1", "loaded", ts),
        assistant("m2", ts, tool_use("t2", "Bash", command="grep -n feat changes/a.md"), out=50),
        assistant("m2", ts, tool_use("t3", "Bash", command="python3 - <<'EOF'\nprint(1)\nEOF")),
        tool_result("t2", "x" * 400, ts),
        tool_result("t3", "boom", ts, error=True),
        assistant("m3", ts, tool_use("t4", "Agent", prompt="help")),
        tool_result("t4", "started", ts, toolUseResult={"agentId": "abc"}),
        prompt("thanks, now something else", ts),
        assistant("m4", ts, tool_use("t5", "Bash", command="echo after the run")),
        prompt("<command-name>/deps</command-name>", ts),
        assistant("m5", ts, tool_use("t6", "Bash", command="python3 skills/deps/scripts/list_deps.py")),
        tool_result("t6", "ok", ts),
    ])
    write_jsonl(proj / "s1" / "subagents" / "agent-abc.jsonl", [assistant("s1", ts), assistant("s1", ts), assistant("s2", ts)])
    tagged = [dict(assistant(m, ts), attributionSkill="plug:digest") for m in ("w1", "w2")]
    write_jsonl(proj / "s1" / "subagents" / "workflows" / "wf_1" / "agent-wf9.jsonl", tagged)


def snapshot(root, *args):
    r = run(root, "snapshot", "--projects-dir", str(root / "projects"), "--json", *args)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_static_metrics_separate_prose_steps_from_scripted_ones(tmp_path):
    make_skills(tmp_path)
    skills = snapshot(tmp_path)["skills"]
    digest, deps = skills["digest"]["static"], skills["deps"]["static"]
    assert digest["recipe_blocks"] == [{"line": 12, "commands": 3}]
    assert [h["line"] for h in digest["data_step_hints"]] == [10]
    assert digest["version"] == "1.0.0" and digest["scripts"] == []
    assert deps["scripts"] == ["list_deps.py"] and deps["unreferenced_scripts"] == []
    assert deps["data_step_hint_count"] == 0 and deps["recipe_blocks"] == []
    assert deps["description_tokens"] == round(len("Lists dependencies with a script.") / 4)
    assert deps["reference_files"] == 1 and deps["reference_tokens"] == 100


def test_usage_is_attributed_to_the_run_between_invocation_and_next_prompt(tmp_path):
    make_skills(tmp_path)
    make_transcripts(tmp_path)
    skills = snapshot(tmp_path, "--days", "36500")["skills"]
    digest, deps = skills["digest"]["usage"], skills["deps"]["usage"]
    assert digest["runs"] == 1 and digest["kinds"] == {"skill-tool": 1}
    # m2 appears twice with the same id and counts once; m0 and m4 are outside the run.
    assert digest["per_run"]["api_calls"] == 2
    assert digest["per_run"]["output_tokens"] == 60
    assert digest["per_run"]["cost_eq_tokens"] == 2 * (100 + 0.1 * 1000) + 5 * 60
    assert digest["per_run"]["tool_result_tokens"] == round((400 + len("boom") + len("started")) / 4, 1)
    assert digest["adhoc_bash_calls"] == 2 and digest["inline_code_calls"] == 1 and digest["failures"] == 1
    assert {h["head"] for h in digest["top_adhoc"]} == {"grep -n feat", "python3 -"}
    # Two API calls in each subagent transcript, 1,110 tokens each. One is linked by the Agent call's id,
    # the other only by its attributionSkill tag.
    assert digest["agent_calls"] == 1 and digest["subagents"] == 2
    assert digest["per_run"]["subagent_tokens"] == 4440
    assert digest["per_run"]["subagent_cost_eq_tokens"] == 2 * 2 * (100 + 0.1 * 1000 + 5 * 10)
    assert digest["total_cost_eq_tokens"] == 700 + 1000
    assert deps["runs"] == 1 and deps["kinds"] == {"slash": 1}
    assert deps["own_script_calls"] == 1 and deps["adhoc_bash_calls"] == 0


def test_named_skills_limit_the_snapshot_and_unknown_names_fail(tmp_path):
    make_skills(tmp_path)
    assert list(snapshot(tmp_path, "deps")["skills"]) == ["deps"]
    r = run(tmp_path, "snapshot", "nope", "--projects-dir", str(tmp_path / "projects"))
    assert r.returncode != 0 and "no SKILL.md for 'nope'" in r.stderr


def test_compare_reports_load_change_and_marks_use_as_not_measured(tmp_path):
    make_skills(tmp_path)
    make_transcripts(tmp_path)
    base = tmp_path / "base.json"
    snapshot(tmp_path, "--days", "36500", "--out", str(base))
    skill_md = tmp_path / "skills" / "digest" / "SKILL.md"
    skill_md.write_text(skill_md.read_text().split("1. Read")[0] + "1. Run `python3 scripts/count.py changes`.\n")
    (tmp_path / "skills" / "digest" / "scripts").mkdir()
    (tmp_path / "skills" / "digest" / "scripts" / "count.py").write_text("print(3)\n")

    r = run(tmp_path, "compare", str(base), "--json")
    assert r.returncode == 0, r.stderr
    diff = json.loads(r.stdout)["skills"]
    assert diff["deps"]["status"] == "unchanged"
    digest = diff["digest"]
    assert digest["status"] == "changed" and digest["static"]["scripts"] == [0, 1]
    assert digest["static"]["recipe_blocks"] == [1, 0]
    assert digest["static"]["body_tokens"][1] < digest["static"]["body_tokens"][0]
    assert digest["runs"] == [1, 0] and digest["use_measured"] is False
    assert digest["per_run"]["api_calls"] == [2, None]

    text = run(tmp_path, "compare", str(base)).stdout
    assert "not measured yet" in text and "Other skills: 1 unchanged." in text


def test_compare_measures_runs_that_started_after_the_baseline(tmp_path):
    make_skills(tmp_path)
    make_transcripts(tmp_path)
    base = tmp_path / "base.json"
    snapshot(tmp_path, "--days", "36500", "--out", str(base))
    (tmp_path / "skills" / "digest" / "SKILL.md").write_text(PROSE_SKILL.replace("count the entries", "use the totals"))
    make_transcripts(tmp_path, ts=NEW)

    diff = json.loads(run(tmp_path, "compare", str(base), "--json").stdout)["skills"]["digest"]
    assert diff["runs"] == [1, 1] and diff["use_measured"] is True
    assert diff["per_run"]["api_calls"] == [2, 2]


def test_a_subagent_that_edits_the_skill_it_read_is_not_a_run(tmp_path):
    make_skills(tmp_path)
    sub = tmp_path / "projects" / "-tmp-proj" / "s2" / "subagents"
    read = tool_use("r1", "Read", file_path="/repo/skills/digest/SKILL.md")
    write_jsonl(tmp_path / "projects" / "-tmp-proj" / "s2.jsonl", [prompt("go", OLD)])
    write_jsonl(sub / "agent-use.jsonl", [assistant("a1", OLD, read), assistant("a2", OLD)])
    edit = tool_use("e1", "Edit", file_path="/repo/skills/digest/SKILL.md")
    write_jsonl(sub / "agent-dev.jsonl", [assistant("b1", OLD, read), assistant("b2", OLD, edit)])
    usage = snapshot(tmp_path, "--days", "36500")["skills"]["digest"]["usage"]
    assert usage["runs"] == 1 and usage["kinds"] == {"read-in-subagent": 1}
