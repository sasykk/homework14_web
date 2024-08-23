from config import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = config.SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    The get_db function is a context manager that returns the database session.
    It also ensures that the connection to the database is closed after each request.

    :return: A database session
    :doc-author: Trelent
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
