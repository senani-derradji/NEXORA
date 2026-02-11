from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///C:/Users/DERRADJI/Desktop/MM/NEXORA/nexora.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    print(f"Existing tables before init: {existing_tables}")

    base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()

    print(f"Tables after init: {all_tables}")