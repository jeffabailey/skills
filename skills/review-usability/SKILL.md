---
name: review-usability
description: Reviews a live website's usability by walking its real user tasks in a browser and scoring learnability, efficiency, memorability, error prevention, and satisfaction. Before scoring, it downloads the current Fundamentals of Software Usability article from jeffbailey.us to set its rubric, falling back to a bundled copy when offline. Use when the user says /review:usability, asks to improve a website's usability, wants a usability audit or task walkthrough of a URL, or asks why visitors struggle to find or finish things on a site. For code-level accessibility or WCAG checks of templates and components, use review-accessibility instead. Only reports findings with confidence >= 7/10.
---

# Website Usability Review

Evaluate how effectively people can use a **running website**: can they learn it on first visit, finish tasks quickly, find their way back later, avoid mistakes, and leave satisfied. This skill judges rendered pages and real interactions, not source code.

Scope against `review-accessibility`: completing a top task **by keyboard** is in scope here, because the article treats keyboard access as efficiency (Mistake 4). Screen-reader behavior, ARIA, color contrast, and WCAG conformance are not; note them in one line and point to `review-accessibility`.

Reference: [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/) — see also [Fundamentals](https://jeffbailey.us/categories/fundamentals/)

## Domain Knowledge

The rubric comes from the article itself, pulled fresh on every run so the review tracks the current version of the article rather than a copy frozen into this skill.

Download it before doing anything else:

```bash
ARTICLE_URL="https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/llm.txt"
CACHE_DIR="${TMPDIR:-/tmp}/review-usability"
ARTICLE="$CACHE_DIR/fundamentals-of-software-usability.txt"
mkdir -p "$CACHE_DIR"
if curl -fsSL --max-time 20 -A "skills-review-usability/1.0" "$ARTICLE_URL" -o "$ARTICLE.tmp" \
   && grep -q "Learnability" "$ARTICLE.tmp"; then
  mv "$ARTICLE.tmp" "$ARTICLE"
  echo "SOURCE: live $ARTICLE_URL (fetched $(date '+%Y-%m-%d %H:%M %Z'))"
else
  rm -f "$ARTICLE.tmp"
  echo "SOURCE: fallback references/wisdom.md (live fetch failed)"
fi
```

Then pull out only the sections the review uses. They are about a quarter of the article (roughly 11 KB of 41 KB), and the rest (introductions, misconceptions, future trends) never changes a score:

```bash
SRC="$ARTICLE"; [ -f "$SRC" ] || SRC="${CLAUDE_SKILL_DIR:-skills/review-usability}/references/wisdom.md"
awk '/^## /{k2=($0 ~ /^## Section (6|7|9):/); k3=0}
     /^### /{k3=($0 ~ /^### (When .* Fails|Quick Check:)/)}
     k2||k3' "$SRC" > "$CACHE_DIR/rubric-sections.md"
grep -c '^#' "$CACHE_DIR/rubric-sections.md"   # expect about 24 headings
```

Read `rubric-sections.md`. If it has fewer than about 15 headings, the article has been restructured: read the source in full instead. When the live fetch failed, the source is `references/wisdom.md`, the same article synced weekly by `.github/workflows/sync-wisdom.yml`; its `Last updated:` line dates the snapshot.

Record the `SOURCE:` line in the report header, so a reader knows which version of the rubric produced the scores.

What each extracted section is for:

- **When … Fails** and **Quick Check** for each of the five dimensions: the questions each dimension is scored against. Open a dimension's **Design Patterns** subsection only when a remediation needs it.
- **Common Usability Mistakes** (Section 7). Treat each one as a named finding type.
- **Usability Testing** (Section 6). It shapes the "Validate with real users" section of the report.
- **When NOT to Focus on Usability** (Section 9). Use it to keep recommendations proportionate to the site.

Browser scripts for the walkthrough (viewport size, content offset, keyboard reach, shortcut probes, render-error scan, Back-button probe) live in `references/browser-recipes.md`. Use them instead of writing new ones each run.

If the article's content contradicts this file, the article wins. It is the source of truth; this file only describes the procedure.

## Workflow

1. **Load the rubric.** Run the fetch and extraction above and read the extracted sections.

2. **Profile the site.** Take the target URL from the user. If none is given, ask for one. Identify what kind of site it is (blog or docs, marketing, e-commerce, web app, or a single static or placeholder page) and its primary visitors. If the user has analytics or Search Console data, use it to find the pages and entry points real visitors use. Otherwise, infer them from the navigation, the sitemap (`/sitemap.xml`), and the home page.

   - **Local target:** a local build or preview server is fine for checking fixes before they deploy. Some things only the real host shows: HTTP caching headers, the custom 404 page (a static server substitutes its own), compression, and speed. Check those against the live URL, and label each finding with the host it came from.
   - **Re-review:** if a previous usability report exists (the user names it, or it sits at the output path), read it first. Walk the same top tasks so the scores are comparable. The report then adds a "Prev" score column and a "Prior Findings" table giving each earlier finding's status (Fixed, Still present, Deferred, or Not verifiable here) with one line of evidence. Also probe the fixes for regressions: edge-case input (special characters in search, such as `c++` and `a&b`), states that should stay hidden, and links the fix added. Check each fix from both sides: that the problem is gone, and that whatever sits next to it still works (removing one search tag must not hide titles or excerpts).

3. **Define 1 to 5 top tasks, as many as the site really supports.** These are the things a visitor came to do. For a content site that usually means: land on an article from search and get the answer; find related content; search the site; browse a topic or category; copy a code sample; subscribe or follow. A single static page may support only one or two (read it, follow its link); don't pad the list with tasks the site has no reason to offer.

   Confirm the task list with the user when they are available, because the wrong tasks make the whole review wrong (the article's "When Usability Testing Fails"). When nobody can confirm (a non-interactive run, or the user said "just do it"), infer the tasks from the navigation, sitemap, and home page, proceed, and mark each one **Unconfirmed (inferred from <source>)** in the Top Tasks table so the reader knows to check them.

   **Budget.** A full checklist pass on every task at two viewports does not fit one session, so set the scope before walking: at most about 12 distinct pages, every task at desktop, the one or two most important tasks also at phone width and by keyboard, and the high-yield checks first (answer placement, search, related content, Back, 404, phone layout). Anything the budget leaves out goes under **Not Verified** by name, so silence is never read as a pass.

4. **Walk each task.** Use a browser automation tool if one is available (Playwright, Chrome DevTools, or a similar MCP server), at a desktop viewport (about 1280px) and, for the tasks the budget names, a phone viewport (about 390px) and keyboard alone. For each step, record the URL, what was clicked or typed, what happened, and a screenshot path when you can capture one. With no browser tool, fall back to fetching HTML with `curl` and mark every interaction-dependent check (search results, menus, focus behavior, animations) as **not verified** rather than guessing.

   - **Recipes:** use the scripts in `references/browser-recipes.md` for viewport size, content offset, keyboard reach, shortcuts, render errors, and the Back probe.
   - **Viewports:** if the tool cannot set an exact width (a maximized window often refuses to resize), use device emulation or open a popup at the target size, for example `window.open(url, "phone", "popup,width=390,height=844")` from a page script, then switch the tool to the new page. Browser chrome makes the inner height smaller than requested. Any width within about 50px is fine. Record the actual width **and inner height** of each viewport in the report header: the desktop "first screen" check depends on height, and a maximized window with browser chrome is often only 600-700px tall.
   - **Cache:** start from a fresh profile or reload with the cache bypassed, so you judge what a new visitor gets. Then check what a *returning* visitor gets: read the HTML response's `Cache-Control` with `curl -sI <url>`. A long `max-age` on HTML means returning visitors can see stale pages (a memorability finding). A missing `Cache-Control` header is not a finding by itself; note it in one line, since browsers then cache heuristically from `Last-Modified`.
   - **Reading page state:** prefer small scripts that return compact JSON (element offsets, computed styles, `document.activeElement`, result counts) over full accessibility snapshots. On long pages a snapshot can exceed 60,000 characters per action, and some tools (Chrome DevTools `press_key`) attach one to every key press, even a single Tab. Check keyboard reach from the page's tab order, and fire shortcuts by dispatching a `KeyboardEvent` from a script (recipes in `references/browser-recipes.md`).
   - **Shortcut probes may navigate.** A `/` or `Ctrl+K` handler can load a search page, which destroys the script context ("Execution context was destroyed"). That is a result: read `location.href` in a new call and record where the shortcut went.
   - **Render errors:** scan only text outside `pre` and `code`, because articles often show error messages in code samples.
   - **Timing:** after an action that triggers a CSS transition, wait past it before reading computed styles, or you will read the starting value.
   - **Back button:** browsers often restore a page from the back/forward cache without running any of its scripts, so a Back test can pass even when the page's own restore code is broken. Set a marker first (`window.__probe = 1`); if the marker survives Back, the cache served the page. Then reload to exercise the restore code, and report both results.

5. **Run the checklist.** Evaluate the walked pages against `references/checklist.md`. Every finding needs a URL plus the element or step where it occurred.

6. **Translate before judging.** The article's patterns are written for applications in general. Map each one to this site before scoring it, for example: "undo" on a content site is a working back button and reversible filters; "bulk operations" rarely apply. Mark a check **N/A** when the site has no matching interaction, and never lower a score for a pattern the site has no reason to offer.

   - **"Answer in the first screen":** measure where the main content starts, in pixels and in screens. On a 390px-wide phone, content that starts beyond about 1.5 screens (roughly 1,250px) is a finding. Navigation that *is* the route to the answer, such as an open list of fixes on an error-fix guide, counts as content, not as clutter.
   - **Empty search results:** search for a nonsense string (for example `qzxwvkjh`). If fuzzy matching still returns results, try one more string, then mark the check **not verified** instead of passing it.
   - **Page speed:** measure with a DevTools performance trace or Lighthouse against the real host. Local static servers (such as `python -m http.server`) have no compression or CDN and give misleading numbers. When a page is slow only in the browser session and fast with `curl`, list it under Not Verified.

7. **Score each dimension** on a 1-10 scale against its quick-check questions. A score needs evidence from the walkthrough. When a dimension has fewer than two checks the site gives you anything to observe (on a single static page, Error Prevention may have only a 404), write **N/A — <reason>** instead of a number, or give the score with "(thin evidence: <what was observed>)". The Overall score is the mean of the numeric dimensions, one decimal, and the report says which were averaged.

8. **Find patterns.** An issue repeated across a page template (every article, every category page) outranks a one-off, because fixing the template fixes every page.

9. **Self-check, then write the report** (format below), including a short plan for testing the top tasks with real users. Before writing, confirm:
   - every Detailed Finding's **Location** has a full `https://` URL (or the local URL plus host label) **and** the element or task step; a finding that only names a template ("article template at 390px") gets the URL of the page where it was seen;
   - every finding has confidence >= 7; drop the rest or move them to Not Verified;
   - the header records both viewports as width x height and the browser tool;
   - each top task is marked confirmed or Unconfirmed, and there are 1 to 5 of them;
   - the Overall equals the mean of the numeric scores.

## Confidence and Severity

Only report findings with confidence >= 7/10. For each finding, check:

- Did you observe it on the live site, rather than infer it from how sites usually work?
- Can you name the URL and the element or step?
- Would a typical visitor on one of the top tasks actually run into it?

If any answer is no, leave it out. An expert walkthrough predicts problems; only real users confirm them. Say so in the report instead of inflating confidence.

Severity:

- **CRITICAL** — a top task cannot be completed (a broken search, a dead primary navigation link, content hidden on mobile).
- **HIGH** — a top task completes, but most visitors will struggle or give up (the answer sits below several screens of preamble; there is no route from an article to related content).
- **MEDIUM** — friction that slows visitors or makes them hesitate (inconsistent labels across templates, weak link affordance, no search shortcut).
- **LOW** — polish (micro-interactions, minor visual inconsistency).

## Scoring Dimensions (1-10 each)

Each dimension is scored against the article's matching **Quick Check** questions and **When … Fails** signs:

1. **Learnability** — Can a first-time visitor complete the top tasks without help? Familiar layout and icon conventions, discoverable features, clear link and button affordances.
2. **Efficiency** — How many steps and how much scrolling does a top task take? Answer placement, search quality and speed, keyboard access, navigation depth, page speed as the visitor feels it.
3. **Memorability** — Would a returning visitor find their way again? Consistent navigation, terminology, and visual layout across page templates; stable, predictable URLs.
4. **Error Prevention and Recovery** — Are dead ends and mistakes prevented, and easy to recover from? Helpful 404 pages, empty-search results, form validation, a back button that works, reversible filters.
5. **Satisfaction** — Does the site feel polished, respectful, and responsive? No layout shift or intrusive interruptions, readable typography, responsive interactions.

## Output Format

Write the report to the path the user gives. Otherwise, write it to `docs/usability-review.md` in the current working directory, unless that directory is the reviewed site's own repository and the user hasn't asked for the report to live there. In that case, ask for a path or use a scratch or temporary directory, so the review doesn't leave an untracked file in their site. Keep screenshots next to the report.

```markdown
# Usability Review: <site>

Rubric source: <the fetch step's SOURCE line, without its "SOURCE:" prefix>
Reviewed: <date> · Viewports: desktop <w>x<h>px, phone <w>x<h>px · Browser tool: <name, or "none (HTML only)"> · Target: <live URL or local build>

## Summary

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Learnability | X/10 | ... |
| Efficiency | X/10 | ... |
| Memorability | X/10 | ... |
| Error Prevention and Recovery | X/10 | ... |
| Satisfaction | X/10 | ... |
| **Overall** | **X/10** | Mean of <dimensions averaged> |

A dimension may read `N/A — reason`. On a re-review, add a "Prev" column after Score.

## Prior Findings (re-review only)

| # | Finding | Status | Evidence |
|---|---------|--------|----------|

## Top Tasks Walked

| Task | Confirmed? | Completed? | Steps | Where it got hard |
|------|-----------|-----------|-------|-------------------|

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [scoring dimension]
- **Article mistake:** [one of Section 7's mistakes, or "none"]
- **Location:** full URL (https://...), plus the element or task step
- **Evidence:** What you did and what happened, with a screenshot path if captured.
- **Impact:** Which visitors are affected, and on which task.
- **Remediation:** A concrete change, naming the template or component to edit when it can be identified.

(repeat, ordered by severity; template-wide issues first)

## Top Action Items (up to 5, by impact)

1. [SEVERITY] Description -- URL or template

## Not Verified

Checks skipped for lack of a browser tool, access, or budget, so nobody reads silence as a pass.

## Validate with Real Users

A five-person, task-based test plan for the top tasks: the task prompts, what to observe, and what result would confirm or refute each HIGH or CRITICAL finding.

## Reference

Based on [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/) and guidance from https://jeffbailey.us/categories/fundamentals/
```

Rank action items by how many visitors a fix helps on the top tasks, then by severity, then by effort. Keep recommendations proportionate to the site: a personal blog does not need an e-commerce checkout's rigor (the article's "When NOT to Focus on Usability").
