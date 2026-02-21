# Development Process Checklist

A detailed checklist for evaluating repository process maturity. Derived from the Fundamentals series by Jeff Bailey.

---

## 1. Documentation

### README Completeness

- [ ] Project name and one-line description
- [ ] Problem the project solves and who it is for
- [ ] Prerequisites and system requirements
- [ ] Setup and installation instructions (testable, produce working environment)
- [ ] Usage examples with expected output
- [ ] How to run tests
- [ ] How to contribute (or link to CONTRIBUTING.md)
- [ ] License information
- [ ] Contact or support information
- [ ] Badges for build status, coverage, version (where applicable)

Source: Clear documentation reduces support burden and enables self-service. Writing for your audience means starting with their problem. Setup instructions should be testable and produce a working environment.
Reference: [Fundamentals of Technical Writing](https://jeffbailey.us/blog/2025/10/12/fundamentals-of-technical-writing/) and [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)

### API Documentation

- [ ] All public APIs documented with parameters, return values, and error codes
- [ ] Examples for common use cases included
- [ ] Error responses documented with recovery steps
- [ ] API versioning strategy documented
- [ ] Generated docs match current code (not stale)

Source: API documentation should include complete context: endpoint, purpose, request body, response, error responses, and a testable example. Incomplete examples give false confidence.
Reference: [Fundamentals of Technical Writing](https://jeffbailey.us/blog/2025/10/12/fundamentals-of-technical-writing/)

### Architecture Documentation

- [ ] High-level architecture diagram or description exists
- [ ] Key design decisions documented with rationale and trade-offs
- [ ] Architecture Decision Records (ADRs) used for significant choices
- [ ] Component boundaries and responsibilities described
- [ ] Data flow documented for critical paths
- [ ] ADRs reference constraints considered (time, budget, team skills, existing systems)

Source: There is always a design -- an unplanned design is terrible, but it is still a design. Document reasoning for decisions: why did you choose this approach? Consider constraints and think about six-month implications.
Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)

### Content Currency

- [ ] Documentation updated alongside code changes (commits touch both)
- [ ] No references to removed files, tools, or deprecated features
- [ ] Review schedule established (quarterly minimum)
- [ ] Outdated content archived or removed
- [ ] Details prone to change (version numbers, paths) minimized in favor of stable concepts

Source: Outdated docs are worse than no docs. Keep it current. Omit details prone to change and focus on underlying concepts that remain stable.
Reference: [Fundamentals of Technical Writing](https://jeffbailey.us/blog/2025/10/12/fundamentals-of-technical-writing/)

---

## 2. Development Workflow

### Branch Strategy

- [ ] Branching approach is documented or consistently evident in git history
- [ ] Either trunk-based (short-lived branches, frequent merges) or git-flow (feature/release/hotfix branches) followed consistently
- [ ] Branch naming convention followed (feature/, bugfix/, hotfix/ prefixes or equivalent)
- [ ] No long-lived branches accumulating merge conflicts
- [ ] Branch protection rules configured on main/production branches

Source: Choose your branching strategy and apply it consistently. Trunk-based development requires robust CI/CD and disciplined teams. Git-flow provides clear separation of concerns but has longer integration cycles.
Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)

### CI/CD Pipeline

- [ ] CI configuration exists and runs on every pull request
- [ ] Tests execute automatically before merge
- [ ] Linting and formatting checks enforced
- [ ] Build process is scripted and reproducible
- [ ] Deployment is automated or documented step-by-step
- [ ] Pipeline failures block merge

Source: Continuous integration detects problems in hours, not weeks. High release costs slow the feedback loop. Automated delivery extends feedback into production.
Reference: [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/) and [Fundamentals of Software Development Operations](https://jeffbailey.us/blog/2026/01/13/fundamentals-of-software-development-operations/)

### Commit Hygiene

- [ ] Commit messages are descriptive (explain what and why)
- [ ] Convention followed (Conventional Commits, imperative mood, or ticket references)
- [ ] Commits are small and focused (one logical change per commit)
- [ ] History is clean (rebased/squashed when appropriate)
- [ ] No commits with messages like "fix", "update", "wip", "stuff" without context

Source: Commit often with small, focused commits that are easier to understand and review. Write clear commit messages explaining what and why.
Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)

### PR Process

- [ ] Pull request template exists guiding description, testing, and impact
- [ ] PRs are focused and small (under 400 lines preferred)
- [ ] PRs include description of what changed and why
- [ ] PRs reference related issues or tickets
- [ ] PRs include testing evidence (automated test results, manual test steps)

Source: Review code with focused pull requests. Small, concentrated pull requests catch bugs, share knowledge, and are easier to review and merge.
Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)

---

## 3. Code Review Practices

- [ ] Code reviews happen before merge (not post-merge or never)
- [ ] Multiple reviewers engaged for significant changes
- [ ] CODEOWNERS file maps directories to responsible reviewers
- [ ] Review comments are substantive (not just "LGTM")
- [ ] Review turnaround is reasonable (PRs do not sit for weeks)
- [ ] Reviews check for: correctness, readability, test coverage, error handling, security
- [ ] Knowledge sharing happens through reviews (not just gatekeeping)

