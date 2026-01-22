from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from connection_data import Database

# DEVELOPMENT
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, echo=True)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
base = declarative_base()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()