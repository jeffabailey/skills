# User Interface Tells

Tells in web and app interfaces. Items keep stable numbers (1 to 31) so reports can cite them ("UI 5"); they are grouped by category, so numbers within a group are not sequential. **High signal** items are the ones to fix first when a cluster appears.

Before fixing anything, read the project's design system (tokens, type scale, spacing, components). Every fix below uses what already exists. If a fix seems to need a new token, variant, or font, stop and ask.

## The composition tell

Individual items here are weak evidence. Designers used every one of them before AI did, and frameworks and trends have always made sites converge. The strong tell is a stack of them in one view with no reason behind any choice:

> Gradient hero + eyebrow + huge H1 + gray subtitle + pill buttons + glass cards + purple accents + pulsing badges + Inter + JetBrains Mono + "Elevate your workflow"

Count hits per view (one screen, route, or component tree):

- **0 to 2:** leave them unless they fail the removal test.
- **3 to 5:** the view leans generated. Fix high-signal items until at most two remain.
- **6 or more:** the view reads generated. Fix every item that fails the removal or reason test.

The removal test for UI: if you delete the element, can the user still do and understand everything they could before? If yes, it was decoration without intent.

## Color and surface

### 1. Gradients everywhere (high signal)

Gradient backgrounds, buttons, borders, text, and accents, especially purple-to-blue or purple-to-pink.

**Detect:** `linear-gradient|radial-gradient|conic-gradient`, `bg-gradient-to-`, `from-(purple|violet|indigo|fuchsia|pink)-`, `bg-clip-text text-transparent`.

**Fix:** use a flat color from the existing palette. Keep a gradient only where it encodes something (a range, a heat scale, a progress fill) or is part of the documented brand.

### 2. Rainbow color palettes

Many unrelated hues used only to tell elements apart, with no link to the product and no hierarchy (every card, tag, or stat a different color).

**Detect:** count distinct hue families in one view; look for per-item color arrays (`colors = ["blue","green","purple","orange"...]`) and `bg-{color}-100 text-{color}-700` repeated across hues.

**Fix:** reduce to the brand's primary, one accent, neutrals, and semantic colors (success, warning, danger) used only for those meanings. Distinguish items with labels, position, or icons instead of hue.

### 11. Glassmorphism

Translucent cards, blurred backdrops, frosted panels, glowing borders.

**Detect:** `backdrop-filter`, `backdrop-blur`, `bg-white/10`, `bg-opacity-`, `rgba(255,255,255,0.1)`, `box-shadow` with large colored spread, `ring-*/50`.

**Fix:** solid surface token with the system's standard border or elevation. Keep blur only where content genuinely sits over moving or image content (a sheet over a map) and legibility is verified.

### 22. Huge hero gradient blob (high signal)

A large blurred gradient shape behind an otherwise empty hero.

**Detect:** absolutely positioned `div` with `blur-3xl`, `filter: blur(` over 40px, `rounded-full` plus gradient, `-z-10`, `pointer-events-none`, `aria-hidden` on a shape with no content.

**Fix:** delete it. If the hero feels empty after that, the hero has too little content; see item 14.

### 23. Dark mode only

A dark theme with no light theme, and no response to `prefers-color-scheme`.

**Detect:** hardcoded dark backgrounds on `html`/`body`; no `@media (prefers-color-scheme` and no theme switch; Tailwind `dark` class forced on `<html>`.

**Fix:** if the design system has light tokens, honor `prefers-color-scheme` and default to the user's setting. If it has none, report it rather than inventing a palette.

## Typography

### 8. Generic font choices

Inter for everything, JetBrains Mono for anything technical, no typographic decision beyond picking a popular modern font.

**Detect:** `font-family` values, `next/font` imports, Google Fonts links, `fontFamily` in Tailwind config.

**Fix:** if the project already has a brand or chosen typeface, use it. If Inter is the deliberate system font, keep it and fix the other tells. Do not swap to a new trending font; report the choice for a human to make.

### 9. Fake-tech typography (high signal)

`//` before labels, `>` or `$` prompts before non-command text, `{ }` or `< />` around ordinary words, `_` cursors, monospace used only to look technical.

**Detect:** text nodes starting with `// `, `> `, `$ `, `~/`; `font-mono` on headings, nav, or labels that are not code.

**Fix:** remove the decoration and use the body or heading font. Keep monospace for code, commands, file paths, and tabular numbers.

### 19. Wide-tracked uppercase

ALL CAPS labels with heavy letter spacing, usually as eyebrows (item 16).

