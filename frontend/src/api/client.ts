// eslint-disable-next-line @typescript-eslint/no-explicit-any
const BASE = (import.meta as any).env?.VITE_API_URL ?? "http://localhost:8000/api";

function token(): string | null {
  return localStorage.getItem("access_token");
}

function authHeaders(): Record<string, string> {
  const t = token();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
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
