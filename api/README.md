# Question-map API

FastAPI backend for the "AI kérdés-válasz kommentár" button in the right panel. It runs the
[meforshim](../meforshim) pipeline (git submodule) on demand and caches results in `meforshim/out/`.

```
git clone --recurse-submodules <repo>      # or: git submodule update --init
python -m venv venv && venv/bin/pip install -r api/requirements.txt
cp meforshim/.env.example meforshim/.env   # add the LLM keys
cd api && ../venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001
```

Endpoints: `GET/POST /api/map/Genesis.17.17` (status/start), `GET /api/map/Genesis.17.17/html`.
Env: `MAX_PARALLEL_JOBS` (2), `MAX_NEW_PER_DAY` (200), `MEFORSHIM_OUT`, `ALLOWED_ORIGINS` (dev CORS).
The frontend uses `/api` (nginx proxy, see `deploy/`); override with `NEXT_PUBLIC_API_BASE`.

Production: run it with pm2 (`api/ecosystem.config.js`), see the root README.
