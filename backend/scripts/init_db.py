"""Create the database schema from the SQLAlchemy models.

This is the reliable, single source of truth for the demo: the schema always
matches app/models. It enables the PostGIS extension, then creates every table.
Run this once on a fresh database before seeding:

    python scripts/init_db.py

In a production setup this would be replaced by versioned Alembic migrations
(see migrations/), but for the seeded demo we create directly from the models.
"""
import sys
from sqlalchemy import text
from app.db.session import engine, Base
import app.models  # noqa: F401  -- registers every model on Base.metadata


def init(drop: bool = False):
    with engine.connect() as conn:
        if drop:
            # Full reset: drop everything in the public schema (handles tables
            # left over from older schema versions), then reinstall PostGIS.
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
            print("Reset public schema.")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    print("Schema created. Tables:", sorted(Base.metadata.tables.keys()))


if __name__ == "__main__":
    init(drop="--drop" in sys.argv)
