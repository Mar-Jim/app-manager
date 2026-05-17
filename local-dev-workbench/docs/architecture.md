# Architecture

`local-dev-workbench` is a local monorepo with a Python core, a local FastAPI backend, and a React + Vite dashboard.

## Components

- `packages/core`: Python package containing domain models, project detection, generated command definitions, SQLite initialization, Typer CLI, and FastAPI app.
- `apps/web`: Local dashboard that reads from the FastAPI backend through Vite's development proxy.
- `apps/vscode`: Placeholder folder for a future extension.
- `handoff`: Persistent session state for future Codex runs.
- `templates`: Future local templates for prompts, bundles, apps, and tickets.

## Runtime Flow

1. The user starts the backend with `workbench serve`.
2. The web app runs locally with `npm run web:dev`.
3. The dashboard calls local endpoints for health, detection, and generated commands.
4. Generated commands are displayed for review. They are not executed by the app in the initial version.

## Persistence

SQLite is initialized under `.workbench/workbench.sqlite3` by `workbench doctor`. The initial schema stores command history metadata for future approval and execution tracking.
