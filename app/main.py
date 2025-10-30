from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from datetime import datetime
import pytz

from .database import get_db, engine, Base, test_connection
from . import models, schemas, services, utils, crud

# Create database tables
def create_tables():
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Country Currency & Exchange API",
    description="A RESTful API for country data with currency exchange rates and GDP calculations",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    create_tables()
    # Test database connection
    test_connection()

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Country not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Endpoints
@app.post(
    "/countries/refresh",
    response_model=schemas.RefreshResponse,
    status_code=status.HTTP_200_OK
)
def refresh_countries(db: Session = Depends(get_db)):
    """
    Fetch all countries and exchange rates from external APIs, then cache them in the database.
    """
    try:
        # Fetch processed country data from external APIs
        processed_countries = services.external_api_service.get_processed_country_data()
        
        countries_processed = 0
        
        for country_data in processed_countries:
            # Check if country exists
            existing_country = crud.get_country_by_name(db, country_data["name"])
            
            if existing_country:
                # Update existing country
                crud.update_country(db, country_data["name"], country_data)
            else:
                # Create new country
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
            last_refresh=latest_refresh or datetime.now(pytz.UTC)
        )
        
        return {
            "message": "Countries data refreshed successfully",
            "countries_processed": countries_processed,
            "timestamp": datetime.now(pytz.UTC)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "External data source unavailable",
                "details": str(e)
            }
        )

@app.get(
    "/countries",
    response_model=List[schemas.CountryResponse]
)
def get_countries(
    region: Optional[str] = Query(None, description="Filter by region"),
    currency: Optional[str] = Query(None, description="Filter by currency code"),
    sort: Optional[str] = Query(None, description="Sort by gdp_desc, gdp_asc, population_desc, population_asc"),
    db: Session = Depends(get_db)
):
    """
    Get all countries from the database with optional filtering and sorting.
    """
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

@app.get(
    "/countries/{name}",
    response_model=schemas.CountryResponse
)
def get_country(name: str, db: Session = Depends(get_db)):
    """
    Get a specific country by name.
    """
    country = crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(
            status_code=404,
            detail={"error": "Country not found"}
        )
    return country

@app.delete(
    "/countries/{name}",
    status_code=status.HTTP_200_OK
)
def delete_country(name: str, db: Session = Depends(get_db)):
    """
    Delete a country record by name.
    """
    # First check if country exists
    country = crud.get_country_by_name(db, name)
    if not country:
        raise HTTPException(
            status_code=404,
            detail={"error": "Country not found"}
        )
    
    success = crud.delete_country(db, name)
    if not success:
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to delete country"}
        )
    
    return {"message": f"Country {name} deleted successfully"}

@app.get(
    "/status",
    response_model=schemas.StatusResponse
)
def get_status(db: Session = Depends(get_db)):
    """
    Get total countries count and last refresh timestamp.
    """
    total_countries = crud.get_countries_count(db)
    last_refreshed_at = crud.get_latest_refresh_time(db)
    
    return {
        "total_countries": total_countries,
        "last_refreshed_at": last_refreshed_at
    }

@app.get("/countries/image")
def get_countries_image():
    """
    Serve the generated summary image.
    """
    image_path = "cache/summary.png"
    
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=404,
            detail={"error": "Summary image not found"}
        )
    
    return FileResponse(
        image_path,
        media_type="image/png",
        filename="summary.png"
    )

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