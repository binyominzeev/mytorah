"use client";

import { useEffect, useRef } from "react";
import type { CommentaryEntry } from "@/lib/types";
import QuestionMap from "./QuestionMap";

export default function CommentaryPanel({
  open,
  onClose,
  sefariaHref,
  sefariaLabel,
  mapRef,
  onMapDone,
  commentaries,
}: {
  open: boolean;
  onClose: () => void;
  sefariaHref?: string;
  sefariaLabel?: string;
  mapRef?: string;
  onMapDone?: (ref: string) => void;
  commentaries: CommentaryEntry[];
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ pointerId: number; startY: number; startHeight: number; moved: boolean } | null>(null);
  const ignoreNextClickRef = useRef(false);

  useEffect(() => {
    if (!open && panelRef.current) {
      panelRef.current.style.height = "";
      panelRef.current.classList.remove("resized", "dragging");
    }
  }, [open]);

  function handlePointerDown(event: React.PointerEvent<HTMLButtonElement>) {
    if (!event.isPrimary || event.button !== 0 || !panelRef.current) return;

    dragRef.current = {
      pointerId: event.pointerId,
      startY: event.clientY,
      startHeight: panelRef.current.getBoundingClientRect().height,
      moved: false,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handlePointerMove(event: React.PointerEvent<HTMLButtonElement>) {
    const drag = dragRef.current;
    const panel = panelRef.current;
    if (!drag || drag.pointerId !== event.pointerId || !panel) return;

    const deltaY = drag.startY - event.clientY;
    if (Math.abs(deltaY) > 4) drag.moved = true;
    if (!drag.moved) return;

    const maxHeight = window.innerHeight * 0.9;
    const minHeight = Math.min(140, maxHeight);
    panel.classList.add("resized", "dragging");
    panel.style.height = `${Math.max(minHeight, Math.min(maxHeight, drag.startHeight + deltaY))}px`;
  }

  function handlePointerUp(event: React.PointerEvent<HTMLButtonElement>) {
    const drag = dragRef.current;
    const panel = panelRef.current;
    if (!drag || drag.pointerId !== event.pointerId || !panel) return;

    dragRef.current = null;
    panel.classList.remove("dragging");
    if (!drag.moved) return;

    ignoreNextClickRef.current = true;
    window.setTimeout(() => {
      ignoreNextClickRef.current = false;
    }, 0);

    const deltaY = drag.startY - event.clientY;
    const height = drag.startHeight + deltaY;
    if (deltaY < 0 && height < 150) {
      panel.style.height = "";
      panel.classList.remove("resized");
      onClose();
      return;
    }

    const maxHeight = window.innerHeight * 0.9;
    const minHeight = Math.min(140, maxHeight);
    panel.classList.add("resized");
    panel.style.height = `${Math.max(minHeight, Math.min(maxHeight, height))}px`;
  }

  function handlePointerCancel(event: React.PointerEvent<HTMLButtonElement>) {
    if (dragRef.current?.pointerId !== event.pointerId) return;
    dragRef.current = null;
    panelRef.current?.classList.remove("dragging");
  }

  function handleHandleClick() {
    if (ignoreNextClickRef.current) {
      ignoreNextClickRef.current = false;
      return;
    }
    onClose();
  }

  return (
    <div ref={panelRef} className={open ? "commentary-container open" : "commentary-container"}>
      <button
        type="button"
        className="panel-close"
        aria-label="Alsó panel bezárása"
        aria-expanded={open}
        tabIndex={open ? 0 : -1}
        onClick={handleHandleClick}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerCancel}
      />
      {sefariaHref ? (
        <div id="sefaria-box" className="commentary">
          <p className="vrs-label">{sefariaLabel}</p>
          <p>
            <strong>
              <a id="sefaria-link" href={sefariaHref} target="_blank" rel="noreferrer">
                Open on Sefaria
              </a>
            </strong>
          </p>
        </div>
      ) : (
        <div className="panel-empty">
          <div className="seal">א</div>
          Kattints egy pászukra,
          <br />
          és megjelenik itt a Sefaria-link.
        </div>
      )}
      {mapRef && <QuestionMap mapRef={mapRef} onDone={onMapDone} />}
      {commentaries.map((c) => (
        <div key={c.id} id={`commentary-${c.id}`} className="commentary" dangerouslySetInnerHTML={{ __html: c.html }} />
      ))}
    </div>
  );
}
