import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Health = {
  status: string;
  app: string;
  version: string;
};

type ProjectDetection = {
  root: string;
  project_type: string;
  markers: string[];
  message: string;
};

type GeneratedCommand = {
  id: string;
  label: string;
  command: string[];
  risk: string;
  requires_approval: boolean;
};

const actionLabels = ["Validate Bundle", "Run Tests", "Create Codex Prompt", "Create Handoff"];

function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [project, setProject] = useState<ProjectDetection | null>(null);
  const [commands, setCommands] = useState<GeneratedCommand[]>([]);

  useEffect(() => {
    void fetch("/health").then((res) => res.json()).then(setHealth).catch(() => setHealth(null));
    void fetch("/api/project/detect").then((res) => res.json()).then(setProject).catch(() => setProject(null));
    void fetch("/api/commands").then((res) => res.json()).then(setCommands).catch(() => setCommands([]));
  }, []);

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
              <dd>{project?.project_type ?? "Detecting"}</dd>
            </div>
            <div>
              <dt>Root</dt>
              <dd>{project?.root ?? "Local workspace"}</dd>
            </div>
            <div>
              <dt>Markers</dt>
              <dd>{project?.markers.length ? project.markers.join(", ") : "No markers yet"}</dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <h2>Actions</h2>
          <div className="actions">
            {actionLabels.map((label) => (
              <button key={label} type="button">{label}</button>
            ))}
          </div>
        </article>

        <article className="panel commands">
          <h2>Generated Commands</h2>
          {commands.map((item) => (
            <div className="command" key={item.id}>
              <strong>{item.label}</strong>
              <code>{item.command.join(" ")}</code>
              <span>Approval required</span>
            </div>
          ))}
        </article>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
