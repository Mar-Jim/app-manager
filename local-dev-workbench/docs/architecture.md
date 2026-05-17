# Architecture

`local-dev-workbench` is a local monorepo with a Python core, a local FastAPI backend, and a React + Vite dashboard.

## Components

- `packages/core`: Python package containing domain models, project detection, Databricks Asset Bundle project generation, generated command definitions, SQLite initialization, Typer CLI, and FastAPI app.
- `apps/web`: Local dashboard that reads from the FastAPI backend through Vite's development proxy.
- `apps/vscode`: Placeholder folder for a future extension.
- `handoff`: Persistent session state for future Codex runs.
- `templates`: Jinja templates for generated local projects, including Databricks Asset Bundle job, pipeline, SQL, and dashboard skeleton starters.

## Runtime Flow

1. The user starts the backend with `workbench serve`.
2. The web app runs locally with `npm run web:dev`.
3. The dashboard calls local endpoints for health, detection, and generated commands.
4. Generated commands are displayed for review. They are not executed by the app in the initial version.
5. The Create Project page calls `POST /api/projects/create` first with `dry_run: true` to preview generated files, then with `dry_run: false` to write the selected starter project.

## Project Generation

Databricks Asset Bundle starter generators live in `dev_workbench.projects` and render Jinja templates from `templates/databricks_bundle_*`.

Supported generators:

- `bundle-job`: `databricks.yml`, `resources/job.yml`, `src/jobs/main.py`, tests, README, and `.gitignore`.
- `bundle-pipeline`: `databricks.yml`, `resources/pipeline.yml`, `src/pipelines/pipeline.py`, tests, and README.
- `bundle-sql`: `databricks.yml`, `resources/sql.yml`, `sql/001_create_tables.sql`, tests, and README.
- `bundle-dashboard`: `databricks.yml`, `resources/dashboard.yml`, `dashboards/README.md`, and README.

Generated bundles intentionally include only a `dev` target. The company deployment model expects staging and production promotion to be handled by an external deployer repo, so the project generators do not create `stg` or `prd` targets by default.

Project creation is overwrite-safe. The generator reports conflicts and does not write over existing files unless `force` is provided. The API defaults to dry-run previews for UI confirmation.

GitHub Actions generation is optional and disabled by default. When requested, it creates a validation workflow for the dev target only.

## Persistence

SQLite is initialized under `.workbench/workbench.sqlite3` by `workbench doctor`. The initial schema stores command history metadata for future approval and execution tracking.
