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

function commandText(command: GeneratedCommand) {
  return [command.command, ...command.args].join(" ");
}

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [project, setProject] = useState<ProjectDetection | null>(null);
  const [commands, setCommands] = useState<GeneratedCommand[]>([]);
  const [selectedCommand, setSelectedCommand] = useState<GeneratedCommand | null>(null);
  const [runResult, setRunResult] = useState<CommandRunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

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

      <section className="grid">
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
      </section>

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
