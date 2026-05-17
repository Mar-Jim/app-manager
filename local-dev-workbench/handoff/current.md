# Current Handoff

## Goal

Add Codex prompt generation and a handoff workflow so future sessions can start with focused context and avoid context bloat.

## Current State

- `local-dev-workbench` is a Typer/FastAPI/React monorepo for local-first Databricks and assistant workflows.
- CLI now includes `workbench prompt create`, `workbench prompt create --task-type add-workflow`, `fix-bundle-error`, `add-databricks-app`, and `write-tests`.
- CLI now includes `workbench handoff create` and `workbench handoff show`.
- FastAPI exposes prompt creation, prompt saving, handoff creation, and current handoff read endpoints.
- React now has a Codex Prompts page with task type selection, task description input, generated prompt preview, Copy, Save to `prompts/`, and Create handoff actions.
- Prompt generation includes project detection, local notes when present, selected command output when available, validation commands, and fixed Databricks external-deployer constraints.

## Architecture Decisions

- Prompt and handoff rendering live in `dev_workbench.prompts` so CLI, API, and UI share deterministic behavior.
- Prompt generation uses local project detection and small optional context snippets; it does not scan large source files unless a future feature explicitly selects them.
- Databricks bundle prompts always state that this repo usually defines only `dev`; `stg` and `prd` are handled by the external deployer repo unless explicitly requested.
- Generated handoffs use the new required section format and can be manually refined at session end.

## Files Changed

- `packages/core/src/dev_workbench/models.py`
- `packages/core/src/dev_workbench/prompts.py`
- `packages/core/src/dev_workbench/cli.py`
- `packages/core/src/dev_workbench/api/app.py`
- `packages/core/tests/test_prompts.py`
- `packages/core/tests/test_cli.py`
- `packages/core/tests/test_api.py`
- `apps/web/src/main.tsx`
- `apps/web/src/styles.css`
- `docs/prompt_playbook.md`
- `docs/handoff_protocol.md`
- `handoff/current.md`

## Commands Run

- `.venv/bin/pytest packages/core/tests/test_prompts.py packages/core/tests/test_cli.py packages/core/tests/test_api.py` -> passed, 19 tests.
- `npm run web:build` -> passed, TypeScript and Vite production build completed.
- `.venv/bin/pytest` -> passed, 41 tests.
- `.venv/bin/workbench prompt create --task-type add-workflow --task 'Smoke check prompt generation'` -> passed and printed the expected prompt sections.
- `curl -s http://127.0.0.1:8787/health` -> passed, API returned status `ok`.
- `npm run dev` from `apps/web` -> started Vite on `http://127.0.0.1:5177/`.
- Browser verification at `http://127.0.0.1:5177/` -> opened Codex Prompts page and generated a prompt successfully.
- `kill 74504 74918` -> stopped two incorrect Vite attempts that had been launched with extra positional arguments.

## Test Results

- Focused Python prompt/CLI/API tests passed.
- Full Python test suite passed.
- Web production build passed.
- CLI prompt generation smoke check passed.
- Browser check of the new Codex Prompts page passed on Vite port `5177`.

## Open Issues

- Prompt saving uses timestamped file names by default, so exact filenames are intentionally not deterministic.
- Recent command output is only included when supplied by the UI or present under `.workbench/command_outputs/`; command run history is still not persisted with stdout/stderr.
- Source-file selection for richer prompts is not implemented yet.

## Next Recommended Codex Prompt

Continue building `local-dev-workbench`. Start by reading `handoff/current.md`, then implement persistent command run history in SQLite, including stdout/stderr summaries, and expose selectable recent command outputs in the Codex Prompts page.

## Constraints

- This repo usually defines only dev target.
- stg/prd are handled by external deployer repo.
- Do not add stg/prd targets unless explicitly requested.
- Prefer local-first commands.
- Ask before execution.
- Do not read large source files for prompt generation unless the user selects them.

## Do Not Change

- Do not add Databricks `stg` or `prd` bundle targets unless explicitly requested.
- Do not include secrets, tokens, private hostnames, customer data, or private source snippets in prompts or handoff files.
- Do not execute deploy or cloud-mutating commands without explicit approval.
