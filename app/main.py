from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime, timezone

# Import from current directory - use absolute imports
from database import get_db, engine, Base, test_connection
import models
import schemas
import services
import utils
import crud

# Create database tables
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

app = FastAPI(
    title="Country Currency & Exchange API",
    description="A RESTful API for country data with currency exchange rates and GDP calculations",
    version="1.0.0",
    docs_url="/",
    redoc_url=None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Create cache directory
    os.makedirs("cache", exist_ok=True)
    # Create database tables
    tables_created = create_tables()
    if tables_created:
        print("🚀 Application started successfully")
    else:
        print("⚠️  Application started with database warnings")

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now(timezone.utc),
        "service": "Country Currency & Exchange API"
    }

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
    
    sort_by = sort_mapping.get(sort)
    
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