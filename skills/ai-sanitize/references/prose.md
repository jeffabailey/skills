# Prose Tells

Tells in writing, from single words up to whole-piece structure. Items are numbered so reports can cite them ("Prose 3"). **High signal** items are the ones to fix first when a cluster appears.

Enforcement rule: if a sentence matches a pattern below and fails the removal or reason test, rewrite it. Do not just delete the flagged word and leave a broken sentence.

Scope: applies to articles, docs, READMEs, commit and PR text, emails, and UI copy (headings, buttons, empty states, tooltips). For UI copy, also read `ui.md` items 13 to 15.

## 1. Performative and AI-coded phrases (high signal)

Phrases that perform tone instead of carrying content.

- "No fluff", "Let's dive in", "Let's dive deep", "Let's unpack this"
- "Here's the kicker", "Here's the thing", "The best part?", "The important part is this"
- "And honestly...", "Let me be honest", "Read this twice"
- "You're not imagining this", "You're thinking about this exactly the right way", "That's rare"
- "Let me ground you", "Shouting into the void"
- "Quietly [doing something]" ("quietly reshaping how teams work")
- "Key takeaway", "The bottom line"
- "load-bearing" (figurative), "the whole trick", "keeps [it] honest", "X are real" (as in "the tradeoffs are real")
- "fostering", "delve", "tapestry", "testament to", "navigate the complexities", "in today's fast-paced world", "ever-evolving landscape", "at the end of the day", "game-changer", "a deep dive"

**Fix:** state the point directly. "Here's the kicker: the cache never expires" becomes "The cache never expires." Replace figurative stock phrases with the literal claim: "the tradeoffs are real" becomes "the tradeoffs exist" or, better, names the tradeoff. "Keeps the test honest" becomes "keeps the test correct".

**Detect:** `grep -niE "dive in|deep dive|here's the (kicker|thing)|the best part\?|no fluff|honestly|quietly |key takeaway|load.bearing|the whole trick|keeps? .* honest|foster|delve|tapestry|testament|landscape|game.changer|fast-paced"`

## 2. Marketing buzzwords and hype (high signal)

"Elevate", "seamless", "next-generation", "supercharge", "unleash", "unlock", "empower", "harness", "revolutionize", "transform your workflow", "robust", "cutting-edge", "world-class", "effortless", "powerful", "blazing fast".

**Fix:** replace with what the thing does, measured if possible. "A powerful, blazing-fast search" becomes "Search returns results in under 50 ms on 10,000 posts." If there is no concrete fact to put in its place, delete the adjective.

**Detect:** `grep -niE "elevat|seamless|next.gen|supercharg|unleash|unlock|empower|harness|revolutioni|robust|cutting.edge|world.class|effortless|blazing"`

## 3. Contrast framing as a crutch (high signal)

- "It's not X, it's Y" / "This isn't A. It's B." / "Not chaos. Clarity."
- "X isn't just Y, it's Z" / "More than just a tool"

Contrast is legitimate when the reader actually holds the wrong belief X. It is a tell when X is a straw man added for rhythm.

**Fix:** state Y. "This isn't a to-do app. It's a system for your life." becomes whatever the product concretely does: "It schedules tasks around your calendar."

**Detect:** `grep -niE "(it'?s|this is|that'?s) not (just )?[a-z ]+[,.;:] (it'?s|this is)|isn'?t just|not just a|more than just"`

## 4. Fragmented pseudo-profound sentences

- Short. Isolated. Fragments.
- One-sentence paragraphs and line breaks used for weight.
- A closing fragment that restates the paragraph ("Simple. Fast. Done.").

**Fix:** join fragments into full sentences that carry the reasoning between them. Keep a short sentence only where the rhythm serves a real turn in the argument, at most once per section.

## 5. Reflexive triads

Grouping everything in threes: three adjectives, three bullets, three parallel clauses, "fast, reliable, and scalable".

**Fix:** use the number of items the content actually has. If two of the three are filler, keep one. If there are five, list five.

## 6. Over-signposting

- "Here's the key takeaway", "Let's back up", "To be clear", "Before we move on", "It's worth noting that", "Importantly,"
- Telling the reader what to feel, notice, or remember ("This is where it gets interesting").
- "In this article, we will explore..." intros and "In conclusion" / "In summary" outros that repeat the body.

**Fix:** delete the signpost and let the sentence after it stand. Replace summary outros with a concrete next step, or end the piece where the content ends.

## 7. Fake engagement

