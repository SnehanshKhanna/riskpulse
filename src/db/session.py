import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use SQLite fallback as requested
# Data is stored in data/interim/riskpulse.db by default
DEFAULT_DB_URL = "sqlite:///./data/interim/riskpulse.db"

# Allows overriding via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# SQLite specifically needs check_same_thread=False for FastAPI + SQLAlchemy
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL, connect_args=connect_args, echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
