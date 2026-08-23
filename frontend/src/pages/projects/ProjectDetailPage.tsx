import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import { projectsApi, Project } from "../../services/projects";
import { tasksApi, Task } from "../../services/tasks";
import { notesApi, Note } from "../../services/notes";
import { formatDateTime } from "../../utils/dateFormat";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"tasks" | "notes">("tasks");
  const navigate = useNavigate();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [proj, tasksData, notesData] = await Promise.all([
        projectsApi.get(projectId),
        tasksApi.list(),
        notesApi.list(),
      ]);
      setProject(proj);
      setTasks(tasksData.items.filter(t => t.project_id === projectId));
      setNotes(notesData.items.filter(n => n.project_id === projectId));
    } catch (e: any) {
      console.error("Failed to load project detail:", e);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) loadData();
  }, [loadData, projectId]);

  const handleClose = async () => {
    if (!project) return;
    if (!window.confirm(`Close project "${project.name}"?`)) return;
    try {
      await projectsApi.close(project.id);
      loadData();
    } catch (e: any) {
      console.error("Close failed:", e);
    }
  };

  if (loading) return <div className="loading-bar">Loading project...</div>;
  if (!project) return <div className="empty-state">Project not found.</div>;

  return (
    <>
      <PageHeader
        title={project.name}
        subtitle={project.description || "Project detail"}
        actions={
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn" onClick={() => navigate("/projects")}>
              ← Back
            </button>
            <button className="btn btn-primary" onClick={handleClose} disabled={!project.active}>
              Close Project
            </button>
          </div>
        }
      />

      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">{project.name}</div>
            <div className="card-subtitle">
              Status: <span className={`status-badge ${project.active ? "status-ok" : "status-disabled"}`}>{project.active ? "Active" : "Inactive"}</span>
              Tasks: {tasks.length} | Notes: {notes.length}
            </div>
          </div>
        </div>
        <div className="card-body">
          <div style={{ marginBottom: 12 }}>
            <strong>Description:</strong> {project.description || "—"}
          </div>
          <div>
            <strong>Created:</strong> {formatDateTime(project.created_at)}
          </div>
          <div>
            <strong>Updated:</strong> {formatDateTime(project.updated_at)}
          </div>
        </div>
      </div>

      <div className="tabs" style={{ marginTop: 16 }}>
        <button
          className={`tab ${activeTab === "tasks" ? "active" : ""}`}
          onClick={() => setActiveTab("tasks")}
        >
          Tasks ({tasks.length})
        </button>
        <button
          className={`tab ${activeTab === "notes" ? "active" : ""}`}
          onClick={() => setActiveTab("notes")}
        >
          Notes ({notes.length})
        </button>
      </div>

      {activeTab === "tasks" && (
        <div className="table-container" style={{ marginTop: 8 }}>
          {tasks.length === 0 ? (
            <div className="empty-state">No tasks in this project yet.</div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Assignee</th>
                  <th>Due</th>
                  <th>Started</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.id}>
                    <td>
                      <strong>{task.title}</strong>
                      {task.description && (
                        <div style={{ fontSize: "0.85em", opacity: 0.6 }}>{task.description}</div>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge ${task.status === "completed" ? "status-ok" : task.status === "in_progress" ? "status-warning" : "status-disabled"}`}>
                        {task.status}
                      </span>
                    </td>
                    <td>{task.priority}</td>
                    <td>{task.assignee || "—"}</td>
                    <td>{task.due_date || "—"}</td>
                    <td>{task.started_at ? new Date(task.started_at).toLocaleString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === "notes" && (
        <div style={{ marginTop: 8 }}>
          {notes.length === 0 ? (
            <div className="empty-state">No notes in this project yet.</div>
          ) : (
            <div className="grid gap-2">
              {notes.map((note) => (
                <div key={note.id} className="card">
                  <div className="card-header">
                    <div className="card-title">{note.title}</div>
                    <div className="card-subtitle">{formatDateTime(note.updated_at)}</div>
                  </div>
                  <div className="card-body">
                    <div style={{ whiteSpace: "pre-wrap" }}>{note.content}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
