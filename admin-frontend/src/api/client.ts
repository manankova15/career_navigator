const env = import.meta.env;

function resolveApiBase(): string {
  const raw = env?.VITE_API_URL?.trim();
  if (raw) {
    const b = raw.replace(/\/+$/, "");
    if (b.endsWith("/api")) return b;
    try {
      const u = new URL(b);
      if (u.port === "8000") return `${u.origin}/api`;
    } catch {
      /* ignore */
    }
    return b;
  }
  if (typeof window !== "undefined") return "/api";
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
    window.location.href = "/login";
    throw new Error("Сессия истекла. Войдите снова.");
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    const d = err.detail;
    const msg = typeof d === "string" ? d : JSON.stringify(d ?? err);
    throw new Error(msg);
  }
  if (resp.status === 204) return undefined as T;
  const ct = resp.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) return resp.json();
  return undefined as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
};

export function saveToken(t: string) {
  localStorage.setItem("access_token", t);
}
export function clearToken() {
  localStorage.removeItem("access_token");
}
