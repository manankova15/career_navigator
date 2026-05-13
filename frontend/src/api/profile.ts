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
  /** Канонический код города (см. CITIES в vacanciesConstants). */
  location?: string | null;
  /** Канонический код специализации (см. SPECIALIZATION_OPTIONS). */
  specialization?: string | null;
  /** Канонический код профессиональной области (см. PROFESSION_AREAS). */
  target_industry?: string | null;
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

export interface ProfilePreferences {
  work_formats: string[];
  salary_from?: number | null;
  salary_to?: number | null;
  seniority?: string | null;
}

export async function getPreferences(): Promise<ProfilePreferences | null> {
  return api.get<ProfilePreferences | null>("/profiles/me/preferences");
}

export async function updatePreferences(
  data: Partial<ProfilePreferences>,
): Promise<ProfilePreferences> {
  return api.put<ProfilePreferences>("/profiles/me/preferences", data);
}
