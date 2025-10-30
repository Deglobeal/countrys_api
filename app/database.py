import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    
    print("=== Checking Database Configuration ===")
    
    # Priority 1: Use DATABASE_URL (the one you just set)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("✅ Using DATABASE_URL from environment")
        if database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
        return database_url
    
    # Priority 2: Use individual MYSQL environment variables
    # Note: Railway uses MYSQLHOST, MYSQLUSER, MYSQLPASSWORD, MYSQLDATABASE (no underscores)
    mysql_user = os.getenv("MYSQLUSER", "root")
    mysql_password = os.getenv("MYSQLPASSWORD")
    mysql_host = os.getenv("MYSQLHOST")
    mysql_port = os.getenv("MYSQLPORT", "3306")
    mysql_database = os.getenv("MYSQLDATABASE", "railway")
    
    print(f"MYSQLHOST: {mysql_host}")
    print(f"MYSQLUSER: {mysql_user}")
    print(f"MYSQLPASSWORD: {'*' * len(mysql_password) if mysql_password else 'None'}")
    print(f"MYSQLPORT: {mysql_port}")
    print(f"MYSQLDATABASE: {mysql_database}")
    
    if all([mysql_user, mysql_password, mysql_host, mysql_port, mysql_database]):
        db_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        print(f"✅ Using individual MYSQL* variables: {db_url}")
        return db_url
    
    # Priority 3: Try alternative variable names (with underscores)
    mysql_user_alt = os.getenv("MYSQL_USER", "root")
    mysql_password_alt = os.getenv("MYSQL_PASSWORD")
    mysql_host_alt = os.getenv("MYSQL_HOST")
    mysql_port_alt = os.getenv("MYSQL_PORT", "3306")
    mysql_database_alt = os.getenv("MYSQL_DATABASE", "railway")
    
    if all([mysql_user_alt, mysql_password_alt, mysql_host_alt, mysql_port_alt, mysql_database_alt]):
        db_url = f"mysql+pymysql://{mysql_user_alt}:{mysql_password_alt}@{mysql_host_alt}:{mysql_port_alt}/{mysql_database_alt}"
        print(f"✅ Using individual MYSQL_* variables: {db_url}")
        return db_url
    
    # Priority 4: Hardcoded fallback
    print("⚠️ Using hardcoded fallback database URL")
    return "mysql+pymysql://root:RbTPPtfUFcRMPILnOJLVSpOpdGDgUJVc@mysql.railway.internal:3306/railway"

# Get the database URL
DATABASE_URL = get_database_url()

print(f"🎯 Final DATABASE_URL: {DATABASE_URL}")

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