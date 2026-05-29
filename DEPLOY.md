# Deploying NCRTC Bus Management System

Architecture once deployed:

```
Vercel (React static)  ──HTTPS──▶  Render (FastAPI)  ──▶  Neon (PostgreSQL + PostGIS)
   your-app.vercel.app             your-api.onrender.com    (already created + seeded)
```

- **Database** is already live and seeded on Neon — nothing to do.
- **Backend** runs on Render (free). The live-map simulator runs *inside* the backend
  (env `RUN_SIMULATOR=true`), so no separate worker is needed.
- **Frontend** is built to static files on Vercel (free).

> Free-tier note: Render free web services **sleep after ~15 min idle**; the first request
> after a nap takes ~30–60s to wake. Fine for a demo, not for production traffic.

---

## 0. Prerequisites
- A **GitHub** account, **Render** account, **Vercel** account (all free).
- Your Neon connection string (the `postgresql://…?sslmode=require` URL).

## 1. Push the code to your own GitHub
This repo was cloned from someone else's GitHub, so point it at a repo you own:

```bash
# from the project root
git remote remove origin            # detach the original remote (ignore error if none)
git add -A
git commit -m "Deploy-ready: full PRD build"
# create an empty repo on github.com first, then:
git remote add origin https://github.com/<your-username>/NCRTC-Bus-Management-System.git
git branch -M main
git push -u origin main
```

> `.env` is git-ignored (your DB password is never pushed). Only `.env.example` is committed.

## 2. Deploy the backend on Render
Easiest is the Blueprint (`render.yaml` is already in the repo):

1. Render dashboard → **New** → **Blueprint** → connect GitHub → pick your repo.
2. Render reads `render.yaml` and creates the **ncrtc-backend** web service.
3. When prompted, fill the two secret env vars:
   - `DATABASE_URL` = your Neon string (`postgresql://…?sslmode=require`)
   - `SECRET_KEY` = any long random string
4. Click **Apply**. First build takes a few minutes.
5. Copy the service URL, e.g. `https://ncrtc-backend.onrender.com`. Open `/docs` to confirm it's up.

(Manual alternative, no Blueprint: New → **Web Service** → root directory `backend`,
build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`,
add the env vars from `render.yaml`.)

> The DB is already seeded, so the backend just connects — no migration/seed step needed.
> To start fresh you could run `python scripts/init_db.py --drop && python scripts/seed.py`
> from a Render shell, but you normally won't.

## 3. Deploy the frontend on Vercel
1. Vercel → **Add New** → **Project** → import your GitHub repo.
2. **Root Directory**: set to `frontend`.
3. Framework preset: **Vite** (auto-detected; `vercel.json` already sets build/output + SPA routing).
4. **Environment Variables** → add:
   - `VITE_API_URL` = your Render backend URL (e.g. `https://ncrtc-backend.onrender.com`)
5. **Deploy**. You'll get `https://<your-app>.vercel.app`.

> `VITE_API_URL` is baked in at build time. If you change the backend URL later, set the
> variable again and **redeploy** the frontend.

## 4. Test
- Open the Vercel URL → log in with a demo account (`admin` / `admin123`).
- Map shows buses; with `RUN_SIMULATOR=true` they move (once the Render service is awake).
- `https://<your-api>.onrender.com/docs` shows the interactive API.

## 5. Optional hardening
- **CORS**: `app/main.py` allows all origins (`*`) for demo convenience. To lock it down,
  replace `allow_origins=["*"]` with your Vercel URL.
- **Custom domain**: both Vercel and Render support free custom domains.
- **Keep-awake**: a free uptime pinger (e.g. cron-job.org hitting `/`) every 10 min keeps
  the Render service from sleeping.
- **One simulator only**: if the backend runs the simulator (`RUN_SIMULATOR=true`), don't
  also run `scripts/tick.py` against the same DB — they'd double-write pings.
