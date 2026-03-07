from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

base = declarative_base()

engine = None
SessionLocal = None


def init_database(database_url: str):
    global engine, SessionLocal

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )


def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db_tables():
    if engine is None:
        raise RuntimeError("Database not initialized.")
    base.metadata.create_all(bind=engine)