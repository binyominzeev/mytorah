"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

type Status = { state: "none" | "queued" | "running" | "done" | "error"; stage?: string; progress?: number; error?: string };

export default function QuestionMap({ mapRef }: { mapRef: string }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [shown, setShown] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    setStatus(null);
    setShown(false);
    return () => clearTimeout(timer.current);
  }, [mapRef]);

  useEffect(() => {
    if (status?.state === "done") setShown(true);
  }, [status]);

  async function call(method: "GET" | "POST"): Promise<Status | null> {
    try {
      const r = await fetch(`${API}/map/${mapRef}`, { method });
      if (!r.ok) {
        setStatus({ state: "error", error: r.status === 429 ? "A napi keret elfogyott, próbáld holnap." : undefined });
        return null;
      }
      const s: Status = await r.json();
      setStatus(s);
      return s;
    } catch {
      setStatus({ state: "error", error: "A szerver nem elérhető." });
      return null;
    }
  }

  async function poll() {
    const s = await call("GET");
    if (s && (s.state === "queued" || s.state === "running")) {
      timer.current = setTimeout(poll, 2000);
    }
  }

  async function load() {
    clearTimeout(timer.current);
    const s = await call("GET");
    if (!s) return;
    if (s.state === "done") return setShown(true);
    if (s.state === "none" || s.state === "error") {
      const started = await call("POST");
      if (!started) return;
    }
    timer.current = setTimeout(poll, 1500);
  }

  const busy = status?.state === "queued" || status?.state === "running";
  const done = status?.state === "done";
  const htmlUrl = `${API}/map/${mapRef}/html`;

  return (
    <div className="qmap">
      {!shown && (
        <button type="button" className="qmap-btn" onClick={load} disabled={busy}>
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
      {status?.state === "error" && (
        <p className="qmap-error">{status.error ?? "A generálás nem sikerült."}</p>
      )}
      {shown && done && (
        <>
          <a className="qmap-open" href={htmlUrl} target="_blank" rel="noreferrer">
            Megnyitás új lapon
          </a>
          <iframe className="qmap-frame" src={htmlUrl} title={`Kérdés-térkép ${mapRef}`} />
        </>
      )}
    </div>
  );
}
