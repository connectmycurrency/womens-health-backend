import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL is set as an environment variable on Render, pointing at
# your Postgres/Supabase instance. If it isn't set, this falls back to a
# local SQLite file so you can run and test the backend without any
# external database.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./womens_health.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
