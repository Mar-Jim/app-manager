import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Health = {
  status: string;
  app: string;
  version: string;
};

type ProjectDetection = {
  project: {
    root_path: string;
    project_type: string;
    detected_files: string[];
  };
  databricks_bundle: {
    bundle_file: string;
    targets: string[];
    only_dev_target: boolean;
    deployment_strategy: string;
  } | null;
  message: string;
};

type GeneratedCommand = {
  id: string;
  label: string;
  command: string;
  args: string[];
  working_dir: string;
  risk_level: "low" | "medium" | "high" | "destructive";
  reason: string;
  requires_confirmation: boolean;
};

type CommandRunResult = {
  command_id: string;
  status: string;
  stdout: string;
  stderr: string;
  exit_code: number | null;
  started_at: string;
  ended_at: string;
};

type ProjectKind = "bundle-job" | "bundle-pipeline" | "bundle-sql" | "bundle-dashboard";
type PromptTaskType = "add-workflow" | "fix-bundle-error" | "add-databricks-app" | "write-tests";

type ProjectCreateResult = {
  kind: ProjectKind;
  name: string;
  root_path: string;
  dry_run: boolean;
  created: boolean;
  files: string[];
  conflicts: string[];
};

type GeneratedPromptResult = {
  task_type: PromptTaskType;
  prompt: string;
  project_summary: string;
};

type PromptSaveResult = {
  path: string;
  prompt: string;
};

type HandoffResult = {
  path: string;
  content: string;
};

const projectTypes: { value: ProjectKind; label: string }[] = [
  { value: "bundle-job", label: "Workflow job" },
  { value: "bundle-pipeline", label: "DLT or Lakeflow pipeline" },
  { value: "bundle-sql", label: "SQL and tables" },
  { value: "bundle-dashboard", label: "Dashboard skeleton" },
];

const promptTaskTypes: { value: PromptTaskType; label: string }[] = [
  { value: "add-workflow", label: "Add workflow" },
  { value: "fix-bundle-error", label: "Fix bundle error" },
  { value: "add-databricks-app", label: "Add Databricks App" },
  { value: "write-tests", label: "Write tests" },
];

function commandText(command: GeneratedCommand) {
  return [command.command, ...command.args].join(" ");
}

