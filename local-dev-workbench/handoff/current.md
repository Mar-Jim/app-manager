# Current Handoff

## Goal

Create a polished standalone HTML tutorial for `local-dev-workbench`, link it from the README, verify available tests, and document the work for the next Codex session.

## Current State

- `docs/tutorial.html` now exists as a single self-contained HTML file.
- The tutorial is designed for local browser use and does not rely on external CDNs, fonts, images, scripts, or JavaScript libraries.
- `README.md` links to the tutorial near the top of the file.
- The tutorial reflects the implemented repo shape: Typer CLI, FastAPI backend, React/Vite dashboard, Python core, Jinja templates, SQLite local state, Databricks CLI command suggestions, and Azure DevOps draft/post workflow.

## Architecture Decisions

- Documented the implemented architecture first:
  - Local Web UI
  - FastAPI Local Backend
  - Python Core
  - CLI / SQLite / Templates / Databricks CLI / Azure DevOps
- Marked the VS Code extension as optional/future because `apps/vscode` is currently a placeholder.
- Kept all token examples as placeholders and avoided fake secret values.
- Documented recommended YAML config locations while clearly noting that the current implemented Azure DevOps setup path is environment variables.

## Files Changed

- `docs/tutorial.html`
- `README.md`
- `handoff/current.md`

## Tutorial Sections Added

- A. Overview
- B. Architecture diagram
- C. Security model
- D. First-time setup
- E. Local configuration
- F. Environment variables
- G. Databricks setup
- H. Running the app
- I. Using the dashboard
- J. Project detection examples
- K. Command approval workflow
- L. Creating Databricks Asset Bundles
- M. Codex prompt workflow
- N. Handoff workflow
- O. Todos and worklog
- P. Azure DevOps workflow
- Q. Testing checklist
- R. Troubleshooting
- S. Team onboarding guide
- T. FAQ

## Commands Run

- `pwd`
- `rg --files`
- `git status --short`
- `sed -n '1,260p' README.md`
- `sed -n '1,260p' packages/core/src/dev_workbench/cli.py`
- `sed -n '260,560p' packages/core/src/dev_workbench/cli.py`
- `sed -n '1,260p' packages/core/src/dev_workbench/commands.py`
- `sed -n '1,260p' packages/core/src/dev_workbench/projects.py`
- `sed -n '1,260p' packages/core/src/dev_workbench/detect.py`
- `sed -n '1,260p' packages/core/src/dev_workbench/prompts.py`
- `sed -n '1,280p' packages/core/src/dev_workbench/api/app.py`
- `sed -n '1,260p' apps/web/src/main.tsx`
- `sed -n '1,260p' docs/architecture.md`
- `sed -n '1,260p' docs/security_model.md`
- `sed -n '1,260p' package.json`
- `sed -n '1,220p' apps/web/package.json`
- `sed -n '1,260p' pyproject.toml`
- `find docs -maxdepth 2 -type f -print`
- `test -f docs/tutorial.html; echo $?`
- `rg -n "your-local-token|ado config check|planned|WORKBENCH_ADO_PAT_ENV_VAR|<YOUR|&lt;YOUR" docs/tutorial.html README.md`
- `.venv/bin/pytest`
- `npm run web:build`
- `rg` check for remaining literal backticks or token-like examples in `docs/tutorial.html`
- `python -m html.parser docs/tutorial.html`

## Test Results

- `.venv/bin/pytest` passed: 59 tests.
- `npm run web:build` passed: TypeScript and Vite production build completed.
- `python -m html.parser docs/tutorial.html` completed without parser errors.

## Assumptions Made

- Teammates will open `docs/tutorial.html` directly in a browser from the local checkout.
- The current project root for app work is `/Users/marcelo/Documents/app-manager/local-dev-workbench`.
- The user-requested config file locations are recommended conventions, but current implemented ADO config uses environment variables and SQLite metadata.
- `workbench ado config check` was requested as a setup command but is not implemented, so the tutorial labels it as planned and recommends `workbench ado tickets list` for current setup guidance.
- The default README ADO PAT variable is `AZURE_DEVOPS_EXT_PAT`; the tutorial shows how to set `WORKBENCH_ADO_PAT_ENV_VAR="AZURE_DEVOPS_PAT"` to use the requested placeholder name.

## Commands That Could Not Be Verified

- `workbench ado config check` could not be verified because it is not implemented.
- Live Databricks CLI auth and `databricks bundle validate -t dev` were not run because they depend on local Databricks credentials and a target bundle repo.
- Live Azure DevOps ticket listing/posting was not run because it depends on real organization, project, and PAT configuration.

## Open Issues

- There is still no implemented CLI/API command to persist ADO config metadata; environment variables are the practical setup path today.
- Config-file loading for `.workbench.local.yml` and `~/.local-dev-workbench/config.yml` is documented as a recommended convention, not an implemented primary loader.

## Next Recommended Codex Prompt

Add a local ADO config checker/editor for the CLI and dashboard. It should persist only non-secret metadata, never store PAT values, and include tests that confirm missing-token setup guidance remains safe.

## Constraints

- Keep source code and project data local.
- Do not send code externally.
- Do not automatically post comments to Azure DevOps.
- All Azure DevOps updates must be drafted first and require explicit approval before posting.
- Do not store PAT values in SQLite.
- Do not add Databricks `stg` or `prd` bundle targets unless explicitly requested.
- Prefer local-first commands.

## Do Not Change

- Do not add Databricks `stg` or `prd` bundle targets unless explicitly requested.
- Do not include secrets, tokens, private hostnames, customer data, or private source snippets in prompts or handoff files.
- Do not execute deploy or cloud-mutating commands without explicit approval.