**Detect:** `uppercase` plus `tracking-widest|tracking-[0.2em]`, `letter-spacing: 0.1em` or more, `text-transform: uppercase`.

**Fix:** sentence case at the system's label style. Keep uppercase only for short, established conventions the system already uses (table headers, keyboard keys).

### 24. Poor mobile typography

Headings that wrap into tall blocks with oversized line height; display sizes that do not scale down; text that looks oddly spaced at phone width.

**Detect:** fixed large `font-size` with no responsive step; `leading-relaxed|leading-loose` on headings; `line-height` above 1.3 on display text.

**Fix:** use the system's responsive type scale (or `clamp()` if the system uses it), heading line height about 1.1 to 1.25, and check at 390px.

### 27. Monospace everything

Monospace across the whole site to feel "developer".

**Detect:** `font-mono` or a mono family on `body`, layout wrappers, or most text.

**Fix:** body text in a proportional face from the system; monospace only for code and data.

## Components

### 3. Pulsing status badges (high signal)

Glowing or animated "Active"/"Live"/"Online" dots, especially where the state can never change.

**Detect:** `animate-pulse`, `animate-ping`, `@keyframes pulse`, glow `box-shadow` on small dots, badges whose text is a constant.

**Fix:** if the state never changes, delete the badge. If it changes, show a static indicator with a text label; animate only a transient state (connecting, syncing) and respect `prefers-reduced-motion`.

### 4. Everything becomes a badge

"Verified", "Featured", "New", "Pro", "Active", achievement pills, descriptive words turned into chips.

**Detect:** `Badge`, `Chip`, `Tag`, `Pill` components or `rounded-full px-2 text-xs` spans; count per card.

**Fix:** keep a badge only for status that changes or a filterable category. Move descriptive words back into text. At most one badge per item unless the item has multiple real, changing states.

### 5. "Fingernail" cards (high signal when repeated)

Cards with a colored strip along one edge, repeated on every card in a list.

**Detect:** `border-l-4`, `border-left: 4px solid`, `border-t-4` plus a color, a colored absolutely positioned bar inside a card.

**Fix:** remove the strip. If the color meant something (category, severity), express it with a label or icon; if every card gets the same strip, it meant nothing.

### 20. Pill-shaped everything

Pill buttons, pill badges, pill containers, pill inputs with no functional reason.

**Detect:** `rounded-full` on buttons, inputs, containers; `border-radius: 9999px`.

**Fix:** use the system's standard radius. Keep full rounding for things that are conventionally round (avatars, toggle tracks, icon buttons) or where the system defines it.

### 21. Pill cards

Cards with very large corner radius, often combined with gradients and glass.

**Detect:** `rounded-2xl|rounded-3xl` on cards; `border-radius` of 20px or more on containers.

**Fix:** the system's card radius. One radius scale, applied consistently.

### 25. Oversized theme toggle

A dark-mode toggle so large or styled that it reads as a brand element.

**Detect:** theme switch in the header larger than other nav controls, animated sun/moon illustrations, gradient tracks.

**Fix:** a small icon button matching other header controls, or move it to settings.

## Layout and composition

### 14. Every page treated like a landing page (high signal)

Functional screens (dashboards, settings, lists) open with a hero: huge H1, gray subtitle, marketing copy before the controls. "Welcome to your Dashboard, Sam ✨".

**Detect:** `text-4xl` or larger H1 plus a muted `<p>` subtitle at the top of authenticated or functional routes; greeting strings; error and empty pages that stack an interjection H1 over the real message (`grep -niE "oops|uh.oh|whoops|well, this is awkward"`).

**Fix:** a compact page title at the system's page-heading size, then the content. Drop the subtitle unless it gives information the user needs (a date range, a count, a status).

### 16. Eyebrow section labels (high signal)

Small uppercase, wide-tracked, often colored text above a heading ("FEATURES" over "Everything you need").

**Detect:** a small `uppercase tracking-*` element immediately before an `h1`/`h2`/`h3`; `eyebrow`, `kicker`, `overline` class names.

**Fix:** delete the eyebrow. If it held useful context (a category), fold it into the heading or breadcrumb.

### 17. Numbered section eyebrows

"01. ABOUT", "02. FEATURES", "03. PRICING" where the order carries no meaning.

**Detect:** labels matching `^0\d[.\s/]`.

**Fix:** remove the numbers. Keep numbering only for real sequences (steps in a procedure).

### 18. Eyebrow + heading + subtitle + content

A section that says the same thing three times before the content: "FEATURES / Features / Everything you need to... / [content]".

**Fix:** one heading that names the section specifically, then the content. Delete the eyebrow and any subtitle that restates the heading.

