import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Base class for all models
class Base(DeclarativeBase):
    pass

# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=False,          # Set to True to see SQL queries
    future=True          # Use SQLAlchemy 2.0 style
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)
