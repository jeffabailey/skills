---
name: review-accessibility
description: Reviews frontend code for accessibility and usability fitness, scoring across semantic HTML, keyboard navigation, screen reader support, color/contrast, progressive enhancement, responsive design, and usability heuristics. Computes WCAG contrast ratios with a bundled script that resolves CSS custom properties per theme (light/dark). Use when the user says /review:accessibility, requests an accessibility audit, asks for a11y review, wants WCAG compliance check, asks to check color contrast, alt text, or keyboard navigation in templates, components, or CSS, or needs usability evaluation of frontend code. For walking a live site's tasks in a browser, use review-usability. Only reports findings with confidence >= 7/10.
---

# Accessibility and Usability Fitness Review

Analyze frontend code (HTML, CSS, JavaScript, templates, components) for accessibility and usability fitness against WCAG 2.1 AA baseline and usability best practices.

Reference: [Fundamentals of Software Accessibility](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-accessibility/), [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/), [Fundamentals of Color and Contrast](https://jeffbailey.us/blog/2025/12/05/fundamentals-of-color-and-contrast/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

- `references/rubric.md` is the scoring source: severity levels, 1-10 anchors per dimension, N/A rules, and the Overall formula. Read it first; it is short. Scores taken from it are repeatable; improvised ones are not.
- `references/checklist.md` is what to check, file by file, with the WCAG thresholds.
- `scripts/contrast.py` computes contrast ratios. Every ratio in a report comes from it, because guessed ratios are the most common wrong number in accessibility reviews.
- `references/wisdom.md` is optional background, auto-generated from the three articles above (about 2,500 lines). Grep it by heading for a specific question (`grep -n "^#" references/wisdom.md`); never read it whole.

## Configuration

Invoke the resolver CLI to obtain effective weights and thresholds for the review target. Never load `fitness-config.json` directly.

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/fitness-config.py" show --path <target>
```

`${CLAUDE_SKILL_DIR}` is this skill's directory; the resolver ships two levels up in the plugin's `scripts/`. If your agent does not expand the variable, substitute the directory containing this `SKILL.md`.

Where `<target>` is the file or directory under review. The CLI walks up to discover any module override and merges it with the root config. Copy its `Config:` and `Effective weights:` lines into the report header (the template has the slots) as the provenance trail (AC-03.1, AC-08.2). Those weights rank the ten review domains for review-full; they do not weight the seven dimensions here. Use `statusThresholds` from the `effective` JSON block (between `<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->` and `<!-- END_EFFECTIVE_CONFIG_JSON -->`) for the status band when present.

## Modes

- **Full review** (default): all seven dimensions over the frontend surface or the diff.
- **Focused review**: the user asks one thing, such as "check color contrast", "are my images missing alt text", or "can this menu be used by keyboard". Score only the dimension(s) asked about, mark the rest `N/A — not requested`, and answer the question in `## Direct Answer`. Skip steps that cannot affect the answer. A focused run is never a full audit, so it always writes to a scoped report path (see Output Format).

## Workflow

1. **Load the rubric** — Read `references/rubric.md` and `references/checklist.md`. Run the resolver.

2. **Identify scope** — Find the HTML templates, JSX/TSX/Vue/Svelte components, CSS, and UI JavaScript. Review changed files for a diff, the named files when the user names them, otherwise the whole frontend. Note context that lives outside scope but decides a finding (base layout with the skip link, theme files that define color tokens) and read just enough of it to reach confidence 7.

3. **Decide applicability** — For each dimension, decide whether anything in scope can show it. Mark the rest `N/A — <reason>` using the rubric's N/A rules. A placeholder score skews the Overall here and the domain average in review-full.

4. **Run the checklist** — Evaluate each file against `references/checklist.md`. Record file:line evidence for every finding. Alt text and other text alternatives belong to Screen Reader Support (what assistive technology announces), not Semantic HTML; score a missing alt once, there.

5. **Compute contrast** — When Color and Contrast applies, run the script over every stylesheet that defines or overrides the color tokens (theme and framework files included, read-only), so `var()` chains resolve:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/contrast.py" css <css and template files...> --fails-only
   python3 "${CLAUDE_SKILL_DIR}/scripts/contrast.py" css <css files...> --pair=--muted:--card   # extra token pairs
   python3 "${CLAUDE_SKILL_DIR}/scripts/contrast.py" pair '#6b5a80' '#ffffff'                # literal colors
   ```

   Template and HTML files are read for inline `<style>` blocks. `--fails-only` still prints unresolved (`UNRES`) rows and a per-theme count, because an unchecked pair is not a pass. It reports each theme (base/light, dark, others it finds) separately, merges theme overrides per selector, checks text at 4.5:1 and borders/outlines at 3:1, and flags `outline: none`. Add `:3` to a `--pair` for a non-text check (focus backgrounds, icons). Rows marked `(page)` assume the element sits on the page background; when a rule repaints part of the page (a `.list` or card background), add `--pair` rows for the tokens drawn on it. `text?` rows are tokens that may never be used as text: confirm in the markup. When the markup or theme that would confirm a row is not available, report it only if the token's role is clear from its name or a comment, say in the finding that usage was not verified, and keep confidence at 7. `UNRES` means the script could not resolve a value (gradient, `currentColor`, `color-mix()`); check it by hand or leave it out. For colors in markup (inline styles, utility classes), resolve the hex values and use `pair`. Quote the ratio the script printed.

6. **Score each dimension** — Use the anchors in `references/rubric.md`. A score needs file:line evidence from the code.

7. **Identify patterns** — Systemic issues (a shared partial, a design token, a global CSS rule) are one finding listing every location, ranked above one-off issues.

8. **Self-check, then write** — Before writing: every file:line exists and says what the finding claims; every finding has confidence >= 7; every ratio came from the script; the Overall equals the stated computation; any CRITICAL caps it at 4.0. Then write the report.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

Severity levels (CRITICAL, HIGH, MEDIUM, LOW) with WCAG-mapped examples are defined in `references/rubric.md`.

## Scoring Dimensions (1-10 each)

Anchors for each band are in `references/rubric.md`; what to check is in `references/checklist.md`.

1. **Semantic HTML** — Heading hierarchy, landmark elements, form labels, correct element types, table structure
2. **Keyboard Navigation** — Tab order, focus indicators, skip links, focus trapping in modals, keyboard patterns for custom widgets
3. **Screen Reader Support** — Alt text and other text alternatives, accessible names, ARIA roles and states, live regions, error linking, hidden content management
4. **Color and Contrast** — Text contrast ratios, UI component contrast, color-independent information, focus indicator contrast, system preference respect
5. **Progressive Enhancement** — Core functionality without JS, standard form submission fallbacks, media fallbacks, prefers-reduced-motion support
6. **Responsive Design** — Viewport meta, relative units, zoom support, touch targets, breakpoint handling, text readability at all sizes
7. **Usability Heuristics** — Nielsen's 10 heuristics: system status visibility, real-world match, user control, consistency, error prevention, recognition over recall, flexibility, minimalist design, error recovery, help and documentation

## Output Format

Write the report to `docs/accessibility-review.md` at the root of the repository that contains the target, unless the user gives a path. For a review scoped to a subdirectory or a file set, or a focused review, write `docs/accessibility-review-<scope-slug>.md` instead, where the slug is the focused topic or the scope's directory/file names in kebab-case, at most 40 characters (for example `docs/accessibility-review-color-contrast.md` or `docs/accessibility-review-layouts-partials.md`), so a partial run never replaces the whole-repo report that review-full reads.

```markdown
# Accessibility and Usability Review

**Target:** <path(s) or scope reviewed; "focused: <topic>" for a focused review>
Config: <copied from resolver output>
Effective weights: <copied from resolver output>

## Direct Answer

(Whenever the user asked a specific question, in either mode — "what fails AA?", "is the contrast OK?": answer it in 1-3 sentences, with the numbers. Omit the section otherwise.)

## Summary

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Semantic HTML | X/10 or N/A — reason | ... |
| Keyboard Navigation | X/10 or N/A — reason | ... |
| Screen Reader Support | X/10 or N/A — reason | ... |
| Color/Contrast | X/10 or N/A — reason | ... |
| Progressive Enhancement | X/10 or N/A — reason | ... |
| Responsive Design | X/10 or N/A — reason | ... |
| Usability Heuristics | X/10 or N/A — reason | ... |
| **Overall** | **X.X/10** (status) | Mean of <dimensions scored>; capped at 4.0 if any CRITICAL |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **WCAG:** [success criterion, e.g. 1.4.3 Contrast (Minimum)]
- **Location:** file:line (every location, for systemic issues)
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found (and the computed ratio, for contrast).
- **Impact:** What users are affected and how.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

## Contrast Table

(When Color/Contrast was scored: the failing pairs and the main text pairs per theme, copied from contrast.py output: theme, foreground, background, ratio, required, result, file:line. List UNRES pairs as "not verified".)

## Dimension Details

### [Dimension Name] (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

### ...

## Top Action Items (by impact, up to 5)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full accessibility checklist used in this review.

## Reference

Based on [Fundamentals of Software Accessibility](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-accessibility/), [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/), [Fundamentals of Color and Contrast](https://jeffbailey.us/blog/2025/12/05/fundamentals-of-color-and-contrast/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Prioritize action items by: severity of user impact, number of users affected, and effort to fix. Systemic issues rank above one-off issues. Fewer than five is fine.

WCAG 2.1 AA is the baseline standard. Note any findings that would additionally meet or fail AAA criteria, but do not require AAA for a passing score.