Source: Fresh eyes see different things. Code reviews are regular peer review of code quality. Pair programming and mob programming spread knowledge and boost quality.
Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/) and [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/)

---

## 4. Dependency Management

### Lockfiles and Pinning

- [ ] Lockfile exists and is committed (package-lock.json, Cargo.lock, go.sum, poetry.lock, etc.)
- [ ] Lockfile is NOT in .gitignore
- [ ] Dependency versions pinned or bounded (not floating "latest")
- [ ] Dependency policy documented (criteria for adding new dependencies)

### Update Cadence

- [ ] Automated dependency update tool configured (Dependabot, Renovate, or equivalent)
- [ ] Update PRs appear regularly in history
- [ ] Dependencies not more than one major version behind
- [ ] Security patches applied promptly (within days, not months)

### Vulnerability Management

- [ ] Vulnerability scanning configured (Snyk, npm audit, cargo audit, OWASP dependency-check)
- [ ] No known critical vulnerabilities in dependency tree
- [ ] Remediation plan exists for known vulnerabilities
- [ ] License compliance tracked or documented

Source: Keep third-party libraries up to date. Dependency management is part of security-first development. Automated security vulnerability detection helps catch problems early.
Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/) and [Fundamentals of Software Development Operations](https://jeffbailey.us/blog/2026/01/13/fundamentals-of-software-development-operations/)

---

## 5. Project Organization

### Directory Structure

- [ ] Structure follows recognizable pattern for language/framework
- [ ] Module boundaries are clear (not everything in one flat directory)
- [ ] Entry points are obvious (main, index, handler files clearly named)
- [ ] Test files co-located or in clear parallel structure
- [ ] Logical grouping: source, tests, configuration, documentation separated

### Configuration Management

- [ ] Configuration separated from code
- [ ] Environment variables used for environment-specific values
- [ ] No hardcoded secrets, API keys, or credentials in source
- [ ] Configuration documented with defaults and valid values
- [ ] .env.example or equivalent provided for required environment variables

### Repository Hygiene

- [ ] .gitignore is comprehensive for the tech stack
- [ ] No build artifacts committed
- [ ] No IDE-specific files committed (unless team-agreed)
- [ ] No large binary files committed without LFS
- [ ] Repository size is reasonable

Source: Consistent formatting, logical structure, clear interfaces. Use linters and formatters. Group related code together. Plan for potential issues.
Reference: [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/)

---

## 6. Agile and Iteration Signals

### Iteration Evidence

- [ ] Work organized in iterations or sprints (visible in issue tracker or project board)
- [ ] Each iteration delivers working software (not partial features across many iterations)
- [ ] Regular demos or reviews occur (release notes, sprint reviews, changelogs)
- [ ] Velocity or throughput is tracked (not gamed)

### Retrospective Artifacts

- [ ] Evidence of retrospectives (notes, action items, process changes)
- [ ] Action items from retrospectives are tracked and completed
- [ ] Process improvements visible over time (not same problems recurring)

### Backlog Health

- [ ] Issues are triaged and labeled
- [ ] Issues have clear acceptance criteria
- [ ] Stale issues are closed or revisited periodically
- [ ] Priorities are visible (milestones, labels, or board columns)
- [ ] Technical debt tracked with dedicated labels or backlog

Source: Short iterations create learning opportunities. Feedback shapes outcomes. Retrospectives only matter if they lead to experiments the team actually tries. "Working software in use" is a stronger outcome signal than a number on a board. Skipping retrospectives or building partial features limits feedback.
Reference: [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/) and [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/)

---

## 7. Open Source Readiness

### Required Files

- [ ] LICENSE file present with OSI-approved license (if open source)
- [ ] LICENSE file specifies correct license text (not just a name)
- [ ] CONTRIBUTING.md with clear contribution workflow
- [ ] CODE_OF_CONDUCT.md establishing community norms

### Contributor Experience

- [ ] Issues labeled "good first issue" or "help wanted" for newcomers
- [ ] Contribution workflow documented (fork, branch, PR, review cycle)
- [ ] Development environment setup is scripted or containerized
- [ ] Response time to contributions is reasonable (PRs not ignored for months)
- [ ] Templates for issues and PRs guide contributors

### Governance

- [ ] Decision-making process documented or evident
- [ ] Maintainer roles and responsibilities clear
- [ ] License compatibility of dependencies verified
- [ ] Contributor License Agreement (CLA) or Developer Certificate of Origin (DCO) if required

Source: Licenses set rules for creators and users. Contribution is a relationship -- the code matters, but communication and follow-through usually matter more. Clear goals, contribution guidelines, and documentation reduce contributor friction. Communities require more than goodwill; projects succeed when expectations are clear and contributors feel safe, respected, and effective.
Reference: [Fundamentals of Open Source](https://jeffbailey.us/blog/2025/03/06/fundamentals-of-open-source/)

---

## 8. Operational Readiness

### Monitoring and Observability

- [ ] Health check endpoints exist
- [ ] Metrics instrumentation present (response times, error rates, throughput)
- [ ] Structured logging implemented (not just print statements)
- [ ] Alerting configured for critical failures
- [ ] Dashboards exist for operational visibility

### Incident Response

- [ ] On-call or incident response process documented
- [ ] Runbooks exist for common failure scenarios
- [ ] Post-mortem process documented and practiced
- [ ] Rollback procedure documented and tested

### Reliability Practices

- [ ] Error handling is consistent across the codebase
- [ ] Graceful degradation patterns present (timeouts, circuit breakers, retries)
- [ ] Load testing or capacity planning evidence exists
- [ ] Disaster recovery plan documented

Source: Operations can't manage what they can't see. Build visibility from the start. Your deployment practices determine execution speed. Your code quality determines operational reliability. Systems without monitoring fail silently, causing cascading damage before detection.
Reference: [Fundamentals of Software Development Operations](https://jeffbailey.us/blog/2026/01/13/fundamentals-of-software-development-operations/)

---

## 9. Decision Quality

### Avoiding Common Fallacies

- [ ] Decisions documented with rationale (not just conclusions)
- [ ] Alternatives considered and documented (not false dichotomies)
- [ ] Technology choices justified by project needs (not authority appeals or hype)
- [ ] Estimates grounded in historical data (not optimism)
- [ ] Sunk cost reasoning does not drive "continue vs. stop" decisions
- [ ] Change requests evaluated for impact before acceptance (scope management)

### Project Management Signals

- [ ] Success criteria defined for major initiatives
- [ ] Scope clearly documented with in-scope and out-of-scope items
- [ ] Risk register or risk tracking exists for significant projects
- [ ] Regular status communication visible (not silence followed by surprises)
- [ ] Dependencies between projects or teams identified and tracked

Source: Software development is fundamentally about making decisions. The sunk cost fallacy traps teams in failing projects. False dichotomies limit options. The planning fallacy causes underestimates. Clear scope prevents rework and scope creep. Risk management prepares you for problems. Regular communication prevents surprises.
Reference: [Logical Fallacies in Software Development](https://jeffbailey.us/blog/2026/02/01/logical-fallacies-in-software-development/), [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/), and [Fundamentals of Program Management](https://jeffbailey.us/blog/2026/01/09/fundamentals-of-program-management/)

---

## 10. Product Alignment

- [ ] User problems documented (not just feature specs)
- [ ] Product metrics defined and tracked (adoption, retention, engagement)
- [ ] Feature validation evidence exists (user research, A/B tests, usage data)
- [ ] Iteration based on feedback visible (not build-and-forget)
- [ ] Roadmap or vision document aligns development with user needs
- [ ] Success criteria follow SMART framework (Specific, Measurable, Achievable, Relevant, Time-bound)

Source: Product development creates software that solves real problems. Build features that matter by focusing on user needs and validating value. Measure success using metrics that reveal whether products work. Validate continuously -- taste as you cook. "Build it and they will come" is a myth.
Reference: [Fundamentals of Software Product Development](https://jeffbailey.us/blog/2025/11/28/fundamentals-of-software-product-development/)

---

## Source Articles

All checklist items are derived from the following articles:

1. [Fundamentals of Software Development](https://jeffbailey.us/blog/2025/10/02/fundamentals-of-software-development/) - Decision-making, version control, testing, code quality, design principles
2. [Fundamentals of Agile Software Development](https://jeffbailey.us/blog/2025/12/23/fundamentals-of-agile-software-development/) - Iteration, feedback, collaboration, retrospectives, technical practices
3. [Fundamentals of Software Product Development](https://jeffbailey.us/blog/2025/11/28/fundamentals-of-software-product-development/) - User research, MVP validation, metrics, product iteration
4. [Fundamentals of Software Project Management](https://jeffbailey.us/blog/2026/01/12/fundamentals-of-software-project-management/) - Scope, planning, risk management, triple constraint, communication
5. [Fundamentals of Technical Writing](https://jeffbailey.us/blog/2025/10/12/fundamentals-of-technical-writing/) - Documentation quality, audience awareness, content currency, information architecture
6. [Fundamentals of Open Source](https://jeffbailey.us/blog/2025/03/06/fundamentals-of-open-source/) - Licensing, contributing, governance, community, project management
7. [Fundamentals of Program Management](https://jeffbailey.us/blog/2026/01/09/fundamentals-of-program-management/) - Strategic alignment, project coordination, dependency management, governance
8. [Fundamentals of Software Development Operations](https://jeffbailey.us/blog/2026/01/13/fundamentals-of-software-development-operations/) - Development velocity, reliability, operational visibility, cross-functional coordination
9. [Logical Fallacies in Software Development](https://jeffbailey.us/blog/2026/02/01/logical-fallacies-in-software-development/) - Sunk cost, false dichotomy, confirmation bias, planning fallacy, decision quality
