/**
 * Formats vacancy descriptions for safe rendering.
 *
 * Handles two formats:
 *  1. HTML (from HH.ru) — cleaned and rendered via dangerouslySetInnerHTML
 *  2. Telegram Markdown-like text — converted to HTML
 */

/**
 * Returns true if the string looks like it contains HTML markup.
 */
export function isHtml(text: string): boolean {
  return /<(p|br|ul|li|strong|b|em|i|h[1-6]|div|span|a)[^>]*>/i.test(text);
}

/**
 * Sanitise an HTML vacancy description.
 * Keeps structural/formatting tags, removes scripts/styles/iframes/forms.
 */
export function sanitizeHtml(html: string): string {
  // Remove dangerous tags entirely (with content)
  let s = html
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/<iframe[\s\S]*?<\/iframe>/gi, "")
    .replace(/<form[\s\S]*?<\/form>/gi, "");

  // Strip event handlers and javascript: hrefs from any tag
  s = s.replace(/\s(on\w+)="[^"]*"/gi, "");
  s = s.replace(/\s(on\w+)='[^']*'/gi, "");
  s = s.replace(/href\s*=\s*["']javascript:[^"']*["']/gi, 'href="#"');

  // Open all links in new tab
  s = s.replace(/<a\s/gi, '<a target="_blank" rel="noopener noreferrer" ');

  return s;
}

/**
 * Convert Telegram-style plain text to HTML.
 * Handles:
 *  - **bold** → <strong>
 *  - *italic* → <em>
 *  - `code` → <code>
 *  - [text](url) → <a href>
 *  - ▪️ / • / – / * at line start → <li> items
 *  - Double newlines → paragraphs
 *  - Single newlines → <br>
 *  - Emoji bullet lists
 */
export function telegramToHtml(text: string): string {
  // Escape HTML entities first (avoid double-escaping)
  let s = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Markdown links [text](url)
  s = s.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
  );

  // Bold: **text** or __text__
  s = s.replace(/\*\*(.+?)\*\*/gs, "<strong>$1</strong>");
  s = s.replace(/__(.+?)__/gs, "<strong>$1</strong>");

  // Italic: *text* or _text_ (single, not already inside strong)
  s = s.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/gs, "<em>$1</em>");
  s = s.replace(/(?<!_)_(?!_)(.+?)(?<!_)_(?!_)/gs, "<em>$1</em>");

  // Inline code: `code`
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Split into lines for list/paragraph handling
  const lines = s.split("\n");
  const out: string[] = [];
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Detect bullet: emoji bullets (▪️ ▸ ◾ • ➤ ✅ ✔️ →), dash -, asterisk *
    const isBullet = /^(▪️|▸|◾|◼|•|➤|✅|✔️|→|🔹|🔸|📌|▶|»|-|\*)\s/.test(trimmed);

    if (isBullet) {
      if (!inList) { out.push("<ul>"); inList = true; }
      // Remove the bullet character
      const content = trimmed.replace(/^(▪️|▸|◾|◼|•|➤|✅|✔️|→|🔹|🔸|📌|▶|»|-|\*)\s+/, "");
      out.push(`<li>${content}</li>`);
    } else {
      if (inList) { out.push("</ul>"); inList = false; }
      if (trimmed === "") {
        // Empty line → paragraph break
        if (out.length > 0 && out[out.length - 1] !== "<br>") {
          out.push("<br>");
        }
      } else {
        out.push(line);
        // Add <br> after non-empty, non-last lines
        if (i < lines.length - 1 && lines[i + 1].trim() !== "") {
          out.push("<br>");
        }
      }
    }
  }
  if (inList) out.push("</ul>");

  return out.join("\n");
}

/**
 * Prepare a vacancy description for rendering.
 * Returns { html, isHtmlContent } — use dangerouslySetInnerHTML with `html`.
 */
export function prepareDescription(description: string | null | undefined): string {
  if (!description) return "";

  const text = description.trim();

  if (isHtml(text)) {
    return sanitizeHtml(text);
  }

  return telegramToHtml(text);
}
