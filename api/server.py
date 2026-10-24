"""Backend a pászuk kérdés-térképhez (meforshim) — a VPS-en fut, az nginx a /api/ alatt proxyzza.

GET  /api/map/{ref}          -> állapot: none | queued | running | done | error (+ progress, stage)
POST /api/map/{ref}          -> elindítja a generálást (ha már kész vagy fut, nem csinál semmit)
GET  /api/map/{ref}/html     -> a kész, önálló HTML (iframe-be tölthető)

A {ref} alakja: Genesis.17.17. A kész eredmények a meforshim/out/ alatt maradnak (gyorsítótár).
Indítás az api/ mappából: uvicorn server:app --host 127.0.0.1 --port 8001
"""
import asyncio
import os
import re
import sys
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

ROOT = Path(__file__).resolve().parent.parent
MEFORSHIM = ROOT / "meforshim"
OUT = Path(os.environ.get("MEFORSHIM_OUT", MEFORSHIM / "out")).resolve()
MAX_PARALLEL = int(os.environ.get("MAX_PARALLEL_JOBS", "2"))
MAX_NEW_PER_DAY = int(os.environ.get("MAX_NEW_PER_DAY", "200"))
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "")

sys.path.insert(0, str(MEFORSHIM))
import sefaria  # noqa: E402

app = FastAPI(title="mytorah meforshim API", docs_url=None, redoc_url=None)
if ALLOWED_ORIGINS:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS.split(","), allow_methods=["GET", "POST"])

jobs: dict[str, dict] = {}
started: list[float] = []
sem: asyncio.Semaphore | None = None


def parse(ref: str) -> tuple[str, str]:
    """-> ('Genesis.17.17', 'Genesis 17:17'); 404, ha nem Tóra-vers."""
    try:
        book, ch, v = sefaria.parse_ref(ref)
    except (SystemExit, Exception):
        raise HTTPException(404, "Ismeretlen vers")
    return f"{book}.{ch}.{v}", f"{book} {ch}:{v}"


# Dark site theme (see app/globals.css), injected into the map page when it is served.
# --font-* are provided by the embedding page (components/QuestionMap.tsx); the fallbacks are for standalone use.
THEME = """<style>
:root{--bg:transparent;--card:transparent;--fg:#e8e2d2;--mut:#a6a693;--line:#2b2f3c;--acc:#e0bc63;--ok:#7fbf8f;--warn:#e0a458;--chip:rgba(255,255,255,.06)}
html{font-size:14px}
body{font:14px/1.5 var(--font-body,Georgia,serif);color:var(--fg);background:transparent}
header{display:none}
main{padding:0}
.card{border:0;padding:0;margin:0}
.bar{gap:8px;margin:0 0 10px;font:12.5px var(--font-ui,system-ui,sans-serif);color:var(--mut)}
select,input[type=search],button{font:12.5px var(--font-ui,system-ui,sans-serif);padding:4px 9px;border:1px solid #8a7038;border-radius:7px;background:transparent;color:var(--acc)}
input[type=search]{color:var(--fg);border-color:var(--line);flex:1;min-width:90px}
input[type=search]::placeholder{color:var(--mut)}
button:hover{border-color:#c9a24b}
summary{padding:3px 5px}
summary:hover{background:rgba(255,255,255,.04)}
.l1>summary{font-size:14.5px;font-weight:600;color:var(--acc)}
.l2{margin-left:14px}.l2>summary{font-size:14px;font-weight:500}
.l3{margin-left:30px;border-left:2px solid #8a7038;font-size:13.5px;color:var(--fg)}
.n,.tag{font:11px var(--font-ui,system-ui,sans-serif);color:var(--mut)}
.who{color:var(--acc);font-weight:600}
.quote{direction:auto;font-family:var(--font-hebrew-text,var(--font-hebrew,serif));font-size:14px}
.hl{background:rgba(201,162,75,.25)}
::selection{background:#c9a24b;color:#14161d}
</style>"""


def html_path(dot: str) -> Path:
    return OUT / dot / "kerdes-terkep.html"


def build_html(dot: str) -> bool:
    import viewer
    try:
        return bool(viewer.build(str(OUT / dot)))
    except Exception:
        return False


async def run_cmd(args: list[str], on_line) -> int:
    proc = await asyncio.create_subprocess_exec(
        sys.executable, *args, cwd=MEFORSHIM,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    async for raw in proc.stdout:
        on_line(raw.decode("utf-8", "replace").rstrip())
    return await proc.wait()


async def run_job(dot: str, human: str) -> None:
    job = jobs[dot]
    async with sem:
        job.update(state="running", stage="Letöltés a Sefariáról", progress=3)
        total, done = 0, 0
        tail: list[str] = []

        def on_line(line: str) -> None:
            nonlocal total, done
            tail.append(line)
            del tail[:-15]
            if m := re.match(r"Tisztítás: (\d+) magyarázó", line):
                total = int(m.group(1))
                job.update(stage=f"Kinyerés: 0/{total} magyarázó", progress=10)
            elif total and re.match(r"  .+: \d+ kérdés, \d+ utalás", line):
                done += 1
                job.update(stage=f"Kinyerés: {done}/{total} magyarázó",
                           progress=10 + int(60 * min(done, total) / total))
            elif line.startswith("Összevonás"):
                job.update(stage="Kérdések összevonása", progress=75)
            elif line.startswith("Kész:"):
                job.update(stage="HTML készítése", progress=95)

        try:
            code = await run_cmd(["pipeline.py", human, "--out", str(OUT)], on_line)
            if code == 0 and build_html(dot):
                job.update(state="done", stage="Kész", progress=100)
            else:
                msg = next((l for l in reversed(tail) if "Nincs kommentár" in l), None)
                job.update(state="error", error=msg or "A generálás nem sikerült.")
                print("\n".join(tail), file=sys.stderr)
        except Exception as e:
            print(f"job {dot} failed: {e!r}", file=sys.stderr)
            job.update(state="error", error="A generálás nem sikerült.")


def status(dot: str) -> dict:
    job = jobs.get(dot)
    if job and job["state"] in ("queued", "running"):
        return dict(job)
    if html_path(dot).exists() or (any((OUT / dot).glob("result-*.json")) and build_html(dot)):
        return {"state": "done", "stage": "Kész", "progress": 100}
    if job:
        return dict(job)
    return {"state": "none", "progress": 0}


@app.on_event("startup")
async def _startup() -> None:
    global sem
    sem = asyncio.Semaphore(MAX_PARALLEL)


@app.get("/api/map/{ref}")
async def get_status(ref: str):
    return status(parse(ref)[0])


@app.post("/api/map/{ref}")
async def start(ref: str):
    dot, human = parse(ref)
    st = status(dot)
    if st["state"] != "none" and st["state"] != "error":
        return st
    now = time.time()
    started[:] = [t for t in started if now - t < 86400]
    if len(started) >= MAX_NEW_PER_DAY:
        raise HTTPException(429, "A napi generálási keret elfogyott, próbáld holnap.")
    started.append(now)
    jobs[dot] = {"state": "queued", "stage": "Sorban áll", "progress": 0}
    asyncio.create_task(run_job(dot, human))
    return jobs[dot]


@app.get("/api/map/{ref}/html")
async def get_html(ref: str):
    dot, _ = parse(ref)
    if status(dot)["state"] != "done":
        raise HTTPException(404, "Még nincs kész")
    page = html_path(dot).read_text(encoding="utf-8")
    return HTMLResponse(page.replace("</head>", THEME + "</head>", 1))
