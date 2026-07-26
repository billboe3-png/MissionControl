# Frontend Architecture

Mission Control's frontend is a React 18 single-page application built with TypeScript and Vite.

## Build Tooling

### Vite

Vite handles dev server, hot module replacement, and production bundling:

```ts
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
});
```

Start the dev server:

```bash
cd frontend
npm run dev        # http://localhost:5173
```

Production build:

```bash
npm run build      # outputs to dist/
npm run preview    # preview the production build locally
```

### TypeScript

TypeScript is configured in strict mode with ES2020 target:

```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "noEmit": true,
    "isolatedModules": true
  }
}
```

The project uses project references: `tsconfig.json` references `tsconfig.app.json` (app code) and `tsconfig.node.json` (tooling).

Type-check before committing:

```bash
npx tsc --noEmit
```

## Application Structure

### Entry Point

`src/main.tsx` renders the root component:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

### Root Component

`src/App.tsx` defines the route tree using React Router:

```tsx
import { Routes, Route } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { Dashboard } from "./pages/dashboard/Dashboard";
import { Hosts } from "./pages/remote/Hosts";
import { Login } from "./pages/auth/Login";
// ...

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/remote/hosts" element={<Hosts />} />
        <Route path="/remote/credentials" element={<Credentials />} />
        {/* ... */}
      </Route>
    </Routes>
  );
}
```

## Layout System

The app uses a Windows Admin Center-inspired layout:

```
┌─────────────────────────────────────────────┐
│  Sidebar (collapsible)  │     TopBar         │
│                         │  (breadcrumbs)      │
│  ┌──────────────────┐   ├─────────────────────┤
│  │ Dashboard        │   │                     │
│  │ Infrastructure   │   │     Content          │
│  │ Remote Ops       │   │     (<Outlet />)     │
│  │ Automation       │   │                     │
│  │ Platform         │   │                     │
│  │ Settings         │   │                     │
│  └──────────────────┘   ├─────────────────────┤
│                         │  StatusBar           │
│                         │  (clock, version)    │
└─────────────────────────────────────────────┘
```

### Layout Components

| Component | File | Purpose |
|-----------|------|---------|
| `AppLayout` | `src/layouts/AppLayout.tsx` | Top-level layout with sidebar, topbar, outlet, statusbar |
| `Sidebar` | `src/layouts/Sidebar.tsx` | Collapsible navigation sidebar |
| `TopBar` | `src/layouts/TopBar.tsx` | Breadcrumb navigation from route metadata |
| `StatusBar` | `src/layouts/StatusBar.tsx` | Live clock, connection status, version |

### Navigation Groups

The sidebar organizes navigation into collapsible groups:

- **Dashboard** — main dashboard view
- **Infrastructure** — overview, system, docker, git, health
- **Remote Operations** — hosts, credentials, execute, history, files
- **Automation** — playbooks, schedules, execution logs
- **Platform** — agents, integrations, Zabbix, Proxmox, Hyper-V, Identity
- **Settings** — general, appearance, about

## Components

### Common Components (`src/components/common/`)

Reusable UI primitives used across all pages:

| Component | Purpose |
|-----------|---------|
| `DataTable` | Tabular data display with row click, sorting, and empty states |
| `EmptyState` | Shown when a list has no data |
| `PageHeader` | Page title, subtitle, and action buttons |
| `SearchInput` | Filter input for lists |
| `StatusBadge` | Colored badge for status values |
| `Modal` | Dialog wrapper for create/edit forms |
| `ConfirmDialog` | Confirmation dialog with callback |

### Dashboard Components (`src/components/dashboard/`)

| Component | Purpose |
|-----------|---------|
| `StatCard` | Metric display card (CPU, memory, disk) |
| `HealthBadges` | Service health status indicators |
| `QuickActions` | Shortcut buttons for common operations |

### Domain Components (`src/components/<domain>/`)

Domain-specific components live alongside their page directories or in domain-specific component folders.

## Pages (`src/pages/`)

Pages are organized by domain:

