# Purpose Signals

How to tell what a project is for from a small, read-only scan. The result is a classification: one archetype from `purpose-profiles.md`, `mixed`, or `unknown`, plus a confidence level and the evidence paths behind it.

## Read budget

The fast scan reads at most 40 files. Listing directories does not count toward the budget; opening a file does.

- Never run project code, install dependencies, or use the network.
- Never write, move, or delete anything in the project.
- Cite only paths that your own read or list tools returned. If a path was not returned by a tool, it is not evidence.

## Scan order

Stop reading once the classification is high confidence or the budget is spent.

1. **Layout.** In a git repository, run `git -C <target> ls-files` and count files by extension and top-level directory. Without git, list the top level and one level below it. Note any manifest or site-generator config one folder down (for example `hugo/config.toml`, `site/astro.config.mjs`, `web/package.json`): many repositories keep the site or app in a subfolder, and the later steps apply there too.
2. **README.** The first README at the target root. Look for what the project says it is and who uses it.
3. **Manifests.** `package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`, `pom.xml`, `build.gradle*`, `Gemfile`, `composer.json`, `*.csproj`. Read dependencies and any `bin` or entry-point fields.
4. **Deploy and CI.** `Dockerfile`, `docker-compose*`, Kubernetes manifests, Helm charts, Terraform, `.github/workflows/*`, static-site host config (`netlify.toml`, `vercel.json`), and static-site generator config (`hugo.toml`, `config.toml`, `astro.config.*`, `_config.yml`, `mkdocs.yml`, `docusaurus.config.*`) at the root or in the subfolder found in step 1.
5. **Entry points.** Only if still unclear: `main.*`, `cmd/`, `src/index.*`, `app/`, route or handler directories, and executable scripts at the root (`*.sh`, `*.bash`, `*.zsh`, `*.fish`, or files with a shebang and no extension). Read the first screen of each, plus the dispatch block of a script; do not trace code.

A project with no README or manifest is common for small shell tools. Do not lower confidence just because those files are missing; judge the signals that are there.

## Signals by archetype

A strong signal on its own points at one archetype. Disqualifiers rule an archetype out even when a strong signal is present.

| Archetype | Strong signals | Disqualifiers |
|---|---|---|
| database-backend | Database driver or ORM in the manifest (`pgx`, `psycopg`, `sqlalchemy`, `prisma`, `gorm`, `diesel`); a `migrations/` or `schema/` directory; a StatefulSet, PersistentVolumeClaim or managed database in deploy config; a README describing stored records | Pages or templates served to people (then consider `mixed`) |
| web-frontend | HTML templates, `content/` of Markdown pages, static-site generator config at the root or in a subfolder (`hugo/config.toml`, `site/astro.config.mjs`); frontend framework dependencies (`react`, `vue`, `svelte`, `astro`, `next`); CSS or asset pipelines; a static host config | No pages a person visits (build output only consumed by other code) |
| cli-tool | `bin` field in `package.json`, `[project.scripts]` in `pyproject.toml`, a `cmd/` directory in Go, argument parsing libraries (`cobra`, `clap`, `click`, `argparse` as the entry point); a shell script with a shebang that dispatches on its arguments (`case "$1"`, `getopts`, `while [[ $# -gt 0 ]]`) and prints a `usage:` line; a README or other doc showing shell usage | Long-running server entry point |
| library-sdk | Published package metadata with no entry point; `src/` or `lib/` exporting a public API; API docs or typed stubs; examples of importing the package | A deploy config for a running service |
| data-pipeline | Orchestrator or job config (`airflow`, `dagster`, `prefect`, `dbt_project.yml`, cron or batch jobs); `extract`/`transform`/`load` directories; schema files for inputs and outputs | Request handlers that answer users directly |
| api-service | HTTP or gRPC server framework (`express`, `fastapi`, `gin`, `axum`, `spring-boot`); route or handler directories; OpenAPI or `.proto` files; a Deployment with a Service or ingress; calls out to payment, auth or other external APIs | Its own database migrations or stateful storage (then `database-backend`) |

Signals are independent when they come from different files or different kinds of evidence. A manifest dependency and a deploy manifest are two signals. Two dependencies in the same manifest are one.

## Confidence

| Level | Meaning | What the skill does |
|---|---|---|
| high | Two or more independent strong signals for one archetype, and no strong signal for a competing archetype | Use that archetype's profile |
| medium | One strong signal only, or strong signals for two archetypes (`mixed`) | Ask the user for the primary purpose before proposing |
| low | No strong signal for any archetype | Ask once. With no answer, classify as `unknown` and keep the baseline |

`unknown` always has low confidence. A user's answer sets the confidence to `user-confirmed`. A purpose the user already stated in the request counts as that answer, so do not ask again; see step 3 of `SKILL.md`.

## Reporting the classification

Show one line for the purpose in plain words, the archetype ID, and the confidence. Then list the evidence, one path per line with a short note on what it shows:

```text
Purpose: database-backed service (no UI)   archetype: database-backend   confidence: high
Evidence (fast scan):
  go.mod                     pgx/v5 dependency
  migrations/                23 SQL migrations
  deploy/statefulset.yaml    StatefulSet with a PodDisruptionBudget
```

If the user corrects the purpose, use their answer and say so. Do not argue with the correction.
