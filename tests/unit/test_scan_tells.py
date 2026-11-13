import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills/ai-sanitize/scripts/scan-tells.py"
spec = importlib.util.spec_from_file_location("scan_tells", SCRIPT)
scan_tells = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_tells)

ARTICLE = """\
# Title

## Intro

Let's dive in. This tool is seamless and robust.
It's not just a tool, it's a platform — honestly.

```sh
echo "seamless — robust"
```

## Usage

Run the command. It prints one line.
"""

PAGE = """\
<div class="bg-gradient-to-r from-purple-500 animate-pulse">
<p class="eyebrow">Oops!</p>
</div>
"""


def run(capsys, *args):
    code = scan_tells.main([str(a) for a in args])
    return code, capsys.readouterr().out


def by_rule(out):
    line = next(ln for ln in out.splitlines() if ln.startswith("by rule: "))
    return dict(item.rsplit(" ", 1) for item in line[len("by rule: "):].split(", "))


def test_prose_known_hits_per_rule(tmp_path, capsys):
    target = tmp_path / "post.md"
    target.write_text(ARTICLE, encoding="utf-8")
    code, out = run(capsys, target)
    assert code == 0
    assert by_rule(out) == {"prose-1*": "2", "prose-2*": "2", "prose-3*": "1", "prose-11*": "1"}
    assert f'{target}:5  prose-1  "dive in"' in out
    assert ":9  " not in out, "fenced code is not prose"
    assert f"{target}#Intro 6" in out
    assert "3+ hits in one section: yes (1 section(s))" in out


def test_ui_file_gets_ui_and_prose_rules(tmp_path, capsys):
    target = tmp_path / "hero.html"
    target.write_text(PAGE, encoding="utf-8")
    _, out = run(capsys, target)
    assert by_rule(out) == {"ui-1*": "2", "ui-3*": "1", "ui-14*": "1", "ui-16*": "1"}
    assert f"{target}#(file) 5" in out


def test_no_hits_and_empty_file(tmp_path, capsys):
    clean, empty = tmp_path / "clean.md", tmp_path / "empty.md"
    clean.write_text("# Notes\n\nThe cache expires after 60 seconds.\n")
    empty.write_text("")
    _, out = run(capsys, clean, empty)
    assert out.startswith("scanned 2 file(s): 0 candidate hit(s);")
    assert "by rule" not in out
    assert out.rstrip().endswith("3+ hits in one section: no")


def test_before_reports_gone_new_and_unchanged(tmp_path, capsys):
    before, after = tmp_path / "before.md", tmp_path / "after.md"
    before.write_text(ARTICLE, encoding="utf-8")
    after.write_text("# Title\n\nThis tool is robust. Unlock it.\n", encoding="utf-8")
    _, out = run(capsys, after, "--before", before)
    assert 'gone (5): prose-1 "dive in" x1, prose-1 "honestly" x1, prose-2 "seamless" x1' in out
    assert 'new (1): prose-2 "unlock" x1' in out
    _, out = run(capsys, before, "--before", before)
    assert f"unchanged: {before} is identical to {before}" in out


def test_output_is_capped_and_all_lifts_the_cap(tmp_path, capsys):
    target = tmp_path / "long.md"
    target.write_text("A seamless thing.\n" * 40)
    _, out = run(capsys, target)
    assert out.count("prose-2  ") == 30
    assert "... 10 more (--all)" in out
    _, out = run(capsys, target, "--all")
    assert out.count("prose-2  ") == 40


def test_directory_walk_skips_unknown_types(tmp_path, capsys):
    (tmp_path / "a.md").write_text("Seamless.\n")
    (tmp_path / "b.bin").write_text("Seamless.\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "c.md").write_text("Seamless.\n")
    _, out = run(capsys, tmp_path)
    assert out.startswith("scanned 1 file(s): 1 candidate hit(s);")


@pytest.mark.parametrize("args, message", [
    (["missing.md"], "no such file or directory: missing.md"),
    (["{tmp}/data.bin"], "cannot pick a medium"),
    (["{tmp}/a.md", "{tmp}/b.md", "--before", "{tmp}/a.md"], "--before needs one target file"),
])
def test_errors_are_one_line_and_exit_2(tmp_path, capsys, args, message):
    for name in ("data.bin", "a.md", "b.md"):
        (tmp_path / name).write_text("x\n")
    with pytest.raises(SystemExit) as exc:
        scan_tells.main([a.replace("{tmp}", str(tmp_path)) for a in args])
    err = capsys.readouterr().err
    assert exc.value.code == 2
    assert message in err and err.count("\n") == 1


def test_rules_come_from_the_detect_lines(tmp_path):
    for name in ("ui", "graphics"):
        (tmp_path / f"{name}.md").write_text("# Empty\n")
    (tmp_path / "prose.md").write_text(
        "## 7. Fake words (high signal)\n\n"
        '**Detect:** `grep -niE "foo|ba[rz]"`, `plain-word`, `(unclosed`. **By reading:** `div` and `span`.\n\n'
        "## 8. Shape\n\n"
        "**Detect by reading:** `font-size` values.\n\n"
        "## 9. Rhythm\n\n"
        "**Detect:** read it aloud.\n"
    )
    rules, lines, skipped = scan_tells.load_rules(str(tmp_path))
    assert [(rule, high) for rule, high, _ in rules["prose"]] == [("prose-7", True)] * 3
    assert rules["prose"][0][2].search("a BAZ here")
    assert rules["prose"][1][2].search("a plain-word here")
    assert not rules["prose"][1][2].search("not-plain-word")
    assert rules["prose"][2][2].search("an (unclosed paren"), "no | group, so it is literal text"
    assert (lines, skipped) == (3, 4)
    assert rules["ui"] == [] and rules["graphics"] == []


def test_real_references_parse(capsys):
    rules, lines, skipped = scan_tells.load_rules()
    assert lines == 32
    assert all(rules[m] for m in ("prose", "ui", "graphics"))
    assert skipped > 0
