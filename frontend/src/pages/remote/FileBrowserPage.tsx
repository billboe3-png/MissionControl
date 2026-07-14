import { useCallback, useEffect, useRef, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import EmptyState from "../../components/common/EmptyState";
import { useToast } from "../../contexts/ToastContext";
import { filesApi, FileListItem } from "../../services/files";
import { hostsApi, HostData } from "../../services/remote";

function formatSize(bytes: number | null): string {
    if (bytes === null) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileBrowserPage() {
    const { showToast } = useToast();
    const [hosts, setHosts] = useState<HostData[]>([]);
    const [selectedHostId, setSelectedHostId] = useState<number | "">("");
    const [currentPath, setCurrentPath] = useState("/");
    const [items, setItems] = useState<FileListItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [creatingFolder, setCreatingFolder] = useState(false);
    const [newFolderName, setNewFolderName] = useState("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        hostsApi.list().then((d) => setHosts(d.items)).catch(() => {});
    }, []);

    const loadDirectory = useCallback(async () => {
        if (!selectedHostId) return;
        try {
            setLoading(true);
            setError(null);
            const data = await filesApi.list(selectedHostId, currentPath);
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to list directory");
        } finally {
            setLoading(false);
        }
    }, [selectedHostId, currentPath]);

    useEffect(() => {
        loadDirectory();
    }, [loadDirectory]);

    const navigateTo = (path: string) => {
        setCurrentPath(path);
    };

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !selectedHostId) return;
        try {
            const reader = new FileReader();
            reader.onload = async () => {
                const b64 = (reader.result as string).split(",")[1];
                const remotePath = `${currentPath.replace(/\/$/, "")}/${file.name}`;
                await filesApi.upload(selectedHostId, remotePath, b64);
                showToast("File uploaded");
                loadDirectory();
            };
            reader.readAsDataURL(file);
        } catch {
            showToast("Upload failed", "error");
        }
        e.target.value = "";
    };

    const handleDownload = async (item: FileListItem) => {
        if (!selectedHostId) return;
        try {
            const result = await filesApi.download(selectedHostId, item.path);
            if (result.content_base64) {
                const binary = atob(result.content_base64);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
                const blob = new Blob([bytes]);
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = item.name;
                a.click();
                URL.revokeObjectURL(url);
                showToast("Downloaded");
            }
        } catch {
            showToast("Download failed", "error");
        }
    };

    const handleDelete = async (item: FileListItem) => {
        if (!selectedHostId) return;
        if (!confirm(`Delete "${item.name}"?`)) return;
        try {
            await filesApi.remove(selectedHostId, item.path);
            showToast("Deleted");
            loadDirectory();
        } catch {
            showToast("Delete failed", "error");
        }
    };

    const handleCreateFolder = async () => {
        if (!selectedHostId || !newFolderName.trim()) return;
        try {
            const folderPath = `${currentPath.replace(/\/$/, "")}/${newFolderName.trim()}`;
            await filesApi.mkdir(selectedHostId, folderPath);
            showToast("Folder created");
            setCreatingFolder(false);
            setNewFolderName("");
            loadDirectory();
        } catch {
            showToast("Failed to create folder", "error");
        }
    };

    const pathParts = currentPath.split("/").filter(Boolean);

    return (
        <>
            <PageHeader
                title="File Browser"
                subtitle="Browse and manage remote files"
                actions={
                    selectedHostId ? (
                        <>
                            <input
                                type="file"
                                ref={fileInputRef}
                                style={{ display: "none" }}
                                onChange={handleUpload}
                            />
                            <button
                                className="btn btn-primary"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                Upload
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => setCreatingFolder(true)}
                            >
                                New Folder
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={loadDirectory}
                            >
                                Refresh
                            </button>
                        </>
                    ) : undefined
                }
            />

            <div className="form-row" style={{ maxWidth: 400, marginBottom: 16 }}>
                <label className="form-label">Host</label>
                <select
                    className="form-select"
                    value={selectedHostId}
                    onChange={(e) => {
                        setSelectedHostId(Number(e.target.value) || "");
                        setCurrentPath("/");
                    }}
                >
                    <option value="">Select a host…</option>
                    {hosts.map((h) => (
                        <option key={h.id} value={h.id}>
                            {h.name} ({h.hostname})
                        </option>
                    ))}
                </select>
            </div>

            {selectedHostId && (
                <nav className="breadcrumb" style={{ marginBottom: 16 }}>
                    <span
                        className="breadcrumb-item"
                        style={{ cursor: "pointer" }}
                        onClick={() => navigateTo("/")}
                    >
                        /
                    </span>
                    {pathParts.map((part, i) => {
                        const subPath = "/" + pathParts.slice(0, i + 1).join("/");
                        return (
                            <span key={subPath} className="breadcrumb-separator">
                                <span className="breadcrumb-chevron">›</span>
                                <span
                                    className="breadcrumb-item"
                                    style={{ cursor: "pointer" }}
                                    onClick={() => navigateTo(subPath)}
                                >
                                    {part}
                                </span>
                            </span>
                        );
                    })}
                </nav>
            )}

            {creatingFolder && (
                <div className="execute-form" style={{ marginBottom: 16, maxWidth: 400 }}>
                    <div className="form-row">
                        <label className="form-label">Folder name</label>
                        <input
                            className="form-input"
                            type="text"
                            value={newFolderName}
                            onChange={(e) => setNewFolderName(e.target.value)}
                            placeholder="new-folder"
                            autoFocus
                        />
                    </div>
                    <div style={{ display: "flex", gap: 8 }}>
                        <button className="btn btn-primary" onClick={handleCreateFolder}>
                            Create
                        </button>
                        <button
                            className="btn btn-sm"
                            onClick={() => {
                                setCreatingFolder(false);
                                setNewFolderName("");
                            }}
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {error && <div className="error-banner">{error}</div>}

            {!selectedHostId ? (
                <EmptyState
                    icon="📂"
                    title="Select a host"
                    description="Choose a remote host to browse its filesystem."
                />
            ) : loading ? (
                <div className="loading">Loading…</div>
            ) : items.length === 0 ? (
                <EmptyState
                    icon="📂"
                    title="Empty directory"
                    description="This directory contains no files or folders."
                />
            ) : (
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Size</th>
                                <th>Permissions</th>
                                <th style={{ width: 120 }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {currentPath !== "/" && (
                                <tr
                                    className="clickable"
                                    onClick={() => {
                                        const parent = currentPath.replace(/\/[^/]+\/?$/, "") || "/";
                                        navigateTo(parent);
                                    }}
                                >
                                    <td><span style={{ color: "var(--primary)" }}>📁 ..</span></td>
                                    <td>—</td>
                                    <td>—</td>
                                    <td></td>
                                </tr>
                            )}
                            {items.map((item) => (
                                <tr
                                    key={item.path}
                                    className={item.is_directory ? "clickable" : undefined}
                                    onClick={
                                        item.is_directory
                                            ? () => navigateTo(item.path)
                                            : undefined
                                    }
                                >
                                    <td>
                                        <span style={{ marginRight: 6 }}>
                                            {item.is_directory ? "📁" : "📄"}
                                        </span>
                                        {item.name}
                                    </td>
                                    <td>{formatSize(item.size_bytes)}</td>
                                    <td style={{ fontFamily: "monospace", fontSize: "0.82rem" }}>
                                        {item.permissions ?? "—"}
                                    </td>
                                    <td>
                                        <div style={{ display: "flex", gap: 4 }}>
                                            {!item.is_directory && (
                                                <button
                                                    className="btn btn-sm btn-primary"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDownload(item);
                                                    }}
                                                >
                                                    DL
                                                </button>
                                            )}
                                            <button
                                                className="btn btn-sm btn-danger"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDelete(item);
                                                }}
                                            >
                                                Del
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
