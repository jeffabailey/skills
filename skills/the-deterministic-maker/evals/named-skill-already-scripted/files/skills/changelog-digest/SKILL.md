---
name: changelog-digest
description: Turns the change notes in changes/ into a release digest with counts by type, the breaking changes, and a short summary. Use when the user asks for a changelog digest, a release summary, or "what's in this release".
metadata:
  version: "1.0.0"
---

# Changelog Digest

Each file in `changes/` is one change. Its frontmatter has `title`, `type` (feat, fix, chore, or docs), `scope`, and `breaking` (true or false).

## Workflow

1. List every file in `changes/`. Open each one and read its frontmatter.
2. Count the entries of each type. Work out each type's percentage of the total, rounded to a whole number.
3. List all entries marked `breaking: true`, with the file name and the title.
4. Count the entries per scope and find the scope with the most entries.
5. Write the digest:
   - a table of types with counts and percentages
   - the breaking changes
   - two or three sentences on what this release is mostly about and what a user should watch for when upgrading

Check that the counts in the table add up to the number of files before you finish.
