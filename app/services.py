import requests
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class ExternalAPIService:
    def __init__(self):
        self.countries_api_url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
        self.exchange_api_url = "https://open.er-api.com/v6/latest/USD"
        self.timeout = 30

    def fetch_countries_data(self) -> List[dict]:
        """Fetch country data from RestCountries API"""
        try:
            response = requests.get(self.countries_api_url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch countries data: {e}")
            raise Exception(f"Could not fetch data from RestCountries API: {str(e)}")

    def fetch_exchange_rates(self) -> Dict[str, float]:
        """Fetch exchange rates from Open Exchange Rates API"""
        try:
            response = requests.get(self.exchange_api_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get("result") == "success":
                return data.get("rates", {})
            else:
                raise Exception("Exchange rate API returned unsuccessful result")
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            raise Exception(f"Could not fetch data from Exchange Rates API: {str(e)}")

    def extract_currency_code(self, currencies: List[dict]) -> Optional[str]:
        """Extract currency code from currencies array"""
        if not currencies or len(currencies) == 0:
            return None
        
        # Get the first currency code
        first_currency = currencies[0]
        return first_currency.get("code")

    def calculate_estimated_gdp(self, population: int, exchange_rate: Optional[float]) -> Optional[float]:
        """Calculate estimated GDP using the formula: population × random(1000-2000) ÷ exchange_rate"""
        if not exchange_rate or exchange_rate <= 0:
            return None
            
        random_multiplier = random.uniform(1000, 2000)
        estimated_gdp = (population * random_multiplier) / exchange_rate
        
        # Round to 1 decimal place for consistency
        return round(estimated_gdp, 1)

    def get_processed_country_data(self) -> List[dict]:
        """Fetch and process all country data with exchange rates"""
        try:
            # Fetch data from both APIs
            countries_data = self.fetch_countries_data()
            exchange_rates = self.fetch_exchange_rates()
            
            processed_countries = []
            
            for country in countries_data:
                # Extract currency code
                currency_code = self.extract_currency_code(country.get("currencies", []))
                
                # Get exchange rate
                exchange_rate = None
                if currency_code:
                    exchange_rate = exchange_rates.get(currency_code)
                
                # Calculate estimated GDP
                population = country.get("population", 0)
                estimated_gdp = self.calculate_estimated_gdp(population, exchange_rate)
                
                processed_country = {
                    "name": country.get("name"),
                    "capital": country.get("capital"),
                    "region": country.get("region"),
                    "population": population,
                    "currency_code": currency_code,
                    "exchange_rate": exchange_rate,
                    "estimated_gdp": estimated_gdp,
                    "flag_url": country.get("flag"),
                    "last_refreshed_at": datetime.now(pytz.UTC)
                }
                
                processed_countries.append(processed_country)
            
            return processed_countries
            
        except Exception as e:
            logger.error(f"Error processing country data: {e}")
            raise

# Create global service instance
external_api_service = ExternalAPIService()