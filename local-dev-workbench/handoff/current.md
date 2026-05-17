# Current Handoff

## State

Created the initial `local-dev-workbench` monorepo and added local command generation with approval-gated execution:

- Python core package under `packages/core/src/dev_workbench`
- Typer CLI with `doctor`, `detect`, `serve`, `handoff create`, `commands list`, `commands suggest`, and `commands run`
- FastAPI backend with `/health`, `/api/project/detect`, `/api/commands`, `/api/commands/suggest`, and `/api/commands/run`
- SQLite initialization through the Python standard library
- React + Vite dashboard under `apps/web`
- Placeholder future VS Code extension folder under `apps/vscode`
- pytest coverage for CLI, API, detection, command suggestion, risk classification, subprocess invocation, confirmation gating, and destructive blocking
- Architecture, security model, and handoff protocol docs
- Structured detection models: `ProjectInfo`, `DatabricksBundleInfo`, and `DetectionResult`
- Structured command models: `GeneratedCommand`, `CommandRunRequest`, and `CommandRunResult`
- Local filesystem project detection for Databricks Asset Bundles, Databricks Apps, Python projects, Node projects, VS Code extensions, and unknown folders
- Safe Databricks bundle target parsing from `databricks.yml` or `databricks.yaml`
- Deployment strategy hints for dev-only bundles and dev/stg/prd bundles
- Jinja-backed Databricks Asset Bundle starter generators for workflow jobs, DLT or Lakeflow pipelines, SQL/table projects, and dashboard skeletons
- `workbench create bundle-job NAME`
- `workbench create bundle-pipeline NAME`
- `workbench create bundle-sql NAME`
- `workbench create bundle-dashboard NAME`
- `POST /api/projects/create` with dry-run preview support
- React Create Project page with project type, name, output path, deployment strategy, overwrite option, preview, and create actions

## What Works

- `workbench doctor` initializes `.workbench/workbench.sqlite3` and reports local status.
- `workbench detect` prints readable project detection text by default.
- `workbench detect --json` prints the same structured detection result as JSON.
- `workbench commands suggest` and `workbench commands list` display generated commands without executing them.
- `workbench commands run COMMAND_ID` runs only known generated command IDs.
- Medium, high, and destructive CLI commands require `--yes`.
- Destructive commands are classified and blocked with a clear error.
- `workbench serve` starts the local FastAPI app on `127.0.0.1:8787`.
- `GET /api/project/detect` returns `DetectionResult`.
- `GET /api/commands/suggest` returns Databricks Asset Bundle command suggestions.
- `POST /api/commands/run` executes only generated command IDs and returns stdout/stderr/exit metadata.
- The Vite dashboard shows project detection, generated command action cards, a command review modal, copy/run/cancel controls, and stdout/stderr after runs.
- The CLI can generate starter Databricks Asset Bundle repos from templates under `templates/databricks_bundle_*`.
- Generated bundle projects include only a `dev` target by default. Staging and production are intentionally left to the external deployer repo.
- Project generation refuses to overwrite existing files unless `--force` or API `force: true` is used.
- The dashboard Create Project page previews files before writing them through the backend endpoint.
- `--include-github-action` can optionally add a dev-target bundle validation workflow; it is disabled by default.

## Databricks Asset Bundle Suggestions

- `validate-bundle`: `databricks bundle validate -t dev`
- `run-tests`: `pytest`
- `deploy-dev`: `databricks bundle deploy -t dev`
- `bundle-summary`: `databricks bundle validate -t dev --output json`

## Verification

Run from the repository root:

```bash
.venv/bin/pytest
npm run web:build
.venv/bin/workbench detect --json
.venv/bin/workbench commands suggest
.venv/bin/workbench create bundle-job demo-job --output-dir /tmp
```

For a Databricks Asset Bundle test fixture, run inside a folder with `databricks.yml`:

```bash
workbench commands suggest
workbench commands run validate-bundle
workbench commands run deploy-dev --yes
```

## Files Changed

- `packages/core/src/dev_workbench/models.py`
- `packages/core/src/dev_workbench/commands.py`
- `packages/core/src/dev_workbench/projects.py`
- `packages/core/src/dev_workbench/cli.py`
- `packages/core/src/dev_workbench/api/app.py`
- `templates/databricks_bundle_job/*`
- `templates/databricks_bundle_pipeline/*`
- `templates/databricks_bundle_sql/*`
- `templates/databricks_bundle_dashboard/*`
- `packages/core/tests/test_commands.py`
- `packages/core/tests/test_projects.py`
- `packages/core/tests/test_cli.py`
- `packages/core/tests/test_api.py`
- `apps/web/src/main.tsx`
- `apps/web/src/styles.css`
- `README.md`
- `docs/security_model.md`
- `handoff/current.md`

## Known Gaps

- `npm install` previously reported 2 moderate dependency advisory findings.
- Bundle Summary uses the Databricks CLI JSON output flag; a future slice should detect unsupported CLIs and fall back to normal validate.
- VS Code extension is only a placeholder folder.
- Databricks bundle detection only reads local configuration and target names; it does not validate bundles or call Databricks during detection.
- Databricks App detection is local marker detection only.
- Command run history is not persisted to SQLite yet.
- Workflow/job generation currently creates a Python `src/jobs/main.py` starter; notebook-style job starters are not implemented yet.

## Next Recommended Prompt

Continue building `local-dev-workbench`. Start by reading `handoff/current.md`, then implement persistent command run history in SQLite and expose it through the API/dashboard.
