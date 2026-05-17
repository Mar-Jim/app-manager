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
- `packages/core/src/dev_workbench/cli.py`
- `packages/core/src/dev_workbench/api/app.py`
- `packages/core/tests/test_commands.py`
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

## Next Recommended Prompt

Continue building `local-dev-workbench`. Start by reading `handoff/current.md`, then implement persistent command run history in SQLite and expose it through the API/dashboard.
