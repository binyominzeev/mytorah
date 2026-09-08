import { marked } from "marked";

marked.setOptions({ gfm: true, breaks: false });

/** Strips an Obsidian YAML frontmatter block (---\n...\n---\n) from the start of a note. */
export function removeCssClasses(mdText: string): string {
  return mdText.replace(/^---\n[\s\S]*?\n---\n/, "");
}

function escapeAttr(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/"/g, "&quot;");
}

/**
 * Converts vault Markdown to HTML, turning Obsidian-style wiki links into
 * commentary references (`data-commentary-id`) instead of Python's inline onclick.
 */
export function markdownToHtml(mdText: string): string {
  // [[id|caption]] -> commentary link
  let text = mdText.replace(
    /\[\[([^\]|]+)\|([^\]]+)\]\]/g,
    (_m, id: string, caption: string) =>
      `<a href="#" class="commentary-link" data-commentary-id="${escapeAttr(id.trim())}">${caption}</a>`
  );

  // [[caption]] -> commentary link, id derived from the caption text
  text = text.replace(
    /\[\[([^\]]+)\]\]/g,
    (_m, id: string) =>
      `<a href="#" class="commentary-link" data-commentary-id="${escapeAttr(
        id.trim().replace(/ /g, "-")
      )}">${id}</a>`
  );

  // Force every source line break to start a new Markdown paragraph.
  text = text.replace(/\n/g, "  \n\n");

  let html = marked.parse(text, { async: false }) as string;

  // Standard Markdown links to vault notes ([label](file.md)) -> commentary link
  html = html.replace(
    /<a href="([^"]+\.md)">([^<]+)<\/a>/g,
    (_m, file: string, label: string) =>
      `<a href="#" class="commentary-link" data-commentary-id="${escapeAttr(
        file.replace(/\.md$/, "")
      )}">${label}</a>`
  );

  return html;
}
