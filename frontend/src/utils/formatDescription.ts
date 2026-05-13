/**
 * Безопасный HTML и Telegram-подобный текст → HTML для рендера
 */

/** Эвристика: в строке есть HTML-теги */
export function isHtml(text: string): boolean {
  return /<(p|br|ul|li|strong|b|em|i|h[1-6]|div|span|a)[^>]*>/i.test(text);
}

/** HTML описания: структурные теги, без script/style/iframe/form */
export function sanitizeHtml(html: string): string {
  // script / style / iframe / form
  let s = html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<iframe[\s\S]*?<\/iframe>/gi, "")
    .replace(/<form[\s\S]*?<\/form>/gi, "");

  // on* и javascript: в href
  s = s.replace(/\s(on\w+)="[^"]*"/gi, "");
  s = s.replace(/\s(on\w+)='[^']*'/gi, "");
  s = s.replace(/href\s*=\s*["']javascript:[^"']*["']/gi, 'href="#"');

  // Ссылки — target=_blank
  s = s.replace(/<a\s/gi, '<a target="_blank" rel="noopener noreferrer" ');

  return s;
}

/** Plain text: markdown-подобная разметка, списки, переносы → HTML */
export function telegramToHtml(text: string): string {
  // Экранирование & < >
  let s = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Markdown [text](url)
  s = s.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
  );

  // **bold** / __bold__
  s = s.replace(/\*\*(.+?)\*\*/gs, "<strong>$1</strong>");
  s = s.replace(/__(.+?)__/gs, "<strong>$1</strong>");

  // *italic* / _italic_ (вне strong)
  s = s.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/gs, "<em>$1</em>");
  s = s.replace(/(?<!_)_(?!_)(.+?)(?<!_)_(?!_)/gs, "<em>$1</em>");

  // `code`
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Построчно: списки и <br>
  const lines = s.split("\n");
  const out: string[] = [];
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Маркеры списка (emoji, -, *)
    const isBullet = /^(▪️|▸|◾|◼|•|➤|✅|✔️|→|🔹|🔸|📌|▶|»|-|\*)\s/.test(trimmed);

    if (isBullet) {
      if (!inList) { out.push("<ul>"); inList = true; }
      const content = trimmed.replace(/^(▪️|▸|◾|◼|•|➤|✅|✔️|→|🔹|🔸|📌|▶|»|-|\*)\s+/, "");
      out.push(`<li>${content}</li>`);
    } else {
      if (inList) { out.push("</ul>"); inList = false; }
      if (trimmed === "") {
        // Пустая строка
        if (out.length > 0 && out[out.length - 1] !== "<br>") {
          out.push("<br>");
        }
      } else {
        out.push(line);
        // <br> между непустыми строками
        if (i < lines.length - 1 && lines[i + 1].trim() !== "") {
          out.push("<br>");
        }
      }
    }
  }
  if (inList) out.push("</ul>");

  return out.join("\n");
}

/** Подготовка описания вакансии к рендеру (HTML или telegramToHtml) */
export function prepareDescription(description: string | null | undefined): string {
  if (!description) return "";

  const text = description.trim();

  if (isHtml(text)) {
    return sanitizeHtml(text);
  }

  return telegramToHtml(text);
}
