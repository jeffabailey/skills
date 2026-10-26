import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/review-accessibility/scripts/contrast.py"
spec = importlib.util.spec_from_file_location("contrast", SCRIPT)
contrast = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contrast)


def r(fg, bg):
    return round(contrast.ratio(contrast.parse_color(fg), contrast.parse_color(bg)), 2)


def test_known_ratios():
    assert r("#999", "#fff") == 2.85
    assert r("#333333", "white") == 12.63
    assert r("#767676", "#ffffff") == 4.54
    assert r("rgb(0 0 0 / 50%)", "#fff") == 3.98


def test_unresolvable_is_none():
    assert contrast.parse_color("oklch(50% .1 200)") is None
    assert contrast.parse_color("currentColor") is None


def test_theme_tokens_and_overrides(tmp_path):
    css = tmp_path / "t.css"
    css.write_text(
        ":root { --bg: #fff; --muted: #aaa; }\n"
        ':root[data-theme="dark"] { --bg: #111; }\n'
        ".chip:hover { background: #8b4fd6; color: #fff; }\n"
        ':root[data-theme="dark"] .chip:hover { color: var(--bg); }\n'
    )
    out = contrast.check_css([str(css)])
    light, dark = out.split("## theme: dark")
    assert "2.32 | 4.5 | text? | --muted" in light
    # the dark-only override replaces the base color instead of being checked alone
    assert "3.77 | 4.5 | text | var(--bg) = #111111 -> #8b4fd6 (rule) | " in dark
    assert "#fff = #ffffff" not in dark
