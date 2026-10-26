# Accessibility Scoring Rubric

Hand-maintained scoring rubric. sync-wisdom does not regenerate this file.

Baseline: WCAG 2.1 AA. AAA and WCAG 2.2 items are recommendations: they can lower a score by at most one point and are never above LOW severity. Thresholds below match `checklist.md`; if the two ever disagree, this file wins and checklist.md should be fixed.

## Severity

| Level | Definition | Examples |
|-------|-----------|----------|
| CRITICAL | A whole task is impossible for a group of users, with no workaround. | Modal or widget traps keyboard focus (2.1.2); the only submit/checkout control is a `<div onclick>` with no keyboard access (2.1.1) |
| HIGH | A WCAG A/AA failure on core content or a primary flow; users can get through only with real effort or help. | Informative `<img>` with no `alt` (1.1.1); body or link text below 4.5:1 (1.4.3); `outline: none` with no visible replacement (2.4.7) |
| MEDIUM | A WCAG A/AA failure on secondary content, or a partial failure with a workaround. | Heading levels skip h2 to h4 (1.3.1); disclosure button without `aria-expanded` (4.1.2); focus ring or input border below 3:1 (1.4.11) |
| LOW | Best practice, AAA, or WCAG 2.2 recommendation; no AA failure. | Touch target 24-43px (2.5.5 AAA); redundant `role="button"` on `<button>`; line length over 80ch |

Contrast severity: rate a failure by what the pair carries and where. Body, link, or metadata text in the default state is HIGH. Text that appears only in a state (hover, active, selected) or on a secondary control is MEDIUM. Icon-only controls are non-text, so judge them at 3:1 rather than 4.5:1. A focus indicator under 3:1 is MEDIUM; if it is the only focus cue, it is HIGH (2.4.7).

A pattern repeated across files (shared partial, design token, global CSS rule) is one finding with every location listed, and ranks above one-off issues of the same severity. Reach raises the action-item rank, not the severity: a missing `alt` in a partial on every page is still one HIGH finding. Severity sets the band: count findings, not locations.

## Dimension anchors

Score what is in scope. Each band names the worst thing allowed in it; a target lands in the highest band whose conditions all hold.

### 1. Semantic HTML
Landmarks, headings, form labels, element choice, lists and tables. (Alt text is scored under Screen Reader Support.)
- **9-10:** `lang` on `<html>`, one `<main>`, landmarks for header/nav/footer, one h1 and no skipped levels, every input has a `<label>`, native elements for buttons and links, data tables have `<th scope>`.
- **7-8:** One or two MEDIUM issues (a skipped heading level, a list built from divs), no HIGH.
- **5-6:** One HIGH finding (an unlabeled input, a clickable div; one shared partial counts once) or 3+ MEDIUM findings.
- **3-4:** Two or more distinct HIGH findings, or no landmarks at all.
- **1-2:** Div soup: interactive elements and structure carry no semantics anywhere in scope.

### 2. Keyboard Navigation
Reachability, focus visibility, order, skip link, focus management in widgets.
- **9-10:** Every control is a native focusable element or has `tabindex="0"` plus key handlers; visible focus style on all of them; no `tabindex` > 0; skip link first; modals trap and return focus and close on Escape.
- **7-8:** Minor gaps: a weak but visible focus style, a missing skip link where headings and landmarks exist.
- **5-6:** One HIGH: `outline: none`/`0` without replacement on some controls, or one custom widget without key handlers.
- **3-4:** Focus removed globally (`*:focus { outline: none }`) or several mouse-only controls.
- **1-2:** Any CRITICAL keyboard trap, or primary actions unreachable by keyboard.

### 3. Screen Reader Support
Text alternatives, accessible names, ARIA roles/states, live regions, hidden content.
- **9-10:** Informative images have meaningful `alt`, decorative ones `alt=""` or `aria-hidden`; icon-only controls have an accessible name; ARIA states (`aria-expanded`, `aria-invalid`) stay in sync; dynamic updates use a live region that exists before content is injected.
- **7-8:** One or two MEDIUM issues (vague alt such as "image", a stale `aria-expanded`), no HIGH.
- **5-6:** One HIGH: an informative `<img>` with no `alt`, an icon button with no name, or form errors not linked with `aria-describedby`.
- **3-4:** Two or more distinct HIGH findings, or ARIA misuse hides real content (`aria-hidden` on focusable elements).
- **1-2:** Core content or controls are unannounced or misannounced throughout.

