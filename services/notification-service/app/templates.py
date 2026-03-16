"""
Notification template registry.

Each template is a function that takes a context dict and returns
a (subject, body) tuple. Body is plain text; HTML version is derived
by wrapping in a simple HTML layout for email.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class RenderedMessage:
    subject: str
    body: str           # plain-text
    html_body: str      # HTML for email


TemplateFunc = Callable[[dict[str, Any]], tuple[str, str]]


# ── Individual templates ──────────────────────────────────────────────────────

def _tpl_welcome(ctx: dict[str, Any]) -> tuple[str, str]:
    name = ctx.get("name", "there")
    subject = "Welcome to Career Navigator!"
    body = (
        f"Hi {name},\n\n"
        "Welcome to Career Navigator — your personal career growth platform.\n\n"
        "Here's what you can do:\n"
        "  • Browse and get personalised vacancy recommendations\n"
        "  • Take skill assessments and track your progress\n"
        "  • Identify skill gaps and get learning recommendations\n\n"
        "Get started by completing your profile:\n"
        f"  {ctx.get('profile_url', 'https://career-navigator.local/profile')}\n\n"
        "Good luck with your career journey!\n\n"
        "— Career Navigator Team"
    )
    return subject, body


def _tpl_email_verification(ctx: dict[str, Any]) -> tuple[str, str]:
    name = ctx.get("name", "there")
    code = ctx.get("verification_code", "")
    link = ctx.get("verification_link", "")
    subject = "Verify your Career Navigator email"
    body = (
        f"Hi {name},\n\n"
        "Please verify your email address to activate your account.\n\n"
        f"Verification code: {code}\n\n"
        f"Or click this link: {link}\n\n"
        "This link expires in 24 hours.\n\n"
        "If you didn't register, please ignore this email.\n\n"
        "— Career Navigator Team"
    )
    return subject, body


def _tpl_new_vacancy_match(ctx: dict[str, Any]) -> tuple[str, str]:
    name = ctx.get("name", "there")
    count = ctx.get("new_count", 0)
    top_title = ctx.get("top_vacancy_title", "")
    top_company = ctx.get("top_vacancy_company", "")
    link = ctx.get("vacancies_link", "https://career-navigator.local/vacancies")
    subject = f"You have {count} new vacancy match{'es' if count != 1 else ''}!"
    lines = [
        f"Hi {name},",
        "",
        f"We found {count} new {'vacancies' if count != 1 else 'vacancy'} matching your profile.",
    ]
    if top_title and top_company:
        lines += [
            "",
            f"Top pick: {top_title} at {top_company}",
        ]
    lines += [
        "",
        f"View all recommendations: {link}",
        "",
        "— Career Navigator",
    ]
    body = "\n".join(lines)
    return subject, body


def _tpl_assessment_result(ctx: dict[str, Any]) -> tuple[str, str]:
    name = ctx.get("name", "there")
    title = ctx.get("assessment_title", "assessment")
    score = ctx.get("percentage", 0)
    earned = ctx.get("earned_score", 0)
    max_s = ctx.get("max_score", 0)
    weak = ctx.get("weak_skills", [])
    link = ctx.get("result_link", "https://career-navigator.local/assessments")
    subject = f"Your results: {title}"
    lines = [
        f"Hi {name},",
        "",
        f"You completed \"{title}\".",
        f"Score: {earned}/{max_s} ({score:.1f}%)",
    ]
    if score >= 75:
        lines.append("Great job! Keep it up.")
    elif score >= 50:
        lines.append("Good effort! Review the topics below to improve.")
    else:
        lines.append("Don't give up! Study the areas below and try again.")

    if weak:
        lines += ["", "Areas to improve:"]
        for skill in weak:
            lines.append(f"  • {skill}")

    lines += [
        "",
        f"View detailed feedback: {link}",
        "",
        "— Career Navigator",
    ]
    body = "\n".join(lines)
    return subject, body


def _tpl_weekly_digest(ctx: dict[str, Any]) -> tuple[str, str]:
    name = ctx.get("name", "there")
    new_vacancies = ctx.get("new_vacancies_count", 0)
    pending_assessments = ctx.get("pending_assessments_count", 0)
    top_skill_gap = ctx.get("top_skill_gap", "")
    link = ctx.get("dashboard_link", "https://career-navigator.local/dashboard")
    subject = "Your weekly Career Navigator digest"
    lines = [
        f"Hi {name}, here's your weekly summary:",
        "",
    ]
    if new_vacancies:
        lines.append(f"  📋 {new_vacancies} new vacancy matches waiting for you")
    if pending_assessments:
        lines.append(f"  📝 {pending_assessments} assessments available to take")
    if top_skill_gap:
        lines.append(f"  🎯 Top skill gap to work on: {top_skill_gap}")
    lines += [
        "",
        f"Open your dashboard: {link}",
        "",
        "Update notification preferences in your profile settings.",
        "",
        "— Career Navigator",
    ]
    body = "\n".join(lines)
    return subject, body


def _tpl_assessment_reminder(ctx: dict[str, Any]) -> tuple[str, str]:
    name = ctx.get("name", "there")
    days = ctx.get("days_since_last", 7)
    link = ctx.get("assessments_link", "https://career-navigator.local/assessments")
    subject = "It's time to practise your skills!"
    body = (
        f"Hi {name},\n\n"
        f"You haven't taken an assessment in {days} days.\n\n"
        "Regular practice helps close skill gaps faster. "
        "New assessments are available for you now.\n\n"
        f"Take an assessment: {link}\n\n"
        "— Career Navigator"
    )
    return subject, body


def _tpl_password_reset(ctx: dict[str, Any]) -> tuple[str, str]:
    name = ctx.get("name", "there")
    link = ctx.get("reset_link", "")
    subject = "Reset your Career Navigator password"
    body = (
        f"Hi {name},\n\n"
        "We received a request to reset your password.\n\n"
        f"Reset link (valid for 1 hour): {link}\n\n"
        "If you didn't request this, you can safely ignore this email.\n\n"
        "— Career Navigator Team"
    )
    return subject, body


# ── Registry ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, TemplateFunc] = {
    "welcome": _tpl_welcome,
    "email_verification": _tpl_email_verification,
    "new_vacancy_match": _tpl_new_vacancy_match,
    "assessment_result": _tpl_assessment_result,
    "weekly_digest": _tpl_weekly_digest,
    "assessment_reminder": _tpl_assessment_reminder,
    "password_reset": _tpl_password_reset,
}

SUPPORTED_TEMPLATES = sorted(_REGISTRY.keys())


def _wrap_html(subject: str, body: str) -> str:
    """Wrap plain-text body in a minimal HTML email layout."""
    html_body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_body = html_body.replace("\n", "<br>\n")
    return (
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>{subject}</title></head>"
        f"<body style='font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px'>"
        f"<h2 style='color:#2c5282'>{subject}</h2>"
        f"<div style='line-height:1.6'>{html_body}</div>"
        f"<hr style='margin-top:30px'>"
        f"<p style='color:#718096;font-size:12px'>Career Navigator &mdash; "
        f"<a href='https://career-navigator.local/settings/notifications'>manage notifications</a></p>"
        f"</body></html>"
    )


def render(template_name: str, context: dict[str, Any]) -> RenderedMessage:
    """Render a template and return subject + plain + HTML body."""
    func = _REGISTRY.get(template_name)
    if func is None:
        # Fallback: treat template_name as the subject itself
        subject = template_name.replace("_", " ").title()
        body = str(context.get("message", f"Notification: {template_name}"))
        return RenderedMessage(subject=subject, body=body, html_body=_wrap_html(subject, body))

    subject, body = func(context)
    return RenderedMessage(subject=subject, body=body, html_body=_wrap_html(subject, body))
