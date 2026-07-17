const TOKEN_KEY = "mc_token";

function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

export interface ApiClientOptions extends RequestInit {
    /** Override the default JSON Content-Type header. */
    json?: unknown;
}

/**
 * Shared fetch wrapper that attaches the stored auth token and handles
 * common error responses.  Use this instead of raw `fetch()` for all
 * calls to `/api/v1/...` endpoints.
 *
 * Usage:
 *   const data = await apiClient<ResponseType>("/api/v1/dashboard");
 *   const created = await apiClient<CreatedType>("/api/v1/items", {
 *       method: "POST",
 *       json: { name: "foo" },
 *   });
 */
export async function apiClient<T = unknown>(
    url: string,
    options: ApiClientOptions = {},
): Promise<T> {
    const { json, ...init } = options;

    const headers = new Headers(init.headers);

    const token = getToken();
    if (token && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    if (json !== undefined && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
        init.body = JSON.stringify(json);
    }

    const response = await fetch(url, { ...init, headers });

    if (response.status === 401) {
        // Token expired or invalid — clear stored auth so the app
        // redirects to the login page on next render.
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem("mc_user");
        window.location.href = "/login";
        throw new Error("Session expired. Please log in again.");
    }

    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        throw new Error(detail ?? `Request failed (${response.status})`);
    }

    // 204 No Content — nothing to parse.
    if (response.status === 204) {
        return undefined as T;
    }

    return response.json() as Promise<T>;
}
