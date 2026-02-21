# Accessibility and Usability Checklist

This checklist is used by the review-accessibility skill to evaluate frontend code. It is derived from the following source articles:

- [Fundamentals of Software Accessibility](https://jeffbailey.us/blog/2025/11/30/fundamentals-of-software-accessibility/)
- [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/)
- [Fundamentals of Frontend Engineering](https://jeffbailey.us/blog/2025/11/26/fundamentals-of-frontend-engineering/)
- [Fundamentals of Color and Contrast](https://jeffbailey.us/blog/2025/12/05/fundamentals-of-color-and-contrast/)
- [Fundamentals of the Web](https://jeffbailey.us/blog/2026/01/05/fundamentals-of-the-web/)
- [Fundamentals of Software User Experience](https://jeffbailey.us/blog/2024/01/25/fundamentals-of-software-user-experience/)
- [Fundamentals of Typography](https://jeffbailey.us/blog/2026/01/17/fundamentals-of-typography/)

Baseline standard: WCAG 2.1 Level AA.

---

## 1. Semantic HTML

### Document Structure
- [ ] HTML document has `lang` attribute on the `<html>` element
- [ ] One `<main>` element per page
- [ ] `<header>`, `<footer>`, `<nav>`, `<aside>` used for landmark regions
- [ ] `<article>` wraps self-contained content (blog posts, cards, comments)
- [ ] `<section>` groups thematically related content and has a heading

### Heading Hierarchy
- [ ] Exactly one `<h1>` per page
- [ ] Headings follow logical order (h1, h2, h3) without skipping levels
- [ ] Headings are used for structure, not for visual styling
- [ ] Screen readers can navigate by headings to build a document outline

### Forms
- [ ] Every `<input>`, `<select>`, and `<textarea>` has an associated `<label>`
- [ ] Labels connected via `for`/`id` attribute pairing, or by wrapping the input
- [ ] Appropriate input types used (`email`, `tel`, `url`, `number`, `search`)
- [ ] Required fields marked with `required` attribute and `aria-required="true"`
- [ ] Placeholder text does not replace labels
- [ ] Form groups use `<fieldset>` and `<legend>` where appropriate

### Interactive Elements
- [ ] Buttons are `<button>` elements, not `<div>` or `<span>` with click handlers
- [ ] Links are `<a>` elements with meaningful `href`
- [ ] No `<div role="button">` when `<button>` would work
- [ ] No `<div role="navigation">` when `<nav>` would work

### Images and Media
- [ ] Informative images have descriptive `alt` text that conveys meaning
- [ ] Decorative images have `alt=""` (empty alt attribute)
- [ ] Complex images (charts, diagrams) have extended descriptions
- [ ] `<img>` elements never omit the `alt` attribute entirely
- [ ] Video has captions; audio has transcripts

### Lists and Tables
- [ ] Ordered and unordered lists use `<ol>`/`<ul>` with `<li>`, not styled divs
- [ ] Data tables use `<th>` with `scope` attribute for headers
- [ ] Data tables have `<caption>` describing the table content
- [ ] Layout tables are not used (use CSS grid/flexbox instead)

---

## 2. ARIA Usage

### The First Rule of ARIA
- [ ] ARIA is used only when no native HTML element provides the needed semantics
- [ ] No redundant ARIA on elements that already have native semantics (e.g., `role="button"` on `<button>`)
- [ ] ARIA does not conflict with native element semantics

### Roles
- [ ] `role="dialog"` or `role="alertdialog"` used on modal containers
- [ ] `role="alert"` used for important, time-sensitive messages
- [ ] `role="tab"`, `role="tabpanel"`, `role="tablist"` used correctly for tab interfaces
- [ ] `role="menu"` and `role="menuitem"` used only for actual application menus, not navigation

### Labels
- [ ] `aria-label` provides text for elements with no visible label (icon buttons, etc.)
- [ ] `aria-labelledby` references visible heading/label text where available
- [ ] `aria-describedby` links supplementary descriptions (hints, error messages) to inputs
- [ ] Navigation regions distinguished with `aria-label` when multiple `<nav>` elements exist

### States
- [ ] `aria-expanded` reflects open/closed state of collapsible sections and menus
- [ ] `aria-selected` reflects selection state in tab interfaces
- [ ] `aria-checked` reflects checked state for custom checkboxes/toggles
- [ ] `aria-disabled` reflects disabled state (in addition to visual disabled styling)
- [ ] `aria-hidden="true"` applied to purely decorative elements
- [ ] `aria-invalid="true"` set on inputs that fail validation
- [ ] All ARIA states kept in sync with visual state via JavaScript

### Live Regions
- [ ] `aria-live="polite"` used for non-urgent updates (search results, status messages)
- [ ] `aria-live="assertive"` used for urgent updates (error alerts, session warnings)
- [ ] `aria-atomic="true"` set when the entire region content should be announced
- [ ] Live regions exist in the DOM before content is injected (not dynamically created)

---

## 3. Keyboard Navigation

### Tab Order and Focus
- [ ] All interactive elements reachable via Tab key
- [ ] Tab order follows visual reading order (left-to-right, top-to-bottom)
- [ ] No `tabindex` values greater than 0
- [ ] `tabindex="0"` used only to add non-interactive elements to tab order when necessary
- [ ] `tabindex="-1"` used for programmatic focus management (e.g., moving focus to error messages)

### Focus Indicators
- [ ] Default browser focus outlines preserved, or replaced with equally visible custom styles
- [ ] `outline: none` never used without a visible alternative focus style
- [ ] Focus indicators meet 3:1 contrast ratio against surrounding colors
- [ ] Focus indicator style consistent across the interface

### Skip Links
- [ ] "Skip to main content" link is the first focusable element on the page
- [ ] Skip link target (`#main-content`) points to the `<main>` element or equivalent
- [ ] Skip link is visible when focused (can be visually hidden when not focused)

### Focus Management
- [ ] Modals: focus moves to the first focusable element inside the modal on open
- [ ] Modals: focus is trapped within the modal (Tab/Shift+Tab cycle within it)
- [ ] Modals: focus returns to the trigger element when the modal closes
- [ ] Modals: Escape key closes the modal
- [ ] Dropdown menus: arrow keys navigate within the menu
- [ ] Dropdown menus: Escape closes the menu and returns focus to the trigger
- [ ] Single-page apps: focus managed on route changes (moved to main content or page heading)
- [ ] Dynamically inserted content does not steal focus unexpectedly

### Keyboard Patterns for Widgets
- [ ] Tabs: arrow keys switch between tabs, Tab moves into the tab panel
- [ ] Accordions: Enter/Space toggles sections
- [ ] Carousels: arrow keys navigate between slides, with pause/stop controls
- [ ] Drag-and-drop: keyboard alternative provided (e.g., move up/down buttons)

---

## 4. Color and Contrast

### Text Contrast (WCAG 2.1 AA)
- [ ] Normal text (<18pt / <14pt bold): contrast ratio >= 4.5:1
- [ ] Large text (>=18pt / >=14pt bold): contrast ratio >= 3:1
- [ ] Text inside buttons, inputs, and other UI components meets the same ratios

### Non-Text Contrast (WCAG 2.1 AA)
- [ ] UI component boundaries (button borders, input borders): contrast ratio >= 3:1 against adjacent colors
- [ ] Graphical objects conveying information (icons, chart elements): contrast ratio >= 3:1
- [ ] Focus indicators: contrast ratio >= 3:1 against surrounding colors

### Color Independence
- [ ] Error states use icon and/or text in addition to red color
- [ ] Success states use icon and/or text in addition to green color
- [ ] Warning states use icon and/or text in addition to yellow/orange color
- [ ] Links distinguishable from body text by underline or 3:1 contrast plus non-color cue
- [ ] Charts and graphs use patterns, labels, or textures in addition to color
- [ ] Form validation feedback includes text message, not just border color change

### User Preferences
- [ ] `prefers-color-scheme` media query supported (or manual toggle available)
- [ ] `prefers-contrast` respected when applicable
- [ ] `prefers-reduced-motion` respected (see Progressive Enhancement section)
- [ ] Forced colors / high contrast mode does not break the layout

### Common Contrast Mistakes to Check
- [ ] No light gray (#999 or lighter) text on white backgrounds
- [ ] No placeholder text used as the only label (placeholders typically fail contrast)
- [ ] No low-contrast disabled states that make content unreadable
- [ ] Dark mode tested separately for contrast compliance

---

## 5. Progressive Enhancement

### Core Functionality Without JavaScript
- [ ] Page content visible without JavaScript
- [ ] Navigation links work without JavaScript (real `href` values)
- [ ] Forms submit to server-side endpoints without JavaScript
- [ ] No blank/empty page when JavaScript fails or is disabled

### Graceful Degradation
- [ ] JavaScript-enhanced features degrade to functional HTML equivalents
- [ ] CSS animations and transitions are enhancements, not requirements
- [ ] Third-party widget failures don't break the page

### Motion and Animation
- [ ] `@media (prefers-reduced-motion: reduce)` used to disable or reduce animations
- [ ] Essential motion (loading spinners) still present but simplified
- [ ] Auto-playing animations have pause/stop controls
- [ ] No seizure-inducing content (flashing more than 3 times per second)

### Browser and Device Support
- [ ] Feature detection used instead of browser detection (e.g., `'serviceWorker' in navigator`)
- [ ] Polyfills or fallbacks provided for critical features
- [ ] Content works without CSS custom properties (if targeting older browsers)

---

## 6. Responsive Design

### Viewport
- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1.0">` present
- [ ] No `user-scalable=no` or `maximum-scale=1` that prevents zooming

### Layout
- [ ] Containers use relative units (%, vw, rem) not fixed pixel widths
- [ ] CSS Grid or Flexbox used for layout, not floats or absolute positioning for page structure
- [ ] No horizontal scrollbar at any standard breakpoint (320px to 1920px)
- [ ] Content reflows properly at 320px viewport width (WCAG 1.4.10 Reflow)

### Zoom
- [ ] Content readable and functional at 200% browser zoom
- [ ] No content or functionality lost at 200% zoom
- [ ] Text does not overflow containers when zoomed
- [ ] No fixed-height containers that clip text when font size increases

### Typography
- [ ] Body text at least 16px (1rem) base size
- [ ] Line height 1.4-1.6 for body text
- [ ] Line length constrained to 45-75 characters (max-width ~65ch)
- [ ] Font sizes use rem or em, allowing user font-size preferences to take effect
- [ ] Heading hierarchy provides clear visual distinction at all viewport sizes

### Touch and Interaction
- [ ] Touch targets at least 44x44px
- [ ] Adequate spacing between touch targets to prevent mis-taps
- [ ] Hover-dependent interactions have touch-friendly alternatives
- [ ] No functionality available only on hover (tooltips need focus trigger too)

---

## 7. Usability Heuristics (Nielsen's 10)

### 1. Visibility of System Status
- [ ] Loading states shown during async operations (spinners, skeletons, progress bars)
- [ ] Success confirmation after form submissions and destructive actions
- [ ] Error states clearly displayed with actionable messages
- [ ] Progress indicators for multi-step processes

### 2. Match Between System and Real World
- [ ] Labels and copy use language the user understands (not internal jargon)
- [ ] Icons match conventional meanings (trash for delete, magnifying glass for search)
- [ ] Information organized in a natural, logical order

### 3. User Control and Freedom
- [ ] Undo available for reversible actions
- [ ] Cancel option available in multi-step flows
- [ ] Easy way to exit or go back from any state
- [ ] No trapped states where the user cannot navigate away

### 4. Consistency and Standards
- [ ] Same terminology for same concepts throughout the interface
- [ ] Same interaction patterns for same actions (all "delete" buttons behave the same)
- [ ] Visual patterns consistent (button styles, form layouts, spacing)
- [ ] Follows platform conventions (standard link styles, button placement)

### 5. Error Prevention
- [ ] Confirmation dialogs before destructive actions (delete, overwrite, submit)
- [ ] Input constraints prevent invalid data (type="email", maxlength, pattern)
- [ ] Disabled submit buttons until required fields are completed
- [ ] Real-time validation for fields with specific format requirements

### 6. Recognition Rather Than Recall
- [ ] Important actions visible, not buried in deep menus
- [ ] Recent items, suggestions, or defaults reduce memory burden
- [ ] Contextual help and hints available where needed
- [ ] Navigation structure is discoverable without documentation

### 7. Flexibility and Efficiency of Use
- [ ] Keyboard shortcuts available for frequent actions
- [ ] Bulk operations available where users handle multiple items
- [ ] Power-user features available without penalizing new users
- [ ] Smart defaults reduce the number of decisions required

### 8. Aesthetic and Minimalist Design
- [ ] No unnecessary visual elements that don't serve a purpose
- [ ] Clear visual hierarchy through size, weight, color, and spacing
- [ ] Adequate whitespace for visual breathing room
- [ ] Content density appropriate for the use case

### 9. Help Users Recognize, Diagnose, and Recover from Errors
- [ ] Error messages state what went wrong in plain language
- [ ] Error messages suggest how to fix the problem
- [ ] Errors linked to the specific field that caused them (via aria-describedby)
- [ ] Form errors don't clear already-entered valid data

### 10. Help and Documentation
- [ ] Inline help or tooltips for complex fields
- [ ] Contextual guidance where users are likely to need it
- [ ] Error recovery documentation accessible from error states

---

## Common Accessibility Mistakes (Quick Reference)

These are the most frequently encountered a11y problems, compiled from the source articles:

| Mistake | What's wrong | Fix |
|---------|-------------|-----|
| Missing alt text | `<img src="chart.png">` | Add `alt="Sales increased 25% from Q1 to Q2"` |
| Clickable div | `<div onclick="submit()">Submit</div>` | Replace with `<button type="submit">Submit</button>` |
| Missing form label | `<input placeholder="Name">` | Add `<label for="name">Name</label>` before input |
| Low contrast | `color: #999` on `background: #fff` (2.84:1) | Use `color: #333` (12.63:1) |
| Removed focus outline | `*:focus { outline: none }` | Provide visible custom focus style |
| Silent dynamic update | `div.textContent = 'Saved'` | Add `aria-live="polite"` to the container |
| ARIA overuse | `<div role="button" tabindex="0">` | Replace with `<button>` |
| Color-only error | Red border on invalid input | Add error icon + text message + `aria-invalid` |
| Skipped heading | h1 followed directly by h3 | Use h2 for the intermediate level |
| Mouse-only interaction | Hover-only tooltip | Add focus trigger and keyboard dismiss |
| No skip link | Users must tab through all nav links | Add `<a href="#main-content" class="skip-link">Skip to main content</a>` |
| Modal focus escape | Tab exits the modal to background content | Implement focus trapping within the modal |
| Fixed-width layout | `width: 1200px` | Use `max-width: 1200px; width: 100%` |
| Zoom breakage | Content overflows at 200% zoom | Use relative units, test at 200% zoom |
| Motion sickness risk | Persistent animations without opt-out | Add `@media (prefers-reduced-motion: reduce)` |

---

## WCAG 2.1 AA Quick Reference

### Contrast Ratios

| Element | Minimum Ratio |
|---------|--------------|
| Normal text (<18pt / <14pt bold) | 4.5:1 |
| Large text (>=18pt / >=14pt bold) | 3:1 |
| UI components (borders, focus rings) | 3:1 |
| Graphical objects | 3:1 |

### For AAA (enhanced, not required)

| Element | Minimum Ratio |
|---------|--------------|
| Normal text | 7:1 |
| Large text | 4.5:1 |

### Key WCAG 2.1 AA Success Criteria

- 1.1.1 Non-text Content: alt text for images
- 1.3.1 Info and Relationships: semantic structure
- 1.4.3 Contrast (Minimum): 4.5:1 / 3:1
- 1.4.4 Resize Text: usable at 200% zoom
- 1.4.10 Reflow: no horizontal scroll at 320px width
- 1.4.11 Non-text Contrast: 3:1 for UI components
- 1.4.13 Content on Hover or Focus: dismissible, hoverable, persistent
- 2.1.1 Keyboard: all functionality available via keyboard
- 2.1.2 No Keyboard Trap: user can navigate away from all components
- 2.4.1 Bypass Blocks: skip navigation mechanism
- 2.4.3 Focus Order: logical and predictable
- 2.4.6 Headings and Labels: descriptive
- 2.4.7 Focus Visible: focus indicator always visible
- 2.5.5 Target Size: at least 44x44px (AAA, but recommended for AA)
- 3.1.1 Language of Page: lang attribute on html element
- 3.3.1 Error Identification: errors described in text
- 3.3.2 Labels or Instructions: input purpose clear
- 4.1.2 Name, Role, Value: custom widgets expose name, role, and state

---

## Testing Tools Reference

### Automated
- axe DevTools (browser extension)
- WAVE (browser extension)
- Lighthouse (Chrome DevTools)
- eslint-plugin-jsx-a11y (for React projects)
- axe-core (CI/CD integration)

### Manual
- Keyboard-only navigation test (Tab, Shift+Tab, Enter, Space, Escape, arrows)
- VoiceOver (macOS: Cmd+F5), NVDA (Windows, free), JAWS (Windows)
- WebAIM Contrast Checker
- Color Oracle / Sim Daltonism (color blindness simulation)
- Browser zoom to 200%
- Disable JavaScript and verify core functionality
- Enable `prefers-reduced-motion` in OS settings
