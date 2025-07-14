#!/usr/bin/env python3

import requests
from datetime import datetime

def validator(time, hours=None):
    if(isinstance(time, str)):
        time = datetime.fromisoformat(time.replace("Z", "+00:00")).astimezone()
    now = datetime.now().replace(minute=0, second=0, microsecond=0).astimezone()

    if hours is None:
        return time >= now
    
    return time in hours

def get_temperature_forecast(hours=None):
    lat, lon = 50.76415, 15.16004
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m"
    resp = requests.get(url)
    data = resp.json()
    # Pole teplot na další hodiny:
    temps = data["hourly"]["temperature_2m"]
    #print(temps[:24])  # Prvních 24 hodin
    return list(filter(lambda h: validator(h[0], hours), zip(data["hourly"]["time"], temps)))

if __name__ == "__main__":
    print(get_temperature_forecast())