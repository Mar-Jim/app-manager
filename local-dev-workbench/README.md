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
workbench handoff create
```

`workbench detect` reads local files only. It detects Databricks Asset Bundles, Databricks Apps, Python projects, Node projects, VS Code extensions, and unknown folders. For Databricks Asset Bundles, it parses `databricks.yml` or `databricks.yaml`, reports target names, and adds a deployment strategy hint for dev-only and dev/stg/prd target layouts.

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

## Run Web Dashboard

In a second terminal:

```bash
cd local-dev-workbench
npm install
npm run web:dev
```

Open `http://127.0.0.1:5173`.

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
templates/                 Future local templates
docs/                      Architecture and process docs
handoff/current.md         Current state for future Codex sessions
```

## Safety Model

This app is built for restrictive company environments. Source code and project data stay local. Commands are represented as generated command plans with approval metadata and should only be executed after explicit user approval.
