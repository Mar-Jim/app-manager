# Handoff Protocol

Future Codex sessions should start by reading `handoff/current.md`.

## CLI

Create or refresh the current handoff:

```bash
workbench handoff create
workbench handoff create --task-type add-workflow --task "Add command run history."
```

Show the current handoff:

```bash
workbench handoff show
```

## Required Sections

- Goal
- Current State
- Architecture Decisions
- Files Changed
- Commands Run
- Test Results
- Open Issues
- Next Recommended Codex Prompt
- Constraints
- Do Not Change

## Update Rules

- Update `handoff/current.md` at the end of every meaningful session.
- Keep it concise but specific.
- Include exact commands that were run and their result.
- Include the next recommended prompt so a future session can continue without full prior context.
- Preserve important architecture decisions and do-not-change constraints.
- Use generated handoffs as a starting point, then replace placeholders with the real session summary.

## Safety

Do not put secrets, tokens, private source snippets, customer data, or company-sensitive details into handoff files. Reference local paths and task state instead.

For Databricks bundle projects, keep the handoff explicit that this repo usually owns only the `dev` target and that `stg` or `prd` targets are handled by the external deployer repo unless explicitly requested.
