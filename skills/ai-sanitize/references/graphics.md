# Graphics Tells

Tells in SVG, icons, ASCII art, diagrams, charts, cover and OG images, and generated illustrations. Items are numbered so reports can cite them ("Graphics 2"). The same rule applies as everywhere: a graphic earns its place by showing something the reader needs. Decoration that fails the removal test goes.

You cannot judge a graphic from its source alone. Render it (open the SVG, build the Mermaid, view the image) before and after every fix. If you cannot render it, report it as not verified.

## 1. Decorative gradient blobs and glows (high signal)

Blurred gradient shapes, glowing orbs, aurora backgrounds, purple-to-blue meshes that fill space without depicting anything.

**Detect:** SVG `<filter>` with `feGaussianBlur` on large shapes; `<radialGradient>` or `<linearGradient>` on background `<circle>`/`<ellipse>`/`<path>`; CSS blobs (see `ui.md` item 22).

**Fix:** delete. If the graphic has no subject left, the graphic was only decoration; remove it or replace it with one that shows real content (a screenshot, a diagram, a photo).

## 2. Misaligned and inconsistent vector art (high signal)

Icons or shapes a few units off-center; mismatched stroke widths, corner styles, or sizes in one set; paths that almost meet; text in SVG not centered in its box.

**Detect:** mixed `stroke-width` values in one icon set; `viewBox` sizes that differ across icons in a row; odd fractional `transform="translate(...)"` offsets; `<text>` without `text-anchor="middle"`/`dominant-baseline` where centering is intended.

**Fix:** use one icon set at one size and stroke per context. Center with `viewBox` and anchors, not hand offsets. Snap coordinates to whole or half units. Replace a hand-drawn icon with the project's icon set when one exists.

## 3. Emoji and sparkle decoration

✨, 🚀, 🎯 used as illustration, in diagram nodes, chart titles, or cover art.

**Fix:** remove. Use text labels in diagrams and the project's icon set in UI.

## 4. ASCII art that does not work (high signal)

Banner text in ASCII whose letterforms are wrong, lines that drift out of alignment, boxes whose corners do not meet, words that do not spell what they claim.

**Detect:** render it in a monospace font at its real width and read it. Check every row has the intended length and that box-drawing characters connect.

**Fix:** delete decorative ASCII art. Keep ASCII only when it is functional (a directory tree, a tiny table in a terminal-only context) and verified to line up. Generate banners with a real tool (`figlet`, `toilet`) rather than by hand.

## 5. Rainbow and unmotivated palettes

Every node, bar, or segment a different hue with no encoding; saturated neon on dark backgrounds.

**Fix:** color encodes data or nothing. Use one neutral for structure, one accent for the point of the graphic, and a sequential or categorical palette only when color maps to a variable. Keep text contrast readable in light and dark contexts.

## 6. Diagram tells

- Arrow text standing in for a diagram ("Idea → Build → Ship → Profit").
- Mermaid nodes with emoji, gradient fills, or a `style` line per node in different colors.
- Every box the same shape and weight, so nothing is the point.
- Three-box or four-box "framework" diagrams that restate the surrounding paragraph.
- Wide left-to-right flows that force horizontal scrolling on phones.

**Fix:** draw a real diagram only when relationships matter; otherwise, write the sentence. Label edges with what flows along them. Highlight the one node the reader should look at. Prefer top-to-bottom layout for long flows if the project does. Follow the project's diagram conventions.

## 7. Chart tells

- 3D, glossy, or glowing effects; gradient-filled bars.
- Decorative donut charts for one number.
- Legends for a single series; gridlines and borders on everything.
- Titles that describe the chart type ("Bar Chart of Revenue") instead of the finding ("Revenue doubled after the pricing change").

**Fix:** flat marks, direct labels, a title that states the finding. Replace a one-number chart with the number.

## 8. Generated-image tells

Stock AI illustration: glossy 3D isometric scenes, faceless people with smooth skin, glowing brains and circuit boards for "AI", floating devices with holograms, teal-and-orange grading, symmetrical centered compositions, heavy bokeh.

Defects: garbled or near-miss text and logos, wrong finger or limb counts, melted hands and objects, inconsistent shadows and light direction, patterns that blur into noise at the edges, duplicate objects.

**Fix:** for defects, regenerate or crop them out; never ship garbled text in an image. For the style tells, prefer a real screenshot, a photo, a diagram of the actual system, or a plain typographic cover in the site's own style. If the project has a cover-image convention, follow it. Do not replace one generated image with another in the same style.

## 9. Placeholder and filler visuals

Generic hero art, "abstract tech" backgrounds, laptop-on-desk stock photos, illustration packs used unchanged, avatars from the same generator on every testimonial.

**Fix:** remove, or replace with something specific to the subject. A real screenshot of the product beats any illustration of it.

## Keep

- Graphics that show the product, data, or system as it is.
- A brand illustration style the project has documented, even if it uses gradients or glass.
- Alt text: when you remove or replace an image, update or remove its `alt` and any caption that referred to it.