```
src/pages/
├── agents/          Agent management
├── ai/              AI assistant
├── auth/            Login, user management, password change
├── automation/      Playbook CRUD, execution logs
├── companies/       Company management
├── dashboard/       Main dashboard
├── hyperv/          Hyper-V VM management
├── identity/        Identity provider management
├── infrastructure/  Overview, System, Docker, Git, Health
├── proxmox/         Proxmox VE management
├── remote/          Hosts, Credentials, Execute, History, Files
├── settings/        General, Appearance, About
└── zabbix/          Zabbix monitoring
```

### Page Pattern

Every page follows a consistent structure:

```tsx
import { useState, useEffect } from "react";
import { PageHeader } from "../../components/common/PageHeader";
import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { HostModal } from "../../components/modals/HostModal";
import { apiClient } from "../../services/apiClient";
import type { RemoteHost } from "../../types";

export function Hosts() {
  const [hosts, setHosts] = useState<RemoteHost[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadHosts();
  }, []);

  async function loadHosts() {
    const data = await apiClient.get("/api/v1/remote/hosts");
    setHosts(data);
    setLoading(false);
  }

  return (
    <div className="page">
      <PageHeader
        title="Remote Hosts"
        subtitle="Manage SSH and WinRM connections"
        actionLabel="Add Host"
        onAction={() => setShowModal(true)}
      />
      {loading ? (
        <div className="loading">Loading...</div>
      ) : hosts.length === 0 ? (
        <EmptyState
          title="No hosts"
          description="Add your first remote host to get started."
        />
      ) : (
        <DataTable
          data={hosts}
          columns={[
            { key: "name", label: "Name" },
            { key: "hostname", label: "Hostname" },
            { key: "protocol", label: "Protocol" },
          ]}
          onRowClick={(host) => navigate(`/remote/hosts/${host.id}`)}
        />
      )}
      {showModal && <HostModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
```

## State Management

Mission Control uses React's built-in state primitives — no external state library.

### Local State

Component-level state with `useState` and `useEffect` for data fetching.

### Contexts (`src/contexts/`)

| Context | Purpose |
|---------|---------|
| `SidebarContext` | Sidebar collapsed/expanded state |
| `ToastContext` | Global toast notification queue |

Contexts are minimal. Most state is local to the page or component that owns it.

## API Client (`src/services/`)

The API client is a thin wrapper around `fetch`:

```ts
// src/services/apiClient.ts
const API_BASE = "/api/v1";

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const token = localStorage.getItem("token");
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}

export const apiClient = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body: unknown) => request<T>("PUT", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
};
```

### Usage in Components

```ts
import { apiClient } from "../services/apiClient";
import type { HostResponse } from "../types";

const hosts = await apiClient.get<HostResponse[]>("/remote/hosts");
const newHost = await apiClient.post<HostResponse>("/remote/hosts", hostData);
```

## Types (`src/types/`)

TypeScript type definitions mirror the backend Pydantic schemas:

```ts
export interface RemoteHost {
  id: number;
  name: string;
  hostname: string;
  protocol: "ssh" | "winrm";
  port: number;
  is_active: boolean;
  company_id: number | null;
  created_at: string;
}

export interface CredentialProfile {
  id: number;
  name: string;
  username: string;
  auth_type: "password" | "ssh_key";
  host_id: number;
}
```

## Styling

The app uses a custom dark-theme CSS layer in `src/styles.css`. No CSS framework (Tailwind, Bootstrap) is used in production — Tailwind is a devDependency for utility reference only.

All pages follow the same visual patterns:
- Dark backgrounds (`#1a1a2e`, `#16213e`)
- Light text (`#e0e0e0`)
- Accent colors for status (green = success, red = error, yellow = warning)
- Consistent spacing and border-radius

## Cross-References

- See [CODING_STANDARDS.md](CODING_STANDARDS.md) for TypeScript naming conventions.
- See [BACKEND.md](BACKEND.md) for the API endpoints these pages consume.
- See [API.md](API.md) for backend endpoint patterns.
- See [TESTING.md](TESTING.md) for frontend testing plans.
