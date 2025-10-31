from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
import models
import schemas
from typing import List, Optional
from datetime import datetime

# Country CRUD operations
def get_countries(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    region: Optional[str] = None,
    currency: Optional[str] = None,
    sort_by: Optional[str] = None
) -> List[models.Country]:
    query = db.query(models.Country)
    
    # Apply filters
    if region:
        query = query.filter(models.Country.region == region)
    if currency:
        query = query.filter(models.Country.currency_code == currency)
    
    # Apply sorting
    if sort_by == "gdp_desc":
        query = query.order_by(desc(models.Country.estimated_gdp))
    elif sort_by == "gdp_asc":
        query = query.order_by(asc(models.Country.estimated_gdp))
    elif sort_by == "population_desc":
        query = query.order_by(desc(models.Country.population))
    elif sort_by == "population_asc":
        query = query.order_by(asc(models.Country.population))
    else:
        query = query.order_by(asc(models.Country.name))
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()

def get_country_by_name(db: Session, name: str) -> Optional[models.Country]:
    return db.query(models.Country).filter(models.Country.name == name).first()

def create_country(db: Session, country: schemas.CountryCreate) -> models.Country:
    db_country = models.Country(**country.dict())
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

def update_country(db: Session, name: str, country_data: dict) -> Optional[models.Country]:
    # Find existing country
    existing_country = get_country_by_name(db, name)
    if not existing_country:
        return None
        
    # Update country
    db.query(models.Country).filter(models.Country.name == name).update(country_data)
    db.commit()
    
    # Return updated country
    return get_country_by_name(db, name)

def delete_country(db: Session, name: str) -> bool:
    country = db.query(models.Country).filter(models.Country.name == name).first()
    if country:
        db.delete(country)
        db.commit()
        return True
    return False

def get_countries_count(db: Session) -> int:
    return db.query(models.Country).count()

def get_latest_refresh_time(db: Session) -> Optional[datetime]:
    country = db.query(models.Country).order_by(desc(models.Country.last_refreshed_at)).first()
    return country.last_refreshed_at if country else None # type: ignore