import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL, preferring Railway's DATABASE_URL"""
    # Priority 1: Use Railway's DATABASE_URL
    railway_db_url = os.getenv("DATABASE_URL")
    if railway_db_url:
        # Convert mysql:// to mysql+pymysql:// for SQLAlchemy
        if railway_db_url.startswith("mysql://"):
            railway_db_url = railway_db_url.replace("mysql://", "mysql+pymysql://", 1)
        return railway_db_url
    
    # Priority 2: Use individual environment variables
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    
    if all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # No database configuration found
    raise ValueError(
        "No database configuration found. "
        "Please set either DATABASE_URL or all individual DB_* environment variables."
    )

# Get the database URL
DATABASE_URL = get_database_url()

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Simple test to verify connection"""
    try:
        with engine.connect() as conn:
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print("❌ Connection failed:", e)
        return False