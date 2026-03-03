# Domain Knowledge Reference

Auto-generated from blog posts. Do not edit manually.
Last updated: 2026-03-03

---

## Source: fundamentals-of-maintainability

URL: https://jeffbailey.us/blog/2026/02/22/fundamentals-of-maintainability

## Introduction

Why do some codebases feel easy to change while others turn every fix into a weekend project? The difference is maintainability.

**Maintainability** is how easily you can modify software to correct faults, improve performance, or adapt to new requirements. The [International Organization for Standardization (ISO)][iso-25010] defines it as a core quality attribute in ISO/IEC 25010. Maintainable code costs less to change, carries lower risk when refactoring, and lets new team members contribute without weeks of orientation.

I've spent more hours than I want to admit untangling code that "worked" but was impossible to modify safely. The symptoms were always similar: functions that did five things, names that lied, TODO comments from years ago, and modules that imported half the codebase. Understanding why those patterns hurt helped me avoid them.

**What this is (and isn't):** This article explains maintainability principles and trade-offs, focusing on *why* certain code structures resist change. It doesn't cover step-by-step refactoring recipes or specific tools. For that, see [Fundamentals of Software Design][software-design] and refactoring guides.

**Why maintainability fundamentals matter:**

* **Lower change cost** - Simple code takes less time to modify and test.
* **Safer refactoring** - Low coupling and clear structure reduce regression risk.
* **Faster onboarding** - New developers understand the system without reverse-engineering.
* **Longer system life** - Systems that stay changeable stay useful.

This article outlines five dimensions that shape maintainability:

1. **Structural complexity:** How many paths through the code, how deep the nesting, how long the functions.
2. **Understandability:** Whether names and flow communicate intent without deep digging.
3. **Technical debt indicators:** TODO/FIXME counts, duplication, magic numbers, lint suppressions.
4. **Coupling and dependency depth:** How modules depend on each other and how deep those dependencies go.
5. **Code smell density:** God classes, long methods, feature envy, shotgun surgery.

> Type: **Explanation** (understanding-oriented).  
> Primary audience: **beginner to intermediate** developers who want to understand why some code is hard to change.

### Prerequisites and Audience

**Prerequisites:** Basic programming experience (you've written and modified code). Familiarity with functions, classes, and modules helps.

**Primary audience:** Developers who modify existing codebases, tech leads setting quality standards, or anyone wondering why "it works" isn't enough.

**Jump to:** [Section 1: Structural Complexity](#section-1-structural-complexity) • [Section 2: Understandability](#section-2-understandability) • [Section 3: Technical Debt Indicators](#section-3-technical-debt-indicators) • [Section 4: Coupling and Dependency Depth](#section-4-coupling-and-dependency-depth) • [Section 5: Code Smell Density](#section-5-code-smell-density) • [Common Mistakes](#section-6-common-maintainability-mistakes) • [Common Misconceptions](#section-7-common-misconceptions) • [When NOT to Prioritize Maintainability](#section-8-when-not-to-prioritize-maintainability) • [Future Trends](#future-trends) • [Limitations and Specialists](#limitations-and-when-to-involve-specialists) • [Glossary](#glossary)

**Escape routes:** If you need a quick audit checklist, skim the TL;DR and the [maintainability review skill][maintainability-skill] in the [skills repository][skills-repo]. If you're deciding whether to invest in maintainability, read Section 1 and Section 4.

### TL;DR: Maintainability Fundamentals in One Pass

If you only remember one workflow, make it this:

* **Keep functions short and shallow** so changes stay local and testable.
* **Name for intent** so readers understand what the code does without tracing call graphs.
* **Extract and track technical debt** so TODO/FIXME and duplication don't accumulate in the dark.
* **Minimize coupling and depth** so one change doesn't ripple across the system.

**The maintainability workflow:**

```text
ASSESS COMPLEXITY → IMPROVE UNDERSTANDABILITY → REDUCE DEBT → LOWER COUPLING → ELIMINATE SMELLS
```

### Learning Outcomes

By the end of this article, you will be able to:

* Explain **why** structural complexity (cyclomatic complexity, nesting, length) affects change cost and when to refactor.
* Describe **why** understandability depends on naming, flow clarity, and consistency.
* Explain **why** technical debt indicators (TODO, duplication, magic numbers) compound over time.
* Understand **why** coupling and dependency depth make changes risky and expensive.
* Describe how code smells signal design problems and when to address them.

## Section 1: Structural Complexity

Structural complexity measures execution paths, logic nesting depth, and code within a unit. High complexity complicates testing, reasoning, and increases bug hiding.

Think of a maze. A simple function is a straight corridor: one path in, one out. A complex function is a maze with branches, loops, and nested rooms. Every branch multiplies the number of paths you must consider when modifying behavior.

### Understanding Structural Complexity

**Cyclomatic complexity** counts the number of independent code paths. Each `if`, `else`, `for`, `while`, `catch`, and `?:` adds a path. A function with complexity 15 has 15 execution paths, so it requires at least 15 test cases to cover them all, since changing one branch might break another.

**Nesting depth** measures how many levels of braces or indent you descend. Deep nesting obscures control flow. A loop inside an `if` inside a `try` inside another `if` means four levels of context to hold in your head. Extract to named functions, and the flow becomes obvious.

**Lines per function and per class** matter because humans have limited capacity. A 200-line function isn't a single abstraction but many concepts packed together. Keep functions under 30 lines and classes under 300 lines for readability.

### Why Low Complexity Helps

Low complexity localizes change, impacting a small, predictable surface. High complexity causes small modifications to trigger unexpected paths, often untested.

Tools like SonarQube and CodeClimate report cyclomatic complexity, with a threshold of 10 for critical paths; above that, consider splitting or simplifying.

### Examples

**High structural complexity:**

```python
def process_order(order):
    if order:
        if order.status == "pending":
            if order.items:
                for item in order.items:
                    if item.quantity > 0:
                        if item.in_stock:
                            if order.customer.verified:
                                if order.payment.valid:
                                    # 7 levels deep, many branches
                                    apply_discount(order, item)
                                    update_inventory(item)
                                    send_confirmation(order)
```

**Lower complexity:**

```python
def process_order(order):
    if not order or not order.is_processable():
        return
    for item in order.items:
        if not item.is_eligible():
            continue
        process_eligible_item(order, item)

def process_eligible_item(order, item):
    apply_discount(order, item)
    update_inventory(item)
    send_confirmation(order)
```

The second version uses guard clauses, early returns, and extraction, with each function having a single responsibility and fewer paths.

### Trade-offs for Structural Complexity

Sometimes complexity is inherent in the problem. A state machine or parser may have many branches by nature. The goal isn't zero complexity; it's complexity that matches the domain and is contained in well-named units.

### Quick Check: Structural Complexity

Before moving on:

* Can you count the cyclomatic complexity of a function by counting branches?
* Why does nesting beyond 4 levels hurt readability?
* What line-count guardrails do you use for functions and classes?

**Answer guidance:** **Ideal result:** You can estimate complexity and explain why long, nested functions are harder to change. If you're unsure, re-read the cyclomatic complexity and nesting sections.

## Section 2: Understandability

Understandability reflects how quickly a developer grasps what code does and why, based on naming, control-flow clarity, and consistency. Code that "works" but needs hours of tracing is costly to maintain.

Names are the main interface between code and reader. A function `process()` says little, while `calculateOrderTotalWithTax()` reveals the action, domain, and scope. Good names diminish the need for comments and clarify misuse.

### Understanding Understandability

**Naming clarity:** Use specific verbs (`validateInput`, `fetchUser`, `applyDiscount`), nouns (`orderTotal`, `userPreferences`), and booleans (`isValid`, `hasPermission`, `canEdit`). Avoid generic names like `data`, `info`, `temp`, or `handler` without context.

**Control-flow clarity:** Code should read top-to-bottom or follow named steps. Hidden side effects, non-obvious mutations, and "clever" control flow hinder understanding. Early returns and helpers clarify the sequence.

**Non-obvious logic:** When the code does something surprising (a workaround, a business rule, an invariant), document the *why*. Links to Architecture Decision Records (ADRs) or issue trackers help. Comments that restate what the code does add noise.

### Why Understandability Matters

Understandable code reduces onboarding time and prevents misinterpretation. Misreading intent may cause bugs or wrong 'improvements'. Clear names and flow make correct changes obvious.

Consistency is as crucial as individual names. When modules return errors while others throw exceptions, developers must remember the correct pattern. Consistent patterns form habits.

### Trade-offs for Understandability

Over-naming can obscure. A 50-character function name may be accurate but unreadable. Balance precision with brevity. Domain jargon helps domain experts but may confuse newcomers; use a glossary or link to domain docs when needed.

### Quick Check: Understandability

* Does `handle()` communicate intent? What would a better name be?
* Why do "why" comments help more than "what" comments?
* How does inconsistency across modules affect maintainability?

**Answer guidance:** **Ideal result:** Names should communicate intent and ensure consistency to reduce cognitive load. If your code uses vague names, consider a naming pass.

## Section 3: Technical Debt Indicators

Technical debt is deferred work that complicates future changes, marked by TODO/FIXME/HACK comments, duplicated logic, magic numbers/strings, and broad lint suppressions. If unchecked, it worsens.

Ward Cunningham compared quick and dirty code to financial debt: borrowing time by skipping quality and paying interest each time it's touched, with interest growing over time.

### Understanding Technical Debt Indicators

**TODO/FIXME/HACK:** A few items are acceptable, but dozens of untracked comments lack ownership and deadlines. Each should link to an issue or have an owner and target date. HACK without explanation is risky.

**Duplication:** Copy-pasted blocks increase maintenance; extract shared logic into functions or modules. The DRY principle states business rules should have one source of truth.

**Magic numbers and strings:** `86400` in code could signify seconds per day or something else. `"active"` might be a status or filter. Named constants (`SECONDS_PER_DAY`, `OrderStatus.ACTIVE`) clarify intent and make changes safer.

**Lint suppressions:** Using `eslint-disable` for an entire file hides new violations, but targeted suppressions with explanations are acceptable. Untracked suppressions accumulate and weaken linting.

**Useless or redundant documentation:** Documentation that duplicates the source of truth, like a README copying directory contents, adds maintenance but offers no unique value. Similarly, docs that restate code or a single canonical document should be avoided. Keep documentation that helps someone understand or do something the code alone doesn't; delete or stop maintaining the rest.

### Why Tracking Debt Helps

Tracking debt prevents hidden growth. Duplication spreads bugs: fix one, miss others. Magic values cause bugs when constants change inconsistently. Suppressions teach the team to ignore lint.

### Trade-offs for Technical Debt

Some TODO comments are acceptable, like "TODO: add retry when backend supports it", but volume and neglect are problems. Enforcing "no new TODO without an issue" prevents buildup.

### Quick Check: Technical Debt

* Why does duplication increase the cost of bug fixes?
* What is the risk of magic numbers when requirements change?
* How many untracked TODO/FIXME comments are in your current project?

**Answer guidance:** **Ideal result:** You can explain how each indicator compounds over time. If your codebase has many untracked items, start by triaging the highest-risk ones.

## Section 4: Coupling and Dependency Depth

Coupling measures module dependency. **Afferent coupling** shows how many modules depend on this one (more dependents = fragile). **Efferent coupling** indicates how many modules this module depends on (more dependencies = rigid). **Dependency depth** reflects layers of transitive dependencies.

A module used by 70% of the codebase becomes a bottleneck: changing it risks breaking most of the system. A module importing 20 others is hard to test alone. Deep inheritance (5+ levels) complicates understanding behavior as it's spread across many classes.

### Understanding Coupling

**Afferent coupling:** High afferent coupling makes a module a hub, with many dependents. Changes ripple widely. Mitigate by defining a narrow, stable API and hiding internals.

**Efferent coupling:** High efferent coupling indicates many dependencies, requiring mocks or multiple dependencies for testing. Prefer using abstractions (interfaces) and dependency injection.

**Dependency direction:** Dependencies should point inward toward the domain. Domain code should not depend on infrastructure (database, HTTP client, UI framework). Inversion keeps the core logic independent of delivery mechanisms.

**Inheritance depth:** Deep inheritance (5+ levels) spreads behavior through many classes, with changes affecting all descendants. Composition and shallow inheritance (2-3 levels) are easier to understand.

### Why Low Coupling Helps

Low coupling means changes stay local; fix bugs in one module without affecting others. Low depth allows understanding a module without tracing long dependencies. Clear boundaries (presentation, domain, data) prevent skip-layer imports.

### Trade-offs for Coupling

Some coupling is inevitable, but aim to minimize it where change occurs. Stable modules tolerate higher coupling; frequently changing ones benefit from isolation.

### Quick Check: Coupling

* What does "afferent coupling" mean? Why is high afferent coupling risky?
* Why should the domain code not depend on the infrastructure?
* How does deep inheritance make changes harder?

**Answer guidance:** **Ideal result:** Coupling increases change cost and dependency direction matters. If your architecture lacks clear boundaries, consider defining layers.

## Section 5: Code Smell Density

Code smells are indicators of deeper design issues. They don't always mean the code is wrong but highlight areas to check. Common ones include god classes, long methods, feature envy, inappropriate intimacy, shotgun surgery, and dead code.

A **god class** with 500+ lines has many responsibilities, risking breaking other features when changed. **Long methods** (50+ lines) conceal multiple concepts and are hard to test. **Feature envy** happens when methods use another object's data more than their own, indicating misplaced logic. **Shotgun surgery** involves making many edits for a single change, showing scattered related logic.

### Understanding Code Smells

**God classes and long methods:** Split by responsibility, use helpers with descriptive names, and keep classes under 300 lines and methods under 30 lines for hot paths.

**Feature envy and inappropriate intimacy:** Move behavior to the data-owning object. Use interfaces to hide internals. Avoid classes accessing each other's private state.

**Shotgun surgery:** Co-locate related logic to prevent scattering a single concept across 10 files. Refactor to group related code.

**Dead code:** Remove unused functions and commented-out blocks. Version control preserves history; dead code causes noise and confusion.

### Why Addressing Smells Helps

Smells indicate refactoring opportunities, which can reduce complexity, improve understanding, and lower coupling. While not all require urgent action, ignoring them can cause issues to worsen.

### Trade-offs for Code Smells

Refactoring costs; focus on smells in frequently changed code. Stable, rarely touched modules may not warrant effort. Use the [maintainability review skill][maintainability-skill] review skill for scores and evidence before fixing.

### Quick Check: Code Smells

* What is "feature envy" and what does it suggest?
* Why does "shotgun surgery" make changes expensive?
* When might you defer addressing a code smell?

**Answer guidance:** **Ideal result:** You recognize common smells and explain why they indicate design issues. If your codebase has many smells, review to prioritize by impact.

## Section 6: Common Maintainability Mistakes

These mistakes create technical debt and increase change costs. Avoiding them saves time and reduces risk.

### Mistake 1: Treating "It Works" as Enough

Shipping code that passes tests but is hard to understand or change. The next developer (or future you) pays the cost.

**Incorrect:** "The tests pass, ship it." No consideration of readability, complexity, or duplication.

**Correct:** Consider maintainability as part of "done." Refactor before merging when complexity or duplication is high.

### Mistake 2: Accumulating TODO Without Tracking

Adding TODO/FIXME comments without linking to issues or assigning owners. They multiply until nobody knows which matter.

**Incorrect:** `// TODO: fix this` with no issue reference, no owner, no priority.

**Correct:** `// TODO(#123): fix validation when API returns null` with an issue that has an owner and target.

### Mistake 3: Copy-Paste Instead of Extract

Duplicating logic to "save time" instead of extracting shared behavior. Each copy becomes a separate place to fix and a source of subtle bugs.

**Incorrect:** Same validation logic in five controllers, each slightly different.

**Correct:** One `validateOrderRequest()` used by all controllers.

### Mistake 4: Deep Nesting Instead of Guard Clauses

Nesting conditionals and loops instead of using early returns or extraction. Deep nesting obscures the happy path.

**Incorrect:** Four levels of `if` with logic at the innermost level.

**Correct:** Guard clauses at the top return early for invalid cases; main logic reads linearly.

### Mistake 5: Ignoring Lint Warnings

Suppressing lint rules broadly instead of fixing the issue causes suppressions to accumulate and the team to ignore lint output.

**Incorrect:** `eslint-disable-next-line` for entire categories or files.

**Correct:** Fix the issue or use a targeted suppression with a comment explaining why and when to remove it.

### Mistake 6: Keeping Useless Documentation

Maintaining documentation that duplicates the source of truth or adds no unique value, like a README listing modules already in the directory, or prose repeating `SKILL.md` or config files. Changes require parallel updates, with the doc providing no new info beyond the code or source.

**Incorrect:** A hand-maintained list of components that quickly becomes outdated with any change; documents kept “for completeness” but unused.

**Correct:** Document the *pattern* or *how to discover* the current set (e.g., “see `src/` for the current list"), dropping redundant enumerations. Keep only docs that help someone do or understand something they couldn’t from the code or one canonical doc alone."”)

### Quick Check: Common Mistakes

* Which mistake have you seen most often in codebases?
* What would "done" include for maintainability in your team?
* How do you decide when to extract duplicated logic?

**Answer guidance:** **Ideal result:** You can specify mistakes and suggest corrections. If your team lacks maintainability standards, consider adopting some guardrails.

## Section 7: Common Misconceptions

* **"Maintainability is a luxury."** It's an investment. Poor maintainability costs in bugs, features, and onboarding. The choice is paying now or later.

* **"We'll refactor later."** Later rarely comes, and debt compounds. The busiest, most critical code is hardest to refactor due to high risk. Refactor while the code is still understandable.

* **"Complexity is unavoidable."** Some complexity is inherent, but much is accidental due to poor decomposition, missing abstractions, and copy-paste. Separate inherent from accidental and reduce the latter.

* **"Naming doesn't matter if the code works."** Names help developers understand code. Bad names cause confusion; good names clarify intent. Code is read more than written.

* **Low coupling** involves few, explicit dependencies—not none. Well-defined interfaces and dependency injection lower coupling while enabling essential collaboration.

## Section 8: When NOT to Prioritize Maintainability

Maintainability isn't always top priority. Knowing when to deprioritize helps focus on what matters.

**Throwaway prototypes:** Code that will be discarded soon doesn't need perfect structure. Keep it simple to run but avoid over-investing.

**Stable, rarely-changed code:** A stable module that hasn't changed in years and isn't planned for changes. Refactoring is risky without clear benefits. Document it and leave it untouched unless necessary.

**Tight deadlines with no slack:** When delay consequences outweigh future costs, accept the debt intentionally and document it. Don't ignore it.

**Learning experiments:** Personal or team experiments to try new approaches aim for learning over production quality. Clean up or delete afterward.

**One-off scripts:** Scripts that run once and are never modified. Prioritize correctness over maintainability for a single run.

Even when deprioritized, basics like meaningful names, avoiding duplication, and noting what the code does help. You may revisit it sooner than expected.

## Building Maintainable Systems

### Key Takeaways

* **Structural complexity:** Keep functions short, shallow nesting, and low cyclomatic complexity. Extract and name helpers.
* **Understandability:** Name for intent. Document implicit logic. Maintain consistency throughout the codebase.
* **Technical debt:** Track TODO/FIXME. Remove duplication. Use named constants instead of magic numbers. Avoid redundant or unnecessary documentation.
* **Coupling:** Minimize coupling, depend on abstractions, and keep dependency depth low.
* **Code smells:** Use signals to address high-impact smells on hot paths first.

### How These Concepts Connect

Complexity, understandability, and smells reinforce each other. Reducing complexity improves understandability. Extracting from a god class reduces coupling. Fixing duplication cuts technical debt. Improving one aspect often benefits others.

### Getting Started with Maintainability

If you're new to maintainability thinking, start with a narrow workflow:

1. **Audit** one module for structural complexity (long functions, deep nesting).
2. **Improve names** in that module so the intent is clear.
3. **Count** TODO/FIXME and duplication in the same module.
4. **Map** coupling: what depends on this module, what does it depend on?
5. **Address** the highest-impact issue first.

Once this feels routine, expand to adjacent modules or run the [maintainability review skill][maintainability-skill] for a scored assessment.

### Next Steps

**Immediate actions:**

* Run `/review:review-maintainability` on your current project (if you have the skill installed).
* Pick one module and estimate its cyclomatic complexity and nesting depth.
* Audit TODO/FIXME in your codebase and create issues for untracked items.

**Learning path:**

* Read [Fundamentals of Naming][naming] for deeper naming guidance.
* Read [Fundamentals of Software Design][software-design] for design principles that support maintainability.
* Explore the [maintainability review skill][maintainability-skill] and its checklist.

**Questions for reflection:**

* Which dimension is weakest in your primary codebase?
* What would "good enough" maintainability look like for your team?
* How do you decide when to refactor versus when to ship?

### The Maintainability Workflow: A Quick Reminder

```text
ASSESS COMPLEXITY → IMPROVE UNDERSTANDABILITY → REDUCE DEBT → LOWER COUPLING → ELIMINATE SMELLS
```

Assess first to understand your position. Improve clarity for safer changes. Reduce debt to prevent compounding. Lower coupling to localize changes. Eliminate smells where most harmful.

### Final Quick Check

Before you move on:

1. Why does cyclomatic complexity matter for testing and change?
2. How do magic numbers create risk when requirements change?
3. What is afferent coupling, and why is high afferent coupling risky?
4. What does "feature envy" suggest about where logic belongs?
5. When might you deliberately deprioritize maintainability?

If any answer feels fuzzy, revisit the matching section.

### Self-Assessment: Can You Explain These in Your Own Words?

* Structural complexity and why it affects change cost.
* Why naming is the primary interface for understandability.
* How technical debt indicators compound over time.
* The difference between afferent and efferent coupling.
* Why code smells are signals, not guarantees.

If you can explain these clearly, you've internalized the fundamentals.

## Future Trends

### AI-Assisted Refactoring

Tools suggesting extractions, renames, and simplifications improve by identifying patterns and proposing changes. Human review remains essential: AI may optimize for metrics without understanding domain intent. Use these tools to speed up refactoring, not replace judgement.

### Automated Maintainability Scoring

Fitness review skills and static analysis tools now score maintainability with `file:line` evidence, tracking trends, and detecting degradation early. More tools will integrate metrics into pull request workflows.

### Shift-Left Maintainability

Teams are applying maintainability checks earlier: in the editor, in pre-commit hooks, and in CI. Catching complexity and duplication before merge reduces rework. The trend is toward continuous feedback rather than periodic audits.

## Limitations and When to Involve Specialists

### When Fundamentals Aren't Enough

Maintainability fundamentals apply to most codebases. Some situations need more:

* **Legacy systems with no tests:** Refactoring without tests is risky. Specialists can design characterization tests and incremental migration strategies.
* **Performance-critical code:** Optimizations sometimes require complexity. A specialist can help distinguish necessary from accidental complexity.
* **Domain-heavy systems:** When business logic is dense and subtle, domain experts, plus maintainability knowledge, produce better outcomes.

### When to Involve Specialists

Consider specialists when:

* A module has resisted multiple refactoring attempts.
* The team lacks experience with the patterns needed (e.g., dependency inversion, event sourcing).
* Legal or compliance requirements constrain how code can be changed.

### Working with Specialists

When working with specialists:

* Share your maintainability goals and constraints.
* Provide the [maintainability review][maintainability-skill] output if you have it; evidence speeds diagnosis.
* Plan incremental changes rather than big-bang rewrites.

## Glossary

## References

### Standards

* [ISO/IEC 25010:2011, Systems and software Quality Requirements and Evaluation (SQuaRE)][iso-25010]: Defines maintainability as a product quality attribute. May have been superseded by newer revisions; verify for current use.
* [ISO 25010 Maintainability Characteristics][iso-25010-detail]: Breakdown of maintainability sub-characteristics (modularity, reusability, analyzability, etc.).

### Tools and Resources

* [SonarQube, Complexity][sonarqube-complexity]: Explains cyclomatic and cognitive complexity metrics.
* [CodeClimate / Qlty, Maintainability][codeclimate-maintainability]: Commercial maintainability scoring and trends (Qlty is the successor to Code Climate Quality).
* [Maintainability review skill][maintainability-skill]: Open-source SKILL.md for fitness review; includes checklist and scoring dimensions.
* [Skills repository][skills-repo]: Installable fitness review skills for Claude Code and Cursor.
* [Glossary of computer science](https://en.wikipedia.org/wiki/Glossary_of_computer_science)

### Related Articles

* [Fundamental Skills][fundamental-skills]: How fitness review skills encode fundamentals into repeatable audits.
* [Fundamentals of Naming][naming]: Naming principles that support understandability.
* [Fundamentals of Software Design][software-design]: Design principles that support maintainability.

### Note on Verification

Maintainability standards and tooling evolve. Verify current ISO revisions and tool capabilities. Test with your actual codebase to ensure metrics and recommendations fit your context.

[iso-25010]: https://www.iso.org/standard/35733.html
[iso-25010-detail]: https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
[sonarqube-complexity]: https://www.sonarsource.com/resources/cognitive-complexity/
[codeclimate-maintainability]: https://docs.qlty.sh/cloud/maintainability/metrics
[maintainability-skill]: https://github.com/jeffabailey/skills/tree/main/src/review-maintainability
[skills-repo]: https://github.com/jeffabailey/skills
[fundamental-skills]: /blog/2026/02/21/fundamental-skills/
[naming]: /blog/2025/12/31/fundamentals-of-naming/
[software-design]: /blog/2025/11/05/fundamentals-of-software-design/
