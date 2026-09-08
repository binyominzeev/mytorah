import fs from "node:fs";
import path from "node:path";
import { markdownToHtml, removeCssClasses } from "./markdown";
import type { ChapterVerses, CommentaryEntry, NavBook, ParashaData, RowData } from "./types";

const VAULT_PATH = process.env.CONTENT_PATH || "";

const SEFARIA_BOOK_MAP: Record<string, string> = {
  "1 Berésit": "Genesis",
  "2 Smot": "Exodus",
  "3 Vájikrá": "Leviticus",
  "4 Bámidbár": "Numbers",
  "5 Devárim": "Deuteronomy",
};

function requireVaultPath(): string {
  if (!VAULT_PATH) {
    throw new Error(
      "CONTENT_PATH environment variable is not set. Point it at the synced vault content folder."
    );
  }
  return VAULT_PATH;
}

/** Obsidian/Hebrew names carry accents and spaces; URLs/slugs drop accents and use hyphens. */
export function slugify(name: string): string {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

function isDir(p: string): boolean {
  try {
    return fs.statSync(p).isDirectory();
  } catch {
    return false;
  }
}

function readMarkdownFile(filePath: string): string {
  if (!fs.existsSync(filePath)) return "";
  return fs.readFileSync(filePath, "utf-8");
}

function listBooks(): string[] {
  const root = requireVaultPath();
  return fs
    .readdirSync(root)
    .filter((name) => !name.startsWith(".") && isDir(path.join(root, name)));
}

function listParashot(book: string): string[] {
  const bookPath = path.join(requireVaultPath(), book);
  return fs
    .readdirSync(bookPath)
    .filter((name) => !name.startsWith(".") && isDir(path.join(bookPath, name)));
}

function hasParashaContent(book: string, parasha: string): boolean {
  const parashaPath = path.join(requireVaultPath(), book, parasha);
  const heFile = path.join(parashaPath, "HE.md");
  const huFile = path.join(parashaPath, "HU.md");
  return (
    fs.existsSync(heFile) &&
    fs.statSync(heFile).size > 0 &&
    fs.existsSync(huFile) &&
    fs.statSync(huFile).size > 0
  );
}

interface CustomSort {
  [book: string]: string[];
}

function loadCustomSort(): CustomSort {
  try {
    const raw = fs.readFileSync(
      path.join(requireVaultPath(), ".obsidian", "bookmarks.json"),
      "utf-8"
    );
    const data = JSON.parse(raw);
    const sortspec = (data.items || []).find(
      (item: { title?: string }) => item.title === "sortspec"
    );
    if (!sortspec) return {};

    const order: CustomSort = {};
    for (const book of sortspec.items || []) {
      const bookTitle = String(book.title).replace(/\\\\/g, "").trim();
      order[bookTitle] = (book.items || []).map((p: { title: string }) => p.title);
    }
    return order;
  } catch {
    return {};
  }
}

export function getNavStructure(): NavBook[] {
  const customOrder = loadCustomSort();
  const booksInVault = new Map<string, string[]>();
  for (const book of listBooks()) {
    booksInVault.set(book, [...listParashot(book)].sort());
  }

  const nav: NavBook[] = [];
  const processedBooks = new Set<string>();

  for (const [book, parashot] of Object.entries(customOrder)) {
    const available = booksInVault.get(book);
    if (!available) continue;
    processedBooks.add(book);

    const processedParashot = new Set<string>();
    const list: NavBook["parashot"] = [];
    for (const parasha of parashot) {
      if (available.includes(parasha)) {
        list.push({ name: parasha, slug: slugify(parasha), available: hasParashaContent(book, parasha) });
        processedParashot.add(parasha);
      }
    }
    for (const parasha of available) {
      if (!processedParashot.has(parasha)) {
        list.push({ name: parasha, slug: slugify(parasha), available: hasParashaContent(book, parasha) });
      }
    }
    nav.push({ name: book, parashot: list });
  }

  for (const book of [...booksInVault.keys()].sort()) {
    if (processedBooks.has(book)) continue;
    const list = booksInVault
      .get(book)!
      .map((parasha) => ({ name: parasha, slug: slugify(parasha), available: hasParashaContent(book, parasha) }));
    nav.push({ name: book, parashot: list });
  }

  return nav;
}

export function findParashaBySlug(slug: string): { book: string; parasha: string } | null {
  for (const book of listBooks()) {
    for (const parasha of listParashot(book)) {
      if (slugify(parasha) === slug && hasParashaContent(book, parasha)) {
        return { book, parasha };
      }
    }
  }
  return null;
}

export function listAllParashaSlugs(): string[] {
  const slugs: string[] = [];
  for (const book of listBooks()) {
    for (const parasha of listParashot(book)) {
      if (hasParashaContent(book, parasha)) slugs.push(slugify(parasha));
    }
  }
  return slugs;
}

function extractChapterVerseHu(
  line: string,
  currentChapter: number,
  currentVerse: number
): [number, number] {
  const chapterMatch = /^# (\d+)\. fejezet/.exec(line);
  if (chapterMatch) return [Number(chapterMatch[1]), 0];
  const verseMatch = /^\*\*(\d+)\.\*\*/.exec(line);
  if (verseMatch) return [currentChapter, Number(verseMatch[1])];
  return [currentChapter, currentVerse];
}

interface VerseInfo {
  chapter: number;
  verse: number;
}

const HE_VERSE_MARKER_RE = /<a id="ch(?<chapter>\d+)-vrs(?<verse>\d+)"[^>]*>.*?<\/a>/g;
const HU_VERSE_MARKER_RE = /<strong class="vrs-num vrs-ch(?<chapter>\d+)-vrs(?<verse>\d+)"[^>]*>.*?<\/strong>/g;

/**
 * Wraps the plain text following each verse marker (up to the next marker) in a
 * `verse-text vrs-ch{chapter}-vrs{verse}` span, so hovering highlights the whole
 * verse - not just its number badge - on both the Hebrew and Hungarian side.
 */
function wrapVerseTextSpans(html: string, markerRe: RegExp): string {
  const matches = Array.from(html.matchAll(markerRe));
  if (!matches.length) return html;

  let result = html.slice(0, matches[0].index! + matches[0][0].length);
  for (let i = 0; i < matches.length; i++) {
    const { chapter, verse } = matches[i].groups as { chapter: string; verse: string };
    const markerEnd = matches[i].index! + matches[i][0].length;
    const nextMarker = matches[i + 1];
    const segmentEnd = nextMarker ? nextMarker.index! : html.length;
    const text = html.slice(markerEnd, segmentEnd);
    result += `<span class="verse-text vrs-ch${chapter}-vrs${verse}">${text}</span>`;
    if (nextMarker) {
      result += nextMarker[0];
    }
  }
  return result;
}

/** Turns Hebrew `**{letter}**` verse markers into permalinked anchors, advancing a per-row verse counter. */
function applyVerseLinks(
  html: string,
  slug: string,
  book: string | undefined,
  chapter: number,
  startVerse: number
): { html: string; verses: VerseInfo[] } {
  let verse = startVerse;
  const verses: VerseInfo[] = [];
  const result = html.replace(/<strong>\{(.*?)\}<\/strong>/g, (_m, inner: string) => {
    const href = `/${encodeURIComponent(slug)}/${chapter}/${verse}`;
    const bookAttr = book ? ` data-book="${book}"` : "";
    const link = `<a id="ch${chapter}-vrs${verse}" href="${href}" class="verse-link" data-href="${href}" data-chapter="${chapter}" data-verse="${verse}"${bookAttr}><strong>${inner}</strong></a>`;
    verses.push({ chapter, verse });
    verse += 1;
    return link;
  });
  return { html: result, verses };
}

/** Matches Hungarian `**N.**` verse numbers positionally against the Hebrew verses in the same row. */
function attachHuVerseNumbers(html: string, verses: VerseInfo[], slug: string, book: string | undefined): string {
  let idx = 0;
  return html.replace(/<strong>(\d+\.)<\/strong>/g, (match, numText: string) => {
    if (idx >= verses.length) return match;
    const info = verses[idx];
    idx += 1;
    const href = `/${encodeURIComponent(slug)}/${info.chapter}/${info.verse}`;
    const bookAttr = book ? ` data-book="${book}"` : "";
    return `<strong class="vrs-num vrs-ch${info.chapter}-vrs${info.verse}" role="button" tabindex="0" data-href="${href}" data-chapter="${info.chapter}" data-verse="${info.verse}"${bookAttr}>${numText}</strong>`;
  });
}

function collectCommentaries(
  html: string,
  parashaPath: string,
  seen: Set<string>,
  out: CommentaryEntry[]
): void {
  const re = /data-commentary-id="([^"]+)"/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(html))) {
    const id = match[1];
    if (seen.has(id)) continue;
    seen.add(id);
    const commentPath = path.join(parashaPath, "perusim", `${id}.md`);
    if (fs.existsSync(commentPath)) {
      out.push({ id, html: markdownToHtml(readMarkdownFile(commentPath)) });
    }
  }
}

