---
name: review-usability
description: Reviews a live website's usability by walking its real user tasks in a browser and scoring learnability, efficiency, memorability, error prevention, and satisfaction. Before scoring, it downloads the current Fundamentals of Software Usability article from jeffbailey.us to set its rubric, falling back to a bundled copy when offline. Use when the user says /review:usability, asks to improve a website's usability, wants a usability audit or task walkthrough of a URL, or asks why visitors struggle to find or finish things on a site. For code-level accessibility or WCAG checks of templates and components, use review-accessibility instead. Only reports findings with confidence >= 7/10.
---

# Website Usability Review

Evaluate how effectively people can use a **running website**: can they learn it on first visit, finish tasks quickly, find their way back later, avoid mistakes, and leave satisfied. This skill judges rendered pages and real interactions, not source code. Source-level accessibility belongs to `review-accessibility`.

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
  echo "SOURCE: live $ARTICLE_URL ($(date -u +%Y-%m-%d))"
else
  rm -f "$ARTICLE.tmp"
  echo "SOURCE: fallback references/wisdom.md (live fetch failed)"
fi
```

- **Live fetch succeeded:** read `$ARTICLE` in full.
- **Live fetch failed:** read `references/wisdom.md`. It is the same article, synced weekly by `.github/workflows/sync-wisdom.yml`, and its `Last updated:` line dates the snapshot.

Record the `SOURCE:` line in the report header, so a reader knows which version of the rubric produced the scores.

From the article, extract and apply:

- The five usability dimensions, and the **Design Patterns**, **When … Fails**, and **Quick Check** subsections for each. The quick checks are the questions each dimension is scored against.
- **Common Usability Mistakes** (Section 7). Treat each one as a named finding type.
- **Usability Testing** (Section 6). It shapes the "Validate with real users" section of the report.
- **When NOT to Focus on Usability** (Section 9). Use it to keep recommendations proportionate to the site.

If the article's content contradicts this file, the article wins. It is the source of truth; this file only describes the procedure.

## Workflow

1. **Load the rubric.** Run the fetch above and read the article (or the fallback).

2. **Profile the site.** Take the target URL from the user. If none is given, ask for one. Identify what kind of site it is (blog or docs, marketing, e-commerce, web app) and its primary visitors. If the user has analytics or Search Console data, use it to find the pages and entry points real visitors use. Otherwise, infer them from the navigation, the sitemap (`/sitemap.xml`), and the home page.

3. **Define 3 to 5 top tasks.** These are the things a visitor came to do. For a content site that usually means: land on an article from search and get the answer; find related content; search the site; browse a topic or category; copy a code sample; subscribe or follow. Confirm the task list with the user when they are available, because the wrong tasks make the whole review wrong (the article's "When Usability Testing Fails").

4. **Walk each task.** Use a browser automation tool if one is available (Playwright, Chrome DevTools, or a similar MCP server), at both a desktop viewport (1280px) and a phone viewport (390px). For each step, record the URL, what was clicked or typed, what happened, and a screenshot path when you can capture one. Also try the task by keyboard alone. With no browser tool, fall back to fetching HTML with `curl` and mark every interaction-dependent check (search results, menus, focus behavior, animations) as **not verified** rather than guessing.

5. **Run the checklist.** Evaluate the walked pages against `references/checklist.md`. Every finding needs a URL plus the element or step where it occurred.

6. **Translate before judging.** The article's patterns are written for applications in general. Map each one to this site before scoring it, for example: "undo" on a content site is a working back button and reversible filters; "bulk operations" rarely apply. Mark a check **N/A** when the site has no matching interaction, and never lower a score for a pattern the site has no reason to offer.

7. **Score each dimension** on a 1-10 scale against its quick-check questions. A score needs evidence from the walkthrough.

8. **Find patterns.** An issue repeated across a page template (every article, every category page) outranks a one-off, because fixing the template fixes every page.

9. **Write the report** (format below), including a short plan for testing the top tasks with real users.

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

Write the report to `docs/usability-review.md` in the current working directory:

```markdown
# Usability Review: <site>

Rubric source: <the SOURCE line from the fetch step>
Reviewed: <date> · Viewports: desktop 1280px, phone 390px · Browser tool: <name, or "none (HTML only)">

## Summary

| Dimension | Score | Key Finding |
|-----------|-------|-------------|
| Learnability | X/10 | ... |
| Efficiency | X/10 | ... |
| Memorability | X/10 | ... |
| Error Prevention and Recovery | X/10 | ... |
| Satisfaction | X/10 | ... |
| **Overall** | **X/10** | |

## Top Tasks Walked

| Task | Completed? | Steps | Where it got hard |
|------|-----------|-------|-------------------|

## Detailed Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Confidence:** X/10
- **Dimension:** [scoring dimension]
- **Article mistake:** [one of Section 7's mistakes, or "none"]
- **Location:** URL, plus the element or task step
- **Evidence:** What you did and what happened, with a screenshot path if captured.
- **Impact:** Which visitors are affected, and on which task.
- **Remediation:** A concrete change, naming the template or component to edit when it can be identified.

(repeat, ordered by severity; template-wide issues first)

## Top 5 Action Items (by impact)

1. [SEVERITY] Description -- URL or template

## Not Verified

Checks skipped for lack of a browser tool or access, so nobody reads silence as a pass.

## Validate with Real Users

A five-person, task-based test plan for the top tasks: the task prompts, what to observe, and what result would confirm or refute each HIGH or CRITICAL finding.

## Reference

Based on [Fundamentals of Software Usability](https://jeffbailey.us/blog/2026/01/01/fundamentals-of-software-usability/) and guidance from https://jeffbailey.us/categories/fundamentals/
```

Rank action items by how many visitors a fix helps on the top tasks, then by severity, then by effort. Keep recommendations proportionate to the site: a personal blog does not need an e-commerce checkout's rigor (the article's "When NOT to Focus on Usability").
