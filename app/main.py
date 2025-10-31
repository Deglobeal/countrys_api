from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime, timezone

# Import from current directory - use absolute imports
from database import get_db, engine, Base, test_connection # type: ignore
import models
import schemas
import services
import utils
import crud

# Create FastAPI app
app = FastAPI(
    title="Country Currency & Exchange API",
    description="A RESTful API for country data with currency exchange rates and GDP calculations",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Starting Country Currency & Exchange API...")
    
    # Create cache directory
    os.makedirs("cache", exist_ok=True)
    
    # Test database connection
    db_connected = test_connection()
    if db_connected:
        print("✅ Database connected successfully")
        
        # Create tables
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
    else:
        print("❌ Database connection failed")

@app.get("/")
def read_root():
    return {
        "message": "Country Currency & Exchange API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now(timezone.utc)
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1") # type: ignore
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc),
        "service": "Country Currency & Exchange API"
    }

@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    """Test database connection endpoint"""
    try:
        result = db.execute("SELECT 1") # type: ignore
        return {"database": "connected", "test_query": "success"}
    except Exception as e:
        return {"database": "error", "error": str(e)}


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Country Currency & Exchange API",
        "version": "1.0.0",
        "endpoints": {
            "refresh": "POST /countries/refresh",
            "get_countries": "GET /countries",
            "get_country": "GET /countries/{name}", 
            "delete_country": "DELETE /countries/{name}",
            "status": "GET /status",
            "image": "GET /countries/image"
        }
    }

# Refresh countries endpoint
@app.post(
    "/countries/refresh",
    status_code=status.HTTP_200_OK
)
def refresh_countries(db: Session = Depends(get_db)):
    """Fetch all countries and exchange rates from external APIs"""
    try:
        processed_countries = services.external_api_service.get_processed_country_data()
        countries_processed = 0
        
        for country_data in processed_countries:
            existing_country = crud.get_country_by_name(db, country_data["name"])
            
            if existing_country:
                crud.update_country(db, country_data["name"], country_data)
            else:
                crud.create_country(db, schemas.CountryCreate(**country_data))
            
            countries_processed += 1
        
        # Generate summary image
        all_countries = crud.get_countries(db, limit=1000)
        top_countries = sorted(
            [c for c in all_countries if c.estimated_gdp is not None],
            key=lambda x: x.estimated_gdp,
            reverse=True
        )
        
        latest_refresh = crud.get_latest_refresh_time(db)
        
        utils.image_generator.generate_summary_image(
            total_countries=len(all_countries),
            top_countries=[{"name": c.name, "estimated_gdp": c.estimated_gdp} for c in top_countries],
            last_refresh=latest_refresh or datetime.now(timezone.utc)
        )
        
        return {
            "message": "Countries data refreshed successfully",
            "countries_processed": countries_processed,
            "timestamp": datetime.now(timezone.utc)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": str(e)
            }
        )

@app.get("/countries")
def get_countries(
    region: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all countries with filtering and sorting"""
    sort_mapping = {
        "gdp_desc": "gdp_desc",
        "gdp_asc": "gdp_asc", 
        "population_desc": "population_desc",
        "population_asc": "population_asc"
    }
    
    sort_by = sort_mapping.get(sort) # type: ignore
    
    countries = crud.get_countries(
        db, 
        region=region, 
        currency=currency,
        sort_by=sort_by
    )
    
    return countries

@app.get("/countries/{name}")
def get_country(name: str, db: Session = Depends(get_db)):
    """Get specific country by name"""
    country = crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return country

@app.delete("/countries/{name}")
def delete_country(name: str, db: Session = Depends(get_db)):
    """Delete country by name"""
    country = crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    
    success = crud.delete_country(db, name)
    if not success:
        raise HTTPException(status_code=500, detail={"error": "Failed to delete country"})
    
    return {"message": f"Country {name} deleted successfully"}

@app.get("/status")
def get_status(db: Session = Depends(get_db)):
    """Get API status"""
    total_countries = crud.get_countries_count(db)
    last_refreshed_at = crud.get_latest_refresh_time(db)
    
    return {
        "total_countries": total_countries,
        "last_refreshed_at": last_refreshed_at
    }

@app.get("/countries/image")
def get_countries_image():
    """Serve generated summary image"""
    image_path = "cache/summary.png"
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail={"error": "Summary image not found"})
    
    return FileResponse(image_path, media_type="image/png", filename="summary.png")