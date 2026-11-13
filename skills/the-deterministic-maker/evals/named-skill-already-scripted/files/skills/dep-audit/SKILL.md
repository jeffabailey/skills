---
name: dep-audit
description: Lists a project's Python and npm dependencies and flags the ones that are not pinned. Use when the user asks for a dependency audit, asks which dependencies are unpinned, or wants a release-readiness check on dependencies.
metadata:
  version: "1.2.0"
---

# Dependency Audit

## Workflow

1. Run the collector from the project root:

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/list_deps.py" .
   ```

   It prints one row per dependency (name, version spec, source file, `pinned` or `unpinned`) and a totals line. Use the rows as they are; don't open the manifests again.

2. For each unpinned dependency, judge the risk: does the project run it in production, and has it shipped breaking minor releases before? Say what you know and what you are guessing.
3. Report the unpinned dependencies worth pinning first, each with one sentence of reasoning, then the totals line.
