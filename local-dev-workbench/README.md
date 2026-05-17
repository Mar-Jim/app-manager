# local-dev-workbench

Local-first developer workbench for creating, editing, validating, testing, and managing Databricks Asset Bundles, Databricks Apps, local assistant apps, Codex prompts, handoff files, local todos, and future Azure DevOps ticket updates.

The initial version is intentionally conservative: it can detect local project types, expose local API data, render a local dashboard, and generate command suggestions. It does not execute risky commands automatically.

## Requirements

- Python 3.11+
- Node.js 20+
- npm

## Install Python Package

```bash
cd local-dev-workbench
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run CLI

```bash
workbench doctor
workbench detect
workbench detect --json
workbench commands list
workbench commands suggest
workbench commands run validate-bundle
workbench commands run deploy-dev --yes
workbench create bundle-job my-job
workbench create bundle-pipeline my-pipeline
workbench create bundle-sql my-sql
workbench create bundle-dashboard my-dashboard
workbench todo add "Review failing test"
workbench todo list
workbench todo complete 1
workbench worklog add "Finished SQLite-backed local todos"
workbench worklog summary
workbench ado tickets list
workbench ado ticket show 123
workbench ado ticket draft-update 123 --note "Validated locally"
workbench ado ticket post-update 123 --from-draft --yes
workbench handoff create
```

`workbench detect` reads local files only. It detects Databricks Asset Bundles, Databricks Apps, Python projects, Node projects, VS Code extensions, and unknown folders. For Databricks Asset Bundles, it parses `databricks.yml` or `databricks.yaml`, reports target names, and adds a deployment strategy hint for dev-only and dev/stg/prd target layouts.

## Create Databricks Asset Bundle Projects

The `workbench create` commands generate compact starter Databricks Asset Bundle repos using Jinja templates under `templates/databricks_bundle_*`.

Available project types:

- `workbench create bundle-job NAME`
- `workbench create bundle-pipeline NAME`
- `workbench create bundle-sql NAME`
- `workbench create bundle-dashboard NAME`

Options:

- `--output-dir PATH`
- `--force`
- `--include-github-action/--no-include-github-action` defaults to disabled
- `--deployment-strategy external-deployer`
- `--target dev`

Generated bundles intentionally include only a `dev` target. Staging and production deployments are expected to be handled by the external deployer repo.
When `--include-github-action` is set, the generator adds a dev-target bundle validation workflow only; it does not deploy staging or production.

## Track Local Work

Local todos, work log entries, and ticket-note-ready drafts are stored in SQLite under `.workbench/workbench.sqlite3` in the current working directory. Nothing is sent to Azure DevOps or any external service.

```bash
workbench todo add "Finish API tests"
workbench todo list
workbench todo complete 1
workbench worklog add "Implemented local work log summary"
workbench worklog summary
```

Daily summaries are generated as draft text:

```text
Today I worked on:
Completed:
In progress:
Blockers:
Next steps:
```

The service layer is local-first and keeps ticket note storage separate so Azure DevOps publishing can be added later without changing the todo and work log APIs.

## Azure DevOps Tickets

Azure DevOps support is local-first and permissioned. The workbench can read assigned tickets through the Azure DevOps REST API when local configuration is present, store ticket notes and draft updates in SQLite, and post a drafted update only after explicit approval.

Configuration can come from SQLite metadata or environment variables. PAT values are never stored in SQLite; only the auth mode and env var name are stored.

Environment variables:

- `WORKBENCH_ADO_ORGANIZATION_URL`, such as `https://dev.azure.com/my-org`
- `WORKBENCH_ADO_PROJECT`
- `WORKBENCH_ADO_DEFAULT_QUERY`, optional WIQL query
- `WORKBENCH_ADO_AUTH_MODE`, defaults to `pat_env`
- `WORKBENCH_ADO_PAT_ENV_VAR`, defaults to `AZURE_DEVOPS_EXT_PAT`
- the PAT env var named by `WORKBENCH_ADO_PAT_ENV_VAR`

If organization, project, or token configuration is missing, the CLI, API, and web UI return setup guidance instead of failing the app.

```bash
workbench ado tickets list
workbench ado ticket show 123
workbench ado ticket draft-update 123 --note "Finished local validation"
workbench ado ticket post-update 123 --from-draft --yes
```

Draft updates are deterministic local text built from ticket metadata and local notes. `post-update` refuses to run unless the latest local draft is selected with `--from-draft` and explicitly approved with `--yes`.

## Run Backend

```bash
workbench serve
```

The API binds to `127.0.0.1:8787` by default.

Available endpoints:

- `GET /health`
- `GET /api/project/detect`
- `GET /api/commands`
- `GET /api/commands/suggest`
- `POST /api/commands/run`
- `POST /api/projects/create`
- `GET /api/todos`
- `POST /api/todos`
- `POST /api/todos/{id}/complete`
- `GET /api/worklog`
- `POST /api/worklog`
- `GET /api/worklog/summary`
- `GET /api/ado/tickets`
- `GET /api/ado/tickets/{id}`
- `POST /api/ado/tickets/{id}/draft-update`
- `POST /api/ado/tickets/{id}/post-update`

`POST /api/projects/create` defaults to `dry_run: true` so the dashboard can preview planned files before writing them. Existing files are not overwritten unless `force` is set.

## Run Web Dashboard

In a second terminal:

```bash
cd local-dev-workbench
npm install
npm run web:dev
```

Open `http://127.0.0.1:5173`. The Daily Work page manages local todos, accepts quick notes, and generates a standup draft without sending it anywhere. The Tickets page lists assigned Azure DevOps work items when configured, stores local notes, generates draft updates, and posts only after confirmation.

## Run Tests

```bash
cd local-dev-workbench
source .venv/bin/activate
pytest
```

## Monorepo Layout

```text
apps/web/                  React + Vite local dashboard
apps/vscode/               Placeholder for future VS Code extension
packages/core/src/         Python core package, CLI, and FastAPI app
packages/core/tests/       pytest tests
templates/                 Jinja templates for generated local projects
docs/                      Architecture and process docs
handoff/current.md         Current state for future Codex sessions
```

## Safety Model

This app is built for restrictive company environments. Source code and project data stay local. Commands are represented as generated command plans with approval metadata and should only be executed after explicit user approval.
