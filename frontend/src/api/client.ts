// eslint-disable-next-line @typescript-eslint/no-explicit-any
const env = (import.meta as any).env;

/**
 * Base URL for API calls. Rules:
 * - If VITE_API_URL is set, it is used (trailing slashes stripped).
 * - If it points at the gateway on port 8000 but omits `/api`, `/api` is appended
 *   (the gateway only exposes routes under `/api/*`).
 * - If unset in the browser, use same-origin `/api` so Vite dev proxy or frontend nginx can forward.
 */
function resolveApiBase(): string {
  const raw = env?.VITE_API_URL?.trim() as string | undefined;
  if (raw) {
    const b = raw.replace(/\/+$/, "");
    if (b.endsWith("/api")) return b;
    try {
      const u = new URL(b);
      if (u.port === "8000") {
        return `${u.origin}/api`;
      }
    } catch {
      /* ignore invalid URL */
    }
    return b;
  }
  if (typeof window !== "undefined") {
    return "/api";
  }
  return "http://localhost:8000/api";
}

export const API_BASE = resolveApiBase();

function token(): string | null {
  return localStorage.getItem("access_token");
}

function authHeaders(): Record<string, string> {
  const t = token();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(init.headers ?? {}) },
    ...init,
  });

  if (resp.status === 401) {
    clearToken();
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
    throw new Error("Сессия истекла. Войдите снова.");
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail ?? resp.statusText);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export function saveToken(t: string) { localStorage.setItem("access_token", t); }
export function clearToken() { localStorage.removeItem("access_token"); }
export function getToken() { return token(); }
