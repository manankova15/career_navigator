"""Resume pipeline end-to-end (extract step mocked for stability)."""

from pathlib import Path
from unittest.mock import patch

from app.resume.pipeline import run_resume_pipeline


def _hh_like_text() -> str:
    return """
Резюме
Иванов Иван Иванович
Мужчина, 30 лет, родился 8 февраля 1995

Data Engineer / Analyst
200 000 ₽ на руки

Москва, м. Рязанский проспект, не готов к переезду, готов к командировкам

Контакты
+7 (999) 123-45-67
Телефон подтвержден
ivan@example.com
предпочитаемый способ связи — email

Специализации
Аналитик
Программист

Занятость
полная занятость

График работы
полный день
удаленная работа

Опыт работы
ООО «Ромашка»
Январь 2020 — по настоящее время
Москва
https://romashka.example
Информационные технологии
Инженер данных
Поддержка пайплайнов.

Навыки
Python, SQL, Git

Образование
МГУ
Факультет ВМК
2017

Знание языков
Русский — Родный

Гражданство, время в пути до работы
Гражданство: Россия
Разрешение на работу: Россия
Желательное время в пути до работы: не более часа

hh.ru/applicant/resumes/view?print=true
Резюме обновлено 1 апреля 2026
"""


@patch(
    "app.resume.pipeline.extract_text_from_pdf",
    return_value=(_hh_like_text(), "pypdf"),
)
def test_run_resume_pipeline(mock_extract, tmp_path: Path):
    pdf = tmp_path / "ignored.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    result = run_resume_pipeline(pdf)
    mock_extract.assert_called_once_with(pdf)
    assert result["extraction_method"] == "pypdf"
    assert result["parsed"]["profile"].get("email") == "ivan@example.com"
    assert "sections_detected" in result
    assert isinstance(result["field_confidence"], dict)
