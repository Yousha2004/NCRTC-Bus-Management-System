# NCRTC Bus Management System

A production-quality bus management system for the National Capital Region (NCR) fleet, featuring live tracking, scheduling, incident management, and communication modules.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Alembic, PostgreSQL + PostGIS
- **Frontend**: React (Vite), Leaflet, Tailwind CSS
- **Infrastructure**: Docker, Docker Compose
- **Auth**: JWT-based Role-Based Access Control (RBAC)

## Modules
1. **AVLS**: Real-time GPS tracking and live map visualization.
2. **Scheduling**: Bus assignment and route planning.
3. **IMS**: Incident reporting and tracking.
4. **CMS**: Crew messaging and official notices.

## Setup Instructions

### 1. Prerequisites
- Docker & Docker Compose

### 2. Run the System
```bash
docker-compose up --build
```

### 3. Initialize Database & Seed
```bash
# Enter backend container
docker exec -it ncrtc_backend bash

# Run migrations
alembic upgrade head

# Seed dummy data
export PYTHONPATH=$PYTHONPATH:.
python scripts/seed.py

# Start GPS simulation (optional)
python scripts/tick.py
```

## Demo Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Operator | operator1 | op123 |
| Manager | manager1 | mgr123 |
| Driver | driver1 | dr123 |
| Conductor | conductor1 | co123 |

## Local Development (Alternative)
- **Backend**: `uvicorn app.main:app --reload`
- **Frontend**: `npm run dev`
- **Database**: Ensure PostGIS is installed and `DATABASE_URL` is set.
