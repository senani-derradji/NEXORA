from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
# from connection_data import Database

load_dotenv()

# DEVELOPMENT
DATABASE_URL = os.getenv("DEV_DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
base = declarative_base()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()