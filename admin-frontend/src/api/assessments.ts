import { api } from "./client";

export type AssessmentMode = "quiz" | "multi_select" | "short_text" | "case";
export type Difficulty = "easy" | "medium" | "hard";

export type Option = { id: string; text: string };
export type RubricCriterion = { criterion: string; weight: number };

export type AssessmentItem = {
  id: string;
  assessment_id: string;
  position: number;
  prompt: string;
  mode: AssessmentMode;
  options: Option[];
  correct_option_ids: string[];
  expected_keywords: string[];
  rubric_checklist: RubricCriterion[];
  max_score: number;
  related_skills: string[];
  explanation: string | null;
  created_at: string;
};

export type Assessment = {
  id: string;
  title: string;
  description: string | null;
  topic: string;
  difficulty: Difficulty;
  related_skills: string[];
  is_published: boolean;
  item_count: number;
  created_at: string;
  updated_at: string;
};

export type AssessmentWithItems = Assessment & { items: AssessmentItem[] };

export type AssessmentPage = {
  items: Assessment[];
  total: number;
  page: number;
  page_size: number;
};

export type AssessmentItemPayload = {
  position?: number;
  prompt: string;
  mode: AssessmentMode;
  options?: Option[];
  correct_option_ids?: string[];
  expected_keywords?: string[];
  rubric_checklist?: RubricCriterion[];
  max_score?: number;
  related_skills?: string[];
  explanation?: string | null;
};

export type AssessmentCreatePayload = {
  title: string;
  description?: string | null;
  topic: string;
  difficulty?: Difficulty;
  related_skills?: string[];
  is_published?: boolean;
  items?: AssessmentItemPayload[];
};

export type AssessmentUpdatePayload = Partial<{
  title: string;
  description: string | null;
  topic: string;
  difficulty: Difficulty;
  related_skills: string[];
  is_published: boolean;
}>;

export type AssessmentItemUpdatePayload = Partial<AssessmentItemPayload>;

export function listAssessments(page = 1, pageSize = 50) {
  return api.get<AssessmentPage>(`/admin/assessments?page=${page}&page_size=${pageSize}`);
}

export function getAssessment(id: string) {
  return api.get<AssessmentWithItems>(`/admin/assessments/${id}`);
}

export function createAssessment(payload: AssessmentCreatePayload) {
  return api.post<AssessmentWithItems>(`/admin/assessments`, payload);
}

export function updateAssessment(id: string, payload: AssessmentUpdatePayload) {
  return api.patch<Assessment>(`/admin/assessments/${id}`, payload);
}

export function deleteAssessment(id: string) {
  return api.delete<void>(`/admin/assessments/${id}`);
}

export function publishAssessment(id: string, is_published: boolean) {
  return api.patch<{ success: boolean; message?: string }>(
    `/admin/assessments/${id}/publish`,
    { is_published },
  );
}

export function addAssessmentItem(assessmentId: string, payload: AssessmentItemPayload) {
  return api.post<AssessmentItem>(`/admin/assessments/${assessmentId}/items`, payload);
}

export function updateAssessmentItem(itemId: string, payload: AssessmentItemUpdatePayload) {
  return api.patch<AssessmentItem>(`/admin/assessments/items/${itemId}`, payload);
}

export function deleteAssessmentItem(itemId: string) {
  return api.delete<void>(`/admin/assessments/items/${itemId}`);
}
