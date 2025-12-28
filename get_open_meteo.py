import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
from datetime import datetime
import pytz
import sqlite3
import toml

with open('config.toml') as cin:
    config = toml.loads(cin.read())


# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": config['location']['latitude'],
    "longitude": config['location']['longitude'],
    "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
    "hourly": ["temperature_2m", "precipitation"],
    "timezone": "Europe/Berlin",
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
    start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
    end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
    freq = pd.Timedelta(seconds = hourly.Interval()),
    inclusive = "left"
)}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["precipitation"] = hourly_precipitation

hourly_dataframe = pd.DataFrame(data = hourly_data)

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
daily_precipitation_sum = daily.Variables(2).ValuesAsNumpy()

daily_data = {"date": pd.date_range(
    start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
    end =  pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
    freq = pd.Timedelta(seconds = daily.Interval()),
    inclusive = "left"
)}

daily_data["temperature_2m_max"] = daily_temperature_2m_max
daily_data["temperature_2m_min"] = daily_temperature_2m_min
daily_data["precipitation_sum"] = daily_precipitation_sum

daily_dataframe = pd.DataFrame(data = daily_data)

cet = pytz.timezone('CET')
hourly_dataframe['date'] = hourly_dataframe['date'].dt.tz_convert(cet)
daily_dataframe['date'] = daily_dataframe['date'].dt.tz_convert(cet)


with sqlite3.connect('weather_display.sqlite') as db:
    hourly_dataframe.to_sql('open_meteo_hourly', db, if_exists='replace', index=False)
    daily_dataframe.to_sql('open_meteo_daily', db, if_exists='replace', index=False)

    db.execute('UPDATE times SET time = ? WHERE item = ?', (datetime.now(cet), 'open_meteo'))