"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

type Status = { state: "none" | "queued" | "running" | "done" | "error"; stage?: string; progress?: number; error?: string };

export default function QuestionMap({ mapRef }: { mapRef: string }) {
  const [status, setStatus] = useState<Status | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const current = useRef(mapRef);
  current.current = mapRef;

  // Responses for a verse the user already left are ignored.
  const call = useCallback(async (ref: string, method: "GET" | "POST"): Promise<Status | null> => {
    let s: Status;
    try {
      const r = await fetch(`${API}/map/${ref}`, { method });
      s = r.ok
        ? await r.json()
        : { state: "error", error: r.status === 429 ? "A napi keret elfogyott, próbáld holnap." : undefined };
    } catch {
      s = { state: "error", error: "A szerver nem elérhető." };
    }
    if (current.current !== ref) return null;
    setStatus(s);
    return s;
  }, []);

  const poll = useCallback(
    async (ref: string) => {
      const s = await call(ref, "GET");
      if (s && (s.state === "queued" || s.state === "running")) {
        timer.current = setTimeout(() => poll(ref), 2000);
      }
    },
    [call],
  );

  // On every verse change, check the server: show a finished map, resume a running job.
  useEffect(() => {
    setStatus(null);
    poll(mapRef);
    return () => clearTimeout(timer.current);
  }, [mapRef, poll]);

  // The map is a same-origin iframe: hand it the site's fonts (webfont rules + family variables).
  function styleFrame(e: React.SyntheticEvent<HTMLIFrameElement>) {
    try {
      const doc = e.currentTarget.contentDocument;
      if (!doc) return;
      const fontRules: string[] = [];
      for (const sheet of Array.from(document.styleSheets)) {
        for (const rule of Array.from(sheet.cssRules)) {
          if (rule instanceof CSSFontFaceRule) fontRules.push(rule.cssText);
        }
      }
      const cs = getComputedStyle(document.documentElement);
      const vars = ["--font-body", "--font-ui", "--font-hebrew-text", "--font-hebrew"]
        .map((v) => `${v}:${cs.getPropertyValue(v)};`)
        .join("");
      const style = doc.createElement("style");
      style.textContent = `${fontRules.join("\n")}\n:root{${vars}}`;
      doc.head.appendChild(style);
    } catch {
      // cross-origin API: keep the built-in fallback fonts
    }
  }

  async function generate() {
    clearTimeout(timer.current);
    const s = await call(mapRef, "POST");
    if (s && (s.state === "queued" || s.state === "running")) {
      timer.current = setTimeout(() => poll(mapRef), 1500);
    }
  }

  const busy = status?.state === "queued" || status?.state === "running";
  const done = status?.state === "done";
  const htmlUrl = `${API}/map/${mapRef}/html`;

  return (
    <div className="qmap">
      {status && !done && (
        <button type="button" className="qmap-btn" onClick={generate} disabled={busy}>
          AI kérdés-válasz kommentár
        </button>
      )}
      {busy && (
        <div className="qmap-progress" role="status">
          <div className="qmap-bar">
            <div style={{ width: `${status?.progress ?? 0}%` }} />
          </div>
          <span>{status?.stage}</span>
        </div>
      )}
      {status?.state === "error" && <p className="qmap-error">{status.error ?? "A generálás nem sikerült."}</p>}
      {done && (
        <>
          <a className="qmap-open" href={htmlUrl} target="_blank" rel="noreferrer">
            Megnyitás új lapon
          </a>
          <iframe className="qmap-frame" src={htmlUrl} onLoad={styleFrame} title={`Kérdés-térkép ${mapRef}`} />
        </>
      )}
    </div>
  );
}
