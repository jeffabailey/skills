# Website Usability Checklist

This checklist is used by the review-usability skill to evaluate a running website. It turns the quick checks, failure signs, and common mistakes in the source article into observable checks on rendered pages:

- [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/)

The skill downloads the current article at run time. When an item here disagrees with the article, the article wins.

Mark each item as pass, fail, **N/A** (the site has no matching interaction), or **not verified** (it needs a browser tool you did not have). Every fail needs a URL and an element or task step.

---

## 0. Top Tasks

- [ ] 3 to 5 top tasks written down before walking any page
- [ ] Tasks come from real visitor data (analytics, Search Console, support questions) where available, not from what the site owner wants to promote
- [ ] Each task walked end to end at desktop (1280px) and phone (390px) widths
- [ ] Each task attempted by keyboard alone
- [ ] Steps, scroll depth, and dead ends recorded per task

## 1. Learnability — First-Time Use

### Familiar conventions
- [ ] Site name or logo in the top-left links to the home page
- [ ] Primary navigation sits where visitors expect (top, or a recognizable menu icon on phones)
- [ ] Search uses a magnifying-glass icon or a visible "Search" label
- [ ] Icons are standard; any custom icon also has a text label

### Discoverability
- [ ] Top tasks can be started from the home page without guessing
- [ ] Links look like links (underline, color, or both), and buttons look clickable
- [ ] Important features are not buried under several levels of menu (article Mistake 1: Hiding Important Features)
- [ ] Phone layout keeps navigation and search reachable; nothing a top task needs is hidden at narrow widths

### Orientation
- [ ] Every page tells visitors where they are (page title, breadcrumb, or highlighted navigation item)
- [ ] Page titles and headings describe the content, not the site's internal jargon
- [ ] Visitors landing deep from search (not on the home page) can tell what the site is and where to go next

## 2. Efficiency — Rapid Task Completion

### Getting to the answer
- [ ] The page's main answer or content starts within the first screen on phone and desktop
- [ ] Long pages have a table of contents or jump links
- [ ] Code samples, commands, and values can be copied in one action

### Navigation cost
- [ ] Top tasks finish in few steps; count them and note any avoidable ones
- [ ] Related content is linked from each content page, so visitors don't return to the home page to continue
- [ ] Categories, tags, or series pages group content the way visitors look for it

### Search
- [ ] Search returns relevant results for the site's top topics
- [ ] Results show enough context (title, excerpt) to choose without opening each one
- [ ] Search is reachable in one action from every page

### Keyboard and speed
- [ ] Every top task can be completed by keyboard; focus is visible throughout (article Mistake 4: No Keyboard Shortcuts)
- [ ] A keyboard shortcut opens search, if the site has search (common convention: `/` or `Ctrl+K`)
- [ ] Pages feel fast: content visible quickly, no long blank waits on a typical connection

## 3. Memorability — Returning Visitors

### Consistency across templates
- [ ] Navigation is identical in structure and order on every page template
- [ ] The same action uses the same label everywhere (article Mistake 2: Inconsistent Patterns)
- [ ] Visual styles for links, buttons, headings, and callouts match across templates

### Stable structure
- [ ] URLs are readable and predictable, so a visitor can guess or recall them
- [ ] Old URLs redirect instead of breaking
- [ ] Content is grouped by purpose, so visitors remember where a topic lives

## 4. Error Prevention and Recovery

### Dead ends
- [ ] The 404 page explains what happened and offers search, the home page, and popular links
- [ ] A search with no results suggests alternatives rather than a blank page
- [ ] No broken internal links on the walked pages

### Forms (newsletter, contact, comments) — N/A if the site has none
- [ ] Required fields are marked before submission, not only after
- [ ] Errors say what went wrong and how to fix it, next to the field (article Mistake 3: Poor Error Messages)
- [ ] Entered data survives a failed submission
- [ ] Submission gives clear confirmation of success

### Recovery
- [ ] The browser back button returns to the previous state, including scroll position and search results (the content-site form of article Mistake 5: No Undo Functionality)
- [ ] Filters, toggles, and theme switches are reversible and keep their state across pages where that is expected
- [ ] Irreversible actions, if any, ask for confirmation first

## 5. Satisfaction — Positive Experiences

### Respect
- [ ] No pop-ups, interstitials, or banners block content before the visitor has read anything
- [ ] Nothing autoplays with sound
- [ ] Ads or promotions, if present, don't push the content below the first screen

### Polish
- [ ] No visible layout shift while the page loads (text jumping as images or fonts arrive)
- [ ] Body text is comfortable to read: adequate size, line length, and contrast in light and dark modes
- [ ] Interactions respond immediately with visible feedback (hover, focus, pressed, loading states)
- [ ] Animations are purposeful and respect `prefers-reduced-motion`

## 6. Validation with Real Users

- [ ] The report states the review is an expert walkthrough, not a usability test
- [ ] A five-person, task-based test plan covers the top tasks
- [ ] Each HIGH or CRITICAL finding has a test observation that would confirm or refute it
- [ ] Recommendations stay proportionate to the site's purpose (article Section 9: When NOT to Focus on Usability)
