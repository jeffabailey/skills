# Incident Response

Failure modes for the Project Fitness Review skills and their CI/CD pipeline.

## Severity Levels

| Level | Definition | Example | Response |
|-------|-----------|---------|----------|
| P1 | Skills produce incorrect or dangerous recommendations | Security skill misses a real vulnerability | Fix skill, notify users, publish corrected report |
| P2 | CI/CD pipeline broken for all engines | Workflow YAML syntax error | Fix immediately — all reviews blocked |
| P3 | Single engine broken | API key expired, engine-specific CLI change | Switch to alternate engine, fix when possible |
| P4 | Cosmetic or non-blocking | Report formatting issue, minor scoring inaccuracy | Fix in next PR |

## Troubleshooting

See [`.github/RUN.md`](../.github/RUN.md) for step-by-step troubleshooting of:

- 529 Overloaded (Claude/Anthropic)
- Agent timeout
- MCP server failure
- Workflow concurrency queue exhaustion
- Skill installation failure
- Engine secret missing or invalid

## Rollback

Skills are plain Markdown files tracked in git. To roll back a bad skill change:

```bash
git revert <commit-sha>
git push
```

For workflow changes, revert the specific commit that modified `.github/workflows/fitness-review.yml`.

## Contacts

- Repository owner: [@jeffabailey](https://github.com/jeffabailey)
- Workflow platform (gh-aw): [github.github.io/gh-aw](https://github.github.io/gh-aw/)
