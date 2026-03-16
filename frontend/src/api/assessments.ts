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
  order: number;
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
}

export async function listAssessments(): Promise<AssessmentSummary[]> {
  const data = await api.get<{ items: AssessmentSummary[] }>("/assessments?page_size=50");
  return data.items ?? [];
}

export async function getAssessment(id: string): Promise<AssessmentDetail> {
  return api.get<AssessmentDetail>(`/assessments/${id}`);
}

// assessment-service submits all answers at once — no separate "start" needed
export async function submitAttempt(
  assessmentId: string,
  answers: { item_id: string; selected_option_ids?: string[]; text_answer?: string }[]
): Promise<AttemptResult> {
  return api.post<AttemptResult>(`/assessments/${assessmentId}/submit`, { answers });
}

export async function myAttempts(): Promise<AttemptResult[]> {
  const data = await api.get<{ items: AttemptResult[] }>("/attempts/me?page_size=50");
  return data.items ?? [];
}
