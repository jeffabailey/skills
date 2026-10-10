#!/usr/bin/env python3
"""WCAG 2.x contrast ratios, with CSS custom properties resolved per theme.

Two modes:

  contrast.py pair FG BG [FG BG ...]
      Ratio for literal colors, e.g.  contrast.py pair '#999' white

  contrast.py css FILE [FILE ...] [--bg TOKEN] [--theme NAME] [--pair FG:BG]...
                [--tokens] [--fails-only]
      Parses custom properties (--name: value) declared on :root/html/body/:host,
      groups them into themes, resolves var() chains (with fallbacks), then checks:
        - each --pair (4.5:1 unless a third field sets the ratio), and every token that is not a background (by use or by
          name) as text on the page background token (--bg, else the first of
          --theme, --background, --bg, --body-bg, --color-background, --page-bg);
        - every rule that sets a foreground color:
            color                          -> text, needs 4.5:1 (3:1 if large)
            border-color / outline(-color) -> non-text UI vs the page, needs 3:1
          Text is checked against the rule's own background when it sets one,
          otherwise against the page background (marked "page": verify it);
        - outline: 0/none, flagged CHECK so you confirm a visible replacement.
      Pass every stylesheet that defines or overrides the tokens (theme files
      included), or tokens defined elsewhere stay unresolved. Non-CSS files
      (HTML, templates) are read for their inline <style> blocks.
      --fails-only hides PASS rows but never UNRES rows.

Themes: declarations on :root/html/body are the base ("light"). A selector or
@media wrapper that mentions a scheme (data-theme="dark", .dark, .theme-dark,
prefers-color-scheme: dark, high-contrast, ...) creates an overlay theme that
inherits the base. Rules scoped to one theme are checked only in that theme.

Values the script cannot resolve to an sRGB color (currentColor, color-mix(),
oklch(), gradients, url()) are reported as "unresolved", never guessed.
Semi-transparent colors are composited over the background (and an alpha
background over white for light themes, black for dark ones).

Standard library only. Exit code 0 always; read the PASS/FAIL column.
"""
from __future__ import annotations

import argparse
import colorsys
import os
import re
import sys

NAMED = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000", "green": "#008000",
    "blue": "#0000ff", "yellow": "#ffff00", "gray": "#808080", "grey": "#808080",
    "silver": "#c0c0c0", "maroon": "#800000", "purple": "#800080", "navy": "#000080",
    "teal": "#008080", "olive": "#808000", "orange": "#ffa500", "lime": "#00ff00",
    "aqua": "#00ffff", "cyan": "#00ffff", "fuchsia": "#ff00ff", "magenta": "#ff00ff",
    "darkgray": "#a9a9a9", "darkgrey": "#a9a9a9", "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3", "dimgray": "#696969", "dimgrey": "#696969",
    "gainsboro": "#dcdcdc", "whitesmoke": "#f5f5f5", "crimson": "#dc143c",
    "darkred": "#8b0000", "darkblue": "#00008b", "darkgreen": "#006400",
    "rebeccapurple": "#663399", "indigo": "#4b0082", "gold": "#ffd700",
    "transparent": "#00000000",
}
PAGE_BG_GUESSES = ["--theme", "--background", "--bg", "--body-bg",
                   "--color-background", "--page-bg"]
ROOTISH = {":root", "html", "body", ":host", ""}
SCHEME_RE = re.compile(
    r"""(?:data-(?:theme|mode|color-scheme|bs-theme)\s*=\s*["']?([\w-]+))"""
    r"""|(?:\.(?:theme-|scheme-)?(dark|light|high-contrast|hc)\b)"""
    r"""|(?:prefers-color-scheme\s*:\s*(dark|light))"""
    r"""|(?:prefers-contrast\s*:\s*(more|high))""", re.I)

Color = tuple  # (r, g, b, a) floats, r/g/b in 0..255, a in 0..1


# ---------- color math ----------

