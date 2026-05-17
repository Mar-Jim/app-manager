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

type Todo = {
  id: number;
  text: string;
  completed: boolean;
  created_at: string;
  completed_at: string | null;
};

type WorkLogEntry = {
  id: number;
  text: string;
  created_at: string;
};

type WorkLogSummary = {
  summary: string;
};

type TicketNote = {
  id: number;
  ticket_ref: string;
  text: string;
  created_at: string;
};

type AdoConfig = {
  organization_url: string | null;
  project: string | null;
  default_query: string | null;
  auth_mode: string;
  personal_access_token_env_var: string | null;
  configured: boolean;
  token_available: boolean;
  setup_guidance: string | null;
};

type AdoTicket = {
  id: number;
  title: string;
  state: string | null;
  assigned_to: string | null;
  work_item_type: string | null;
  url: string | null;
  description: string | null;
};

type AdoTicketDraft = {
  id: number;
  ticket_ref: string;
  body: string;
  posted: boolean;
  created_at: string;
  posted_at: string | null;
};

type AdoTicketList = {
  tickets: AdoTicket[];
  config: AdoConfig;
};

type AdoTicketDetail = {
  ticket: AdoTicket;
  notes: TicketNote[];
  latest_draft: AdoTicketDraft | null;
  config: AdoConfig;
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
  const [page, setPage] = useState<"overview" | "create" | "prompts" | "work" | "tickets">("overview");
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
  const [todos, setTodos] = useState<Todo[]>([]);
  const [todoText, setTodoText] = useState("");
  const [worklog, setWorklog] = useState<WorkLogEntry[]>([]);
  const [worklogText, setWorklogText] = useState("");
  const [dailySummary, setDailySummary] = useState<string | null>(null);
  const [workError, setWorkError] = useState<string | null>(null);
  const [isWorkSaving, setIsWorkSaving] = useState(false);
  const [adoTickets, setAdoTickets] = useState<AdoTicket[]>([]);
  const [adoConfig, setAdoConfig] = useState<AdoConfig | null>(null);
  const [activeTicketId, setActiveTicketId] = useState("");
  const [activeTicket, setActiveTicket] = useState<AdoTicketDetail | null>(null);
  const [ticketNoteText, setTicketNoteText] = useState("");
  const [ticketDraft, setTicketDraft] = useState<AdoTicketDraft | null>(null);
  const [ticketConfirmPost, setTicketConfirmPost] = useState(false);
  const [ticketStatus, setTicketStatus] = useState<string | null>(null);
  const [ticketError, setTicketError] = useState<string | null>(null);
  const [isTicketWorking, setIsTicketWorking] = useState(false);

  useEffect(() => {
    void fetch("/health").then((res) => res.json()).then(setHealth).catch(() => setHealth(null));
    void fetch("/api/project/detect").then((res) => res.json()).then(setProject).catch(() => setProject(null));
    void fetch("/api/commands/suggest").then((res) => res.json()).then(setCommands).catch(() => setCommands([]));
    void refreshLocalWork();
    void refreshAdoTickets();
  }, []);

  async function refreshLocalWork() {
    await Promise.all([
      fetch("/api/todos").then((res) => res.json()).then(setTodos).catch(() => setTodos([])),
      fetch("/api/worklog").then((res) => res.json()).then(setWorklog).catch(() => setWorklog([])),
    ]);
  }

  async function refreshAdoTickets() {
    setTicketError(null);
    try {
      const response = await fetch("/api/ado/tickets");
      const payload: AdoTicketList = await response.json();
      if (!response.ok) {
        throw new Error((payload as { detail?: string }).detail ?? "Azure DevOps tickets failed to load.");
      }
      setAdoTickets(payload.tickets);
      setAdoConfig(payload.config);
      if (!activeTicketId && payload.tickets[0]) {
        setActiveTicketId(String(payload.tickets[0].id));
      }
    } catch (error) {
      setAdoTickets([]);
      setTicketError(error instanceof Error ? error.message : "Azure DevOps tickets failed to load.");
    }
  }

  async function loadAdoTicket(ticketId = activeTicketId) {
    if (!ticketId.trim()) {
      return;
    }
    setIsTicketWorking(true);
    setTicketError(null);
    setTicketStatus(null);
    try {
      const response = await fetch(`/api/ado/tickets/${encodeURIComponent(ticketId.trim())}`);
      const payload: AdoTicketDetail = await response.json();
      if (!response.ok) {
        throw new Error((payload as { detail?: string }).detail ?? "Azure DevOps ticket failed to load.");
      }
      setActiveTicket(payload);
      setTicketDraft(payload.latest_draft);
      setAdoConfig(payload.config);
    } catch (error) {
      setTicketError(error instanceof Error ? error.message : "Azure DevOps ticket failed to load.");
    } finally {
      setIsTicketWorking(false);
    }
  }

  async function saveTicketNote() {
    if (!activeTicketId.trim() || !ticketNoteText.trim()) {
      return;
    }
    setIsTicketWorking(true);
    setTicketError(null);
    try {
      const response = await fetch(`/api/ado/tickets/${encodeURIComponent(activeTicketId.trim())}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_ref: activeTicketId.trim(), text: ticketNoteText }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Local note save failed.");
      }
      setTicketNoteText("");
      await loadAdoTicket(activeTicketId);
    } catch (error) {
      setTicketError(error instanceof Error ? error.message : "Local note save failed.");
    } finally {
      setIsTicketWorking(false);
    }
  }

  async function generateTicketDraft() {
    if (!activeTicketId.trim()) {
      return;
    }
    setIsTicketWorking(true);
    setTicketError(null);
    setTicketStatus(null);
    try {
      const response = await fetch(`/api/ado/tickets/${encodeURIComponent(activeTicketId.trim())}/draft-update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: ticketNoteText.trim() || null }),
      });
      const payload: AdoTicketDraft = await response.json();
      if (!response.ok) {
        throw new Error((payload as { detail?: string }).detail ?? "Draft generation failed.");
      }
      setTicketNoteText("");
      setTicketDraft(payload);
      setTicketConfirmPost(false);
      await loadAdoTicket(activeTicketId);
    } catch (error) {
      setTicketError(error instanceof Error ? error.message : "Draft generation failed.");
    } finally {
      setIsTicketWorking(false);
    }
  }

  async function postTicketDraft() {
    if (!activeTicketId.trim() || !ticketDraft || !ticketConfirmPost) {
      return;
    }
    setIsTicketWorking(true);
    setTicketError(null);
    setTicketStatus(null);
    try {
      const response = await fetch(`/api/ado/tickets/${encodeURIComponent(activeTicketId.trim())}/post-update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from_draft: true, yes: ticketConfirmPost }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Post update failed.");
      }
      setTicketStatus(payload.message);
      setTicketConfirmPost(false);
      await loadAdoTicket(activeTicketId);
    } catch (error) {
      setTicketError(error instanceof Error ? error.message : "Post update failed.");
    } finally {
      setIsTicketWorking(false);
    }
  }

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

  async function addTodo() {
    if (!todoText.trim()) {
      return;
    }
    setIsWorkSaving(true);
    setWorkError(null);
    try {
      const response = await fetch("/api/todos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: todoText }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Todo save failed.");
      }
      setTodoText("");
      setTodos((current) => [...current, payload]);
    } catch (error) {
      setWorkError(error instanceof Error ? error.message : "Todo save failed.");
    } finally {
      setIsWorkSaving(false);
    }
  }

  async function completeTodo(todoId: number) {
    setIsWorkSaving(true);
    setWorkError(null);
    try {
      const response = await fetch(`/api/todos/${todoId}/complete`, { method: "POST" });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Todo update failed.");
      }
      setTodos((current) => current.map((todo) => todo.id === todoId ? payload : todo));
    } catch (error) {
      setWorkError(error instanceof Error ? error.message : "Todo update failed.");
    } finally {
      setIsWorkSaving(false);
    }
  }

  async function addWorklog() {
    if (!worklogText.trim()) {
      return;
    }
    setIsWorkSaving(true);
    setWorkError(null);
    try {
      const response = await fetch("/api/worklog", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: worklogText }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail ?? "Work log save failed.");
      }
      setWorklogText("");
      setWorklog((current) => [...current, payload]);
    } catch (error) {
      setWorkError(error instanceof Error ? error.message : "Work log save failed.");
    } finally {
      setIsWorkSaving(false);
    }
  }

  async function generateDailySummary() {
    setIsWorkSaving(true);
    setWorkError(null);
    try {
      const response = await fetch("/api/worklog/summary");
      const payload: WorkLogSummary = await response.json();
      if (!response.ok) {
        throw new Error((payload as { detail?: string }).detail ?? "Summary generation failed.");
      }
      setDailySummary(payload.summary);
    } catch (error) {
      setWorkError(error instanceof Error ? error.message : "Summary generation failed.");
    } finally {
      setIsWorkSaving(false);
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
        <button className={page === "work" ? "active" : ""} type="button" onClick={() => setPage("work")}>
          Daily Work
        </button>
        <button className={page === "tickets" ? "active" : ""} type="button" onClick={() => setPage("tickets")}>
          Tickets
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

      {page === "work" ? (
        <section className="work-layout">
          <article className="panel work-panel">
            <h2>Todos</h2>
            <form className="inline-form" onSubmit={(event) => {
              event.preventDefault();
              void addTodo();
            }}>
              <input value={todoText} onChange={(event) => setTodoText(event.target.value)} placeholder="Add a local todo" />
              <button type="submit" disabled={isWorkSaving || !todoText.trim()}>Add</button>
            </form>
            <div className="todo-list">
              {todos.length ? todos.map((todo) => (
                <div className={`todo-item ${todo.completed ? "complete" : ""}`} key={todo.id}>
                  <span>{todo.text}</span>
                  {todo.completed ? <small>Completed</small> : (
                    <button type="button" onClick={() => void completeTodo(todo.id)} disabled={isWorkSaving}>
                      Complete
                    </button>
                  )}
                </div>
              )) : <p className="empty">No todos yet.</p>}
            </div>
          </article>

          <article className="panel work-panel">
            <h2>Quick Note</h2>
            <form className="create-form" onSubmit={(event) => {
              event.preventDefault();
              void addWorklog();
            }}>
              <label>
                Work log note
                <textarea
                  value={worklogText}
                  onChange={(event) => setWorklogText(event.target.value)}
                  placeholder="Capture what you did, a blocker, or a next step."
                  rows={5}
                />
              </label>
              <div className="form-actions">
                <button type="submit" disabled={isWorkSaving || !worklogText.trim()}>Add Note</button>
                <button type="button" disabled={isWorkSaving} onClick={() => void generateDailySummary()}>
                  Generate Daily Summary
                </button>
              </div>
            </form>
            {workError ? <pre className="output error">{workError}</pre> : null}
            <div className="worklog-list">
              {worklog.length ? worklog.map((entry) => (
                <p key={entry.id}>{entry.text}</p>
              )) : <p className="empty">Notes added today appear here.</p>}
            </div>
          </article>

          <article className="panel prompt-preview summary-panel">
            <h2>Daily Summary Draft</h2>
            {dailySummary ? (
              <pre className="prompt-output">{dailySummary}</pre>
            ) : (
              <p className="empty">Generate a local draft for tickets or standup. Nothing is sent externally.</p>
            )}
          </article>
        </section>
      ) : null}

      {page === "tickets" ? (
        <section className="tickets-layout">
          <article className="panel tickets-list">
            <h2>Assigned Tickets</h2>
            {adoConfig?.setup_guidance ? <p className="notice">{adoConfig.setup_guidance}</p> : null}
            <div className="inline-form ticket-picker">
              <select value={activeTicketId} onChange={(event) => setActiveTicketId(event.target.value)}>
                <option value="">Select ticket</option>
                {adoTickets.map((ticket) => (
                  <option key={ticket.id} value={ticket.id}>
                    {ticket.id}: {ticket.title}
                  </option>
                ))}
              </select>
              <button type="button" disabled={isTicketWorking || !activeTicketId.trim()} onClick={() => void loadAdoTicket()}>
                Open
              </button>
            </div>
            <div className="ticket-cards">
              {adoTickets.length ? adoTickets.map((ticket) => (
                <button key={ticket.id} type="button" className="ticket-card" onClick={() => {
                  setActiveTicketId(String(ticket.id));
                  void loadAdoTicket(String(ticket.id));
                }}>
                  <strong>{ticket.title}</strong>
                  <span>#{ticket.id} · {ticket.state ?? "unknown"}</span>
                </button>
              )) : <p className="empty">No assigned tickets loaded.</p>}
            </div>
          </article>

          <article className="panel ticket-detail">
            <h2>Active Ticket</h2>
            {activeTicket ? (
              <>
                <dl>
                  <div>
                    <dt>Ticket</dt>
                    <dd>#{activeTicket.ticket.id}: {activeTicket.ticket.title}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{activeTicket.ticket.state ?? "unknown"}</dd>
                  </div>
                  <div>
                    <dt>Assignee</dt>
                    <dd>{activeTicket.ticket.assigned_to ?? "unknown"}</dd>
                  </div>
                </dl>
                <div className="worklog-list">
                  {activeTicket.notes.length ? activeTicket.notes.map((note) => (
                    <p key={note.id}>{note.text}</p>
                  )) : <p className="empty">Local notes for this ticket appear here.</p>}
                </div>
              </>
            ) : (
              <p className="empty">Select a ticket to view details and local notes.</p>
            )}
            {ticketError ? <pre className="output error">{ticketError}</pre> : null}
            {ticketStatus ? <p className="notice">{ticketStatus}</p> : null}
          </article>

          <article className="panel">
            <h2>Local Notes</h2>
            <form className="create-form" onSubmit={(event) => {
              event.preventDefault();
              void saveTicketNote();
            }}>
              <label>
                Note
                <textarea
                  rows={5}
                  value={ticketNoteText}
                  onChange={(event) => setTicketNoteText(event.target.value)}
                  placeholder="Capture local context for this ticket."
                />
              </label>
              <div className="form-actions">
                <button type="submit" disabled={isTicketWorking || !activeTicketId.trim() || !ticketNoteText.trim()}>
                  Save Note
                </button>
                <button type="button" disabled={isTicketWorking || !activeTicketId.trim()} onClick={() => void generateTicketDraft()}>
                  Generate Draft Update
                </button>
              </div>
            </form>
          </article>

          <article className="panel prompt-preview">
            <h2>Draft Update</h2>
            {ticketDraft ? (
              <>
                <pre className="prompt-output">{ticketDraft.body}</pre>
                <label className="checkbox confirm-post">
                  <input
                    type="checkbox"
                    checked={ticketConfirmPost}
                    onChange={(event) => setTicketConfirmPost(event.target.checked)}
                  />
                  I approve posting this draft to Azure DevOps
                </label>
                <div className="form-actions">
                  <button type="button" disabled={isTicketWorking || !ticketConfirmPost} onClick={() => void postTicketDraft()}>
                    Post Approved Draft
                  </button>
                </div>
              </>
            ) : (
              <p className="empty">Generate a draft before posting. Drafts stay local until explicitly approved.</p>
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
