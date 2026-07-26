import { useState, useCallback, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";

const STORAGE_KEY = "mc_dashboard_prefs";

interface WidgetConfig {
    id: string;
    label: string;
    icon: string;
    visible: boolean;
    order: number;
    size: "sm" | "md" | "lg";
}

const DEFAULT_WIDGETS: WidgetConfig[] = [
    { id: "fleet", label: "Fleet Overview", icon: "🤖", visible: true, order: 0, size: "md" },
    { id: "infra", label: "Infrastructure", icon: "🏗️", visible: true, order: 1, size: "md" },
    { id: "system", label: "System Health", icon: "⚙️", visible: true, order: 2, size: "md" },
    { id: "automation", label: "Automation", icon: "⚡", visible: true, order: 3, size: "md" },
    { id: "ai", label: "AI Engine", icon: "🧠", visible: true, order: 4, size: "md" },
    { id: "activity", label: "Recent Activity", icon: "📋", visible: true, order: 5, size: "md" },
    { id: "companies", label: "Companies & Sites", icon: "🏢", visible: true, order: 6, size: "md" },
    { id: "insights", label: "AI Insights", icon: "💡", visible: true, order: 7, size: "md" },
    { id: "overview", label: "System Overview", icon: "🖥️", visible: true, order: 8, size: "md" },
];

function loadPrefs(): WidgetConfig[] {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return DEFAULT_WIDGETS;
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
            return parsed;
        }
    } catch { /* ignore */ }
    return DEFAULT_WIDGETS;
}

function savePrefs(widgets: WidgetConfig[]) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(widgets));
}

export default function PersonalDashboardPage() {
    const [widgets, setWidgets] = useState<WidgetConfig[]>(loadPrefs);
    const [customizing, setCustomizing] = useState(false);
    const { showToast } = useToast();

    useEffect(() => {
        savePrefs(widgets);
    }, [widgets]);

    const toggleWidget = (id: string) => {
        setWidgets((prev) =>
            prev.map((w) => (w.id === id ? { ...w, visible: !w.visible } : w)),
        );
    };

    const moveWidget = (id: string, direction: "up" | "down") => {
        setWidgets((prev) => {
            const sorted = [...prev].sort((a, b) => a.order - b.order);
            const idx = sorted.findIndex((w) => w.id === id);
            if (idx < 0) return prev;
            const targetIdx = direction === "up" ? idx - 1 : idx + 1;
            if (targetIdx < 0 || targetIdx >= sorted.length) return prev;
            const temp = sorted[idx].order;
            sorted[idx] = { ...sorted[idx], order: sorted[targetIdx].order };
            sorted[targetIdx] = { ...sorted[targetIdx], order: temp };
            return sorted;
        });
    };

    const resetDefaults = () => {
        setWidgets(DEFAULT_WIDGETS);
        showToast("Dashboard reset to defaults", "success");
    };

    const visibleWidgets = widgets
        .filter((w) => w.visible)
        .sort((a, b) => a.order - b.order);

    return (
        <>
            <PageHeader
                title="Personal Dashboard"
                subtitle="Customize your workspace layout"
                actions={
                    <div className="page-header-actions">
                        <button
                            className={`btn btn-sm ${customizing ? "btn-primary" : "btn-secondary"}`}
                            onClick={() => setCustomizing(!customizing)}
                        >
                            {customizing ? "Done" : "Customize"}
                        </button>
                        {customizing && (
                            <button className="btn btn-sm btn-secondary" onClick={resetDefaults}>
                                Reset
                            </button>
                        )}
                    </div>
                }
            />

            {customizing && (
                <div className="personal-dash-toolbar">
                    <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                        Toggle widgets and reorder them:
                    </span>
                </div>
            )}

            {customizing && (
                <div className="data-table-wrapper" style={{ marginBottom: 20 }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Widget</th>
                                <th>Visible</th>
                                <th>Order</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {widgets
                                .sort((a, b) => a.order - b.order)
                                .map((w) => (
                                    <tr key={w.id}>
                                        <td>
                                            <span>{w.icon}</span>{" "}
                                            <span>{w.label}</span>
                                        </td>
                                        <td>
                                            <input
                                                type="checkbox"
                                                checked={w.visible}
                                                onChange={() => toggleWidget(w.id)}
                                            />
                                        </td>
                                        <td>{w.order + 1}</td>
                                        <td>
                                            <button
                                                className="btn btn-sm btn-secondary"
                                                onClick={() => moveWidget(w.id, "up")}
                                                disabled={w.order === 0}
                                            >
                                                ↑
                                            </button>
                                            <button
                                                className="btn btn-sm btn-secondary"
                                                onClick={() => moveWidget(w.id, "down")}
                                                disabled={w.order === widgets.length - 1}
                                            >
                                                ↓
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                        </tbody>
                    </table>
                </div>
            )}

            <div className={`personal-dash-grid ${customizing ? "customizing" : ""}`}>
                {visibleWidgets.map((w) => (
                    <div key={w.id} className="personal-dash-widget">
                        <div className="widget-card">
                            <div className="widget-header">
                                <div className="widget-title-group">
                                    <span className="widget-icon">{w.icon}</span>
                                    <h3 className="widget-title">{w.label}</h3>
                                </div>
                            </div>
                            <div className="widget-body">
                                <div className="empty-text">
                                    Widget content loads on the Operations Dashboard.
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {visibleWidgets.length === 0 && (
                <div className="empty-state">
                    <span className="empty-state-icon">📊</span>
                    <h3 className="empty-state-title">No widgets visible</h3>
                    <p className="empty-state-description">
                        Enable widgets in customization mode to see them here.
                    </p>
                </div>
            )}
        </>
    );
}
