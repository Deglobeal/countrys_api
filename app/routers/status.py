from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Country
from sqlalchemy import func

router = APIRouter()

@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    total = db.query(func.count(Country.id)).scalar()
    last_refresh = db.query(func.max(Country.last_refreshed_at)).scalar()
    return {"total_countries": total, "last_refreshed_at": last_refresh}
