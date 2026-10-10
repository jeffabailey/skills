---
name: ai-sanitize
description: Removes the tells that make prose, user interfaces, and graphics read as AI-generated, then reports what changed. Rewrites performative phrasing, contrast framing, triads, signposting, emdashes, and marketing filler in prose; strips purple gradients, glassmorphism, pulsing badges, eyebrow labels, pill-everything, emoji decoration, and landing-page treatment of functional screens from UI code; and cleans decorative blobs, misaligned SVGs, broken ASCII art, and rainbow palettes from graphics and diagrams. Use when the user says /ai-sanitize, asks to "remove AI tells", "de-slop", "make this sound less like AI", "make this UI look less AI-generated", "humanize this copy", or asks why a page or draft feels generated. Edits in place by default; pass "report" to list tells without editing.
---

# AI Sanitize

Find and remove the patterns that make work read as machine-made. The patterns are catalogued in three references, one per medium. This file is the procedure.

## The rule behind every reference

AI output combines familiar patterns without a reason for choosing them. No single pattern proves anything. Inter is not an AI font, purple is not an AI color, and an emdash is not an AI character. People used all of them first.

What reads as generated is the **combination** of patterns plus the **absence of intent**. So judge every candidate with two questions:

1. **Removal test.** If you delete it, does the reader lose information or the user lose an ability? If not, it is decoration without intent. Remove it.
2. **Reason test.** Can you name why this choice fits *this* product, audience, or argument? "It looks modern" and "it sounds polished" are not reasons. If there is a reason, keep it, even if it appears in the catalog.

A page with one gradient is fine. A page with a gradient hero, an eyebrow, a huge H1 over a gray subtitle, pill buttons, glass cards, purple accents, a pulsing badge, Inter, JetBrains Mono, and "Elevate your workflow" is the tell.

## Modes

- **Edit (default).** Change the files or text, then report.
- **Report.** The user says "report", "audit", "just list", or "don't change anything". List tells with location and proposed fix. Edit nothing.

## Workflow

### 1. Identify the target and medium

Take the files, directory, URL, or pasted text from the user. If nothing is named, use the files changed in the working tree (`git diff --name-only HEAD`) and say so. Classify each target:

| Medium | Typical targets | Reference |
|--------|-----------------|-----------|
| Prose | `.md`, `.mdx`, `.txt`, docs, READMEs, commit and PR text, pasted drafts, UI copy strings | `references/prose.md` |
| UI | `.html`, `.css`, `.scss`, `.jsx`, `.tsx`, `.vue`, `.svelte`, templates, Tailwind classes, design tokens | `references/ui.md` |
| Graphics | `.svg`, Mermaid, ASCII art, icons, OG images, illustrations, charts, generated images | `references/graphics.md` |

Most UI work touches all three: the markup is UI, the headings and buttons are prose, the hero art is graphics. Load every reference that applies. Read only those.

### 2. Load the project's own rules first

Find the files that actually govern this target before touching anything, and record the path of each one you used. The report cites them.

1. **Start at the instruction files** nearest the target and at the repo root: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `STYLE.md`, `writing-style.md`.
2. **Follow pointers.** Instruction files often delegate: "see `content/prompts/writing-style.md`", "the single authority for voice is...", a Markdown link to a style guide. Open every file they point to that covers writing, voice, or design, and follow its pointers in turn. The real authority is often two hops from the root.
3. **Search for what nothing pointed to:** `find . -path ./node_modules -prune -o \( -iname '*style*.md' -o -iname '*voice*.md' -o -iname 'tokens.json' -o -name 'theme.ts' -o -name 'tailwind.config.*' \) -print`, and for UI, the `:root` custom properties: `grep -rln --include='*.css' --include='*.scss' ':root' . | grep -v node_modules`. Theme folders such as `assets/css/` hold tokens even when no doc mentions them.
4. **Discard what is not a style rule.** Many `CLAUDE.md` and `AGENTS.md` files only configure tools: MCP servers, graph or context policies, token counters, commit rules, build commands. They are not style rules; do not cite them as "Rules applied". If nothing about writing or design turns up, say "none found" rather than citing a tool-policy file.

Example (jeffbaileyblog): both `CLAUDE.md` files are graph and MCP policy; `hugo/AGENTS.md` points to `hugo/content/prompts/writing-style.md` for voice; tokens live in `hugo/assets/css/extended/theme-colors.css`.

How the rules apply:

- The project's rules win over this skill when they conflict. If the project's brand color is purple, purple stays. If the style guide bans emdashes, remove every one.
- Enforce a project rule only where it overlaps an AI tell. A project rule that is not about AI tells (the guide wants "I" where the draft says "we", a heading-case rule, a word count) goes under **Flagged, out of scope** in the report. Rewriting for it is a different job.
- UI fixes must **extend** the existing design system. Use its tokens, type scale, spacing, and components. Never introduce a new button variant, color, or font to replace a tell. A file that cannot import the tokens (a `static/` page outside the build) may copy token values verbatim; that is reuse, not a new color. Cite the tokens file.

### 3. Inventory the tells

Walk the loaded reference(s) and record each hit: location (`file:line`, URL plus selector, or quoted phrase), catalog item, and which test it fails. Use the `Detect` hints in each reference to search quickly, then read the surrounding context before judging. A grep hit is a candidate, not a finding.