- Hollow closing questions: "Curious what others think?", "What's your take?", "Let me know in the comments!"
- Rhetorical questions the text immediately answers ("So what does this mean? It means...").

**Fix:** delete them. Keep a question only if the author will answer replies or the question is genuinely open.

## 8. Over-validation and therapizing

Unneeded empathy, affirmation of basic observations, and patronizing reassurance ("Great question!", "It's completely normal to feel overwhelmed", "You've got this!"), unless the reader asked for emotional support.

**Fix:** delete, and start with the answer.

## 9. Performed insight

Writing that signals depth before earning it: inspirational cadence, "quiet truths", "silent revolutions", "subtle realizations", "the real lesson here", "and that changes everything". Anything that sounds like a LinkedIn post, ad copy, or an influencer caption.

**Fix:** deliver the insight as a plain claim with its evidence. If there is no claim under the cadence, cut the passage.

## 10. Vague escalation and melodrama

"Nightmare scenario", "things get really ugly", "a recipe for disaster", "this is where it all falls apart".

**Fix:** say what actually happened or would happen. "Things get ugly" becomes "the deploy fails and rolls back half the services." For lists of possible failures, prefer "Beware of these potential failures" over "failure modes".

## 11. Emdashes (high signal in bulk)

Emdashes (—) used as the default clause joiner. One is punctuation; one per paragraph is a tell.

**Fix:** use a comma, colon, parentheses, or a period, or rewrite the sentence. If the project's style guide bans emdashes, remove every one.

**Detect:** `grep -n "—"` (also check for ` -- ` used as a dash).

## 12. Formatting as personality

- Bold scattered through paragraphs; bolded full sentences; bold plus italics.
- Bullet lists for narrative that should be prose.
- Headers that restate the obvious ("Introduction", "Why This Matters", "Conclusion").
- Emoji as bullets, as emphasis, or in headings (✨, 🚀, 💡, ✅, 🔥).
- ALL CAPS or underlining for stress.
- Every paragraph ending in a colon that introduces a list.

**Fix:** emphasis is subtractive and works only because most text has none. Allow at most two or three bold or italic runs per section. Bold only short lead-in labels or true warnings. Italics for genuine stress, a term on first mention, or titles. Turn narrative bullets back into paragraphs. Remove decorative emoji; keep at most one per section when it carries tone.

**Detect:** count `\*\*` per section; `grep -nP "[\x{1F300}-\x{1FAFF}\x{2728}\x{2705}]"`.

## 13. Hedging by habit and false balance

"It depends", "there are pros and cons", "both approaches have merit", "may potentially", "could possibly" when the author has an opinion or the evidence points one way.

**Fix:** state the position, then the condition under which it changes. "It depends on your needs" becomes "Use Postgres unless you need offline sync; then use SQLite."

## 14. Generic examples and placeholders

"Imagine a company called Acme", "for example, a user might want to...", "consider a scenario where...", examples that could appear in any article on the topic.

**Fix:** use a concrete, specific example: a real command, a real number, a real error message, a real scene. If the author supplied one elsewhere in the draft, use theirs.

## 15. Clarity rules (Strunk)

Apply after removing the tells above; AI prose often passes the phrase check and still reads soft.

- **Active voice.** "Scripts that have never been run" becomes "Scripts nobody has run."
- **Positive form.** "Does not cover" becomes "omits"; "not always the right answer" becomes "sometimes the wrong answer". Recast double negatives.
- **Omit needless words.** Cut "that is", "there is", "in order to", "the fact that", "it should be noted that".
- **Concrete language.** "Some tasks happen rarely" becomes "tasks that run once a quarter".
- **Emphatic words at the end.** "A backup script that stopped working is not a backup" becomes "A backup script that stopped working is a liability."
- **Related words together.** Keep modifiers next to what they modify.
- **Parallel structure.** Keep list items in one grammatical form.
- **Split parenthetical interruptions** that break a sentence's main predicate into two sentences.

## Do not "fix" these

- The author's profanity, slang, humor, sarcasm, or strong opinion. If the source swears, the result swears.
- First person in personal essays. (Tutorials and how-to guides use imperative and second person instead; follow the project's rule.)
- Sentences starting with "And" or "But" when they read like speech.
- Technical terms, product names, quoted text, code, and command output.
- A pattern the author clearly chose on purpose and uses once (a single deliberate fragment, a real contrast).

Final pass: write plainly. Favor continuity over fragmentation. Let insight come from explanation, not cadence. Match tone to substance.
