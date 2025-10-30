from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, utils
from app.database import get_db
from datetime import datetime
import os
from PIL import Image, ImageDraw, ImageFont

router = APIRouter()

@router.post("/countries/refresh")
def refresh_countries(db: Session = Depends(get_db)):
    try:
        countries_data = utils.fetch_countries() # type: ignore
        exchange_data = utils.fetch_exchange_rates() # type: ignore
    except Exception as e:
        raise HTTPException(status_code=503, detail={"error": "External data source unavailable", "details": str(e)})

    count = 0
    for c in countries_data:
        name = c.get("name")
        population = c.get("population")
        capital = c.get("capital")
        region = c.get("region")
        flag_url = c.get("flag")
        currency_list = c.get("currencies", [])
        currency_code = currency_list[0]["code"] if currency_list else None
        exchange_rate = exchange_data.get(currency_code) if currency_code in exchange_data else None
        gdp = utils.compute_gdp(population, exchange_rate) if exchange_rate else 0 # type: ignore

        existing = db.query(models.Country).filter(models.Country.name.ilike(name)).first()
        if existing:
            existing.capital = capital
            existing.region = region
            existing.population = population
            existing.currency_code = currency_code # type: ignore
            existing.exchange_rate = exchange_rate # pyright: ignore[reportAttributeAccessIssue]
            existing.estimated_gdp = gdp # type: ignore
            existing.flag_url = flag_url
            existing.last_refreshed_at = datetime.utcnow() # type: ignore
        else:
            db.add(models.Country(
                name=name,
                capital=capital,
                region=region,
                population=population,
                currency_code=currency_code,
                exchange_rate=exchange_rate,
                estimated_gdp=gdp,
                flag_url=flag_url
            ))
        count += 1

    db.commit()

    # Generate image
    os.makedirs("app/cache", exist_ok=True)
    summary_img = Image.new("RGB", (600, 400), color="white")
    draw = ImageDraw.Draw(summary_img)
    draw.text((10, 10), f"Total Countries: {count}", fill="black")
    draw.text((10, 40), f"Last Refresh: {datetime.utcnow()}", fill="black")
    summary_img.save("app/cache/summary.png")

    return {"message": f"{count} countries refreshed successfully"}

@router.get("/countries")
def get_countries(region: str = None, currency: str = None, sort: str = None, db: Session = Depends(get_db)): # type: ignore
    query = db.query(models.Country)
    if region:
        query = query.filter(models.Country.region.ilike(region))
    if currency:
        query = query.filter(models.Country.currency_code.ilike(currency))
    if sort == "gdp_desc":
        query = query.order_by(models.Country.estimated_gdp.desc())

    return query.all()

@router.get("/countries/{name}")
def get_country(name: str, db: Session = Depends(get_db)):
    country = db.query(models.Country).filter(models.Country.name.ilike(name)).first()
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return country

@router.delete("/countries/{name}")
def delete_country(name: str, db: Session = Depends(get_db)):
    country = db.query(models.Country).filter(models.Country.name.ilike(name)).first()
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    db.delete(country)
    db.commit()
    return {"message": f"{name} deleted successfully"}

@router.get("/countries/image")
def get_summary_image():
    image_path = "app/cache/summary.png"
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail={"error": "Summary image not found"})
    from fastapi.responses import FileResponse
    return FileResponse(image_path, media_type="image/png")
