# Security Model

The workbench is designed for a restrictive company environment.

## Local-First Rules

- Keep source code and project data on the local machine.
- Do not add cloud services.
- Do not send source code, prompts, project metadata, or command output externally.
- Bind development services to `127.0.0.1` by default.
- Store local state in SQLite.
- Store Azure DevOps PAT values only in environment variables, never in SQLite.

## Command Safety

Commands are modeled as generated plans. Each command includes:

- command id
- user-facing label
- executable name
- argument list
- working directory
- risk level
- reason
- confirmation requirement

The app generates commands only from known local templates. It does not accept arbitrary command text from the dashboard or API.

Supported Databricks Asset Bundle suggestions are:

- `databricks bundle validate -t dev`
- `pytest`
- `databricks bundle deploy -t dev`
- `databricks bundle validate -t dev --output json`

Execution rules:

- Commands run through `subprocess.run` with an argument array and `shell=False`.
- Low-risk commands can run after the user clicks Run or invokes the CLI command.
- Medium, high, and destructive commands require explicit confirmation.
- The CLI requires `--yes` for medium, high, and destructive command IDs.
- The API accepts only generated command IDs through `POST /api/commands/run`.
- Destructive commands are classified and blocked; they are not supported yet.

Risk classification:

- `pytest`: low
- `databricks bundle validate`: low
- `databricks bundle deploy -t dev`: medium
- `git push`: high
- delete, drop, remove, and rm command terms: destructive

Future execution support should include:

- environment variable review
- audit history in SQLite
- richer Databricks CLI capability detection for JSON output fallback

## Azure DevOps Safety

Azure DevOps integration is designed for restrictive company environments where external writes need explicit approval.

Configuration fields:

- `organization_url`
- `project`
- `default_query`
- `auth_mode`
- `personal_access_token_env_var`

SQLite may store configuration metadata and the PAT environment variable name, but it must not store the PAT value. The current implemented auth mode is `pat_env`, which reads the token from the named local environment variable at request time. If required configuration or the token is missing, the app returns setup guidance and keeps running.

Read behavior:

- Ticket listing uses WIQL through the Azure DevOps REST API.
- Ticket details are fetched only when the user opens a ticket or requests it through the CLI/API.
- Local ticket notes are stored in `ticket_notes`.

Draft behavior:

- Draft updates are generated locally from ticket metadata and local notes.
- Drafts are stored in `ticket_update_drafts`.
- Draft generation does not post to Azure DevOps.

Post behavior:

- CLI posting requires `workbench ado ticket post-update ID --from-draft --yes`.
- API posting requires `from_draft: true` and `yes: true`.
- The web UI requires a confirmation checkbox before sending the API approval flag.
- Posting uses the latest local draft body.
- Automatic posting is not supported.
