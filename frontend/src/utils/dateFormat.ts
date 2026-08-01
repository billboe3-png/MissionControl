/** Shared date/time helpers. */

export function formatDateTime(
  iso: string | null | undefined,
  timezone = "UTC",
): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";

  try {
    return d.toLocaleString("en-US", {
      timeZone: timezone,
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
