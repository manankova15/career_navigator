import { api } from "./client";

// Matches AssessmentOut from assessment-service
export interface AssessmentSummary {
  id: string;
  title: string;
  description?: string;
  topic: string;
  difficulty: string;       // "easy" | "medium" | "hard"
  related_skills: string[];
  is_published: boolean;
  item_count: number;
}

// Matches AssessmentWithItemsOut
export interface AssessmentDetail extends AssessmentSummary {
  items: AssessmentItem[];
}

export interface AssessmentItem {
  id: string;
  order?: number;
  position?: number;
  mode: string;             // "quiz" | "multi_select" | "short_text" | "case"
  prompt: string;
  options?: { id: string; text: string }[];
  max_score: number;
  explanation?: string | null;
}

export interface AnswerResult {
  id: string;
  item_id: string;
  mode: string;
  selected_option_ids: string[];
  text_answer?: string | null;
  is_correct?: boolean | null;
  earned_score: number;
  auto_feedback?: string | null;
}

// Matches AttemptSummaryOut / AttemptOut
export interface AttemptResult {
  id: string;
  assessment_id: string;
  assessment_title?: string | null;
  status: string;
  earned_score: number;
  max_score: number;
  percentage: number;
  passed: boolean;
  weak_skills: string[];
  started_at?: string | null;
  submitted_at?: string | null;
  created_at: string;
  completed_at?: string | null;
  answers?: AnswerResult[];
  progress_answers?: { item_id: string; selected_option_ids?: string[]; text_answer?: string | null }[];
}

export async function listAssessments(): Promise<AssessmentSummary[]> {
  const data = await api.get<{ items: AssessmentSummary[] }>("/assessments?page_size=50");
  return data.items ?? [];
}

export async function getAssessment(id: string): Promise<AssessmentDetail> {
  return api.get<AssessmentDetail>(`/assessments/${id}`);
}

export async function getAttempt(attemptId: string): Promise<AttemptResult> {
  return api.get<AttemptResult>(`/attempts/${attemptId}`);
}

/** Start an assessment (creates in_progress attempt for save/resume). */
export async function startAttempt(assessmentId: string): Promise<AttemptResult> {
  return api.post<AttemptResult>(`/assessments/${assessmentId}/start`, {});
}

/** Save partial answers for in-progress attempt. */
export async function saveAttemptProgress(
  attemptId: string,
  answers: { item_id: string; selected_option_ids?: string[]; text_answer?: string | null }[]
): Promise<AttemptResult> {
  return api.patch<AttemptResult>(`/attempts/${attemptId}/progress`, { answers });
}

export async function submitAttempt(
  assessmentId: string,
  answers: { item_id: string; selected_option_ids?: string[]; text_answer?: string }[],
  attemptId?: string | null
): Promise<AttemptResult> {
  return api.post<AttemptResult>(`/assessments/${assessmentId}/submit`, {
    answers,
    attempt_id: attemptId ?? undefined,
  });
}

export async function myAttempts(assessmentId?: string | null): Promise<AttemptResult[]> {
  const params = new URLSearchParams({ page_size: "50" });
  if (assessmentId) params.set("assessment_id", assessmentId);
  const data = await api.get<{ items: AttemptResult[] }>(`/attempts/me?${params.toString()}`);
  return data.items ?? [];
}