def parse_color(text: str) -> Color | None:
    t = text.strip().lower().replace("!important", "").strip()
    if t in NAMED:
        t = NAMED[t]
    m = re.fullmatch(r"#([0-9a-f]{3,8})", t)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
    m = re.fullmatch(r"(rgba?|hsla?)\((.*)\)", t)
    if not m:
        return None
    parts = [p for p in re.split(r"[\s,/]+", m.group(2).strip()) if p]
    if len(parts) not in (3, 4):
        return None

    def num(p, scale):
        return float(p[:-1]) / 100 * scale if p.endswith("%") else float(p)

    try:
        a = num(parts[3], 1) if len(parts) == 4 else 1.0
        if m.group(1).startswith("rgb"):
            r, g, b = (num(p, 255) for p in parts[:3])
        else:
            hue = float(re.sub(r"deg$", "", parts[0]))
            s = num(parts[1], 1) if parts[1].endswith("%") else float(parts[1]) / 100
            li = num(parts[2], 1) if parts[2].endswith("%") else float(parts[2]) / 100
            r, g, b = (c * 255 for c in colorsys.hls_to_rgb((hue % 360) / 360, li, s))
    except ValueError:
        return None
    return (r, g, b, max(0.0, min(1.0, a)))


def composite(fg: Color, bg: Color) -> Color:
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def luminance(c: Color) -> float:
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2])


def ratio(fg: Color, bg: Color, dark: bool = False) -> float:
    if bg[3] < 1:
        bg = composite(bg, (0, 0, 0, 1) if dark else (255, 255, 255, 1))
    if fg[3] < 1:
        fg = composite(fg, bg)
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def hexof(c: Color) -> str:
    s = "#" + "".join(f"{round(v):02x}" for v in c[:3])
    return s + (f"{round(c[3] * 255):02x}" if c[3] < 1 else "")


# ---------- CSS parsing ----------

class Rule:
    def __init__(self, file: str, selector: str, media: str):
        self.file, self.selector, self.media = file, selector, media
        self.decls: dict = {}  # prop -> (value, line)


def parse_css(path: str) -> list[Rule]:
    raw = open(path, encoding="utf-8", errors="replace").read()
    if not path.lower().endswith((".css", ".scss", ".less")):
        # Templates and HTML: keep only <style> blocks, blank the rest (newlines kept,
        # so line numbers still match the file).
        keep = [False] * len(raw)
        for m in re.finditer(r"<style[^>]*>(.*?)</style>", raw, flags=re.S | re.I):
            for i in range(m.start(1), m.end(1)):
                keep[i] = True
        raw = "".join(c if k or c == "\n" else " " for c, k in zip(raw, keep))
    # Blank out comments but keep newlines so offsets map to the same lines.
    src = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw, flags=re.S)
    name = os.path.relpath(path) if not os.path.relpath(path).startswith("..") else path
    rules, stack, start = [], [], 0
    for i, ch in enumerate(src):
        if ch == "{":
            stack.append((" ".join(src[start:i].split()), i + 1))
            start = i + 1
        elif ch == "}":
            if stack:
                head, body_start = stack.pop()
                if not head.startswith("@"):
                    media = " ".join(h for h, _ in stack if h.startswith("@"))
                    parents = [h for h, _ in stack if not h.startswith("@")]
                    sel = head if not parents else " ".join(parents + [head])
                    rule = Rule(name, sel, media)
                    _decls(rule, src, max(body_start, start), i)
                    rules.append(rule)
            start = i + 1
        elif ch == ";" and not stack:
            start = i + 1
    return rules


def _decls(rule: Rule, src: str, lo: int, hi: int) -> None:
    pos = lo
    for chunk in src[lo:hi].split(";"):
        if ":" in chunk and "{" not in chunk:
            prop, val = chunk.split(":", 1)
            off = pos + (len(chunk) - len(chunk.lstrip()))
            rule.decls[prop.strip().lower()] = (" ".join(val.split()), src.count("\n", 0, off) + 1)
        pos += len(chunk) + 1


