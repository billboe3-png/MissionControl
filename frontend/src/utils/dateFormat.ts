let globalTimezone = "UTC";

export function setGlobalTimezone(tz: string) {
  globalTimezone = tz || "UTC";
  try { localStorage.setItem("mc_timezone", globalTimezone); } catch {}
}

export function getGlobalTimezone(): string {
  try {
    const stored = localStorage.getItem("mc_timezone");
    if (stored) return stored;
  } catch {}
  return globalTimezone;
}

/** Format an ISO timestamp using the configured site timezone. */
export function formatDateTime(iso: string | null | undefined): string {
  const tz = getGlobalTimezone();
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";

  try {
    return d.toLocaleString("en-US", {
      timeZone: tz,
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return d.toISOString();
  }
}
