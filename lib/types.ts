export interface RowData {
  heHtml: string;
  huHtml: string;
}

export interface CommentaryEntry {
  id: string;
  html: string;
}

export interface ChapterVerses {
  chapter: number;
  verses: number[];
}

export interface ParashaData {
  book: string;
  parasha: string;
  slug: string;
  sefariaBook?: string;
  rows: RowData[];
  commentaries: CommentaryEntry[];
  chapters: number[];
  verses: ChapterVerses[];
}

export interface NavParasha {
  name: string;
  slug: string;
  available: boolean;
}

export interface NavBook {
  name: string;
  parashot: NavParasha[];
}
