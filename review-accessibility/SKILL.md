---
name: review-accessibility
description: Reviews frontend code for accessibility and usability fitness, scoring across semantic HTML, keyboard navigation, screen reader support, color/contrast, progressive enhancement, responsive design, and usability heuristics. Use when the user says /review:accessibility, requests an accessibility audit, asks for a11y review, wants WCAG compliance check, or needs usability evaluation of frontend code. Only reports findings with confidence >= 7/10.
---

# Accessibility and Usability Fitness Review

Analyze frontend code (HTML, CSS, JavaScript, templates, components) for accessibility and usability fitness against WCAG 2.1 AA baseline and usability best practices.

## Workflow

1. **Identify scope** -- Determine which files to review. Use Grep/Glob to find HTML templates, JSX/TSX components, CSS files, and JavaScript files that produce UI output. Focus on changed files if reviewing a diff, otherwise review the full frontend surface.

2. **Run the checklist** -- Evaluate each file against the accessibility checklist at `references/checklist.md`. Record specific file:line evidence for every finding.

3. **Score each dimension** -- Rate each of the seven dimensions on a 1-10 scale using the rubric below. A score requires evidence from the code.

4. **Identify patterns** -- Look for systemic issues (repeated across multiple files) versus one-off problems. Systemic issues get higher priority.

5. **Produce the report** -- Write a structured report with scores, evidence, and prioritized action items.

## Confidence and Severity

### Confidence Threshold

Only report findings with confidence >= 7/10. For each finding, assess:
- Is this a real pattern in the code, not a guess about runtime behavior?
- Can you point to a specific file and line?
- Is the problematic pattern actually reachable in normal execution?

If any answer is no, do not report it. It is better to miss a theoretical issue than to flood the report with noise.

### Severity Levels

- **CRITICAL** -- Complete barrier preventing users from accessing content or functionality. Missing alt text on informational images, no keyboard access to primary navigation, form inputs with no labels, focus trap with no escape.
- **HIGH** -- Significant barrier affecting a large group of users under realistic conditions. Missing skip links, color-only status indicators, missing ARIA states on interactive widgets, touch targets below 44px on primary actions.
- **MEDIUM** -- Partial barrier affecting some users under specific conditions. Inconsistent heading hierarchy, missing aria-live for dynamic content, contrast ratios slightly below thresholds, incomplete responsive design at certain breakpoints.
- **LOW** -- Enhancement opportunities. Additional ARIA landmarks, improved focus indicator styling, better error message specificity, progressive enhancement for edge cases.

## Scoring Dimensions (1-10 each)

Score meanings:
- **1-3**: Major gaps, significant barriers to users
- **4-6**: Partial implementation, some barriers remain
- **7-8**: Solid implementation, minor issues only
- **9-10**: Exemplary, could serve as a reference implementation

### 1. Semantic HTML

What to check:
- Heading hierarchy (h1-h6) follows logical order without skipping levels
- Landmark elements used correctly (header, nav, main, article, section, aside, footer)
- Form inputs have associated label elements connected via `for` attribute or wrapping
- Lists use ul/ol/li, not styled divs
- Buttons are `<button>`, not clickable divs or spans
- Links are `<a>` with meaningful href, not divs with click handlers
- Images have appropriate alt text (descriptive for informative, empty for decorative)
- Tables use th, caption, and scope for data tables

Good looks like: Semantic elements used consistently. Assistive tech can build a meaningful accessibility tree from the HTML alone.

Bad looks like: Div soup. Headings chosen for visual size rather than document structure. Interactive elements built from generic elements with click handlers. Missing or placeholder alt text.

### 2. Keyboard Navigation

What to check:
- All interactive elements reachable via Tab key (natural tab order follows visual order)
- No use of tabindex > 0 (disrupts natural tab order)
- Focus indicators visible on all focusable elements (outline not removed without replacement)
- Skip links present to bypass navigation
- Modals trap focus within the dialog and return focus to the trigger on close
- Custom widgets support expected keyboard patterns (arrow keys for menus, Escape to close)
- No mouse-only interactions (hover-only tooltips, drag-only interfaces without alternatives)

Good looks like: A user can complete all tasks using only the keyboard. Focus is always visible and moves logically.

Bad looks like: Focus disappears into invisible elements. Tab order jumps unpredictably. Modals allow focus to escape behind them. Interactive elements only respond to mouse events.

### 3. Screen Reader Support

