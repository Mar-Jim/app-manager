# Current Handoff

## State

Created the initial `local-dev-workbench` monorepo and expanded project detection with:

- Python core package under `packages/core/src/dev_workbench`
- Typer CLI with `doctor`, `detect`, `serve`, `handoff create`, and `commands list`
- FastAPI backend with `/health`, `/api/project/detect`, and `/api/commands`
- SQLite initialization through the Python standard library
- React + Vite dashboard under `apps/web`
- Placeholder future VS Code extension folder under `apps/vscode`
- pytest coverage for CLI doctor and API health
- Architecture, security model, and handoff protocol docs
- Structured detection models: `ProjectInfo`, `DatabricksBundleInfo`, and `DetectionResult`
- Local filesystem project detection for Databricks Asset Bundles, Databricks Apps, Python projects, Node projects, VS Code extensions, and unknown folders
- Safe Databricks bundle target parsing from `databricks.yml` or `databricks.yaml`
- Deployment strategy hints for dev-only bundles and dev/stg/prd bundles

## What Works

- `workbench doctor` initializes `.workbench/workbench.sqlite3` and reports local status.
- `workbench detect` prints readable project detection text by default.
- `workbench detect --json` prints the same structured detection result as JSON.
- `workbench commands list` displays generated commands without executing them.
- `workbench serve` starts the local FastAPI app on `127.0.0.1:8787`.
- `GET /api/project/detect` returns `DetectionResult`.
- The Vite dashboard can show API health, current project type, root path, detected files, Databricks targets, deployment strategy hint, placeholder actions, and generated command previews.

## Verification

Latest verification from the repository root:

```bash
.venv/bin/pytest
npm run web:build
.venv/bin/workbench detect --json
```

Results:

- pytest: 12 passed
- web build: Vite production build completed successfully
- `workbench detect --json`: detected this repo as `python_project` with `pyproject.toml` and `package.json`

Note: local commands print `/opt/homebrew/Library/Homebrew/cmd/shellenv.sh: line 18: /bin/ps: Operation not permitted` in this sandbox, but the commands completed successfully.

## Files Changed

- `packages/core/src/dev_workbench/models.py`
- `packages/core/src/dev_workbench/detect.py`
- `packages/core/src/dev_workbench/cli.py`
- `packages/core/src/dev_workbench/api/app.py`
- `packages/core/tests/test_detect.py`
- `packages/core/tests/test_api.py`
- `apps/web/src/main.tsx`
- `pyproject.toml`
- `README.md`
- `handoff/current.md`

## Known Gaps

- `npm install` reports 2 moderate dependency advisory findings.
- Commands are listed only; approval and execution tracking are future work.
- VS Code extension is only a placeholder folder.
- Databricks bundle detection only reads local configuration and target names; it does not validate bundles or call Databricks.
- Databricks App detection is local marker detection only.

## Next Recommended Prompt

Continue building `local-dev-workbench`. Start by reading `handoff/current.md`, then implement the next safe slice: add structured command approval records in SQLite and expose approval state through `/api/commands`, while keeping command execution disabled unless explicitly approved.
