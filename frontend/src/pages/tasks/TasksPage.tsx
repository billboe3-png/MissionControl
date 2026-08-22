import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { tasksApi, Task, TaskCreateInput, TaskUpdateInput } from "../../services/tasks";
import { projectsApi, Project } from "../../services/projects";

type Status = "all" | "pending" | "in_progress" | "completed" | "blocked";
type Priority = "all" | "low" | "medium" | "high" | "critical";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<Status>("all");
  const [priorityFilter, setPriorityFilter] = useState<Priority>("all");
  const [projectFilter, setProjectFilter] = useState<number | "all">("all");
  const { /* showToast */ } = { showToast: (m: string, t: string) => {} };

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await tasksApi.list();
      let items = data.items;
      if (statusFilter !== "all") items = items.filter(t => t.status === statusFilter);
      if (priorityFilter !== "all") items = items.filter(t => t.priority === priorityFilter);
      if (projectFilter !== "all") items = items.filter(t => t.project_id === projectFilter);
      setTasks(items);
    } catch (e: any) {
      setError(e.message || "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, projectFilter]);

  const loadProjects = useCallback(async () => {
    try {
      const data = await projectsApi.list();
      setProjects(data.items.filter(p => p.active));
    } catch {
      // ignore project load errors
    }
  }, []);

  useEffect(() => {
    loadTasks();
    loadProjects();
  }, [loadTasks, loadProjects]);

  const handleSave = () => {
    setShowModal(false);
    setEditingTask(undefined);
    loadTasks();
  };

  const handleStatusChange = async (task: Task, newStatus: string) => {
    try {
      await tasksApi.update(task.id, { status: newStatus });
      loadTasks();
    } catch (e: any) {
      setError(e.message || "Status update failed");
    }
  };

  const handleDelete = async (task: Task) => {
    if (!window.confirm(`Delete task "${task.title}"? This cannot be undone.`)) return;
    try {
      await tasksApi.remove(task.id);
      loadTasks();
    } catch (e: any) {
      setError(e.message || "Delete failed");
    }
  };

  const statusBadgeClass = (status: string) => {
    switch (status) {
      case "completed": return "status-ok";
      case "in_progress": return "status-warning";
      case "blocked": return "status-critical";
      default: return "status-disabled";
    }
  };

  const priorityBadgeClass = (priority: string) => {
    switch (priority) {
      case "critical": return "status-critical";
      case "high": return "status-warning";
      case "medium": return "status-disabled";
      default: return "status-disabled";
    }
  };

  return (
    <>
      <PageHeader
        title="Tasks"
        subtitle="Track work items, assignees, due dates, and status"
        actions={
          <button
            className="btn btn-primary"
            onClick={() => {
              setEditingTask(undefined);
              setShowModal(true);
            }}
          >
            + New Task
          </button>
        }
      />

      {error && <div className="error-banner">{error}</div>}

      <div className="toolbar">
        <div className="filters">
          <label>Status:</label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as Status)}>
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="blocked">Blocked</option>
          </select>
          <label>Priority:</label>
          <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value as Priority)}>
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <label>Project:</label>
          <select value={projectFilter} onChange={(e) => setProjectFilter(e.target.value === "all" ? "all" : Number(e.target.value))}>
            <option value="all">All</option>
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-bar" />
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <h3>No Tasks</h3>
          <p>Create a task to start tracking work.</p>
          <button className="btn btn-primary" onClick={() => { setEditingTask(undefined); setShowModal(true); }}>
            + New Task
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Project</th>
                <th>Assignee</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Due</th>
                <th>Started</th>
                <th style={{ textAlign: "right" }}>Actions</th>
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
                  <td>{task.project_id}</td>
                  <td>{task.assignee || "—"}</td>
                  <td>
                    <span className={`status-badge ${priorityBadgeClass(task.priority)}`}>
                      {task.priority}
                    </span>
                  </td>
                  <td>
                    <select
                      className="form-input"
                      value={task.status}
                      onChange={(e) => handleStatusChange(task, e.target.value)}
                      style={{ minWidth: 120 }}
                    >
                      <option value="pending">Pending</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                      <option value="blocked">Blocked</option>
                    </select>
                  </td>
                  <td>{task.due_date || "—"}</td>
                  <td>{task.started_at ? new Date(task.started_at).toLocaleString() : "—"}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="btn btn-sm" onClick={() => { setEditingTask(task); setShowModal(true); }}>
                      Edit
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(task)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <TaskModal
          task={editingTask}
          projects={projects}
          onSave={handleSave}
          onCancel={() => {
            setShowModal(false);
            setEditingTask(undefined);
          }}
        />
      )}
    </>
  );
}

function TaskModal({ task, projects, onSave, onCancel }: { task?: Task; projects: Project[]; onSave: () => void; onCancel: () => void }) {
  const [projectId, setProjectId] = useState(task?.project_id ?? 0);
  const [title, setTitle] = useState(task?.title ?? "");
  const [description, setDescription] = useState(task?.description ?? "");
  const [status, setStatus] = useState(task?.status ?? "pending");
  const [priority, setPriority] = useState(task?.priority ?? "medium");
  const [assignee, setAssignee] = useState(task?.assignee ?? "");
  const [dueDate, setDueDate] = useState(task?.due_date ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!title.trim() || !projectId) {
      setError("Title and project are required");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload: TaskCreateInput | TaskUpdateInput = {
        project_id: projectId,
        title: title.trim(),
        description: description || undefined,
        status,
        priority,
        assignee: assignee || undefined,
        due_date: dueDate || undefined,
      };
      if (task) {
        await tasksApi.update(task.id, payload);
      } else {
        await tasksApi.create(payload as TaskCreateInput);
      }
      onSave();
    } catch (e: any) {
      setError(e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{task ? "Edit Task" : "New Task"}</h2>
          <button className="modal-close" onClick={onCancel}>&times;</button>
        </div>
        <div className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label>Project *</label>
            <select value={projectId} onChange={(e) => setProjectId(Number(e.target.value))}>
              <option value={0}>Select project...</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Title *</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Wire dashboard to PostgreSQL" />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
          </div>

          <div className="form-group">
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="blocked">Blocked</option>
            </select>
          </div>

          <div className="form-group">
            <label>Priority</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div className="form-group">
            <label>Assignee</label>
            <input value={assignee} onChange={(e) => setAssignee(e.target.value)} placeholder="e.g. Robert Barnes" />
          </div>

          <div className="form-group">
            <label>Due Date</label>
            <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn" onClick={onCancel} disabled={saving}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>
            {saving ? "Saving..." : task ? "Update" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}
