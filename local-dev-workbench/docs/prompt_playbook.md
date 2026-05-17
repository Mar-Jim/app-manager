# Codex Prompt Playbook

Use the workbench prompt workflow to create medium-sized Codex prompts that carry enough local context without copying broad source files.

## CLI

Generate a prompt:

```bash
workbench prompt create
workbench prompt create --task-type add-workflow
workbench prompt create --task-type fix-bundle-error
workbench prompt create --task-type add-databricks-app
workbench prompt create --task-type write-tests
```

Add task-specific direction:

```bash
workbench prompt create --task-type add-workflow --task "Add command history persistence."
```

Save the generated prompt:

```bash
workbench prompt create --task-type write-tests --task "Cover bundle target detection." --save
```

Saved prompts are written under `prompts/`.

## Web UI

Start the backend and frontend, then open the Codex Prompts page:

```bash
workbench serve
npm run web:dev
```

The page lets you choose a task type, enter a task description, generate the prompt, copy it, save it to `prompts/`, or create `handoff/current.md`.

## Prompt Sections

Generated prompts include:

- Goal
- Current repo context
- Constraints
- Company/security assumptions
- Databricks deployment strategy
- Task
- Expected files to change
- Validation commands
- Definition of done
- Handoff update requirement

## Local Context Rules

The generator includes project detection, Databricks target summaries, local notes from `.workbench/notes.md` or `NOTES.md` when present, and selected recent command output passed from the UI or found under `.workbench/command_outputs/`.

It intentionally avoids scanning large source files. Future UI slices can add explicit source-file selection for cases where a prompt needs code context.

## Databricks Bundle Defaults

For Databricks Asset Bundle projects, prompts always include:

- This repo usually defines only dev target.
- stg/prd are handled by external deployer repo.
- Do not add stg/prd targets unless explicitly requested.
- Prefer local-first commands.
- Ask before execution.
