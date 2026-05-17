# Current Handoff

## Goal

Add Azure DevOps integration in local-first, permissioned mode so assigned tickets can be read, local notes can be attached, update drafts can be generated, and approved drafts can be posted only after explicit confirmation.

## Current State

- `local-dev-workbench` is a Typer/FastAPI/React monorepo for local-first Databricks and assistant workflows.
- Azure DevOps support now lives in `dev_workbench.ado`.
- SQLite initialization creates:
  - `ado_config` for metadata such as organization URL, project, query, auth mode, and PAT env var name
  - `ticket_update_drafts` for local draft updates and posted status
  - existing local work tables for todos, work logs, and ticket notes
- PAT values are not stored in SQLite. The implemented auth mode is `pat_env`.
- Config can come from SQLite metadata or environment variables:
  - `WORKBENCH_ADO_ORGANIZATION_URL`
  - `WORKBENCH_ADO_PROJECT`
  - `WORKBENCH_ADO_DEFAULT_QUERY`
  - `WORKBENCH_ADO_AUTH_MODE`
  - `WORKBENCH_ADO_PAT_ENV_VAR`
- If auth is missing, CLI/API/UI return setup guidance and keep running.

## CLI

- `workbench ado tickets list`
- `workbench ado ticket show ID`
- `workbench ado ticket draft-update ID`
- `workbench ado ticket draft-update ID --note "local note"`
- `workbench ado ticket post-update ID --from-draft --yes`

Posting refuses to run unless both `--from-draft` and `--yes` are present.

## API

- `GET /api/ado/tickets`
- `GET /api/ado/tickets/{id}`
- `POST /api/ado/tickets/{id}/notes`
- `POST /api/ado/tickets/{id}/draft-update`
- `POST /api/ado/tickets/{id}/post-update`

Posting requires `{"from_draft": true, "yes": true}`.

## Web UI

- Added a Tickets page.
- Shows assigned tickets when ADO config and token are available.
- Shows setup guidance when config or token is missing.
- Lets the user select an active ticket.
- Lets the user save local notes.
- Generates a draft update from local notes.
- Posts only after the confirmation checkbox is selected.

## Files Changed

- `packages/core/src/dev_workbench/ado.py`
- `packages/core/src/dev_workbench/models.py`
- `packages/core/src/dev_workbench/storage.py`
- `packages/core/src/dev_workbench/cli.py`
- `packages/core/src/dev_workbench/api/app.py`
- `packages/core/tests/test_ado.py`
- `packages/core/tests/test_api.py`
- `packages/core/tests/test_cli.py`
- `apps/web/src/main.tsx`
- `apps/web/src/styles.css`
- `README.md`
- `docs/security_model.md`
- `handoff/current.md`

## Commands Run

- `.venv/bin/pytest packages/core/tests/test_ado.py packages/core/tests/test_api.py packages/core/tests/test_cli.py` -> passed, 30 tests.
- `npm run web:build` -> passed, TypeScript and Vite production build completed.

## Test Results

- Mock Azure DevOps client tests cover ticket listing, draft generation, posting after approval, and no-token setup guidance.
- API tests cover no-token behavior and post confirmation requirements.
- CLI tests cover no-token guidance, local draft generation, and `--yes` enforcement.
- Web production build passed.

## Open Issues

- Only `auth_mode=pat_env` is implemented for REST calls.
- There is not yet a CLI/API command to write ADO config into `ado_config`; environment variables are the practical setup path today.
- Draft update generation is deterministic and local. It does not use an LLM.
- The Tickets page does not edit or delete existing local notes yet.

## Next Recommended Codex Prompt

Continue building `local-dev-workbench`. Start by reading `handoff/current.md`, then add a small local ADO config editor for the CLI and web UI that persists only metadata in SQLite and never stores PAT values.

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