### 4. Color and Contrast
Use `scripts/contrast.py` ratios; never estimate a ratio. Text needs 4.5:1 (3:1 if >=24px or >=18.66px bold); focus indicators, input borders, and meaningful icons need 3:1.
- **9-10:** Every computed text pair passes in every theme; non-text UI passes 3:1; no information by color alone; `prefers-color-scheme` or a toggle handled; dark theme checked.
- **7-8:** Only LOW/MEDIUM: a non-text pair under 3:1 where another cue identifies the control, or a secondary text pair between 4.0 and 4.5.
- **5-6:** One HIGH: a body, link, or muted-text token under 4.5:1 in one theme, or a color-only state (red border as the only error cue).
- **3-4:** Several failing text pairs, or a failing token used across many components.
- **1-2:** Primary body text fails in the default theme.

### 5. Progressive Enhancement
Behavior without JS, motion preferences, fallbacks.
- **9-10:** Content and navigation work without JS (real `href`s, forms with `action`); animations wrapped in `prefers-reduced-motion`; media has fallbacks; feature detection, not UA sniffing.
- **7-8:** One gap, e.g. non-essential animation without a reduced-motion query.
- **5-6:** A secondary feature breaks without JS (a menu that never opens), or autoplaying motion with no pause control.
- **3-4:** Primary content is rendered only by JS with no server fallback.
- **1-2:** Blank page without JS, or flashing content over 3 times per second (2.3.1).

### 6. Responsive Design
Viewport, reflow, zoom, typography, touch targets.
- **9-10:** Viewport meta without `user-scalable=no`/`maximum-scale=1`; layout in relative units with flex/grid; reflows at 320px; font sizes in rem/em; touch targets at least 44x44px.
- **7-8:** Touch targets 24-43px, or isolated fixed px widths that do not cause horizontal scroll.
- **5-6:** One HIGH: fixed-width container or fixed-height text box that clips or scrolls horizontally at 320px or 200% zoom.
- **3-4:** Zoom blocked (`user-scalable=no`), or several fixed-width layouts.
- **1-2:** No viewport meta and a fixed desktop layout.

### 7. Usability Heuristics
Nielsen's 10 heuristics as visible in code: status feedback, error prevention and recovery, consistency, user control.
- **9-10:** Loading, success, and error states exist for async actions; destructive actions confirm or undo; error messages say what failed and how to fix it; consistent control patterns.
- **7-8:** One missing state (no loading indicator on one async action) or inconsistent labels.
- **5-6:** Errors are generic ("Something went wrong") or destructive actions have no confirm/undo.
- **3-4:** Users can lose entered data on error, or flows have no way back or out.
- **1-2:** Core flows give no feedback at all.

## Not applicable (N/A)

Mark a dimension `N/A — <reason>` when nothing in scope can show it, instead of guessing a number:
- Semantic HTML, Keyboard, Screen Reader: no markup in scope (HTML, templates, JSX/TSX, Vue, Svelte).
- Color and Contrast: no colors in scope (no CSS, inline styles, or utility classes), or every color in scope is a token defined outside it and contrast.py reports them all UNRES: `N/A — tokens defined in <file>, not in scope`. If only some pairs resolve, score those and list the unverified ones in the Key Finding.
- Progressive Enhancement: no scripts and no animation in scope.
- Responsive Design: no layout CSS and no document `<head>` in scope.
- Usability Heuristics: no interactive flow in scope (forms, async actions, destructive actions). Static display partials are usually N/A here.
- Focused mode: dimensions the user did not ask about are `N/A — not requested`.

When key evidence lives outside the scope (the skip link is in a base layout, the color tokens are in a theme file), say so in the Key Finding column and score only what you saw. Absence inside scope is evidence, but cite where it should be: `layouts/_default/baseof.html (no skip link)`, `assets/css/ (no prefers-reduced-motion query)`.

## Overall score

- Overall = mean of the scored (non-N/A) dimensions, one decimal. Name the dimensions averaged on the Overall line.
- Any CRITICAL finding caps Overall at 4.0.
- Status bands: a score at or above `statusThresholds.healthy[0]` is Healthy, at or above `statusThresholds.needsAttention[0]` is Needs Attention, anything lower is Critical (defaults 8 / 5 when the resolver gives none). Only the lower bounds count, so a fractional score such as 7.5 is Needs Attention, never a gap; review-full uses the same rule.
- The resolver's `Effective weights:` line weights the ten review domains in review-full; it does not weight these seven dimensions. Quote it for provenance only.
