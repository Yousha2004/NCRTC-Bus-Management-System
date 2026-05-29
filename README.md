# NCRTC Bus Management System

A bus fleet management system for the National Capital Region (NCR) feeder network, built as a
final-year capstone (see the Student PRD). Four modules — live tracking, scheduling, incident
management, and notices — over seeded dummy data, with JWT role-based access and depot scoping.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL + PostGIS
- **Frontend**: React (Vite), Leaflet, Tailwind CSS; mobile driver app at `/driver` (PWA)
- **Auth**: JWT + bcrypt, 5 roles, depot-scoped data access
- **Infra**: Docker Compose (full stack), or run locally against any PostGIS database

## Modules
1. **AVLS** — live map (depot filter, speed, click → side panel with driver/route + last-30-min trail) and a trip **History** page (path by vehicle + date).
2. **Scheduling** — admin route CRUD (ordered stops), weekly **roster grid**, assign duties, **publish**, driver duty + **acknowledge**.
3. **IMS** — raise incidents (type/severity), **panic button**, filtered list, **detail page with status timeline** (notes required) and assignment.
4. **CMS** — notices with **audience targeting**, unread → mark-read, **read receipts**.

## Roles & access
`admin`, `control_operator`, `depot_manager`, `driver`, `conductor`.
Admins and control-room operators see **all depots**; depot managers, drivers and conductors are
**scoped to their own depot**. Every API route requires auth; privileged actions require a role.

---

## Setup

### Option A — Docker (matches the PRD)
```bash
docker-compose up --build
docker exec -it ncrtc_backend bash
python scripts/init_db.py      # create schema (enables PostGIS + creates tables)
python scripts/seed.py         # load demo data
python scripts/tick.py         # (optional) animate the live map
```

### Option B — Local, against a PostGIS database (no Docker)
You need a PostgreSQL database with the PostGIS extension. A free cloud Postgres (e.g. Neon,
Supabase) works — just run `CREATE EXTENSION postgis;` once (or `init_db.py` does it for you).

```bash
# 1. Configure env (copy and edit)
cp .env.example .env            # set DATABASE_URL to your PostGIS database
cp .env.example frontend/.env   # VITE_API_URL=http://localhost:8000

# 2. Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # (Windows)  or  source .venv/bin/activate
pip install -r requirements.txt
set PYTHONPATH=.                # (Windows)  or  export PYTHONPATH=.
python scripts/init_db.py       # creates schema (use --drop to reset)
python scripts/seed.py          # loads demo data
uvicorn app.main:app --reload   # API at http://localhost:8000  (docs at /docs)
python scripts/tick.py          # in a second terminal — animates the map

# 3. Frontend
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

> **Schema note:** the schema is created from the SQLAlchemy models via `scripts/init_db.py`
> (`Base.metadata.create_all`). This keeps the demo reproducible. A production deployment would use
> versioned **Alembic** migrations (the `migrations/` harness is wired up for that).

## Demo Credentials
| Role | Username | Password | Scope |
|------|----------|----------|-------|
| Admin | `admin` | `admin123` | all depots |
| Control operator | `operator1` | `op123` | all depots |
| Depot manager | `manager1` | `mgr123` | Sarai Kale Khan depot |
| Driver | `driver1` | `dr123` | Sarai Kale Khan depot |
| Conductor | `conductor1` | `co123` | Sarai Kale Khan depot |

Bulk seeded users (`user2`…`user72`, `manager2`…`manager5`) all use password `password`.

## The demo flow (PRD §8)
1. **Admin** → Scheduling → create a route (pick stops in order).
2. **Depot manager** → Scheduling → see the weekly roster → **Publish** tomorrow's duties.
3. **Driver** (open `/driver` on a narrow window) → see today's duty → **Acknowledge** → open a notice → tap **PANIC** (raises a P1 incident).
4. **Control operator** → AVLS map updating live → IMS → see the new P1 → open it → **assign** it.
5. AVLS → **History** → pick a vehicle + yesterday's date → see the trip path drawn on the map.
6. API docs at **http://localhost:8000/docs**.

A scripted version of this flow lives in `backend/scripts/demo_test.py`.

## Honesty note (what's real vs simulated)
The system shape is real, but the **GPS feed is simulated**: `scripts/tick.py` writes a new ping for
each active bus every few seconds straight to the database. In production this would be a TCP ingest
service feeding a queue feeding a processor. All other data (depots, vehicles, users, routes, duties,
incidents, notices) is **seeded dummy data** for the demo.
