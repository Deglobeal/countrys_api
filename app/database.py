import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from Railway MySQL environment variables"""
    
    # Debug: Print all MYSQL-related environment variables
    print("=== DEBUG: Checking environment variables ===")
    for key, value in os.environ.items():
        if 'MYSQL' in key or 'DATABASE' in key:
            print(f"{key}: {value}")
    
    # Priority 1: Use Railway's MYSQL_URL
    mysql_url = os.getenv("MYSQL_URL")
    print(f"MYSQL_URL found: {mysql_url is not None}")
    if mysql_url:
        # Convert mysql:// to mysql+pymysql:// for SQLAlchemy
        if mysql_url.startswith("mysql://"):
            mysql_url = mysql_url.replace("mysql://", "mysql+pymysql://", 1)
        print(f"Using MYSQL_URL: {mysql_url}")
        return mysql_url
    
    # Priority 2: Use MYSQL_PUBLIC_URL (external connection)
    mysql_public_url = os.getenv("MYSQL_PUBLIC_URL")
    print(f"MYSQL_PUBLIC_URL found: {mysql_public_url is not None}")
    if mysql_public_url:
        if mysql_public_url.startswith("mysql://"):
            mysql_public_url = mysql_public_url.replace("mysql://", "mysql+pymysql://", 1)
        print(f"Using MYSQL_PUBLIC_URL: {mysql_public_url}")
        return mysql_public_url
    
    # Priority 3: Use individual MYSQL* environment variables
    MYSQL_USER = os.getenv("MYSQLUSER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQLPASSWORD")
    MYSQL_HOST = os.getenv("MYSQLHOST")
    MYSQL_PORT = os.getenv("MYSQLPORT", "3306")
    MYSQL_DATABASE = os.getenv("MYSQLDATABASE", "railway")
    
    print(f"MYSQL_USER: {MYSQL_USER}")
    print(f"MYSQL_PASSWORD: {'*' * len(MYSQL_PASSWORD) if MYSQL_PASSWORD else 'None'}")
    print(f"MYSQL_HOST: {MYSQL_HOST}")
    print(f"MYSQL_PORT: {MYSQL_PORT}")
    print(f"MYSQL_DATABASE: {MYSQL_DATABASE}")
    
    if all([MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE]):
        db_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        print(f"Using individual MYSQL* variables: {db_url}")
        return db_url
    
    # Priority 4: Fallback to original DATABASE_URL or DB_* variables
    railway_db_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL found: {railway_db_url is not None}")
    if railway_db_url:
        if railway_db_url.startswith("mysql://"):
            railway_db_url = railway_db_url.replace("mysql://", "mysql+pymysql://", 1)
        print(f"Using DATABASE_URL: {railway_db_url}")
        return railway_db_url
    
    # Priority 5: Use individual DB_* environment variables
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    
    print(f"DB_USER: {DB_USER}")
    print(f"DB_PASSWORD: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'None'}")
    print(f"DB_HOST: {DB_HOST}")
    print(f"DB_PORT: {DB_PORT}")
    print(f"DB_NAME: {DB_NAME}")
    
    if all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        db_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        print(f"Using individual DB_* variables: {db_url}")
        return db_url
    
    # No database configuration found
    print("=== ERROR: No database configuration found ===")
    raise ValueError(
        "No database configuration found. "
        "Please set MYSQL_URL, DATABASE_URL, or all individual MYSQL* environment variables."
    )

# Get the database URL
try:
    DATABASE_URL = get_database_url()
    print(f"✅ Final DATABASE_URL: {DATABASE_URL}")
except Exception as e:
    print(f"❌ Error getting DATABASE_URL: {e}")
    raise

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