def scheme_of(text: str) -> str | None:
    m = SCHEME_RE.search(text)
    if not m:
        return None
    name = next(g for g in m.groups() if g).lower()
    return {"hc": "high-contrast", "more": "high-contrast", "high": "high-contrast"}.get(name, name)


def strip_scheme(selector: str) -> str:
    s = re.sub(r"\[data-[\w-]+\s*=\s*[^\]]+\]", "", selector)
    s = re.sub(r"\.(?:theme-|scheme-)?(?:dark|light|high-contrast|hc)\b", "", s)
    return s.strip()


def collect_tokens(rules):
    """Returns {theme: {token: (value, file, line)}} with overlays still separate."""
    themes: dict[str, dict] = {"light": {}}
    for r in rules:
        for sel in (s.strip() for s in r.selector.split(",")):
            if strip_scheme(sel) not in ROOTISH:
                continue
            name = scheme_of(sel) or scheme_of(r.media) or "light"
            for prop, (val, line) in r.decls.items():
                if prop.startswith("--"):
                    themes.setdefault(name, {})[prop] = (val, r.file, line)
    merged = {}
    for name, toks in themes.items():
        merged[name] = dict(themes["light"]) if name != "light" else {}
        merged[name].update(toks)
    return merged


def resolve(value: str, tokens: dict, local: dict | None = None, depth: int = 0) -> str:
    if depth > 20:
        return value
    m = re.search(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*(?:\([^()]*\))?[^()]*))?\)", value)
    if not m:
        return value
    name, fallback = m.group(1), m.group(2)
    if local and name in local:
        rep = local[name][0]
    elif name in tokens:
        rep = tokens[name][0]
    elif fallback is not None:
        rep = fallback.strip()
    else:
        return value
    return resolve(value[:m.start()] + rep + value[m.end():], tokens, local, depth + 1)


def color_from(value: str, tokens, local=None) -> tuple[Color | None, str]:
    v = resolve(value, tokens, local)
    if re.search(r"url\(|gradient\(", v):
        return None, v
    for cand in [v] + v.split():  # shorthand: pick the token that parses
        c = parse_color(cand)
        if c:
            return c, v
    return None, v


# ---------- reporting ----------

BG_NAME = re.compile(r"(^--(theme|entry)$)|bg|background|surface|canvas|paper|soft|tint|shadow|border|"
                     r"overlay|backdrop", re.I)


def _row(verdict, cr, need, kind, fg_desc, bg_desc, where, what):
    cr_s = f"{cr:5.2f}" if cr is not None else "  -  "
    return f"{verdict:6s} | {cr_s} | {need} | {kind} | {fg_desc} -> {bg_desc} | {where} | {what}"


def _verdict(cr, need, kind):
    if cr >= need:
        return "PASS"
    return "LARGE" if kind == "text" and cr >= 3.0 else "FAIL"


def token_usage(rules):
    """Which tokens appear in background, color, and token-definition values."""
    use = {"bg": set(), "color": set(), "alias": set()}
    for r in rules:
        for prop, (val, _) in r.decls.items():
            refs = re.findall(r"var\(\s*(--[\w-]+)", val)
            if prop in ("background", "background-color"):
                use["bg"].update(refs)
            elif prop == "color":
                use["color"].update(refs)
            elif prop.startswith("--"):
                use["alias"].update(refs)
    return use


def text_candidates(toks, bgk, use):
    """Tokens worth checking as text: used in color:, or not used at all in these files
    (a theme may consume them elsewhere). Skips backgrounds and palette primitives that
    only feed other tokens."""
    for t in sorted(toks):
        if t == bgk or t in use["bg"] or BG_NAME.search(t):
            continue
        if t in use["color"] or t not in use["alias"]:
            yield t


