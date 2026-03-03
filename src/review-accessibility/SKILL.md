---
name: review-accessibility
description: Reviews frontend code for accessibility and usability fitness, scoring across semantic HTML, keyboard navigation, screen reader support, color/contrast, progressive enhancement, responsive design, and usability heuristics. Use when the user says /review:accessibility, requests an accessibility audit, asks for a11y review, wants WCAG compliance check, or needs usability evaluation of frontend code. Only reports findings with confidence >= 7/10.
---

# Accessibility and Usability Fitness Review

Analyze frontend code (HTML, CSS, JavaScript, templates, components) for accessibility and usability fitness against WCAG 2.1 AA baseline and usability best practices.

Reference: [Fundamentals of Software Accessibility](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-accessibility/), [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/), [Fundamentals of Color and Contrast](https://jeffbailey.us/blog/2025/12/05/fundamentals-of-color-and-contrast/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

For detailed scoring rubrics, severity definitions, what-good-looks-like / what-bad-looks-like criteria, and domain expertise, read `references/wisdom.md` before scoring. That file is auto-generated from:

- [Fundamentals of Software Accessibility](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-accessibility/)
- [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/)
- [Fundamentals of Color and Contrast](https://jeffbailey.us/blog/2025/12/05/fundamentals-of-color-and-contrast/)

Use the wisdom reference when evaluating code and assigning dimension scores.

## Workflow

1. **Read domain knowledge** — Read `references/wisdom.md` to load scoring rubrics, thresholds, and severity definitions.

2. **Identify scope** — Determine which files to review. Use Grep/Glob to find HTML templates, JSX/TSX components, CSS files, and JavaScript files that produce UI output. Focus on changed files if reviewing a diff, otherwise review the full frontend surface.

3. **Run the checklist** — Evaluate each file against the accessibility checklist at `references/checklist.md`. Record specific file:line evidence for every finding.

4. **Score each dimension** — Rate each of the seven dimensions on a 1-10 scale. Apply the rubrics/thresholds from the wisdom reference. A score requires evidence from the code.

5. **Identify patterns** — Look for systemic issues (repeated across multiple files) versus one-off problems. Systemic issues get higher priority.

6. **Produce the report** — Write a structured report with scores, evidence, and prioritized action items.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

For severity level definitions (CRITICAL, HIGH, MEDIUM, LOW) with domain-specific examples, consult `references/wisdom.md`.

## Scoring Dimensions (1-10 each)

Dimensions to score (detailed rubrics including what-to-check, what-good-looks-like, and what-bad-looks-like are in `references/wisdom.md`):

1. **Semantic HTML** — Heading hierarchy, landmark elements, form labels, correct element types, alt text, table structure
2. **Keyboard Navigation** — Tab order, focus indicators, skip links, focus trapping in modals, keyboard patterns for custom widgets
3. **Screen Reader Support** — ARIA roles, labels, states, live regions, error linking, hidden content management
4. **Color and Contrast** — Text contrast ratios, UI component contrast, color-independent information, focus indicator contrast, system preference respect
5. **Progressive Enhancement** — Core functionality without JS, standard form submission fallbacks, media fallbacks, prefers-reduced-motion support
6. **Responsive Design** — Viewport meta, relative units, zoom support, touch targets, breakpoint handling, text readability at all sizes
7. **Usability Heuristics** — Nielsen's 10 heuristics: system status visibility, real-world match, user control, consistency, error prevention, recognition over recall, flexibility, minimalist design, error recovery, help and documentation

## Output Format

Write the report to `docs/accessibility-review.md` with this structure:

```markdown
# Accessibility and Usability Review

## Summary

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Semantic HTML | X/10 | ... |
| Keyboard Navigation | X/10 | ... |
| Screen Reader Support | X/10 | ... |
| Color/Contrast | X/10 | ... |
| Progressive Enhancement | X/10 | ... |
| Responsive Design | X/10 | ... |
| Usability Heuristics | X/10 | ... |
| **Overall** | **X/10** | |

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [which scoring dimension]
- **Location:** file:line
- **Description:** What the issue is and why it matters.
- **Evidence:** The specific code pattern found.
- **Impact:** What users are affected and how.
- **Remediation:** Concrete fix with code example or specific steps.

(repeat for each finding, ordered by severity)

### [Dimension Name] (X/10)
- Evidence: file:line references
- Issues found
- Recommendations

### ...

## Top 5 Action Items (by impact)

1. [CRITICAL/HIGH/MEDIUM] Description -- file:line
2. ...

## Checklist Reference

See references/checklist.md for the full accessibility checklist used in this review.

## Reference

Based on [Fundamentals of Software Accessibility](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-accessibility/), [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/), [Fundamentals of Color and Contrast](https://jeffbailey.us/blog/2025/12/05/fundamentals-of-color-and-contrast/), and guidance from https://jeffbailey.us/categories/fundamentals/
```

Prioritize action items by: severity of user impact, number of users affected, and effort to fix. Systemic issues rank above one-off issues.

WCAG 2.1 AA is the baseline standard. Note any findings that would additionally meet or fail AAA criteria, but do not require AAA for a passing score.
