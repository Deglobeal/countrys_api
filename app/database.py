import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment variables"""
    
    print("=== Checking Database Configuration ===")
    
    # Priority 1: Use Railway's MYSQL_URL
    mysql_url = os.getenv("MYSQL_URL")
    if mysql_url:
        print("✅ Using MYSQL_URL from Railway environment")
        if mysql_url.startswith("mysql://"):
            mysql_url = mysql_url.replace("mysql://", "mysql+pymysql://", 1)
        return mysql_url
    
    # Priority 2: Use individual MySQL variables from Railway
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
    
    # Priority 3: Fallback to local SQLite for testing
    print("⚠️ Using SQLite fallback database")
    return "sqlite:///./test.db"

# Get the database URL
DATABASE_URL = get_database_url()

print(f"🎯 Final DATABASE_URL: {DATABASE_URL}")

# Create engine with connection pooling and timeout settings
engine = create_engine(
    DATABASE_URL, 
    echo=True,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=300,    # Recycle connections after 5 minutes
    connect_args={"connect_timeout": 10}  # 10 second connection timeout
)

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
    """Test database connection"""
    try:
        with engine.connect() as conn:
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False