def effective_rules(rules, theme):
    """Merge unscoped rules with rules scoped to `theme`, per selector, in source order,
    so a dark-only override replaces the base declaration instead of being checked alone."""
    merged = {}
    for r in rules:
        for sel in (s.strip() for s in r.selector.split(",")):
            scope = scheme_of(sel) or scheme_of(r.media)
            if scope is not None and scope != theme:
                continue
            key = re.sub(r"^(?::root|html|body)(?=[\s.#:\[>~+]|$)\s*", "", strip_scheme(sel)).strip()
            if key in ROOTISH:
                continue  # token definitions, not usage
            entry = merged.setdefault(key, {"decls": {}, "file": r.file})
            for prop, (val, line) in r.decls.items():
                entry["decls"][prop] = (val, line, r.file)
    return merged


def check_css(files, bg_token=None, only_theme=None, show_tokens=False, fails_only=False,
              pairs=()):
    rules = [r for f in files for r in parse_css(f)]
    themes = collect_tokens(rules)
    use = token_usage(rules)
    out = []
    for name, toks in themes.items():
        if only_theme and name != only_theme:
            continue
        dark = "dark" in name
        bgk = bg_token or next((k for k in PAGE_BG_GUESSES if k in toks), None)
        page_bg = color_from(toks[bgk][0], toks)[0] if bgk else None
        out.append(f"\n## theme: {name}  (page background: {bgk or 'none'} = "
                   f"{hexof(page_bg) if page_bg else 'unknown'})")
        if show_tokens:
            out.append("### resolved tokens")
            for t, (val, f, ln) in sorted(toks.items()):
                c, _ = color_from(val, toks)
                out.append(f"{t:28s} {hexof(c) if c else 'unresolved':10s} {val}  ({f}:{ln})")
        out.append("result | ratio | need | kind | fg -> bg | where | what")

        # 1. Explicit pairs, then every foreground-looking token vs the page background.
        checks = []
        for fg_t, bg_t, need in pairs:
            checks.append((fg_t, bg_t, "pair", need))
        if page_bg is not None:
            for t in text_candidates(toks, bgk, use):
                checks.append((t, bgk, "token", 4.5))
        for fg_t, bg_t, kind_src, need in checks:
            if fg_t not in toks or bg_t not in toks:
                out.append(_row("UNRES", None, need, kind_src, fg_t, bg_t, "-", "token not defined"))
                continue
            fg, _ = color_from(toks[fg_t][0], toks)
            bg, _ = color_from(toks[bg_t][0], toks)
            where = f"{toks[fg_t][1]}:{toks[fg_t][2]}"
            if fg is None or bg is None:
                if not fails_only:
                    out.append(_row("UNRES", None, need, kind_src, toks[fg_t][0], bg_t, where, fg_t))
                continue
            cr = ratio(fg, bg, dark)
            kind = "text?" if kind_src == "token" else ("text" if need >= 4.5 else "non-text")
            v = _verdict(cr, need, "text" if need >= 4.5 else "non-text")
            if not (fails_only and v == "PASS"):
                out.append(_row(v, cr, need, kind, f"{fg_t} {hexof(fg)}", f"{bg_t} {hexof(bg)}",
                                where, f"{kind_src}: {fg_t} on {bg_t}"))

        # 2. Rules that set a foreground color, after merging theme overrides.
        rows = {}
        for sel, entry in effective_rules(rules, name).items():
            d = entry["decls"]
            local = {k: (v[0], v[1]) for k, v in d.items() if k.startswith("--")}
            bg_decl = d.get("background-color") or d.get("background")
            fill, fill_src = page_bg, "page"
            if bg_decl and not re.fullmatch(r"(none|inherit|initial|unset)( !important)?",
                                            bg_decl[0].strip()):
                c, _ = color_from(bg_decl[0], toks, local)
                if c is None:
                    fill, fill_src = None, "unresolved"  # image, gradient, or unknown color
                elif c[3] > 0:
                    fill, fill_src = c, "rule"
            for prop, kind, need in (("color", "text", 4.5),
                                     ("border-color", "non-text", 3.0),
                                     ("outline-color", "non-text", 3.0),
                                     ("outline", "non-text", 3.0)):
                if prop not in d:
                    continue
                val, line, f = d[prop]
                where = f"{f}:{line}"
                if prop == "outline" and re.fullmatch(r"(0|none)(px)?( !important)?", val.strip()):
                    row = ("CHECK", None, "-", "focus", "outline removed", "confirm a visible "
                           "replacement (box-shadow, border, :focus-visible)", where)
                    rows.setdefault(row, []).append(sel)
                    continue
                # Text sits on the element's own fill; borders and outlines sit against
                # whatever surrounds the element, assumed to be the page background.
                bg, bg_src = (fill, fill_src) if kind == "text" else (page_bg, "page")
                fg, _ = color_from(val, toks, local)
                if fg is None or bg is None:
                    # Always shown, even with --fails-only: an unchecked pair is not a pass.
                    row = ("UNRES", None, need, kind, val, hexof(bg) if bg else "?", where)
                    rows.setdefault(row, []).append(sel)
                    continue
                cr = round(ratio(fg, bg, dark), 2)
                v = _verdict(cr, need, kind)
                if fails_only and v == "PASS":
                    continue
                row = (v, cr, need, kind, f"{val} = {hexof(fg)}", f"{hexof(bg)} ({bg_src})", where)
                rows.setdefault(row, []).append(sel)
        unresolved = 0
        for row, sels in rows.items():
            if row[0] == "UNRES":
                unresolved += 1
            out.append(_row(*row, ", ".join(sels)))
        out.append(f"-- {name}: {unresolved} unresolved rule value(s)"
                   + ("; rerun with the files that define those tokens, or treat them as "
                      "not verified" if unresolved else ""))
    out.append("\nLARGE = passes only for large text (>=24px, or >=18.66px bold). text? = a token "
               "checked as text on the page background; ignore it if the token is never used for text. "
               "(page) = background assumed, confirm the element sits on it. Non-text FAILs matter only "
               "when that border/outline is what identifies the control or its focus state.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pair", help="ratio for literal FG BG pairs")
    p.add_argument("colors", nargs="+")
    c = sub.add_parser("css", help="resolve custom properties per theme and check rules")
    c.add_argument("files", nargs="+")
    c.add_argument("--bg", help="page background token, e.g. --theme")
    c.add_argument("--theme", help="only report this theme (light, dark, ...)")
    c.add_argument("--tokens", action="store_true", help="also print resolved tokens")
    c.add_argument("--fails-only", action="store_true")
    c.add_argument("--pair", action="append", default=[], metavar="FG:BG[:RATIO]",
                   help="extra token pair, e.g. --pair=--muted:--card, or --pair=--ring:--bg:3 "
                        "for a non-text 3:1 check (repeatable)")
    a = ap.parse_args(argv)
    if a.cmd == "pair":
        if len(a.colors) % 2:
            ap.error("pair needs an even number of colors")
        for fg_s, bg_s in zip(a.colors[::2], a.colors[1::2]):
            fg, bg = parse_color(fg_s), parse_color(bg_s)
            if not fg or not bg:
                print(f"{fg_s} on {bg_s}: unresolved color")
                continue
            cr = ratio(fg, bg)
            print(f"{fg_s} on {bg_s}: {cr:.2f}:1  text AA {'PASS' if cr >= 4.5 else 'FAIL'}"
                  f"  large/non-text AA {'PASS' if cr >= 3 else 'FAIL'}"
                  f"  text AAA {'PASS' if cr >= 7 else 'FAIL'}")
    else:
        pairs = []
        for p in a.pair:
            parts = [x.strip() for x in p.split(":")]
            if len(parts) not in (2, 3):
                ap.error(f"--pair expects FG:BG or FG:BG:RATIO, got {p!r}")
            pairs.append((parts[0], parts[1], float(parts[2]) if len(parts) == 3 else 4.5))
        print(check_css(a.files, a.bg, a.theme, a.tokens, a.fails_only, pairs))


if __name__ == "__main__":
    sys.exit(main())