export function getSefariaBook(book: string): string | undefined {
  return SEFARIA_BOOK_MAP[book];
}

export function getParashaData(book: string, parasha: string): ParashaData {
  const parashaPath = path.join(requireVaultPath(), book, parasha);
  const slug = slugify(parasha);
  const sefariaBook = SEFARIA_BOOK_MAP[book];

  const heLines = removeCssClasses(readMarkdownFile(path.join(parashaPath, "HE.md"))).split("\n");
  const huLines = removeCssClasses(readMarkdownFile(path.join(parashaPath, "HU.md"))).split("\n");
  const lineCount = Math.max(heLines.length, huLines.length);

  const rows: RowData[] = [];
  const commentaries: CommentaryEntry[] = [];
  const seenCommentaries = new Set<string>();
  const chapterSet = new Set<number>();
  const versesByChapter = new Map<number, Set<number>>();

  let chapter = 0;
  let verse = 0;

  for (let i = 0; i < lineCount; i++) {
    const heLine = (heLines[i] ?? "").trim();
    const huLine = (huLines[i] ?? "").trim();

    [chapter, verse] = extractChapterVerseHu(huLine, chapter, verse);

    const heHtmlRaw = heLine ? markdownToHtml(heLine) : "&nbsp;";
    let huHtmlRaw = huLine ? markdownToHtml(huLine) : "&nbsp;";

    if (/^# /.test(huLine)) {
      huHtmlRaw = huHtmlRaw.replace("<h1>", `<h1 id="chapter-${chapter}">`);
    }

    const { html: heHtmlLinked, verses: rowVerses } = applyVerseLinks(heHtmlRaw, slug, sefariaBook, chapter, verse);
    const huHtmlLinked = attachHuVerseNumbers(huHtmlRaw, rowVerses, slug, sefariaBook);
    const heHtml = wrapVerseTextSpans(heHtmlLinked, HE_VERSE_MARKER_RE);
    const huHtml = wrapVerseTextSpans(huHtmlLinked, HU_VERSE_MARKER_RE);

    if (rowVerses.length) {
      chapterSet.add(chapter);
      let set = versesByChapter.get(chapter);
      if (!set) {
        set = new Set();
        versesByChapter.set(chapter, set);
      }
      rowVerses.forEach((v) => set!.add(v.verse));
    }

    collectCommentaries(huHtml, parashaPath, seenCommentaries, commentaries);

    rows.push({ heHtml, huHtml });
  }

  const verses: ChapterVerses[] = Array.from(versesByChapter.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([c, vs]) => ({ chapter: c, verses: Array.from(vs).sort((a, b) => a - b) }));

  return {
    book,
    parasha,
    slug,
    sefariaBook,
    rows,
    commentaries,
    chapters: Array.from(chapterSet).sort((a, b) => a - b),
    verses,
  };
}