What to check:
- ARIA roles used only when no semantic HTML equivalent exists
- ARIA labels (aria-label, aria-labelledby) provide clear text for elements without visible labels
- ARIA states (aria-expanded, aria-selected, aria-checked, aria-hidden) stay synchronized with visual state via JavaScript
- Dynamic content updates announced via aria-live regions (polite for non-urgent, assertive for urgent)
- Form errors linked to inputs via aria-describedby
- No conflicting ARIA (e.g., role="button" on a `<button>`)
- Hidden content properly managed (aria-hidden="true" for decorative elements, not for content)

Good looks like: A screen reader user can understand the page structure, identify all interactive elements, and receive feedback on state changes.

Bad looks like: ARIA attributes scattered without purpose. Dynamic content changes silently. Errors appear visually but are not announced. Redundant ARIA on native semantic elements.

### 4. Color and Contrast

What to check:
- Normal text (under 18pt/14pt bold) meets 4.5:1 contrast ratio against background
- Large text (18pt+ or 14pt+ bold) meets 3:1 contrast ratio
- UI components (button borders, input borders, focus rings) meet 3:1 contrast against adjacent colors
- Information is never conveyed by color alone (error states use icons/text alongside red)
- Links distinguishable from surrounding text by more than color (underline or 3:1 contrast plus non-color indicator)
- Focus indicators meet 3:1 contrast
- Dark mode and light mode both tested for contrast compliance
- CSS does not override system preferences without user opt-in (prefers-color-scheme, prefers-contrast)

Good looks like: All text is readable in all themes. Status indicators combine color with text, icons, or patterns. Contrast ratios are verifiable in the CSS values.

Bad looks like: Light gray on white. Color-only status indicators. Focus rings removed with `outline: none` and no replacement. Hardcoded colors that ignore user preferences.

### 5. Progressive Enhancement

What to check:
- Core content and navigation work without JavaScript enabled
- Forms submit via standard HTML form submission when JS fails
- Links navigate via href, not JavaScript-only routing for critical paths
- CSS provides usable layout without JS-generated classes
- Images, video, and media have fallback content
- No critical functionality gated behind a specific browser or feature without fallback
- Animations respect `prefers-reduced-motion` media query

Good looks like: Disabling JavaScript degrades the experience gracefully. The page is still navigable and content is accessible. Media queries handle user preferences.

Bad looks like: Blank page without JavaScript. Forms that do nothing without JS. Content only accessible via JS-powered navigation. Animations that cannot be disabled.

### 6. Responsive Design

What to check:
- Viewport meta tag present with `width=device-width, initial-scale=1.0`
- Layouts use relative units (%, em, rem, vw, vh) not fixed pixel widths for containers
- Content readable and functional at 200% browser zoom
- Touch targets at least 44x44px on mobile
- No horizontal scrolling at standard breakpoints
- Media queries handle common breakpoints
- Text line length constrained (max-width ~65ch) to prevent overly long lines on wide screens
- Font sizes use rem or em, not fixed px for body text

Good looks like: The interface works across phone, tablet, and desktop. Zooming to 200% does not break layout or hide content. Text remains readable at all viewport sizes.

Bad looks like: Fixed-width layouts that overflow on mobile. Tiny touch targets. Text that becomes unreadable or gets cut off when zoomed. No viewport meta tag.

### 7. Usability Heuristics

What to check against Nielsen's 10 heuristics:
- **Visibility of system status**: Loading states, progress indicators, success/error feedback present
- **Match between system and real world**: Labels use user vocabulary, not internal jargon
- **User control and freedom**: Undo available for destructive actions, easy exit from flows
- **Consistency and standards**: Same patterns used for same actions throughout the interface
- **Error prevention**: Confirmation dialogs for destructive actions, input validation before submission, disabled states for invalid forms
- **Recognition over recall**: Options visible, not hidden in deep menus; contextual help available
- **Flexibility and efficiency**: Keyboard shortcuts for power users, bulk operations where appropriate
- **Aesthetic and minimalist design**: No unnecessary elements, clear visual hierarchy, appropriate use of whitespace
- **Help users recognize, diagnose, and recover from errors**: Error messages are specific, actionable, and suggest a fix
- **Help and documentation**: Contextual help, tooltips, and documentation are available when needed

Good looks like: The interface is learnable, efficient, memorable, and satisfying. Error states are handled gracefully with clear recovery paths.

Bad looks like: No loading indicators. Inconsistent button labels. Destructive actions without confirmation. Error messages that say "Invalid input" without explanation.

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

Based on guidance from https://jeffbailey.us/categories/fundamentals/
```

Prioritize action items by: severity of user impact, number of users affected, and effort to fix. Systemic issues rank above one-off issues.

WCAG 2.1 AA is the baseline standard. Note any findings that would additionally meet or fail AAA criteria, but do not require AAA for a passing score.