The `Detect` hints are tuned to common generated output (the purple-gradient landing page, chatbot cadence). Zero grep hits does not mean clean, and many hits do not mean generated. After grepping, read the target once for tells the greps miss: framework boilerplate (Bootstrap defaults, starter-template copy), stock error-page copy ("Oops!"), duplicate calls to action, title-case headings ending in a colon.

Then count by category. Clusters matter more than single hits:

- **0 to 2 isolated hits: no cluster.** The target does not read generated. Say so in the report ("No cluster found: N isolated hits"), fix only hits that fail the removal test, and leave everything else alone. Changing little or nothing is a correct result. Do not invent edits to justify the run; on a human draft that is the most likely outcome.
- **3 or more hits in one view, section, or paragraph:** the composition reads generated. Fix the highest-signal items first (the reference marks them) until the cluster breaks.

### 4. Fix

Apply the fixes each reference gives. Across all media:

- **Subtract before you substitute.** The usual fix is deletion. Replacing a purple gradient with a teal gradient, or Inter with another trending font, swaps one tell for the next.
- **Replace vague with specific.** When something must stay (a heading, a tagline, an illustration), make it say or show something only this product could.
- **Preserve meaning and facts.** Never add claims, statistics, features, or citations that the source did not have. Keep code, commands, quotes, and technical terms exact.
- **Preserve the author's voice.** Keep first person, humor, strong opinions, and profanity that the source already had. Sanitizing tells is not sanitizing personality. Flattening a voice into neutral corporate prose is its own AI tell.
- **Preserve function and accessibility.** If you remove a colored status pill, the status must still be conveyed in text. Keep focus styles, contrast, `prefers-reduced-motion`, and `prefers-color-scheme` support. Never delete a control the user needs.
- **Stay in scope.** Fix tells in the target. Do not redesign pages, restructure arguments, finish unfinished drafts, or sweep unrelated files. Put what you noticed but did not touch (bugs, draft gaps, non-tell style-guide violations, a missing dark scheme) under **Flagged, out of scope**.

### 5. Verify

Copy the original before the first edit (`cp target /tmp/<name>.orig`, or use `git show HEAD:<path>`), then check the result against it. The scripts live in this skill's `scripts/` directory (`${CLAUDE_SKILL_DIR}/scripts/`; substitute the directory containing this `SKILL.md` if the variable is not expanded).

- **Everything:** `python3 scripts/survival-check.py <original> <edited>`. It lists lost front matter, profanity and other voice words, numbers in the text, link targets, code, `<script>` blocks, and element ids. Pass `--keep WORD` for other words the author's voice depends on. Every LOST line needs a fix or a stated reason (you deleted the whole sentence on purpose) in the report.
- **Prose:** reread the result once, start to finish. Run the reference's `Detect` greps again, including emdashes. Confirm no fact changed.
- **UI:** build the page if the project can, then `bash scripts/render.sh <page-or-url> <outdir> before` on the original and `... after` on the result. It writes screenshots at 1280px and at a true 390px viewport, light and dark, and prints the measured `scrollWidth` at 390px (`overflow: ok` or `FAIL`). Look at the screenshots. Do not use `chrome --headless --window-size=390,...` on its own: it lays the page out wider than 390px and clips it, which looks like a pass. Run the project's lint or test command if one exists.
- **Graphics:** render SVG and Mermaid output and look at it. Check alignment, text legibility, and that any ASCII art spells what it claims to.

If you cannot render something, say so under **Not verified** instead of claiming it looks right.

### 6. Report

Keep it short and concrete. No praise, no summary of the skill.

```markdown
## AI Sanitize: <target>

Mode: edit | report
Rules applied: <path of each style file or tokens file actually used, or "none found">
References: prose, ui, graphics
Verdict: <"No cluster found: N isolated hits" | "Cluster: N hits in <view/section>, broken">

### Changes
| Location | Tell | Fix |
|----------|------|-----|
| `hero.tsx:14` | Purple gradient blob behind empty hero (UI 1, 22) | Removed; hero uses `--surface` token |
| `README.md:3` | "Supercharge your workflow" (Prose 1) | "Converts CSV to Parquet in one command" |

### Kept on purpose
- `Badge.tsx`: "Offline" badge conveys real state that changes; passes the removal test.

### Flagged, out of scope
- `index.md`: style guide wants "I" over "we"; the draft uses "we" throughout. Voice rewrite, not an AI tell.

### Verified
- survival-check: ok (or each LOST line with its reason)
- render.sh: 1280 and 390 screenshots light and dark; 390px overflow: ok, scrollWidth=390

### Not verified
- Dark scheme: no local build available.
```

With no cluster and no edits, keep **Changes** with "None" and still fill in the rest. In report mode, rename **Changes** to **Proposed changes**. Omit any other section that would be empty.

## References

- `references/prose.md`: phrase, cadence, structure, formatting, and clarity tells in writing, with rewrites.
- `references/ui.md`: 31 interface tells grouped by color and surface, typography, components, layout, copy, and system consistency, with detection patterns and fixes.
- `references/graphics.md`: tells in SVG, icons, ASCII art, diagrams, charts, and generated images.
- `scripts/survival-check.py`: before/after check that facts, voice, links, code, and scripts survived the edit.
- `scripts/render.sh`: 1280px and true 390px screenshots in light and dark, plus a measured overflow check at 390px.
