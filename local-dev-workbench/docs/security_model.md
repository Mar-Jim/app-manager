# Security Model

The workbench is designed for a restrictive company environment.

## Local-First Rules

- Keep source code and project data on the local machine.
- Do not add cloud services.
- Do not send source code, prompts, project metadata, or command output externally.
- Bind development services to `127.0.0.1` by default.
- Store local state in SQLite.

## Command Safety

Commands are modeled as generated plans. Each command includes:

- command id
- user-facing label
- argv list
- risk description
- approval requirement

The initial app lists commands only. It does not execute risky commands automatically.

Future execution support should include:

- explicit user approval
- command preview
- working directory display
- environment variable review
- stdout/stderr capture
- audit history in SQLite
- denylist or risk gates for destructive operations
