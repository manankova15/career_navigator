import { Vacancy } from "../api/vacancies";

const STORAGE_KEY = "career_navigator_liked_vacancies";

export function getLikedVacancies(): Vacancy[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function setLikedVacancies(list: Vacancy[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch {}
}

export function isLiked(id: string): boolean {
  return getLikedVacancies().some(v => v.id === id);
}

export function toggleLike(vacancy: Vacancy): boolean {
  const list = getLikedVacancies();
  const idx = list.findIndex(v => v.id === vacancy.id);
  if (idx >= 0) {
    list.splice(idx, 1);
    setLikedVacancies(list);
    return false;
  }
  list.push(vacancy);
  setLikedVacancies(list);
  return true;
}
