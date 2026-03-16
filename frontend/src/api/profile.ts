import { api } from "./client";

export interface ProfileSkill {
  id: string;
  skill_id: string;
  skill_name: string;
  self_assessed_level: number;
  confirmed: boolean;
  years_of_experience?: number | null;
}

export interface Profile {
  id: string;
  user_id: string;
  full_name?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  patronymic?: string | null;
  bio?: string | null;
  location?: string | null;
  target_role?: string | null;
  target_industry?: string | null;
  headline?: string | null;
  summary?: string | null;
}

export async function getProfile(): Promise<Profile> {
  return api.get<Profile>("/profiles/me");
}

export async function updateProfile(data: Partial<Profile>): Promise<Profile> {
  return api.put<Profile>("/profiles/me", data);
}

export async function getProfileSkills(): Promise<ProfileSkill[]> {
  return api.get<ProfileSkill[]>("/profiles/me/skills");
}

export async function addProfileSkill(skill_name: string, level = 1): Promise<ProfileSkill> {
  return api.post<ProfileSkill>("/profiles/me/skills", {
    skill_name,
    self_assessed_level: level,
  });
}

export async function removeProfileSkill(skillId: string): Promise<void> {
  return api.del<void>(`/profiles/me/skills/${skillId}`);
}
