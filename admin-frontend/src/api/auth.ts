import { api, saveToken } from "./client";

export type MeResponse = {
  user_id: string;
  full_name: string;
  email: string | null;
  roles: string[];
  is_active: boolean;
};

type TokenResponse = { access_token: string; refresh_token?: string };

export async function login(email: string, password: string): Promise<MeResponse> {
  const data = await api.post<TokenResponse>("/auth/login", { email, password });
  saveToken(data.access_token);
  if (data.refresh_token) localStorage.setItem("refresh_token", data.refresh_token);
  const me = await api.get<MeResponse>("/auth/me");
  const ok = me.roles.some((r) => r === "admin" || r === "superadmin");
  if (!ok) {
    throw new Error("У этой учётной записи нет прав администратора.");
  }
  return me;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}
