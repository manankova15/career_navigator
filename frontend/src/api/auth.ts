import { api, saveToken } from "./client";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MeResponse {
  user_id: string;
  email: string | null;
  full_name: string | null;
  roles: string[];
  is_active: boolean;
}

export async function login(email: string, password: string): Promise<MeResponse> {
  const data = await api.post<TokenResponse>("/auth/login", { email, password });
  saveToken(data.access_token);
  if (data.refresh_token) {
    localStorage.setItem("refresh_token", data.refresh_token);
  }
  return api.get<MeResponse>("/auth/me");
}

export async function register(
  email: string,
  password: string,
  full_name: string,
): Promise<void> {
  const data = await api.post<TokenResponse>("/auth/register", { email, password, full_name });
  saveToken(data.access_token);
  if (data.refresh_token) {
    localStorage.setItem("refresh_token", data.refresh_token);
  }
}

export async function getMe(): Promise<MeResponse> {
  return api.get<MeResponse>("/auth/me");
}

export interface ForgotPasswordResponse {
  message: string;
}

export async function forgotPassword(email: string): Promise<ForgotPasswordResponse> {
  return api.post<ForgotPasswordResponse>("/auth/forgot-password", { email });
}

export function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}
