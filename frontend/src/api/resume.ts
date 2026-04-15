import { API_BASE, getToken } from "./client";

export interface ResumeFile {
  id: string;
  user_id: string;
  original_name: string;
  mime_type: string;
  extension: string;
  size: number;
  sha256: string;
  source_type: string;
  uploaded_at: string;
}

export interface ResumeParseJob {
  id: string;
  resume_file_id: string;
  status: string;
  error_message: string | null;
  parser_version: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface ResumeParseResult {
  id: string;
  resume_file_id: string;
  is_hh_resume: boolean;
  hh_confidence_score: number;
  warnings: string[];
  sections_detected: string[];
  parsed: Record<string, unknown> | null;
}

export interface ProfileImportDraft {
  id: string;
  user_id: string;
  resume_file_id: string;
  draft_json: {
    parsed?: Record<string, unknown>;
    parseMeta?: Record<string, unknown>;
  };
  field_confidence_json: Record<string, unknown> | null;
  status: string;
  created_at: string;
  applied_at: string | null;
}

export interface ResumeUploadResponse {
  resume_file: ResumeFile;
  parse_job: ResumeParseJob;
}

export interface ResumeStatusBundle {
  resume_file: ResumeFile;
  parse_job: ResumeParseJob | null;
  parse_result: ResumeParseResult | null;
  draft: ProfileImportDraft | null;
}

function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function uploadResumePdf(file: File): Promise<ResumeUploadResponse> {
  const fd = new FormData();
  fd.append("file", file);
  const resp = await fetch(`${API_BASE}/profiles/me/resume/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: fd,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Ошибка загрузки");
  }
  return resp.json();
}

export async function getResumeFileStatus(fileId: string): Promise<ResumeStatusBundle> {
  const resp = await fetch(`${API_BASE}/profiles/me/resume/files/${fileId}/status`, {
    headers: { ...authHeaders() },
  });
  if (!resp.ok) throw new Error("Не удалось получить статус");
  return resp.json();
}

export async function applyResumeDraft(
  draftId: string,
  body: Record<string, unknown>,
): Promise<{ draft_id: string; status: string; message: string }> {
  const resp = await fetch(`${API_BASE}/profiles/me/resume/drafts/${draftId}/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Ошибка применения");
  }
  return resp.json();
}
