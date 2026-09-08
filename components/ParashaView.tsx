"use client";

import { useEffect, useRef, useState } from "react";
import type { CommentaryEntry, RowData } from "@/lib/types";
import BilingualTable from "./BilingualTable";
import CommentaryPanel from "./CommentaryPanel";

interface ActiveInfo {
  chapter: number;
  verse: number;
  book?: string;
}

/** One static page serves every /slug, /slug/chapter and /slug/chapter/verse URL (nginx maps them all here); this parses which one it is on mount. */
function parseLocation(slug: string): { chapter: number; verse: number | null } | null {
  const parts = window.location.pathname.split("/").filter(Boolean);
  if (parts[0] !== slug) return null;
  const chapter = Number(parts[1]);
  if (!parts[1] || Number.isNaN(chapter)) return null;
  const verse = parts[2] !== undefined ? Number(parts[2]) : null;
  return { chapter, verse: verse !== null && !Number.isNaN(verse) ? verse : null };
}

export default function ParashaView({
  slug,
  rows,
  commentaries,
}: {
  slug: string;
  rows: RowData[];
  commentaries: CommentaryEntry[];
}) {
  const [panelOpen, setPanelOpen] = useState(false);
  const [activeInfo, setActiveInfo] = useState<ActiveInfo | undefined>();
  const containerRef = useRef<HTMLDivElement>(null);

  function clearActive() {
    containerRef.current?.querySelectorAll(".active-verse").forEach((el) => el.classList.remove("active-verse"));
    containerRef.current?.querySelectorAll("tr.active-row").forEach((el) => el.classList.remove("active-row"));
  }

  function activateVerse(chapter: number, verse: number, scroll: boolean) {
    const container = containerRef.current;
    if (!container) return;
    clearActive();
    const anchor = container.querySelector<HTMLElement>(`#ch${chapter}-vrs${verse}`);
    const huNumber = container.querySelector<HTMLElement>(`strong.vrs-ch${chapter}-vrs${verse}`);
    anchor?.classList.add("active-verse");
    huNumber?.classList.add("active-verse");
    anchor?.closest("tr")?.classList.add("active-row");
    const book = anchor?.dataset.book;
    setActiveInfo({ chapter, verse, book });
    setPanelOpen(true);
    if (scroll) anchor?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  // Initial load: highlight/scroll to whatever the URL (set by nginx's chapter/verse rewrite) asked for.
  useEffect(() => {
    const target = parseLocation(slug);
    if (!target) return;
    if (target.verse !== null) {
      activateVerse(target.chapter, target.verse, true);
    } else {
      containerRef.current
        ?.querySelector<HTMLElement>(`#chapter-${target.chapter}`)
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  // Keep the URL in sync with whichever verse is currently in view while scrolling,
  // without pushing new history entries or touching the active-verse highlight.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let ticking = false;
    function updateFromScroll() {
      ticking = false;
      const anchors = container!.querySelectorAll<HTMLAnchorElement>("a.verse-link[data-chapter]");
      if (!anchors.length) return;
      const threshold = 140;
      let current: HTMLAnchorElement = anchors[0];
      anchors.forEach((a) => {
        if (a.getBoundingClientRect().top - threshold <= 0) current = a;
      });
      const { chapter, verse } = current.dataset;
      if (!chapter || !verse) return;
      const href = `/${encodeURIComponent(slug)}/${chapter}/${verse}`;
      if (window.location.pathname !== href) {
        window.history.replaceState(window.history.state, "", href);
      }
    }
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(updateFromScroll);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [slug, rows]);

  function extractVerseKey(el: Element): string | null {
    const id = el.getAttribute("id");
    if (id && /^ch\d+-vrs\d+$/.test(id)) return id;
    const cls = Array.from(el.classList).find((c) => /^vrs-ch\d+-vrs\d+$/.test(c));
    return cls ? cls.slice(4) : null;
  }

  function setHover(target: EventTarget | null, on: boolean) {
    const el = (target as HTMLElement | null)?.closest('[id^="ch"], [class*="vrs-ch"]');
    if (!el) return;
    const key = extractVerseKey(el);
    if (!key) return;
    containerRef.current?.querySelectorAll(`[id="${key}"], .vrs-${key}`).forEach((node) => {
      node.classList.toggle("verse-hover", on);
    });
  }

  function handleClick(e: React.MouseEvent) {
    const target = e.target as HTMLElement;

    const commentaryEl = target.closest("[data-commentary-id]") as HTMLElement | null;
    if (commentaryEl) {
      e.preventDefault();
      const id = commentaryEl.getAttribute("data-commentary-id")!;
      setPanelOpen(true);
      requestAnimationFrame(() => {
        document.getElementById(`commentary-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
      return;
    }

    const verseEl = target.closest("[data-href][data-chapter][data-verse]") as HTMLElement | null;
    if (verseEl) {
      e.preventDefault();
      const chapter = Number(verseEl.dataset.chapter);
      const verse = Number(verseEl.dataset.verse);
      window.history.pushState(null, "", verseEl.dataset.href!);
      activateVerse(chapter, verse, false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key !== "Enter" && e.key !== " ") return;
    handleClick(e as unknown as React.MouseEvent);
  }

  const sefariaHref =
    activeInfo && activeInfo.book
      ? `https://www.sefaria.org/${activeInfo.book}.${activeInfo.chapter}.${activeInfo.verse}`
      : undefined;
  const sefariaLabel = activeInfo ? `${activeInfo.book ?? ""} ${activeInfo.chapter}:${activeInfo.verse}` : undefined;

  return (
    <div
      ref={containerRef}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onMouseOver={(e) => setHover(e.target, true)}
      onMouseOut={(e) => setHover(e.target, false)}
    >
      <div className="content">
        <BilingualTable rows={rows} />
      </div>
      <CommentaryPanel
        open={panelOpen}
        onClose={() => setPanelOpen(false)}
        sefariaHref={sefariaHref}
        sefariaLabel={sefariaLabel}
        commentaries={commentaries}
      />
    </div>
  );
}
