# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..configs.database import base

TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture()
def db_session():
    base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    base.metadata.drop_all(bind=engine)
