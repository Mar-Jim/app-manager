# Current Handoff

## Goal

Add local todos and work log support so daily work can be tracked locally and summarized for tickets or standup without sending anything externally.

## Current State

- `local-dev-workbench` is a Typer/FastAPI/React monorepo for local-first Databricks and assistant workflows.
- SQLite initialization now creates local work tables for `todos`, `work_log_entries`, `ticket_notes`, and existing `command_history`.
- Core local work behavior lives in `dev_workbench.work.WorkbenchService`, giving CLI, API, UI, and future Azure DevOps integration a shared service boundary.
- CLI now includes:
  - `workbench todo add "text"`
  - `workbench todo list`
  - `workbench todo complete ID`
  - `workbench worklog add "text"`
  - `workbench worklog summary`
- FastAPI now exposes:
  - `GET /api/todos`
  - `POST /api/todos`
  - `POST /api/todos/{id}/complete`
  - `GET /api/worklog`
  - `POST /api/worklog`
  - `GET /api/worklog/summary`
- React now has a Daily Work page with todo management, quick note input, and a Generate Daily Summary button.
- Generated summaries are local draft text only and use this format:
  - Today I worked on:
  - Completed:
  - In progress:
  - Blockers:
  - Next steps:

## Architecture Decisions

- All work-tracking data stays in `.workbench/workbench.sqlite3` under the current working directory.
- `TicketNote` is modeled and persisted locally, but there is no Azure DevOps integration yet.
- Work summary generation is deterministic: today's work log entries feed "Today I worked on", todos completed today feed "Completed", open todos feed "In progress" and "Next steps", and blocker-like work log entries feed "Blockers".
- The service layer is intentionally local-first and can later grow an Azure DevOps adapter without changing CLI/API callers.

## Files Changed

- `packages/core/src/dev_workbench/models.py`
- `packages/core/src/dev_workbench/storage.py`
- `packages/core/src/dev_workbench/work.py`
- `packages/core/src/dev_workbench/cli.py`
- `packages/core/src/dev_workbench/api/app.py`
- `packages/core/tests/test_work.py`
- `packages/core/tests/test_cli.py`
- `packages/core/tests/test_api.py`
- `apps/web/src/main.tsx`
- `apps/web/src/styles.css`
- `README.md`
- `handoff/current.md`

## Commands Run

- `.venv/bin/pytest packages/core/tests/test_work.py packages/core/tests/test_cli.py packages/core/tests/test_api.py` -> passed, 22 tests.
- `.venv/bin/pytest` -> passed, 48 tests.
- `npm run web:build` -> passed, TypeScript and Vite production build completed.
- `npm run web:dev` -> started Vite on `http://127.0.0.1:5175/` for browser verification, then stopped.
- Browser verification at `http://127.0.0.1:5175/` -> opened Daily Work, added a smoke todo, added a smoke work note, generated a daily summary draft, and removed the smoke records from SQLite.

## Test Results

- Focused SQLite, local work service, CLI, and API tests passed.
- Full Python suite passed.
- Web production build passed.
- Browser smoke check of Daily Work passed.

## Open Issues

- Work summary generation is intentionally simple and deterministic; it does not use an LLM.
- Blockers are inferred from words like blocked, blocker, stuck, waiting, dependency, and depends on.
- There is no edit/delete flow for todos or work log entries yet.
- Azure DevOps publishing is intentionally not implemented.

## Next Recommended Codex Prompt

Continue building `local-dev-workbench`. Start by reading `handoff/current.md`, then add persistent command run history in SQLite, including stdout/stderr summaries, and expose selectable recent command outputs in the Codex Prompts page.

## Constraints

- Keep all daily work data local in SQLite.
- Do not integrate with Azure DevOps unless explicitly requested.
- This repo usually defines only dev target.
- stg/prd are handled by external deployer repo.
- Do not add stg/prd targets unless explicitly requested.
- Prefer local-first commands.
- Do not read large source files for prompt generation unless the user selects them.

## Do Not Change

- Do not add Databricks `stg` or `prd` bundle targets unless explicitly requested.
- Do not include secrets, tokens, private hostnames, customer data, or private source snippets in prompts or handoff files.
- Do not execute deploy or cloud-mutating commands without explicit approval.
