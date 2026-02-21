# Trigger Tests

Verify each skill loads at the right time and doesn't load for unrelated queries.

## review-architecture

Should trigger:
- "Review the architecture of this project"
- "Check coupling and cohesion"
- "Analyze the design of this codebase"
- "How is the code structured?"
- "Review naming conventions"
- "Check API design"
- `/review:review-architecture`

Should NOT trigger:
- "Fix this bug"
- "Write a unit test"
- "Deploy to production"

## review-security

Should trigger:
- "Security review"
- "Check for vulnerabilities"
- "Audit security of these changes"
- "Are there any security issues?"
- `/review:review-security`
- `/security-review`

Should NOT trigger:
- "Review the architecture"
- "Check performance"
- "Write documentation"

## review-reliability

Should trigger:
- "Review reliability of this service"
- "Check observability"
- "Is this production-ready?"
- "Review monitoring setup"
- "Check CI/CD pipeline"
- "Audit operational readiness"
- `/review:review-reliability`

Should NOT trigger:
- "Write a test"
- "Fix the CSS"
- "Add a new feature"

## review-testing

Should trigger:
- "Review test quality"
- "Analyze test coverage"
- "Is our testing strategy good?"
- "Check test pyramid balance"
- "Review QA practices"
- `/review:review-testing`

Should NOT trigger:
- "Generate tests" (that's review-jit-test-gen)
- "Fix the deployment"
- "Review the API design"

## review-performance

Should trigger:
- "Check performance"
- "Review scalability"
- "Are there any bottlenecks?"
- "Analyze database queries"
- "Check for N+1 queries"
- "Review caching strategy"
- `/review:review-performance`

Should NOT trigger:
- "Run the tests"
- "Review security"
- "Check accessibility"

## review-algorithms

Should trigger:
- "Review algorithm correctness"
- "Check concurrency safety"
- "Are the right data structures being used?"
- "Check for race conditions"
- "Review edge case handling"
- "Algorithm review"
- `/review:review-algorithms`

Should NOT trigger:
- "Check performance" (that's review-performance)
- "Review security"
- "Generate tests"

## review-data

Should trigger:
- "Review database schema"
- "Check migration safety"
- "Data integrity review"
- "Review data modeling"
- "Check query correctness"
- "Schema design review"
- `/review:review-data`

Should NOT trigger:
- "Check database performance" (that's review-performance)
- "Review security"
- "Check test quality"

## review-accessibility

Should trigger:
- "Check accessibility"
- "Review a11y compliance"
- "Is this WCAG compliant?"
- "Check color contrast"
- "Review keyboard navigation"
- "Audit usability"
- `/review:review-accessibility`

Should NOT trigger:
- "Review backend performance"
- "Check database design"
- "Review CI/CD pipeline"

## review-process

Should trigger:
- "Review development process"
- "Check documentation quality"
- "Is this repo well-organized?"
- "Review project health"
- "Audit development practices"
- `/review:review-process`

Should NOT trigger:
- "Fix this bug"
- "Write a new feature"
- "Check for security issues"

## review-full

Should trigger:
- "Full review"
- "Comprehensive review"
- "Review everything"
- "Project fitness check"
- "Pre-ship review"
- `/review:review-full`

Should NOT trigger:
- "Review just the architecture"
- "Check only security"
- "Generate tests"

## review-jit-test-gen

Should trigger:
- "Generate tests for my changes"
- "Write tests"
- "JIT test generation"
- "Create tests for this code"
- `/review:review-jit-test-gen`

Should NOT trigger:
- "Review test quality" (that's review-testing)
- "Run the tests"
- "Check performance"
