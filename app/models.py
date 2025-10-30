from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime
import pytz
from .database import Base

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    capital = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True, index=True)
    population = Column(Integer, nullable=False)
    currency_code = Column(String(10), nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(Text, nullable=True)
    last_refreshed_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC))
    
    def __repr__(self):
        return f"<Country {self.name}>"