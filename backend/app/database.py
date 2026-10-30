from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# The engine is the connection to PostgreSQL.
# pool_pre_ping checks that a connection is alive before using it.
engine = create_engine(settings.database_url, pool_pre_ping=True)

# A session is one "conversation" with the database.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """All database tables will inherit from this class."""


def get_db():
    """Gives each request its own session and always closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()