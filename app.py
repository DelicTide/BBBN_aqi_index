from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask.views import MethodView
import logging
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Coordinates for Bombay Beach, CA
LATITUDE = 33.3539
LONGITUDE = -115.7339

# API endpoints
NWS_URL = f"https://api.weather.gov/points/{LATITUDE},{LONGITUDE}"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
WAQI_URL = "https://api.waqi.info/feed/geo:"

# Get API key from environment variable
WAQI_API_KEY = os.getenv('WAQI_API_KEY')

async def fetch_nws_data():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(NWS_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    forecast_url = data['properties']['forecast']
                    async with session.get(forecast_url) as forecast_response:
                        if forecast_response.status == 200:
                            forecast_data = await forecast_response.json()
                            current_period = forecast_data['properties']['periods'][0]
                            return {
                                'source': 'National Weather Service',
                                'temperature': current_period['temperature'],
                                'temperatureUnit': current_period['temperatureUnit'],
                                'windSpeed': current_period['windSpeed'],
                                'windDirection': current_period['windDirection'],
                                'shortForecast': current_period['shortForecast']
                            }
        except Exception as e:
            logger.error(f"Error fetching NWS data: {str(e)}")
    return None

async def fetch_open_meteo_data():
    async with aiohttp.ClientSession() as session:
        params = {
            'latitude': LATITUDE,
            'longitude': LONGITUDE,
            'current_weather': 'true',
            'temperature_unit': 'fahrenheit'
        }
        try:
            async with session.get(OPEN_METEO_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'source': 'Open-Meteo',
                        'temperature': data['current_weather']['temperature'],
                        'windspeed': data['current_weather']['windspeed'],
                        'winddirection': data['current_weather']['winddirection']
                    }
        except Exception as e:
            logger.error(f"Error fetching Open-Meteo data: {str(e)}")
    return None

async def fetch_waqi_data():
    async with aiohttp.ClientSession() as session:
        url = f"{WAQI_URL}{LATITUDE};{LONGITUDE}/?token={WAQI_API_KEY}"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == 'ok':
                        return {
                            'source': 'WAQI',
                            'aqi': data['data']['aqi'],
                            'dominant_pollutant': data['data'].get('dominentpol', 'N/A')
                        }
        except Exception as e:
            logger.error(f"Error fetching WAQI data: {str(e)}")
    return None

@app.route('/')
def index():
    return render_template('index.html')

class AirQualityAPI(MethodView):
    async def get(self):
        try:
            nws_data = await fetch_nws_data()
            logger.debug(f"NWS Data: {nws_data}")

            open_meteo_data = await fetch_open_meteo_data()
            logger.debug(f"Open-Meteo Data: {open_meteo_data}")

            waqi_data = await fetch_waqi_data()
            logger.debug(f"WAQI Data: {waqi_data}")

            processed_data = {
                'nws': nws_data,
                'openMeteo': open_meteo_data,
                'waqi': waqi_data,
                'coordinates': {'latitude': LATITUDE, 'longitude': LONGITUDE}
            }
            
            logger.debug(f"Processed data: {processed_data}")
            
            return jsonify(processed_data)
        except Exception as e:
            logger.exception(f"Error in AirQualityAPI.get: {str(e)}")
            return jsonify({'error': 'Unable to fetch data', 'details': str(e)}), 500

app.add_url_rule('/api/airquality', view_func=AirQualityAPI.as_view('airquality'))

if __name__ == '__main__':
    app.run(debug=True)