function App() {
  const [page, setPage] = useState<"overview" | "create" | "prompts">("overview");
  const [health, setHealth] = useState<Health | null>(null);
  const [project, setProject] = useState<ProjectDetection | null>(null);
  const [commands, setCommands] = useState<GeneratedCommand[]>([]);
  const [selectedCommand, setSelectedCommand] = useState<GeneratedCommand | null>(null);
  const [runResult, setRunResult] = useState<CommandRunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [projectKind, setProjectKind] = useState<ProjectKind>("bundle-job");
  const [projectName, setProjectName] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [deploymentStrategy, setDeploymentStrategy] = useState("external-deployer");
  const [includeGithubAction, setIncludeGithubAction] = useState(false);
  const [forceCreate, setForceCreate] = useState(false);
  const [createPreview, setCreatePreview] = useState<ProjectCreateResult | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [promptTaskType, setPromptTaskType] = useState<PromptTaskType>("add-workflow");
  const [promptDescription, setPromptDescription] = useState("");
  const [generatedPrompt, setGeneratedPrompt] = useState<GeneratedPromptResult | null>(null);
  const [promptStatus, setPromptStatus] = useState<string | null>(null);
  const [promptError, setPromptError] = useState<string | null>(null);
  const [isPromptWorking, setIsPromptWorking] = useState(false);

  useEffect(() => {
    void fetch("/health").then((res) => res.json()).then(setHealth).catch(() => setHealth(null));
    void fetch("/api/project/detect").then((res) => res.json()).then(setProject).catch(() => setProject(null));
    void fetch("/api/commands/suggest").then((res) => res.json()).then(setCommands).catch(() => setCommands([]));
  }, []);

  async function runSelectedCommand() {
    if (!selectedCommand) {
      return;
    }

    setIsRunning(true);
    setRunError(null);
    setRunResult(null);
    try {
      const response = await fetch("/api/commands/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          command_id: selectedCommand.id,
          yes: selectedCommand.requires_confirmation,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Command failed to start.");
      }
      setRunResult(payload);
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Command failed to start.");
    } finally {
      setIsRunning(false);
    }
  }

  async function submitProjectCreate(dryRun: boolean) {
    setIsCreating(true);
    setCreateError(null);
    try {
      const response = await fetch("/api/projects/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind: projectKind,
          name: projectName,
          output_dir: outputDir || null,
          force: forceCreate,
          include_github_action: includeGithubAction,
          deployment_strategy: deploymentStrategy,
          target: "dev",
          dry_run: dryRun,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Project creation failed.");
      }
      setCreatePreview(payload);
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Project creation failed.");
    } finally {
      setIsCreating(false);
    }
  }

  function recentCommandOutput() {
    if (!runResult) {
      return [];
    }
    return [
      [
        `command_id: ${runResult.command_id}`,
        `status: ${runResult.status}`,
        `exit_code: ${runResult.exit_code}`,
        runResult.stdout ? `stdout:\n${runResult.stdout}` : "",
        runResult.stderr ? `stderr:\n${runResult.stderr}` : "",
      ].filter(Boolean).join("\n"),
    ];
  }

  async function generateCodexPrompt() {
    setIsPromptWorking(true);
    setPromptError(null);
    setPromptStatus(null);
    try {
      const response = await fetch("/api/prompts/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: promptTaskType,
          task_description: promptDescription,
          recent_command_outputs: recentCommandOutput(),
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Prompt generation failed.");
      }
      setGeneratedPrompt(payload);
    } catch (error) {
      setPromptError(error instanceof Error ? error.message : "Prompt generation failed.");
    } finally {
      setIsPromptWorking(false);
    }
  }

  async function saveCodexPrompt() {
    setIsPromptWorking(true);
    setPromptError(null);
    try {
      const response = await fetch("/api/prompts/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: promptTaskType,
          task_description: promptDescription,
          recent_command_outputs: recentCommandOutput(),
        }),
      });
      const payload: PromptSaveResult = await response.json();
      if (!response.ok) {
        throw new Error((payload as { detail?: string }).detail ?? "Prompt save failed.");
      }
      setGeneratedPrompt({ task_type: promptTaskType, prompt: payload.prompt, project_summary: generatedPrompt?.project_summary ?? "" });
      setPromptStatus(`Saved to ${payload.path}`);
    } catch (error) {
      setPromptError(error instanceof Error ? error.message : "Prompt save failed.");
    } finally {
      setIsPromptWorking(false);
    }
  }

  async function createHandoffFile() {
    setIsPromptWorking(true);
    setPromptError(null);
    try {
      const response = await fetch("/api/handoff/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_type: promptTaskType,
          task_description: promptDescription,
          recent_command_outputs: recentCommandOutput(),
        }),
      });
      const payload: HandoffResult = await response.json();
      if (!response.ok) {
        throw new Error((payload as { detail?: string }).detail ?? "Handoff creation failed.");
      }
      setPromptStatus(`Created ${payload.path}`);
    } catch (error) {
      setPromptError(error instanceof Error ? error.message : "Handoff creation failed.");
    } finally {
      setIsPromptWorking(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local-first</p>
          <h1>Local Dev Workbench</h1>
        </div>
        <div className={`status ${health?.status === "ok" ? "ok" : "pending"}`}>
          {health?.status === "ok" ? "API healthy" : "API unavailable"}
        </div>
      </header>

      <nav className="tabs" aria-label="Workbench pages">
        <button className={page === "overview" ? "active" : ""} type="button" onClick={() => setPage("overview")}>
          Overview
        </button>
        <button className={page === "create" ? "active" : ""} type="button" onClick={() => setPage("create")}>
          Create Project
        </button>
        <button className={page === "prompts" ? "active" : ""} type="button" onClick={() => setPage("prompts")}>
          Codex Prompts
        </button>
      </nav>

      {page === "overview" ? <section className="grid">
        <article className="panel project">
          <h2>Current Project</h2>
          <dl>
            <div>
              <dt>Type</dt>
              <dd>{project?.project.project_type ?? "Detecting"}</dd>
            </div>
            <div>
              <dt>Root</dt>
              <dd>{project?.project.root_path ?? "Local workspace"}</dd>
            </div>
            <div>
              <dt>Detected Files</dt>
              <dd>{project?.project.detected_files.length ? project.project.detected_files.join(", ") : "None"}</dd>
            </div>
            {project?.databricks_bundle ? (
              <>
                <div>
                  <dt>Databricks Targets</dt>
                  <dd>{project.databricks_bundle.targets.length ? project.databricks_bundle.targets.join(", ") : "None"}</dd>
                </div>
                <div>
                  <dt>Deployment Strategy</dt>
                  <dd>{project.databricks_bundle.deployment_strategy}</dd>
                </div>
              </>
            ) : null}
          </dl>
        </article>

        <article className="panel">
          <h2>Actions</h2>
          <div className="actions">
            {commands.length ? commands.map((command) => (
              <button key={command.id} type="button" onClick={() => {
                setSelectedCommand(command);
                setRunResult(null);
                setRunError(null);
              }}>
                <span>{command.label}</span>
                <small>{command.risk_level} risk</small>
              </button>
            )) : <p className="empty">No generated commands for this project.</p>}
          </div>
        </article>

        <article className="panel commands">
          <h2>Generated Commands</h2>
          {commands.length ? commands.map((item) => (
            <button className="command" key={item.id} type="button" onClick={() => setSelectedCommand(item)}>
              <strong>{item.label}</strong>
              <code>{commandText(item)}</code>
              <span>{item.requires_confirmation ? "Confirmation required" : "Low risk"}</span>
            </button>
          )) : <p className="empty">Suggestions appear here for Databricks Asset Bundle projects.</p>}
        </article>
      </section> : null}

      {page === "create" ? (
        <section className="create-layout">
          <article className="panel">
            <h2>Create Project</h2>
            <form className="create-form" onSubmit={(event) => {
              event.preventDefault();
              void submitProjectCreate(true);
            }}>
              <label>
                Project Type
                <select value={projectKind} onChange={(event) => {
                  setProjectKind(event.target.value as ProjectKind);
                  setCreatePreview(null);
                }}>
                  {projectTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </label>
              <label>
                Name
                <input value={projectName} onChange={(event) => {
                  setProjectName(event.target.value);
                  setCreatePreview(null);
                }} placeholder="my-bundle-project" />
              </label>
              <label>
                Output Path
                <input value={outputDir} onChange={(event) => {
                  setOutputDir(event.target.value);
                  setCreatePreview(null);
                }} placeholder="Current backend working directory" />
              </label>
              <label>
                Deployment Strategy
                <select value={deploymentStrategy} onChange={(event) => setDeploymentStrategy(event.target.value)}>
                  <option value="external-deployer">External deployer</option>
                </select>
              </label>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={includeGithubAction}
                  onChange={(event) => {
                    setIncludeGithubAction(event.target.checked);
                    setCreatePreview(null);
                  }}
                />
                Include GitHub Action
              </label>
              <label className="checkbox">
                <input type="checkbox" checked={forceCreate} onChange={(event) => setForceCreate(event.target.checked)} />
                Overwrite existing files
              </label>
              <div className="form-actions">
                <button type="submit" disabled={isCreating || !projectName}>
                  {isCreating ? "Working" : "Preview Files"}
                </button>
                <button
                  type="button"
                  disabled={isCreating || !createPreview || (createPreview.conflicts.length > 0 && !forceCreate)}
                  onClick={() => void submitProjectCreate(false)}
                >
                  Create
                </button>
              </div>
            </form>
            {createError ? <pre className="output error">{createError}</pre> : null}
          </article>

          <article className="panel">
            <h2>Preview</h2>
            {createPreview ? (
              <div className="preview">
                <dl>
                  <div>
                    <dt>Root</dt>
                    <dd>{createPreview.root_path}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{createPreview.created ? "Created" : createPreview.conflicts.length ? "Conflicts found" : "Ready"}</dd>
                  </div>
                </dl>
                {createPreview.conflicts.length ? (
                  <>
                    <h3>Conflicts</h3>
                    <ul>
                      {createPreview.conflicts.map((file) => <li key={file}>{file}</li>)}
                    </ul>
                  </>
                ) : null}
                <h3>Files</h3>
                <ul>
                  {createPreview.files.map((file) => <li key={file}>{file}</li>)}
                </ul>
              </div>
            ) : <p className="empty">Preview the file plan before creating a bundle project.</p>}
          </article>
        </section>
      ) : null}

      {page === "prompts" ? (
        <section className="prompt-layout">
          <article className="panel">
            <h2>Codex Prompts</h2>
            <form className="create-form" onSubmit={(event) => {
              event.preventDefault();
              void generateCodexPrompt();
            }}>
              <label>
                Task Type
                <select value={promptTaskType} onChange={(event) => {
                  setPromptTaskType(event.target.value as PromptTaskType);
                  setGeneratedPrompt(null);
                }}>
                  {promptTaskTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </label>
              <label>
                Task Description
                <textarea
                  value={promptDescription}
                  onChange={(event) => {
                    setPromptDescription(event.target.value);
                    setGeneratedPrompt(null);
                  }}
                  placeholder="Describe the Codex task to generate a focused prompt."
                  rows={8}
                />
              </label>
              <div className="form-actions">
                <button type="submit" disabled={isPromptWorking}>
                  {isPromptWorking ? "Working" : "Generate"}
                </button>
                <button
                  type="button"
                  disabled={!generatedPrompt}
                  onClick={() => void navigator.clipboard.writeText(generatedPrompt?.prompt ?? "")}
                >
                  Copy
                </button>
                <button type="button" disabled={isPromptWorking} onClick={() => void saveCodexPrompt()}>
                  Save to prompts/
                </button>
                <button type="button" disabled={isPromptWorking} onClick={() => void createHandoffFile()}>
                  Create handoff
                </button>
              </div>
            </form>
            {promptStatus ? <p className="notice">{promptStatus}</p> : null}
            {promptError ? <pre className="output error">{promptError}</pre> : null}
          </article>

          <article className="panel prompt-preview">
            <h2>Generated Prompt</h2>
            {generatedPrompt ? (
              <pre className="prompt-output">{generatedPrompt.prompt}</pre>
            ) : (
              <p className="empty">Generated prompts include project detection, Databricks deployment constraints, selected recent command output, and local notes when available.</p>
            )}
          </article>
        </section>
      ) : null}

      {selectedCommand ? (
        <div className="modal-backdrop" role="presentation">
          <section className="modal" aria-modal="true" role="dialog" aria-labelledby="command-review-title">
            <header className="modal-header">
              <div>
                <p className="eyebrow">Command Review</p>
                <h2 id="command-review-title">{selectedCommand.label}</h2>
              </div>
              <span className={`risk ${selectedCommand.risk_level}`}>{selectedCommand.risk_level}</span>
            </header>
            <dl className="review">
              <div>
                <dt>Command</dt>
                <dd><code>{commandText(selectedCommand)}</code></dd>
              </div>
              <div>
                <dt>Working Directory</dt>
                <dd>{selectedCommand.working_dir}</dd>
              </div>
              <div>
                <dt>Reason</dt>
                <dd>{selectedCommand.reason}</dd>
              </div>
            </dl>
            <div className="modal-actions">
              <button type="button" onClick={runSelectedCommand} disabled={isRunning}>
                {isRunning ? "Running" : "Run"}
              </button>
              <button type="button" onClick={() => void navigator.clipboard.writeText(commandText(selectedCommand))}>
                Copy
              </button>
              <button type="button" onClick={() => setSelectedCommand(null)}>
                Cancel
              </button>
            </div>
            {runError ? <pre className="output error">{runError}</pre> : null}
            {runResult ? (
              <div className="results">
                <p>Status: {runResult.status} · Exit code: {runResult.exit_code}</p>
                {runResult.stdout ? <pre className="output">{runResult.stdout}</pre> : null}
                {runResult.stderr ? <pre className="output error">{runResult.stderr}</pre> : null}
              </div>
            ) : null}
          </section>
        </div>
      ) : null}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
