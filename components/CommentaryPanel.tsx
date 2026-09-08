"use client";

import type { CommentaryEntry } from "@/lib/types";

export default function CommentaryPanel({
  open,
  onClose,
  sefariaHref,
  sefariaLabel,
  commentaries,
}: {
  open: boolean;
  onClose: () => void;
  sefariaHref?: string;
  sefariaLabel?: string;
  commentaries: CommentaryEntry[];
}) {
  return (
    <div className={open ? "commentary-container open" : "commentary-container"}>
      <div className="panel-close" onClick={onClose} />
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
      {commentaries.map((c) => (
        <div key={c.id} id={`commentary-${c.id}`} className="commentary" dangerouslySetInnerHTML={{ __html: c.html }} />
      ))}
    </div>
  );
}