### 12. Generic brutalism

"Brutalist" layouts that converge on the same formula: oversized black type, thick borders, hard offset shadows, rigid grids, with no character of their own.

**Detect:** `shadow-[4px_4px_0_0_#000]`, `border-4 border-black` everywhere, display type at viewport-width sizes on every section.

**Fix:** keep it only if brutalism is the documented brand direction. Otherwise, fall back to the system's standard components and report the direction for a human decision.

### 28. The "AI dashboard" composition

Stat cards, pills, badges, gradients, glass, and many colored status dots packed into a dense but generic grid.

**Fix:** this is items 1, 2, 3, 4, 11, and 20 together. Fix those, then ask of each card: does the user act on this number? Remove cards that fail the removal test and order the rest by how often the user needs them.

### 31. Everything gets visual treatment

Every piece of information in a card, every descriptor a badge, every section an icon, every empty area a blob, every heading decorated.

**Detect:** every block wrapped in a tinted card; two calls to action that go to the same place or restate each other ("Return to Homepage" button plus "Looking for something specific? ..." card); help text that offers a feature the page does not have.

**Fix:** let plain text and whitespace carry most of the page. Keep treatment for the few things the user must notice. Emphasis only works when most of the page has none.

## Decoration

### 6. Emoji decoration (high signal)

Emoji in headings, buttons, nav, greetings, and empty states as decoration (✨, 🚀, 🎉, 💡, 🔥).

**Detect:** `grep -nP "[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]"` across templates and copy strings.

**Fix:** remove. Where an icon helps recognition, use the system's icon set, with an accessible label.

### 7. Misaligned decorative elements

SVGs slightly off-center, icons on different baselines or sizes, illustrations that do not share alignment, loose elements positioned a few pixels wrong.

**Detect:** render and inspect; look for magic-number offsets (`top-[3px]`, `translate-y-[1px]`, `margin-top: -2px`) and icons with mixed `w-4`/`w-5` in one row.

**Fix:** align to the grid with flex or grid alignment instead of offsets; one icon size per context. If a decorative element cannot be aligned cleanly, delete it. See `graphics.md` for SVG specifics.

### 26. ASCII art that does not work

AI-generated ASCII typography or art with wrong letterforms, broken alignment, or words that do not spell what they claim.

**Fix:** see `graphics.md` item 4. Usually delete it.

### 29. Decorative UI without intent

An element that exists because modern interfaces "should" have it: a progress ring with no progress, a "Live" indicator on static data, a command palette hint with no command palette, a fake terminal window around a paragraph.

**Fix:** apply the removal test and delete what fails it. This is the meta-tell in component form.

## Copy in the interface

Also apply `prose.md` to every visible string.

### 10. Redundant contextual text

"Built with Hugo", "Written from Neovim", "Powered by Next.js", "Built with modern C++20 features": implementation details the user does not need.

**Fix:** delete from user-facing UI. Keep only where the audience actually chooses on it (a developer tool's docs, an open-source footer the project wants).

### 13. Generic marketing language (high signal)

"Elevate", "Seamless", "Next-generation", "Supercharge", "Unleash", "Empower", "Revolutionize your workflow".

**Fix:** say what the product does, specifically. See `prose.md` item 2.

### 15. Vague inspirational taglines

"One campus. One app.", "Experience the power of...", "The future of...", "Redefining...": polished copy that says nothing about the product.

**Fix:** replace with a sentence only this product could claim ("Book study rooms and see dining hours from one login"). If no such sentence is available from the source, flag it for the author instead of inventing one.

## System consistency

### 30. Design-system inconsistency (high signal in existing codebases)

New button variants, colors, radii, shadows, or spacing values that do not exist in the system; components that ignore existing typography. The AI replaced the design language instead of extending it.

**Detect:** hex colors or pixel values not in the tokens file; new `Button` variants or one-off styled buttons; duplicate components (a second `Card`); arbitrary Tailwind values (`[#7c3aed]`, `p-[13px]`). Framework defaults that ignore the project's palette are the same tell: Bootstrap's `#007bff|#0056b3|#f8f9fa|#dee2e6|#6c757d`, Tailwind's untouched `blue-500`/`gray-*` on a site with its own tokens (`grep -niE "#007bff|#0056b3|#f8f9fa|#dee2e6|#6c757d"`).

**Fix:** map each one-off value to the nearest existing token and each new component to the existing one. Delete the duplicates. If the file cannot import the tokens (a static page outside the build pipeline), copy the token values verbatim into local custom properties and cite the tokens file; that reuses the system rather than adding to it.
