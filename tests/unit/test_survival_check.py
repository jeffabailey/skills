import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/ai-sanitize/scripts/survival-check.py"
spec = importlib.util.spec_from_file_location("survival_check", SCRIPT)
survival = importlib.util.module_from_spec(spec)
spec.loader.exec_module(survival)


def run(tmp_path, before, after, capsys):
    b, a = tmp_path / "before.md", tmp_path / "after.md"
    b.write_text(before)
    a.write_text(after)
    code = survival.main(["survival-check.py", str(b), str(a)])
    return code, capsys.readouterr().out


def test_inline_to_reference_survives(tmp_path, capsys):
    before = "See [the docs](https://example.com/docs) and [post]({{< ref \"blog/x.md\" >}}).\n"
    after = (
        "See [the docs][docs] and [post][p].\n\n"
        "[docs]: https://example.com/docs\n"
        "[p]: {{< ref \"blog/x.md\" >}}\n"
    )
    code, out = run(tmp_path, before, after, capsys)
    assert code == 0, out


def test_removed_link_is_lost(tmp_path, capsys):
    before = "See [a](https://a.example) and [b][b].\n\n[b]: https://b.example\n"
    after = "See [a](https://a.example) and b.\n"
    code, out = run(tmp_path, before, after, capsys)
    assert code == 1
    assert "links: 'https://b.example'" in out
    assert "https://a.example" not in out


def test_voice_and_numbers_still_checked(tmp_path, capsys):
    before = "This shit cut latency by 40% in 3 weeks.\n"
    after = "This cut latency by 40% in weeks.\n"
    code, out = run(tmp_path, before, after, capsys)
    assert code == 1
    assert "voice: 'shit' 1 -> 0" in out
    assert "numbers in text: '3'" in out
