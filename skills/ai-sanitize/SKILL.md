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

Look for a style guide before touching anything: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `writing-style.md`, `STYLE.md`, a design-system package, a tokens file (`tokens.json`, `theme.ts`, `tailwind.config.*`, CSS custom properties on `:root`), or a component library directory.

- The project's rules win over this skill when they conflict. If the project's brand color is purple, purple stays.
- UI fixes must **extend** the existing design system. Use its tokens, type scale, spacing, and components. Never introduce a new button variant, color, or font to replace a tell.

### 3. Inventory the tells

Walk the loaded reference(s) and record each hit: location (`file:line`, URL plus selector, or quoted phrase), catalog item, and which test it fails. Use the `Detect` hints in each reference to search quickly, then read the surrounding context before judging. A grep hit is a candidate, not a finding.

Then count by category. Clusters matter more than single hits:

- **0 to 2 isolated hits:** mention them; fix only if they fail the removal test.
- **3 or more hits in one view, section, or paragraph:** the composition reads generated. Fix the highest-signal items first (the reference marks them) until the cluster breaks.

### 4. Fix

Apply the fixes each reference gives. Across all media:

- **Subtract before you substitute.** The usual fix is deletion. Replacing a purple gradient with a teal gradient, or Inter with another trending font, swaps one tell for the next.
- **Replace vague with specific.** When something must stay (a heading, a tagline, an illustration), make it say or show something only this product could.
- **Preserve meaning and facts.** Never add claims, statistics, features, or citations that the source did not have. Keep code, commands, quotes, and technical terms exact.
- **Preserve the author's voice.** Keep first person, humor, strong opinions, and profanity that the source already had. Sanitizing tells is not sanitizing personality. Flattening a voice into neutral corporate prose is its own AI tell.
- **Preserve function and accessibility.** If you remove a colored status pill, the status must still be conveyed in text. Keep focus styles, contrast, `prefers-reduced-motion`, and `prefers-color-scheme` support. Never delete a control the user needs.
- **Stay in scope.** Fix tells in the target. Do not redesign pages, restructure arguments, or sweep unrelated files.

### 5. Verify

- **Prose:** reread the result once, start to finish. Search it again for the reference's `Detect` patterns, including emdashes. Confirm no fact changed.
- **UI:** build or render the page if the project can. Check it at desktop (about 1280px) and phone (about 390px) widths, in light and dark schemes if both exist. Run the project's lint or test command if one exists.
- **Graphics:** render SVG and Mermaid output and look at it. Check alignment, text legibility, and that any ASCII art spells what it claims to.

If you cannot render something, say so in the report instead of claiming it looks right.

### 6. Report

Keep it short and concrete. No praise, no summary of the skill.

```markdown
## AI Sanitize: <target>

Mode: edit | report
Rules applied: <project style guide path, or "none found">
References: prose, ui, graphics

### Changes
| Location | Tell | Fix |
|----------|------|-----|
| `hero.tsx:14` | Purple gradient blob behind empty hero (UI 1, 22) | Removed; hero uses `--surface` token |
| `README.md:3` | "Supercharge your workflow" (Prose 1) | "Converts CSV to Parquet in one command" |

### Kept on purpose
- `Badge.tsx`: "Offline" badge conveys real state that changes; passes the removal test.

### Not verified
- Dark scheme: no local build available.
```

In report mode, rename **Changes** to **Proposed changes**.

## References

- `references/prose.md`: phrase, cadence, structure, formatting, and clarity tells in writing, with rewrites.
- `references/ui.md`: 31 interface tells grouped by color and surface, typography, components, layout, copy, and system consistency, with detection patterns and fixes.
- `references/graphics.md`: tells in SVG, icons, ASCII art, diagrams, charts, and generated images.
