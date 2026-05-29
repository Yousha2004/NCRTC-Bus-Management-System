from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ncrtc_user:ncrtc_password@localhost/ncrtc_db")

# pool_pre_ping handles cloud Postgres (e.g. Neon) dropping idle connections:
# SQLAlchemy checks a connection is alive before using it and reconnects if not.
# executemany_mode='values_plus_batch' makes bulk INSERT/UPDATE use psycopg2's
# execute_values/execute_batch -> far fewer round-trips to a remote DB.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    executemany_mode="values_plus_batch",
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
