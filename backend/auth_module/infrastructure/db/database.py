"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from ...core.config import config

# Create database engine with proper connection pooling
engine = create_engine(
    config.database_url,
    pool_size=config.database_pool_size,
    max_overflow=config.database_max_overflow,
    pool_timeout=30,  # Wait time for connection from pool
    pool_recycle=3600,  # Reconnect after 1 hour to prevent stale connections
    pool_pre_ping=True,  # Test connections before using them
    echo=False,  # Set to True for SQL debugging
    connect_args={
        "options": "-c statement_timeout=5000"  # 5 second query timeout
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
