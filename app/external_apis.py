import requests
import random
from typing import Dict, Any, Optional

class ExternalAPIs:
    @staticmethod
    def fetch_countries() -> list:
        """Fetch country data from restcountries API"""
        try:
            response = requests.get(
                "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Could not fetch data from countries API: {str(e)}")

    @staticmethod
    def fetch_exchange_rates() -> Dict[str, float]:
        """Fetch exchange rates from open.er-api.com"""
        try:
            response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("rates", {})
        except requests.exceptions.RequestException as e:
            raise Exception(f"Could not fetch data from exchange rates API: {str(e)}")

    @staticmethod
    def process_country_data(country_data: Dict[str, Any], exchange_rates: Dict[str, float]) -> Dict[str, Any]:
        """Process a single country's data"""
        # Extract currency code
        currency_code = None
        if country_data.get('currencies') and len(country_data['currencies']) > 0:
            currency_code = country_data['currencies'][0].get('code')
        
        exchange_rate = None
        estimated_gdp = None
        
        if currency_code and currency_code in exchange_rates:
            exchange_rate = exchange_rates[currency_code]
            # Generate random multiplier between 1000 and 2000
            random_multiplier = random.uniform(1000, 2000)
            estimated_gdp = (country_data['population'] * random_multiplier) / exchange_rate
        elif currency_code:
            # Currency code exists but not in exchange rates
            exchange_rate = None
            estimated_gdp = None
        else:
            # No currency code
            exchange_rate = None
            estimated_gdp = 0
        
        return {
            'name': country_data['name'],
            'capital': country_data.get('capital'),
            'region': country_data.get('region'),
            'population': country_data['population'],
            'currency_code': currency_code,
            'exchange_rate': exchange_rate,
            'estimated_gdp': estimated_gdp,
            'flag_url': country_data.get('flag')
        }