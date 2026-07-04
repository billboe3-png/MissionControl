import { useEffect, useState } from "react";

type ApiStatus = {
  name: string;
  status: string;
  environment: string;
};

const plannedModules = [
  "Dashboard",
  "Tasks",
  "Projects",
  "Notes",
  "Focus Mode",
  "Resume Me",
  "Parking Lot",
  "Integrations"
];

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/v1")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }
        return response.json() as Promise<ApiStatus>;
      })
      .then(setApiStatus)
      .catch((error: Error) => setApiError(error.message));
  }, []);

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-950">
      <section className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-emerald-700">
              Sprint 1 Foundation
            </p>
            <h1 className="mt-3 text-4xl font-semibold tracking-normal md:text-5xl">
              Mission Control
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-600">
              A personal operations center for IT professionals, built as a
              modular monolith with FastAPI, React, PostgreSQL, Redis, and
              Nginx.
            </p>
          </div>
          <div className="rounded-md border border-zinc-200 bg-zinc-50 px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              API Status
            </p>
            <p className="mt-1 text-sm font-semibold">
              {apiStatus ? `${apiStatus.status} (${apiStatus.environment})` : "Checking..."}
            </p>
            {apiError ? <p className="mt-1 text-sm text-red-700">{apiError}</p> : null}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="grid gap-6 md:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-md border border-zinc-200 bg-white p-6">
            <h2 className="text-xl font-semibold">Foundation Services</h2>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {["FastAPI Backend", "React Frontend", "PostgreSQL", "Redis", "Nginx Proxy", "Docker Compose"].map(
                (service) => (
                  <div
                    className="flex items-center justify-between rounded-md border border-zinc-200 px-4 py-3"
                    key={service}
                  >
                    <span className="text-sm font-medium">{service}</span>
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-600" />
                  </div>
                )
              )}
            </div>
          </div>

          <div className="rounded-md border border-zinc-200 bg-white p-6">
            <h2 className="text-xl font-semibold">Planned Modules</h2>
            <ul className="mt-5 space-y-3">
              {plannedModules.map((moduleName) => (
                <li className="flex items-center gap-3 text-sm text-zinc-700" key={moduleName}>
                  <span className="h-2 w-2 rounded-full bg-zinc-400" />
                  {moduleName}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </main>
  );
}

export default App;
